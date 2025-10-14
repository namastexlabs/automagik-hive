"""Utility functions for metrics calculation."""

import statistics
from typing import Any


def calculate_confidence_interval(
    values: list[float],
    confidence: float = 0.95
) -> tuple[float, float]:
    """Calculate confidence interval for a list of values.

    Args:
        values: List of numeric values
        confidence: Confidence level (default 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not values or len(values) < 2:
        return (0.0, 0.0)

    mean = statistics.mean(values)
    stdev = statistics.stdev(values)

    # Use t-distribution approximation
    # For 95% CI with normal distribution, z=1.96
    z_score = 1.96 if confidence == 0.95 else 2.576

    margin = z_score * (stdev / (len(values) ** 0.5))

    return (mean - margin, mean + margin)


def aggregate_metrics(
    metric_dicts: list[dict[str, float]]
) -> dict[str, dict[str, float]]:
    """Aggregate metrics across multiple runs.

    Args:
        metric_dicts: List of metric dictionaries

    Returns:
        Aggregated metrics with mean, min, max, stdev
    """
    if not metric_dicts:
        return {}

    # Collect all metric keys
    all_keys = set()
    for md in metric_dicts:
        all_keys.update(md.keys())

    aggregated = {}

    for key in all_keys:
        values = [md.get(key, 0.0) for md in metric_dicts if key in md]

        if not values:
            continue

        aggregated[key] = {
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "count": len(values)
        }

        # Add confidence interval
        if len(values) >= 2:
            ci_lower, ci_upper = calculate_confidence_interval(values)
            aggregated[key]["ci_95_lower"] = ci_lower
            aggregated[key]["ci_95_upper"] = ci_upper

    return aggregated


def calculate_composite_score(
    metrics: dict[str, float],
    weights: dict[str, float]
) -> float:
    """Calculate weighted composite score.

    Args:
        metrics: Dictionary of metric values
        weights: Dictionary of weights (must sum to 1.0)

    Returns:
        Weighted composite score
    """
    score = 0.0
    total_weight = 0.0

    for key, weight in weights.items():
        if key in metrics:
            score += metrics[key] * weight
            total_weight += weight

    # Normalize if weights don't sum to 1.0
    if total_weight > 0 and total_weight != 1.0:
        score /= total_weight

    return score


def format_metrics_report(
    metrics: dict[str, Any],
    indent: int = 0
) -> str:
    """Format metrics dictionary as readable report.

    Args:
        metrics: Metrics dictionary
        indent: Indentation level

    Returns:
        Formatted report string
    """
    lines = []
    indent_str = "  " * indent

    for key, value in metrics.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_metrics_report(value, indent + 1))
        elif isinstance(value, float):
            lines.append(f"{indent_str}{key}: {value:.4f}")
        elif isinstance(value, list) and value and isinstance(value[0], (int, float)):
            mean_val = statistics.mean(value)
            lines.append(f"{indent_str}{key}: {mean_val:.4f} (n={len(value)})")
        else:
            lines.append(f"{indent_str}{key}: {value}")

    return "\n".join(lines)


def normalize_score(
    score: float,
    min_val: float = 0.0,
    max_val: float = 1.0
) -> float:
    """Normalize score to 0-1 range.

    Args:
        score: Raw score
        min_val: Minimum expected value
        max_val: Maximum expected value

    Returns:
        Normalized score (0-1)
    """
    if max_val == min_val:
        return 1.0

    normalized = (score - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))
