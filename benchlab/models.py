"""Shared data models for results, evaluations, and batch summaries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ExecutionMetrics(BaseModel):
    """Performance and token metrics from a single LLM execution."""

    # Performance timing (ms)
    ttft_ms: float | None = None
    total_generation_ms: float | None = None
    model_load_ms: float | None = None
    prompt_eval_ms: float | None = None
    eval_ms: float | None = None

    # Throughput
    output_tokens_per_sec: float | None = None
    prompt_tokens_per_sec: float | None = None

    # Token counts
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    # Response characteristics
    char_count: int | None = None
    word_count: int | None = None
    sentence_count: int | None = None


class EvaluationScore(BaseModel):
    """Scores from a single evaluator for a single result."""

    evaluator_model: str
    scores: dict[str, float] = Field(default_factory=dict)
    custom_scores: dict[str, float] = Field(default_factory=dict)
    reasoning: str | None = None
    eval_metrics: ExecutionMetrics | None = None


class EvaluationSummary(BaseModel):
    """Aggregated evaluation across all evaluators for a single result."""

    mean_scores: dict[str, float] = Field(default_factory=dict)
    median_scores: dict[str, float] = Field(default_factory=dict)
    std_scores: dict[str, float] = Field(default_factory=dict)
    composite_score: float | None = None
    weighted_composite_score: float | None = None
    krippendorff_alpha: dict[str, float] = Field(default_factory=dict)
    score_ranges: dict[str, list[float]] = Field(default_factory=dict)
    evaluator_count: int = 0


class PromptInfo(BaseModel):
    """Prompt metadata stored with each result."""

    id: str
    name: str
    category: str
    input_text: str
    system_prompt: str | None = None
    expected_output: str | None = None
    tags: list[str] = Field(default_factory=list)
    difficulty: str = "medium"


class ModelInfo(BaseModel):
    """Model metadata stored with each result."""

    name: str
    display_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ResultDocument(BaseModel):
    """A single prompt execution result stored in Elasticsearch."""

    doc_type: Literal["result"] = "result"
    batch_id: str
    result_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    repetition: int = 1

    prompt: PromptInfo
    model: ModelInfo
    output: str = ""
    error: str | None = None
    success: bool = True

    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    evaluations: list[EvaluationScore] = Field(default_factory=list)
    evaluation_summary: EvaluationSummary | None = None


class ModelRanking(BaseModel):
    """Per-model ranking within a batch."""

    model_name: str
    display_name: str
    composite_score: float | None = None
    weighted_composite_score: float | None = None
    mean_scores: dict[str, float] = Field(default_factory=dict)
    total_executions: int = 0
    successful_executions: int = 0
    avg_output_tokens_per_sec: float | None = None
    avg_total_generation_ms: float | None = None


class BatchSummary(BaseModel):
    """Summary document for a completed batch stored in Elasticsearch."""

    doc_type: Literal["batch_summary"] = "batch_summary"
    batch_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "completed"

    total_prompts: int = 0
    total_models: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    batch_duration_seconds: float | None = None

    model_rankings: list[ModelRanking] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    prompt_categories: list[str] = Field(default_factory=list)
    tags_used: list[str] = Field(default_factory=list)
