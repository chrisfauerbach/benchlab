"""Krippendorff's alpha calculation and score aggregation."""

from __future__ import annotations

import statistics
from typing import Any

from benchlab.config import EvaluationConfig
from benchlab.models import EvaluationScore, EvaluationSummary


def compute_krippendorff_alpha(
    ratings: list[list[float | None]],
) -> float:
    """Compute Krippendorff's alpha for interval data.

    Args:
        ratings: List of evaluator ratings. Each inner list is one evaluator's
                 scores for each item. None means missing.

    Returns:
        Alpha coefficient (-1 to 1). 1 = perfect agreement, 0 = chance.
    """
    n_evaluators = len(ratings)
    if n_evaluators < 2:
        return 1.0

    n_items = len(ratings[0])
    if n_items == 0:
        return 1.0

    # Collect all valid values per item
    values_per_item: list[list[float]] = []
    for i in range(n_items):
        vals = []
        for e in range(n_evaluators):
            if i < len(ratings[e]) and ratings[e][i] is not None:
                vals.append(ratings[e][i])  # type: ignore
            values_per_item.append(vals) if False else None
        values_per_item.append(vals)

    # Remove items with fewer than 2 ratings
    values_per_item = [v for v in values_per_item if len(v) >= 2]
    if not values_per_item:
        return 1.0

    # Observed disagreement
    n_total = sum(len(v) for v in values_per_item)
    if n_total < 2:
        return 1.0

    do = 0.0  # observed disagreement
    for vals in values_per_item:
        m = len(vals)
        if m < 2:
            continue
        for i in range(m):
            for j in range(i + 1, m):
                do += (vals[i] - vals[j]) ** 2
        do_divisor = m - 1
        if do_divisor > 0:
            do /= do_divisor

    do /= n_total

    # Expected disagreement
    all_values = [v for vals in values_per_item for v in vals]
    de = 0.0
    n_all = len(all_values)
    if n_all < 2:
        return 1.0
    for i in range(n_all):
        for j in range(i + 1, n_all):
            de += (all_values[i] - all_values[j]) ** 2
    de = de * 2 / (n_all * (n_all - 1))

    if de == 0:
        return 1.0
    return 1 - (do / de)


def aggregate_scores(
    evaluations: list[EvaluationScore],
    config: EvaluationConfig,
) -> EvaluationSummary:
    """Aggregate evaluation scores across multiple evaluators."""
    if not evaluations:
        return EvaluationSummary()

    # Collect all dimension names
    all_dims: set[str] = set()
    for ev in evaluations:
        all_dims.update(ev.scores.keys())

    mean_scores: dict[str, float] = {}
    median_scores: dict[str, float] = {}
    std_scores: dict[str, float] = {}
    score_ranges: dict[str, list[float]] = {}
    alpha_per_dim: dict[str, float] = {}

    for dim in all_dims:
        vals = [
            ev.scores[dim]
            for ev in evaluations
            if dim in ev.scores
        ]
        if not vals:
            continue

        mean_scores[dim] = statistics.mean(vals)
        median_scores[dim] = statistics.median(vals)
        std_scores[dim] = statistics.stdev(vals) if len(vals) > 1 else 0.0
        score_ranges[dim] = [min(vals), max(vals)]

    # Compute Krippendorff's alpha per dimension (if multiple evaluators)
    if len(evaluations) >= 2:
        for dim in all_dims:
            ratings = []
            for ev in evaluations:
                ratings.append([ev.scores.get(dim)])
            alpha_per_dim[dim] = compute_krippendorff_alpha(ratings)

    # Composite scores
    composite = None
    weighted_composite = None
    if mean_scores:
        composite = statistics.mean(mean_scores.values())

        # Weighted composite using config dimensions
        dim_weights = {d.name: d.weight for d in config.scoring_dimensions}
        total_weight = 0.0
        weighted_sum = 0.0
        for dim, score in mean_scores.items():
            w = dim_weights.get(dim, 1.0)
            weighted_sum += score * w
            total_weight += w
        if total_weight > 0:
            weighted_composite = weighted_sum / total_weight

    return EvaluationSummary(
        mean_scores=mean_scores,
        median_scores=median_scores,
        std_scores=std_scores,
        composite_score=composite,
        weighted_composite_score=weighted_composite,
        krippendorff_alpha=alpha_per_dim,
        score_ranges=score_ranges,
        evaluator_count=len(evaluations),
    )
