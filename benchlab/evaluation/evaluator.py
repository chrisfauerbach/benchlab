"""LLM-as-judge evaluation orchestrator."""

from __future__ import annotations

import asyncio
import json
import re

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from benchlab.config import BenchLabConfig
from benchlab.evaluation.agreement import aggregate_scores
from benchlab.evaluation.templates import build_evaluation_prompt
from benchlab.models import (
    EvaluationScore,
    EvaluationSummary,
    ExecutionMetrics,
    ResultDocument,
)
from benchlab.runner.metrics import MetricsCalculator
from benchlab.runner.ollama_client import OllamaClient
from benchlab.storage.elasticsearch import ElasticsearchStorage

console = Console()


class EvaluationOrchestrator:
    """Orchestrates LLM-as-judge evaluation of batch results."""

    def __init__(
        self,
        config: BenchLabConfig,
        ollama: OllamaClient,
        storage: ElasticsearchStorage,
    ) -> None:
        self.config = config
        self.ollama = ollama
        self.storage = storage

    async def evaluate_batch(self, results: list[ResultDocument]) -> None:
        """Evaluate all results in a batch using configured evaluator models."""
        eval_cfg = self.config.evaluation
        successful = [r for r in results if r.success and r.output.strip()]

        if not successful:
            console.print("  [yellow]No successful results to evaluate.[/]")
            return

        total = len(successful) * len(eval_cfg.evaluator_models)
        console.print(f"\n  [bold blue]Evaluating {len(successful)} results with {len(eval_cfg.evaluator_models)} evaluator(s)...[/]")

        sem = asyncio.Semaphore(self.config.ollama.concurrent_requests)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Evaluating...", total=total)

            for evaluator_model in eval_cfg.evaluator_models:
                async def eval_one(result: ResultDocument) -> None:
                    async with sem:
                        score = await self._evaluate_single(
                            result, evaluator_model
                        )
                        if score:
                            result.evaluations.append(score)
                        progress.advance(task)

                tasks = [eval_one(r) for r in successful]
                await asyncio.gather(*tasks)

        # Aggregate scores and compute agreement
        for result in successful:
            if result.evaluations:
                result.evaluation_summary = aggregate_scores(
                    result.evaluations, self.config.evaluation
                )
                # Update in ES
                await self.storage.update_result(
                    result.result_id,
                    {
                        "evaluations": [
                            e.model_dump(mode="json")
                            for e in result.evaluations
                        ],
                        "evaluation_summary": result.evaluation_summary.model_dump(
                            mode="json"
                        ),
                    },
                )

        console.print("  [green]Evaluation complete.[/]")

    async def _evaluate_single(
        self,
        result: ResultDocument,
        evaluator_model: str,
    ) -> EvaluationScore | None:
        """Evaluate a single result with a single evaluator model."""
        eval_cfg = self.config.evaluation
        prompt_text = build_evaluation_prompt(
            prompt_text=result.prompt.input_text,
            response_text=result.output,
            dimensions=eval_cfg.scoring_dimensions,
            expected_output=result.prompt.expected_output,
            require_reasoning=eval_cfg.require_reasoning,
            score_min=eval_cfg.score_min,
            score_max=eval_cfg.score_max,
        )

        try:
            response = await self.ollama.chat(
                evaluator_model,
                [{"role": "user", "content": prompt_text}],
                temperature=0.1,
                num_predict=1024,
            )

            scores, reasoning = self._parse_scores(
                response.content, eval_cfg.score_min, eval_cfg.score_max
            )
            eval_metrics = MetricsCalculator.from_response(response)

            return EvaluationScore(
                evaluator_model=evaluator_model,
                scores=scores,
                reasoning=reasoning,
                eval_metrics=eval_metrics,
            )
        except Exception as e:
            console.print(
                f"  [yellow]Eval failed ({evaluator_model} → "
                f"{result.result_id}): {e}[/]"
            )
            return None

    def _parse_scores(
        self, content: str, score_min: int, score_max: int
    ) -> tuple[dict[str, float], str | None]:
        """Parse JSON scores from evaluator response."""
        # Try to extract JSON from the response
        json_match = re.search(r'\{[^{}]*"scores"[^{}]*\{[^}]*\}[^}]*\}', content, re.DOTALL)
        if not json_match:
            # Fallback: try to find any JSON object
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group())
                scores = data.get("scores", data)
                # Clamp scores
                parsed = {}
                for k, v in scores.items():
                    if k == "reasoning":
                        continue
                    try:
                        val = float(v)
                        parsed[k] = max(score_min, min(score_max, val))
                    except (TypeError, ValueError):
                        pass
                reasoning = data.get("reasoning")
                return parsed, reasoning
            except json.JSONDecodeError:
                pass

        # Last resort: try to find score patterns like "coherence: 7"
        scores = {}
        for match in re.finditer(r'(\w+)\s*[:=]\s*(\d+(?:\.\d+)?)', content):
            name, val = match.group(1).lower(), float(match.group(2))
            if score_min <= val <= score_max:
                scores[name] = val

        return scores, None
