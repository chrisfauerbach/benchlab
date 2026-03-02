"""Run management endpoints - start/status/cancel batch runs."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from benchlab.api.dependencies import get_config, get_ollama, get_storage
from benchlab.api.schemas.requests import RunRequest
from benchlab.config import TargetModel, load_config
from benchlab.prompts.loader import load_prompts_from_directory
from benchlab.runner.batch import BatchRunner
from benchlab.runner.ollama_client import OllamaClient
from benchlab.storage.elasticsearch import ElasticsearchStorage

router = APIRouter(prefix="/runs", tags=["runs"])

# Track active runs
_active_runs: dict[str, dict[str, Any]] = {}


async def _execute_run(batch_id: str, request: RunRequest) -> None:
    """Background task to execute a batch run."""
    _active_runs[batch_id] = {"status": "running", "batch_id": batch_id}
    try:
        config = load_config(request.config_path)

        if request.target_models:
            config.target_models = [
                TargetModel(name=m) for m in request.target_models
            ]
        if request.evaluation_enabled is not None:
            config.evaluation.enabled = request.evaluation_enabled

        prompts = load_prompts_from_directory(request.prompts_dir)
        ollama = OllamaClient(config.ollama)
        storage = ElasticsearchStorage(config.elasticsearch)
        runner = BatchRunner(config, ollama, storage)

        try:
            await runner.run(prompts, batch_id=batch_id)
            _active_runs[batch_id]["status"] = "completed"
        finally:
            await ollama.close()
            await storage.close()

    except Exception as e:
        _active_runs[batch_id]["status"] = "failed"
        _active_runs[batch_id]["error"] = str(e)


@router.post("")
async def start_run(
    request: RunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    batch_id = request.batch_id or uuid.uuid4().hex[:12]

    if batch_id in _active_runs and _active_runs[batch_id]["status"] == "running":
        raise HTTPException(409, f"Batch {batch_id} is already running")

    background_tasks.add_task(_execute_run, batch_id, request)
    _active_runs[batch_id] = {"status": "starting", "batch_id": batch_id}

    return {"batch_id": batch_id, "status": "starting", "message": "Batch run started"}


@router.get("/{batch_id}")
async def get_run_status(batch_id: str) -> dict[str, Any]:
    if batch_id in _active_runs:
        return _active_runs[batch_id]
    # Check ES for completed runs
    storage = get_storage()
    summary = await storage.get_batch_summary(batch_id)
    if summary:
        return {"batch_id": batch_id, "status": summary.get("status", "completed")}
    raise HTTPException(404, f"Run {batch_id} not found")


@router.post("/{batch_id}/cancel")
async def cancel_run(batch_id: str) -> dict[str, Any]:
    if batch_id not in _active_runs:
        raise HTTPException(404, f"Run {batch_id} not found")
    if _active_runs[batch_id]["status"] != "running":
        raise HTTPException(400, f"Run {batch_id} is not running")

    _active_runs[batch_id]["status"] = "cancelling"
    return {"batch_id": batch_id, "status": "cancelling"}
