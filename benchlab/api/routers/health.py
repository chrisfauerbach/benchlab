"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from benchlab import __version__
from benchlab.api.dependencies import get_ollama, get_storage

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    es_status = "unknown"
    ollama_status = "unknown"

    try:
        storage = get_storage()
        info = await storage._client.info()
        es_status = "connected"
    except Exception:
        es_status = "disconnected"

    try:
        ollama = get_ollama()
        models = await ollama.list_models()
        ollama_status = "connected"
    except Exception:
        ollama_status = "disconnected"

    return {
        "status": "ok",
        "version": __version__,
        "elasticsearch": es_status,
        "ollama": ollama_status,
    }
