"""Response schemas for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    elasticsearch: str = "unknown"
    ollama: str = "unknown"


class BatchListResponse(BaseModel):
    batches: list[dict[str, Any]]
    total: int


class BatchDetailResponse(BaseModel):
    summary: dict[str, Any]
    results: list[dict[str, Any]]


class RunStatusResponse(BaseModel):
    batch_id: str
    status: str
    message: str = ""


class ModelStatsResponse(BaseModel):
    models: list[dict[str, Any]]


class LeaderboardResponse(BaseModel):
    rankings: list[dict[str, Any]]
    dimension: str | None = None


class MetricsDistributionResponse(BaseModel):
    field: str
    data: dict[str, Any]


class PromptListResponse(BaseModel):
    prompts: list[dict[str, Any]]
    categories: list[str]
