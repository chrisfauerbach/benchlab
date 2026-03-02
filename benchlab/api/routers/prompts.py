"""Prompt-related endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from benchlab.api.dependencies import get_storage

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("")
async def list_prompts(
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    storage = get_storage()

    # Get distinct prompts from results
    query: dict[str, Any] = {"term": {"doc_type": "result"}}
    if category:
        query = {
            "bool": {
                "must": [
                    {"term": {"doc_type": "result"}},
                    {"term": {"prompt.category": category}},
                ]
            }
        }

    resp = await storage._client.search(
        index=storage._index,
        body={
            "query": query,
            "size": 0,
            "aggs": {
                "by_prompt": {
                    "terms": {"field": "prompt.id", "size": limit},
                    "aggs": {
                        "info": {
                            "top_hits": {
                                "size": 1,
                                "_source": ["prompt"],
                            }
                        },
                        "avg_score": {
                            "avg": {
                                "field": "evaluation_summary.composite_score"
                            }
                        },
                    },
                }
            },
        },
    )

    prompts = []
    for bucket in resp["aggregations"]["by_prompt"]["buckets"]:
        hit = bucket["info"]["hits"]["hits"][0]["_source"]["prompt"]
        hit["result_count"] = bucket["doc_count"]
        hit["avg_composite_score"] = bucket["avg_score"]["value"]
        prompts.append(hit)

    categories = await storage.get_prompt_categories()
    return {"prompts": prompts, "categories": categories}


@router.get("/{prompt_id}/results")
async def get_prompt_results(
    prompt_id: str,
    limit: int = Query(500, ge=1, le=5000),
) -> dict[str, Any]:
    storage = get_storage()
    results = await storage.get_prompt_results(prompt_id, size=limit)
    return {"results": results, "total": len(results)}


@router.get("/categories")
async def list_categories() -> dict[str, Any]:
    storage = get_storage()
    categories = await storage.get_prompt_categories()
    return {"categories": categories}
