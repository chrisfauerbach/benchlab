"""Metric calculation from raw Ollama response data."""

from __future__ import annotations

import re

from benchlab.models import ExecutionMetrics
from benchlab.runner.ollama_client import OllamaResponse


class MetricsCalculator:
    """Calculate execution metrics from an Ollama response."""

    @staticmethod
    def from_response(response: OllamaResponse) -> ExecutionMetrics:
        content = response.content

        # Nano to ms conversion
        ns_to_ms = 1_000_000

        model_load_ms = (
            response.load_duration / ns_to_ms
            if response.load_duration
            else None
        )
        prompt_eval_ms = (
            response.prompt_eval_duration / ns_to_ms
            if response.prompt_eval_duration
            else None
        )
        eval_ms = (
            response.eval_duration / ns_to_ms
            if response.eval_duration
            else None
        )

        # Throughput
        output_tokens_per_sec = None
        if response.eval_count and response.eval_duration and response.eval_duration > 0:
            output_tokens_per_sec = (
                response.eval_count / (response.eval_duration / 1_000_000_000)
            )

        prompt_tokens_per_sec = None
        if (
            response.prompt_eval_count
            and response.prompt_eval_duration
            and response.prompt_eval_duration > 0
        ):
            prompt_tokens_per_sec = (
                response.prompt_eval_count
                / (response.prompt_eval_duration / 1_000_000_000)
            )

        # Response characteristics
        char_count = len(content)
        word_count = len(content.split())
        sentence_count = len(
            [s for s in re.split(r'[.!?]+', content) if s.strip()]
        )

        return ExecutionMetrics(
            ttft_ms=response.ttft_ms,
            total_generation_ms=response.total_generation_ms,
            model_load_ms=model_load_ms,
            prompt_eval_ms=prompt_eval_ms,
            eval_ms=eval_ms,
            output_tokens_per_sec=output_tokens_per_sec,
            prompt_tokens_per_sec=prompt_tokens_per_sec,
            input_tokens=response.prompt_eval_count,
            output_tokens=response.eval_count,
            total_tokens=(
                (response.prompt_eval_count or 0)
                + (response.eval_count or 0)
            )
            or None,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
        )
