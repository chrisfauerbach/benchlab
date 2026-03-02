"""Model-related endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel

from benchlab.api.dependencies import get_ollama, get_storage

router = APIRouter(prefix="/models", tags=["models"])

# In-memory pull status tracking
_pull_status: dict[str, dict[str, str]] = {}


class PullRequest(BaseModel):
    name: str


@router.get("")
async def list_models() -> dict[str, Any]:
    storage = get_storage()
    models = await storage.get_available_models()
    return {"models": models}


@router.get("/stats")
async def get_model_stats(
    model: str | None = Query(None),
) -> dict[str, Any]:
    storage = get_storage()
    stats = await storage.get_model_stats(model_name=model)
    return {"stats": stats}


@router.get("/compare")
async def compare_models(
    models: str = Query(..., description="Comma-separated model names"),
    batch_id: str | None = Query(None),
) -> dict[str, Any]:
    model_list = [m.strip() for m in models.split(",")]
    storage = get_storage()
    comparison = {}
    for model_name in model_list:
        stats = await storage.get_model_stats(model_name=model_name)
        comparison[model_name] = stats
    return {"comparison": comparison}


@router.get("/available")
async def list_available_ollama_models() -> dict[str, Any]:
    ollama = get_ollama()
    try:
        models = await ollama.list_models()
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


async def _do_pull(name: str) -> None:
    """Background task to pull a model from Ollama."""
    _pull_status[name] = {"status": "pulling"}
    try:
        ollama = get_ollama()
        await ollama.pull_model(name)
        _pull_status[name] = {"status": "done"}
    except Exception as e:
        _pull_status[name] = {"status": "error", "error": str(e)}


@router.post("/pull")
async def pull_model(req: PullRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    _pull_status[req.name] = {"status": "pending"}
    background_tasks.add_task(_do_pull, req.name)
    return {"status": "pending", "name": req.name}


@router.get("/pull/{name:path}/status")
async def pull_model_status(name: str) -> dict[str, str]:
    entry = _pull_status.get(name)
    if entry is None:
        return {"status": "unknown"}
    return entry


@router.delete("/{name:path}")
async def delete_model(name: str) -> dict[str, str]:
    ollama = get_ollama()
    await ollama.delete_model(name)
    return {"status": "deleted", "name": name}
