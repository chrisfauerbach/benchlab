"""BatchRunner orchestrator - drives prompt execution across models."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from benchlab.config import BenchLabConfig
from benchlab.models import (
    BatchSummary,
    ModelInfo,
    ModelRanking,
    PromptInfo,
    ResultDocument,
)
from benchlab.prompts.schema import Prompt
from benchlab.runner.metrics import MetricsCalculator
from benchlab.runner.ollama_client import OllamaClient
from benchlab.storage.elasticsearch import ElasticsearchStorage

console = Console()


class BatchRunner:
    """Orchestrates running prompts against models and storing results."""

    def __init__(
        self,
        config: BenchLabConfig,
        ollama: OllamaClient,
        storage: ElasticsearchStorage,
    ) -> None:
        self.config = config
        self.ollama = ollama
        self.storage = storage
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def run(
        self,
        prompts: list[Prompt],
        batch_id: str | None = None,
    ) -> BatchSummary:
        """Execute a full batch run."""
        batch_id = batch_id or uuid.uuid4().hex[:12]
        start_time = time.time()

        console.print(f"\n[bold blue]Starting batch:[/] {batch_id}")
        console.print(
            f"  Prompts: {len(prompts)} | "
            f"Models: {len(self.config.target_models)} | "
            f"Repetitions: {self.config.run.repetitions}"
        )

        # Ensure ES index exists
        await self.storage.ensure_index()

        # Pull models if configured
        if self.config.run.pull_models_on_start:
            await self._pull_models()

        # Warmup
        if self.config.run.warmup_runs > 0:
            await self._warmup()

        # Execute
        results: list[ResultDocument] = []
        total_tasks = (
            len(prompts)
            * len(self.config.target_models)
            * self.config.run.repetitions
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Running prompts...", total=total_tasks)

            sem = asyncio.Semaphore(self.config.ollama.concurrent_requests)

            async def run_one(
                prompt: Prompt,
                model_cfg: Any,
                rep: int,
            ) -> ResultDocument | None:
                if self._cancelled:
                    return None
                async with sem:
                    result = await self._execute_single(
                        prompt, model_cfg, rep, batch_id
                    )
                    progress.advance(task)
                    return result

            tasks = [
                run_one(prompt, model_cfg, rep)
                for prompt in prompts
                for model_cfg in self.config.target_models
                for rep in range(1, self.config.run.repetitions + 1)
            ]
            completed = await asyncio.gather(*tasks)
            results = [r for r in completed if r is not None]

        # Store results
        if results:
            indexed = await self.storage.bulk_index_results(results)
            console.print(f"  Indexed {indexed} results")

        # Evaluation
        if self.config.evaluation.enabled and results:
            from benchlab.evaluation.evaluator import EvaluationOrchestrator

            evaluator = EvaluationOrchestrator(
                config=self.config,
                ollama=self.ollama,
                storage=self.storage,
            )
            await evaluator.evaluate_batch(results)

        # Build summary
        elapsed = time.time() - start_time
        summary = self._build_summary(batch_id, prompts, results, elapsed)
        await self.storage.index_batch_summary(summary)

        self._print_summary(summary)
        return summary

    async def _pull_models(self) -> None:
        """Pull all target + evaluator models."""
        all_models = {m.name for m in self.config.target_models}
        if self.config.evaluation.enabled:
            all_models.update(self.config.evaluation.evaluator_models)

        for model_name in all_models:
            try:
                console.print(f"  Pulling model: {model_name}...")
                await self.ollama.pull_model(model_name)
            except Exception as e:
                console.print(
                    f"  [yellow]Warning: Could not pull {model_name}: {e}[/]"
                )

    async def _warmup(self) -> None:
        """Run warmup requests."""
        console.print(f"  Running {self.config.run.warmup_runs} warmup(s)...")
        for model_cfg in self.config.target_models:
            for _ in range(self.config.run.warmup_runs):
                try:
                    await self.ollama.chat(
                        model_cfg.name,
                        [{"role": "user", "content": "Hello"}],
                        num_predict=10,
                    )
                except Exception:
                    pass

    async def _execute_single(
        self,
        prompt: Prompt,
        model_cfg: Any,
        repetition: int,
        batch_id: str,
    ) -> ResultDocument:
        """Execute a single prompt against a single model."""
        result_id = f"{batch_id}-{prompt.id}-{model_cfg.name}-r{repetition}"
        messages: list[dict[str, str]] = []
        if prompt.system_prompt:
            messages.append({"role": "system", "content": prompt.system_prompt})
        messages.append({"role": "user", "content": prompt.input_text})

        options: dict[str, Any] = {}
        temp = prompt.temperature or self.config.run.default_temperature
        max_tokens = prompt.max_tokens or self.config.run.default_max_tokens
        options["temperature"] = temp
        options["num_predict"] = max_tokens
        options.update(model_cfg.parameters)

        try:
            response = await self.ollama.chat(
                model_cfg.name, messages, **options
            )
            metrics = MetricsCalculator.from_response(response)

            return ResultDocument(
                batch_id=batch_id,
                result_id=result_id,
                repetition=repetition,
                prompt=PromptInfo(
                    id=prompt.id,
                    name=prompt.name,
                    category=prompt.category,
                    input_text=prompt.input_text,
                    system_prompt=prompt.system_prompt,
                    expected_output=prompt.expected_output,
                    tags=prompt.tags,
                    difficulty=prompt.difficulty,
                ),
                model=ModelInfo(
                    name=model_cfg.name,
                    display_name=model_cfg.label,
                    parameters=model_cfg.parameters,
                ),
                output=response.content,
                success=True,
                metrics=metrics,
            )
        except Exception as e:
            return ResultDocument(
                batch_id=batch_id,
                result_id=result_id,
                repetition=repetition,
                prompt=PromptInfo(
                    id=prompt.id,
                    name=prompt.name,
                    category=prompt.category,
                    input_text=prompt.input_text,
                    system_prompt=prompt.system_prompt,
                    expected_output=prompt.expected_output,
                    tags=prompt.tags,
                    difficulty=prompt.difficulty,
                ),
                model=ModelInfo(
                    name=model_cfg.name,
                    display_name=model_cfg.label,
                    parameters=model_cfg.parameters,
                ),
                output="",
                error=str(e),
                success=False,
            )

    def _build_summary(
        self,
        batch_id: str,
        prompts: list[Prompt],
        results: list[ResultDocument],
        elapsed: float,
    ) -> BatchSummary:
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        categories = list({p.category for p in prompts})
        tags = list({t for p in prompts for t in p.tags})

        # Model rankings
        model_results: dict[str, list[ResultDocument]] = {}
        for r in results:
            model_results.setdefault(r.model.name, []).append(r)

        rankings = []
        for model_name, model_res in model_results.items():
            ok = [r for r in model_res if r.success]
            avg_tps = None
            avg_gen = None
            if ok:
                tps_vals = [
                    r.metrics.output_tokens_per_sec
                    for r in ok
                    if r.metrics.output_tokens_per_sec
                ]
                gen_vals = [
                    r.metrics.total_generation_ms
                    for r in ok
                    if r.metrics.total_generation_ms
                ]
                if tps_vals:
                    avg_tps = sum(tps_vals) / len(tps_vals)
                if gen_vals:
                    avg_gen = sum(gen_vals) / len(gen_vals)

            composite = None
            weighted = None
            if ok and ok[0].evaluation_summary:
                composites = [
                    r.evaluation_summary.composite_score
                    for r in ok
                    if r.evaluation_summary and r.evaluation_summary.composite_score
                ]
                if composites:
                    composite = sum(composites) / len(composites)
                w_composites = [
                    r.evaluation_summary.weighted_composite_score
                    for r in ok
                    if r.evaluation_summary
                    and r.evaluation_summary.weighted_composite_score
                ]
                if w_composites:
                    weighted = sum(w_composites) / len(w_composites)

            display_name = model_res[0].model.display_name
            rankings.append(
                ModelRanking(
                    model_name=model_name,
                    display_name=display_name,
                    composite_score=composite,
                    weighted_composite_score=weighted,
                    total_executions=len(model_res),
                    successful_executions=len(ok),
                    avg_output_tokens_per_sec=avg_tps,
                    avg_total_generation_ms=avg_gen,
                )
            )

        rankings.sort(
            key=lambda r: r.composite_score or 0, reverse=True
        )

        return BatchSummary(
            batch_id=batch_id,
            status="completed",
            total_prompts=len(prompts),
            total_models=len(self.config.target_models),
            total_executions=len(results),
            successful_executions=len(successful),
            failed_executions=len(failed),
            batch_duration_seconds=elapsed,
            model_rankings=rankings,
            config_snapshot=self.config.model_dump(mode="json"),
            prompt_categories=categories,
            tags_used=tags,
        )

    def _print_summary(self, summary: BatchSummary) -> None:
        console.print(f"\n[bold green]Batch {summary.batch_id} complete![/]")
        console.print(
            f"  Duration: {summary.batch_duration_seconds:.1f}s | "
            f"Success: {summary.successful_executions}/{summary.total_executions}"
        )
        if summary.model_rankings:
            console.print("\n  [bold]Model Rankings:[/]")
            for i, r in enumerate(summary.model_rankings, 1):
                score_str = (
                    f"score={r.composite_score:.2f}"
                    if r.composite_score
                    else "no score"
                )
                tps_str = (
                    f"{r.avg_output_tokens_per_sec:.1f} tok/s"
                    if r.avg_output_tokens_per_sec
                    else "n/a"
                )
                console.print(
                    f"    {i}. {r.display_name}: {score_str} | {tps_str}"
                )
