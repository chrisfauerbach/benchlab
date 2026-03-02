"""Scoring rubric definitions for LLM-as-judge evaluation."""

from __future__ import annotations

SCALE_DESCRIPTIONS: dict[int, str] = {
    1: "Completely inadequate - fails entirely at the task",
    2: "Very poor - major deficiencies throughout",
    3: "Poor - significant issues that undermine quality",
    4: "Below average - noticeable problems",
    5: "Average - meets basic expectations but nothing more",
    6: "Above average - solid with minor issues",
    7: "Good - well done with few shortcomings",
    8: "Very good - high quality with minimal issues",
    9: "Excellent - outstanding quality",
    10: "Perfect - flawless execution",
}

DIMENSION_RUBRICS: dict[str, dict[str, str]] = {
    "coherence": {
        "description": "Logical flow and consistency of the response",
        "low": "Response is disjointed, contradictory, or hard to follow",
        "high": "Response flows logically, is internally consistent, and is easy to follow",
    },
    "accuracy": {
        "description": "Factual correctness and technical accuracy",
        "low": "Contains significant factual errors or incorrect information",
        "high": "All claims are factually correct and technically accurate",
    },
    "relevance": {
        "description": "How directly the response addresses the prompt",
        "low": "Response is off-topic or only tangentially related to the prompt",
        "high": "Response directly and thoroughly addresses the prompt",
    },
    "completeness": {
        "description": "Coverage of all aspects of the prompt",
        "low": "Major aspects of the prompt are left unaddressed",
        "high": "All aspects of the prompt are thoroughly addressed",
    },
    "conciseness": {
        "description": "Efficiency of communication without unnecessary verbosity",
        "low": "Response is excessively verbose with significant filler",
        "high": "Response is appropriately concise while remaining thorough",
    },
    "helpfulness": {
        "description": "Practical usefulness to the user",
        "low": "Response provides little practical value to the user",
        "high": "Response is highly actionable and practically useful",
    },
}


def get_scale_description(score: int) -> str:
    """Get the description for a score value."""
    return SCALE_DESCRIPTIONS.get(score, "")


def get_dimension_rubric(dimension: str) -> dict[str, str]:
    """Get the rubric for a scoring dimension."""
    return DIMENSION_RUBRICS.get(dimension, {
        "description": dimension,
        "low": f"Poor {dimension}",
        "high": f"Excellent {dimension}",
    })
