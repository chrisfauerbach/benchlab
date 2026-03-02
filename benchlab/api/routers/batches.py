"""Batch management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from benchlab.api.dependencies import get_storage

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("")
async def list_batches(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    storage = get_storage()
    batches = await storage.list_batches(size=limit, offset=offset)
    return {"batches": batches, "total": len(batches)}


@router.get("/{batch_id}")
async def get_batch(batch_id: str) -> dict[str, Any]:
    storage = get_storage()
    summary = await storage.get_batch_summary(batch_id)
    if not summary:
        raise HTTPException(404, f"Batch {batch_id} not found")
    return summary


@router.get("/{batch_id}/results")
async def get_batch_results(
    batch_id: str,
    model: str | None = Query(None),
    prompt_id: str | None = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
) -> dict[str, Any]:
    storage = get_storage()
    results = await storage.get_batch_results(
        batch_id, size=limit, model_name=model, prompt_id=prompt_id
    )
    return {"results": results, "total": len(results)}


@router.get("/{batch_id}/compare")
async def compare_models_in_batch(batch_id: str) -> dict[str, Any]:
    storage = get_storage()
    results = await storage.get_batch_results(batch_id)
    if not results:
        raise HTTPException(404, f"No results for batch {batch_id}")

    by_model: dict[str, list] = {}
    for r in results:
        model_name = r["model"]["name"]
        by_model.setdefault(model_name, []).append(r)

    comparison = {}
    for model_name, model_results in by_model.items():
        successful = [r for r in model_results if r["success"]]
        metrics_vals = [r.get("metrics", {}) for r in successful]
        eval_scores = [
            r.get("evaluation_summary", {})
            for r in successful
            if r.get("evaluation_summary")
        ]

        avg_tps = None
        tps_vals = [m.get("output_tokens_per_sec") for m in metrics_vals if m.get("output_tokens_per_sec")]
        if tps_vals:
            avg_tps = sum(tps_vals) / len(tps_vals)

        avg_gen = None
        gen_vals = [m.get("total_generation_ms") for m in metrics_vals if m.get("total_generation_ms")]
        if gen_vals:
            avg_gen = sum(gen_vals) / len(gen_vals)

        avg_composite = None
        composite_vals = [e.get("composite_score") for e in eval_scores if e.get("composite_score")]
        if composite_vals:
            avg_composite = sum(composite_vals) / len(composite_vals)

        comparison[model_name] = {
            "display_name": model_results[0]["model"]["display_name"],
            "total": len(model_results),
            "successful": len(successful),
            "avg_output_tokens_per_sec": avg_tps,
            "avg_total_generation_ms": avg_gen,
            "avg_composite_score": avg_composite,
        }

    return {"batch_id": batch_id, "models": comparison}


@router.delete("/{batch_id}")
async def delete_batch(batch_id: str) -> dict[str, Any]:
    storage = get_storage()
    deleted = await storage.delete_batch(batch_id)
    return {"batch_id": batch_id, "deleted": deleted}
