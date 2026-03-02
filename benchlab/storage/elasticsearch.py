"""Async Elasticsearch client for BenchLab."""

from __future__ import annotations

from typing import Any

from elasticsearch import AsyncElasticsearch

from benchlab.config import ElasticsearchConfig
from benchlab.models import BatchSummary, ResultDocument
from benchlab.storage.mappings import INDEX_MAPPING


class ElasticsearchStorage:
    """Manages all Elasticsearch interactions for BenchLab."""

    def __init__(self, config: ElasticsearchConfig | None = None) -> None:
        self.config = config or ElasticsearchConfig()
        kwargs: dict[str, Any] = {"hosts": self.config.hosts}
        if self.config.username and self.config.password:
            kwargs["basic_auth"] = (self.config.username, self.config.password)
        self._client = AsyncElasticsearch(**kwargs)
        self._index = self.config.index_name

    async def close(self) -> None:
        await self._client.close()

    async def ensure_index(self) -> None:
        """Create the index if it doesn't exist."""
        exists = await self._client.indices.exists(index=self._index)
        if not exists:
            await self._client.indices.create(
                index=self._index, body=INDEX_MAPPING
            )

    # ── Result CRUD ──────────────────────────────────────────────

    async def index_result(self, result: ResultDocument) -> str:
        """Index a single result document. Returns the ES doc ID."""
        resp = await self._client.index(
            index=self._index,
            id=result.result_id,
            document=result.model_dump(mode="json"),
        )
        return resp["_id"]

    async def bulk_index_results(self, results: list[ResultDocument]) -> int:
        """Bulk-index result documents. Returns count of indexed docs."""
        if not results:
            return 0
        from elasticsearch.helpers import async_bulk

        actions = [
            {
                "_index": self._index,
                "_id": r.result_id,
                "_source": r.model_dump(mode="json"),
            }
            for r in results
        ]
        success, _ = await async_bulk(self._client, actions)
        return success

    async def get_result(self, result_id: str) -> dict[str, Any] | None:
        """Fetch a single result by ID."""
        try:
            resp = await self._client.get(index=self._index, id=result_id)
            return resp["_source"]
        except Exception:
            return None

    async def update_result(
        self, result_id: str, doc: dict[str, Any]
    ) -> None:
        """Partial update of a result document."""
        await self._client.update(
            index=self._index, id=result_id, doc=doc
        )

    async def delete_result(self, result_id: str) -> None:
        """Delete a single result."""
        await self._client.delete(index=self._index, id=result_id)

    # ── Batch Summary ────────────────────────────────────────────

    async def index_batch_summary(self, summary: BatchSummary) -> str:
        """Index a batch summary document."""
        doc_id = f"batch-{summary.batch_id}"
        resp = await self._client.index(
            index=self._index,
            id=doc_id,
            document=summary.model_dump(mode="json"),
        )
        return resp["_id"]

    # ── Queries ──────────────────────────────────────────────────

    async def list_batches(
        self, size: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List batch summaries, newest first."""
        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"term": {"doc_type": "batch_summary"}},
                "sort": [{"timestamp": "desc"}],
                "from": offset,
                "size": size,
            },
        )
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    async def get_batch_summary(
        self, batch_id: str
    ) -> dict[str, Any] | None:
        """Fetch a single batch summary."""
        try:
            resp = await self._client.get(
                index=self._index, id=f"batch-{batch_id}"
            )
            return resp["_source"]
        except Exception:
            return None

    async def get_batch_results(
        self,
        batch_id: str,
        size: int = 1000,
        model_name: str | None = None,
        prompt_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all results for a batch."""
        must = [
            {"term": {"doc_type": "result"}},
            {"term": {"batch_id": batch_id}},
        ]
        if model_name:
            must.append({"term": {"model.name": model_name}})
        if prompt_id:
            must.append({"term": {"prompt.id": prompt_id}})

        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"bool": {"must": must}},
                "sort": [{"timestamp": "asc"}],
                "size": size,
            },
        )
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    async def delete_batch(self, batch_id: str) -> int:
        """Delete all documents for a batch. Returns deleted count."""
        resp = await self._client.delete_by_query(
            index=self._index,
            body={"query": {"term": {"batch_id": batch_id}}},
        )
        return resp.get("deleted", 0)

    async def get_model_stats(
        self, model_name: str | None = None, size: int = 100
    ) -> dict[str, Any]:
        """Aggregate metrics per model across all batches."""
        query: dict[str, Any] = {"term": {"doc_type": "result"}}
        if model_name:
            query = {
                "bool": {
                    "must": [
                        {"term": {"doc_type": "result"}},
                        {"term": {"model.name": model_name}},
                    ]
                }
            }

        resp = await self._client.search(
            index=self._index,
            body={
                "query": query,
                "size": 0,
                "aggs": {
                    "by_model": {
                        "terms": {"field": "model.name", "size": size},
                        "aggs": {
                            "avg_ttft": {"avg": {"field": "metrics.ttft_ms"}},
                            "avg_generation": {
                                "avg": {
                                    "field": "metrics.total_generation_ms"
                                }
                            },
                            "avg_tokens_per_sec": {
                                "avg": {
                                    "field": "metrics.output_tokens_per_sec"
                                }
                            },
                            "avg_composite": {
                                "avg": {
                                    "field": "evaluation_summary.composite_score"
                                }
                            },
                            "total": {"value_count": {"field": "result_id"}},
                        },
                    }
                },
            },
        )
        return resp["aggregations"]["by_model"]

    async def get_leaderboard(self, dimension: str | None = None) -> list[dict[str, Any]]:
        """Get model leaderboard based on composite or specific dimension scores."""
        sort_field = (
            "evaluation_summary.composite_score"
            if not dimension
            else f"evaluation_summary.mean_scores.{dimension}"
        )
        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"term": {"doc_type": "result"}},
                "size": 0,
                "aggs": {
                    "by_model": {
                        "terms": {"field": "model.name", "size": 50},
                        "aggs": {
                            "avg_score": {"avg": {"field": sort_field}},
                            "avg_ttft": {"avg": {"field": "metrics.ttft_ms"}},
                            "avg_tokens_per_sec": {
                                "avg": {
                                    "field": "metrics.output_tokens_per_sec"
                                }
                            },
                        },
                    }
                },
            },
        )
        buckets = resp["aggregations"]["by_model"]["buckets"]
        return sorted(
            buckets,
            key=lambda b: b["avg_score"]["value"] or 0,
            reverse=True,
        )

    async def get_metrics_distribution(
        self, field: str, batch_id: str | None = None
    ) -> dict[str, Any]:
        """Get percentile distribution for a metric field."""
        must: list[dict] = [{"term": {"doc_type": "result"}}]
        if batch_id:
            must.append({"term": {"batch_id": batch_id}})

        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"bool": {"must": must}},
                "size": 0,
                "aggs": {
                    "by_model": {
                        "terms": {"field": "model.name", "size": 50},
                        "aggs": {
                            "percentiles": {
                                "percentiles": {"field": field}
                            },
                            "stats": {"extended_stats": {"field": field}},
                        },
                    }
                },
            },
        )
        return resp["aggregations"]["by_model"]

    async def get_metrics_timeline(
        self, field: str, interval: str = "1d"
    ) -> dict[str, Any]:
        """Get metric values over time."""
        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"term": {"doc_type": "result"}},
                "size": 0,
                "aggs": {
                    "over_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": interval,
                        },
                        "aggs": {
                            "by_model": {
                                "terms": {
                                    "field": "model.name",
                                    "size": 50,
                                },
                                "aggs": {
                                    "avg_value": {"avg": {"field": field}}
                                },
                            }
                        },
                    }
                },
            },
        )
        return resp["aggregations"]["over_time"]

    async def get_prompt_results(
        self, prompt_id: str, size: int = 500
    ) -> list[dict[str, Any]]:
        """Get all results for a specific prompt across batches."""
        resp = await self._client.search(
            index=self._index,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"doc_type": "result"}},
                            {"term": {"prompt.id": prompt_id}},
                        ]
                    }
                },
                "sort": [{"timestamp": "desc"}],
                "size": size,
            },
        )
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    async def get_prompt_categories(self) -> list[str]:
        """Get distinct prompt categories."""
        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"term": {"doc_type": "result"}},
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {"field": "prompt.category", "size": 100}
                    }
                },
            },
        )
        return [
            b["key"]
            for b in resp["aggregations"]["categories"]["buckets"]
        ]

    async def get_available_models(self) -> list[str]:
        """Get distinct model names that have results."""
        resp = await self._client.search(
            index=self._index,
            body={
                "query": {"term": {"doc_type": "result"}},
                "size": 0,
                "aggs": {
                    "models": {
                        "terms": {"field": "model.name", "size": 100}
                    }
                },
            },
        )
        return [
            b["key"]
            for b in resp["aggregations"]["models"]["buckets"]
        ]
