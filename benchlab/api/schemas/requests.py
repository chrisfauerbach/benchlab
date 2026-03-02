"""Request schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    prompts_dir: str = "prompts/examples"
    batch_id: str | None = None
    config_path: str | None = None
    target_models: list[str] | None = None
    evaluation_enabled: bool | None = None


class CompareModelsRequest(BaseModel):
    model_names: list[str] = Field(..., min_length=2)
    batch_id: str | None = None
