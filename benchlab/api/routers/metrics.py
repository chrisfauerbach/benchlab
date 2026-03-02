"""Metrics and leaderboard endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from benchlab.api.dependencies import get_storage

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/leaderboard")
async def get_leaderboard(
    dimension: str | None = Query(None),
) -> dict[str, Any]:
    storage = get_storage()
    rankings = await storage.get_leaderboard(dimension=dimension)

    formatted = []
    for bucket in rankings:
        formatted.append({
            "model": bucket["key"],
            "avg_score": bucket["avg_score"]["value"],
            "avg_ttft_ms": bucket.get("avg_ttft", {}).get("value"),
            "avg_tokens_per_sec": bucket.get("avg_tokens_per_sec", {}).get("value"),
        })

    return {"rankings": formatted, "dimension": dimension}


@router.get("/distribution")
async def get_distribution(
    field: str = Query(..., description="Metric field path, e.g. metrics.ttft_ms"),
    batch_id: str | None = Query(None),
) -> dict[str, Any]:
    storage = get_storage()
    data = await storage.get_metrics_distribution(field, batch_id=batch_id)
    return {"field": field, "data": data}


@router.get("/timeline")
async def get_timeline(
    field: str = Query(..., description="Metric field path"),
    interval: str = Query("1d"),
) -> dict[str, Any]:
    storage = get_storage()
    data = await storage.get_metrics_timeline(field, interval=interval)
    return {"field": field, "interval": interval, "data": data}


@router.get("/aggregations")
async def get_aggregations(
    batch_id: str | None = Query(None),
) -> dict[str, Any]:
    storage = get_storage()
    stats = await storage.get_model_stats()
    return {"aggregations": stats}
