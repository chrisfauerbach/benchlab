"""BenchLab CLI powered by Typer."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from benchlab.config import load_config
from benchlab.prompts.loader import load_prompts_from_directory, validate_prompts

app = typer.Typer(
    name="benchlab",
    help="BenchLab - LLM Evaluation Engine",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    prompts_dir: str = typer.Option("prompts/examples", "--prompts", "-p", help="Prompts directory"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
    batch_id: Optional[str] = typer.Option(None, "--batch-id", "-b", help="Custom batch ID"),
) -> None:
    """Run a benchmark batch against configured models."""
    config = load_config(config_file)
    prompts = load_prompts_from_directory(prompts_dir)

    if not prompts:
        console.print("[red]No prompts found.[/]")
        raise typer.Exit(1)

    console.print(f"Loaded {len(prompts)} prompts from {prompts_dir}")

    from benchlab.runner.ollama_client import OllamaClient
    from benchlab.storage.elasticsearch import ElasticsearchStorage
    from benchlab.runner.batch import BatchRunner

    async def _run() -> None:
        ollama = OllamaClient(config.ollama)
        storage = ElasticsearchStorage(config.elasticsearch)
        runner = BatchRunner(config, ollama, storage)
        try:
            await runner.run(prompts, batch_id=batch_id)
        finally:
            await ollama.close()
            await storage.close()

    asyncio.run(_run())


@app.command(name="validate-prompts")
def validate_prompts_cmd(
    prompts_dir: str = typer.Option("prompts/examples", "--prompts", "-p", help="Prompts directory"),
) -> None:
    """Validate prompt JSON files."""
    valid, errors = validate_prompts(prompts_dir)

    if errors:
        console.print("[red]Validation errors:[/]")
        for err in errors:
            console.print(f"  - {err}")
    else:
        console.print(f"[green]All prompts valid![/] Found {len(valid)} prompts.")

    table = Table(title="Prompts")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Difficulty")
    table.add_column("Tags")

    for p in valid:
        table.add_row(p.id, p.name, p.category, p.difficulty, ", ".join(p.tags))

    console.print(table)

    if errors:
        raise typer.Exit(1)


@app.command(name="list-batches")
def list_batches(
    config_file: Optional[str] = typer.Option(None, "--config", "-c"),
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """List recent batches."""
    config = load_config(config_file)

    from benchlab.storage.elasticsearch import ElasticsearchStorage

    async def _list() -> None:
        storage = ElasticsearchStorage(config.elasticsearch)
        try:
            batches = await storage.list_batches(size=limit)
        finally:
            await storage.close()

        if not batches:
            console.print("No batches found.")
            return

        table = Table(title="Batches")
        table.add_column("Batch ID")
        table.add_column("Status")
        table.add_column("Models")
        table.add_column("Prompts")
        table.add_column("Success/Total")
        table.add_column("Duration")
        table.add_column("Timestamp")

        for b in batches:
            table.add_row(
                b["batch_id"],
                b["status"],
                str(b.get("total_models", 0)),
                str(b.get("total_prompts", 0)),
                f"{b.get('successful_executions', 0)}/{b.get('total_executions', 0)}",
                f"{b.get('batch_duration_seconds', 0):.1f}s",
                b.get("timestamp", ""),
            )

        console.print(table)

    asyncio.run(_list())


@app.command(name="show-batch")
def show_batch(
    batch_id: str = typer.Argument(..., help="Batch ID to show"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c"),
) -> None:
    """Show details of a specific batch."""
    config = load_config(config_file)

    from benchlab.storage.elasticsearch import ElasticsearchStorage

    async def _show() -> None:
        storage = ElasticsearchStorage(config.elasticsearch)
        try:
            summary = await storage.get_batch_summary(batch_id)
            results = await storage.get_batch_results(batch_id)
        finally:
            await storage.close()

        if not summary:
            console.print(f"[red]Batch {batch_id} not found.[/]")
            raise typer.Exit(1)

        console.print(f"\n[bold]Batch: {batch_id}[/]")
        console.print(f"  Status: {summary['status']}")
        console.print(f"  Duration: {summary.get('batch_duration_seconds', 0):.1f}s")
        console.print(
            f"  Executions: {summary.get('successful_executions', 0)}"
            f"/{summary.get('total_executions', 0)} successful"
        )

        if summary.get("model_rankings"):
            console.print("\n  [bold]Model Rankings:[/]")
            for i, r in enumerate(summary["model_rankings"], 1):
                score = r.get("composite_score")
                score_str = f"{score:.2f}" if score else "n/a"
                console.print(f"    {i}. {r['display_name']}: {score_str}")

        if results:
            table = Table(title=f"\nResults ({len(results)})")
            table.add_column("Prompt")
            table.add_column("Model")
            table.add_column("Success")
            table.add_column("Tokens/s")
            table.add_column("Gen Time")
            table.add_column("Score")

            for r in results:
                metrics = r.get("metrics", {})
                eval_sum = r.get("evaluation_summary") or {}
                score = eval_sum.get("composite_score")
                table.add_row(
                    r["prompt"]["name"][:30],
                    r["model"]["display_name"],
                    "yes" if r["success"] else "no",
                    f"{metrics.get('output_tokens_per_sec', 0):.1f}" if metrics.get("output_tokens_per_sec") else "n/a",
                    f"{metrics.get('total_generation_ms', 0):.0f}ms" if metrics.get("total_generation_ms") else "n/a",
                    f"{score:.2f}" if score else "n/a",
                )

            console.print(table)

    asyncio.run(_show())


@app.command(name="list-models")
def list_models(
    config_file: Optional[str] = typer.Option(None, "--config", "-c"),
) -> None:
    """List available Ollama models."""
    config = load_config(config_file)

    from benchlab.runner.ollama_client import OllamaClient

    async def _list() -> None:
        client = OllamaClient(config.ollama)
        try:
            models = await client.list_models()
        finally:
            await client.close()

        if not models:
            console.print("No models found.")
            return

        table = Table(title="Available Models")
        table.add_column("Name")
        table.add_column("Size")
        table.add_column("Modified")

        for m in models:
            size_gb = m.get("size", 0) / (1024**3)
            table.add_row(
                m.get("name", ""),
                f"{size_gb:.1f} GB",
                m.get("modified_at", "")[:19],
            )

        console.print(table)

    asyncio.run(_list())


@app.command()
def export(
    batch_id: str = typer.Argument(..., help="Batch ID to export"),
    output: str = typer.Option("export.json", "--output", "-o", help="Output file"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c"),
) -> None:
    """Export batch results to JSON."""
    config = load_config(config_file)

    from benchlab.storage.elasticsearch import ElasticsearchStorage

    async def _export() -> None:
        storage = ElasticsearchStorage(config.elasticsearch)
        try:
            summary = await storage.get_batch_summary(batch_id)
            results = await storage.get_batch_results(batch_id)
        finally:
            await storage.close()

        data = {
            "batch_summary": summary,
            "results": results,
        }

        out_path = Path(output)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        console.print(f"[green]Exported to {out_path}[/]")

    asyncio.run(_export())


if __name__ == "__main__":
    app()
