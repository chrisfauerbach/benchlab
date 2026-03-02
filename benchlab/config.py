"""Configuration loading and validation via Pydantic models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    timeout: int = 300
    max_retries: int = 3
    concurrent_requests: int = 2


class ElasticsearchConfig(BaseModel):
    hosts: list[str] = ["http://localhost:9200"]
    index_name: str = "benchlab-results"
    username: str | None = None
    password: str | None = None


class TargetModel(BaseModel):
    name: str
    display_name: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

    @property
    def label(self) -> str:
        return self.display_name or self.name


class ScoringDimension(BaseModel):
    name: str
    weight: float = 1.0
    description: str = ""


class EvaluationConfig(BaseModel):
    enabled: bool = True
    evaluator_models: list[str] = Field(default_factory=lambda: ["llama3.2:3b"])
    scoring_dimensions: list[ScoringDimension] = Field(
        default_factory=lambda: [
            ScoringDimension(name="coherence", weight=1.0, description="Logical flow and consistency"),
            ScoringDimension(name="accuracy", weight=1.5, description="Factual correctness"),
            ScoringDimension(name="relevance", weight=1.0, description="Addresses the prompt directly"),
            ScoringDimension(name="completeness", weight=1.0, description="Covers all aspects of the prompt"),
            ScoringDimension(name="conciseness", weight=0.8, description="Avoids unnecessary verbosity"),
            ScoringDimension(name="helpfulness", weight=1.2, description="Practically useful to the user"),
        ]
    )
    score_min: int = 1
    score_max: int = 10
    require_reasoning: bool = True


class RunConfig(BaseModel):
    default_max_tokens: int = 2048
    default_temperature: float = 0.7
    warmup_runs: int = 0
    repetitions: int = 1
    pull_models_on_start: bool = True


class BenchLabConfig(BaseModel):
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    elasticsearch: ElasticsearchConfig = Field(default_factory=ElasticsearchConfig)
    target_models: list[TargetModel] = Field(
        default_factory=lambda: [TargetModel(name="llama3.2:3b")]
    )
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    run: RunConfig = Field(default_factory=RunConfig)


def load_config(path: str | Path | None = None) -> BenchLabConfig:
    """Load configuration from a YAML file, falling back to defaults.

    Environment variable overrides (used in Docker):
      OLLAMA_BASE_URL  → ollama.base_url
      ES_HOSTS         → elasticsearch.hosts (comma-separated)
      ES_USERNAME      → elasticsearch.username
      ES_PASSWORD      → elasticsearch.password
    """
    import os

    candidates = [
        Path(path) if path else None,
        Path("config/benchlab.yaml"),
        Path("benchlab.yaml"),
        Path.home() / ".config" / "benchlab" / "benchlab.yaml",
    ]
    config: BenchLabConfig | None = None
    for candidate in candidates:
        if candidate and candidate.is_file():
            with open(candidate) as f:
                data = yaml.safe_load(f) or {}
            config = BenchLabConfig(**data)
            break

    if config is None:
        config = BenchLabConfig()

    # Apply environment variable overrides
    if url := os.environ.get("OLLAMA_BASE_URL"):
        config.ollama.base_url = url
    if hosts := os.environ.get("ES_HOSTS"):
        config.elasticsearch.hosts = [h.strip() for h in hosts.split(",")]
    if user := os.environ.get("ES_USERNAME"):
        config.elasticsearch.username = user
    if pw := os.environ.get("ES_PASSWORD"):
        config.elasticsearch.password = pw

    return config
