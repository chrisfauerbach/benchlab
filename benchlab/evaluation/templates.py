"""Evaluation prompt templates for LLM-as-judge."""

from __future__ import annotations

from benchlab.config import ScoringDimension
from benchlab.evaluation.rubric import get_dimension_rubric, SCALE_DESCRIPTIONS


def build_evaluation_prompt(
    prompt_text: str,
    response_text: str,
    dimensions: list[ScoringDimension],
    expected_output: str | None = None,
    require_reasoning: bool = True,
    score_min: int = 1,
    score_max: int = 10,
) -> str:
    """Build the evaluation prompt for an LLM judge."""
    dimension_lines = []
    for dim in dimensions:
        rubric = get_dimension_rubric(dim.name)
        dimension_lines.append(
            f"- **{dim.name}** (weight: {dim.weight}): {rubric.get('description', dim.description)}\n"
            f"  - Low ({score_min}): {rubric.get('low', 'Poor')}\n"
            f"  - High ({score_max}): {rubric.get('high', 'Excellent')}"
        )

    scale_lines = "\n".join(
        f"  - {score}: {desc}"
        for score, desc in sorted(SCALE_DESCRIPTIONS.items())
        if score_min <= score <= score_max
    )

    dimensions_block = "\n".join(dimension_lines)
    dim_names = ", ".join(f'"{d.name}"' for d in dimensions)

    expected_block = ""
    if expected_output:
        expected_block = f"""
## Expected Output (Reference)
{expected_output}
"""

    reasoning_block = ""
    reasoning_field = ""
    if require_reasoning:
        reasoning_block = '\n- Provide a brief reasoning for each score in the "reasoning" field'
        reasoning_field = ',\n  "reasoning": "Brief explanation of scores"'

    return f"""You are an expert evaluator assessing the quality of an LLM response.

## Original Prompt
{prompt_text}
{expected_block}
## Response to Evaluate
{response_text}

## Scoring Dimensions
{dimensions_block}

## Scoring Scale ({score_min}-{score_max})
{scale_lines}

## Instructions
- Score each dimension independently on the {score_min}-{score_max} scale
- Be objective and consistent{reasoning_block}
- Respond ONLY with valid JSON in this exact format:

```json
{{
  "scores": {{{", ".join(f'"{d.name}": <{score_min}-{score_max}>' for d in dimensions)}}}{reasoning_field}
}}
```

Evaluate the response now:"""
