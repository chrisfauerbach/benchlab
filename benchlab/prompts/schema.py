"""Pydantic models for prompt JSON files."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationCriterion(BaseModel):
    dimension: str
    weight: float = 1.0
    description: str = ""


class Prompt(BaseModel):
    id: str
    name: str
    category: str = "general"
    input_text: str
    system_prompt: str | None = None
    expected_output: str | None = None
    evaluation_criteria: list[EvaluationCriterion] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: str = "medium"
    max_tokens: int | None = None
    temperature: float | None = None


class PromptFile(BaseModel):
    schema_version: str = "1.0"
    prompts: list[Prompt]
