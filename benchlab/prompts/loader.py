"""Load and validate prompt JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .schema import Prompt, PromptFile


def load_prompt_file(path: Path) -> PromptFile:
    """Load and validate a single prompt JSON file."""
    with open(path) as f:
        data = json.load(f)
    return PromptFile(**data)


def load_prompts_from_directory(directory: str | Path) -> list[Prompt]:
    """Load all prompt files from a directory, returning a flat list of prompts."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Prompts directory not found: {directory}")

    prompts: list[Prompt] = []
    errors: list[str] = []

    for path in sorted(directory.rglob("*.json")):
        try:
            pf = load_prompt_file(path)
            prompts.extend(pf.prompts)
        except (json.JSONDecodeError, ValidationError) as e:
            errors.append(f"{path}: {e}")

    if errors:
        raise ValueError(
            f"Errors loading prompts:\n" + "\n".join(errors)
        )

    return prompts


def validate_prompts(directory: str | Path) -> tuple[list[Prompt], list[str]]:
    """Validate prompts, returning (valid_prompts, errors) without raising."""
    directory = Path(directory)
    if not directory.is_dir():
        return [], [f"Directory not found: {directory}"]

    prompts: list[Prompt] = []
    errors: list[str] = []

    for path in sorted(directory.rglob("*.json")):
        try:
            pf = load_prompt_file(path)
            prompts.extend(pf.prompts)
        except (json.JSONDecodeError, ValidationError) as e:
            errors.append(f"{path}: {e}")

    # Check for duplicate IDs
    seen_ids: set[str] = set()
    for p in prompts:
        if p.id in seen_ids:
            errors.append(f"Duplicate prompt id: {p.id}")
        seen_ids.add(p.id)

    return prompts, errors
