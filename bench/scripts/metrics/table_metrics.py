"""Table accuracy metrics for PDF extraction benchmarking."""

from typing import Any, Optional
import pandas as pd
from rapidfuzz import fuzz


def calculate_table_accuracy(
    extracted_table: Any,
    ground_truth_table: pd.DataFrame
) -> dict[str, float]:
    """Calculate table extraction accuracy.

    Args:
        extracted_table: Extracted table (DataFrame or similar)
        ground_truth_table: Ground truth table as DataFrame

    Returns:
        Dictionary of accuracy metrics
    """
    # Convert to DataFrame if needed
    if not isinstance(extracted_table, pd.DataFrame):
        try:
            extracted_df = pd.DataFrame(extracted_table)
        except Exception:
            return {
                "cell_precision": 0.0,
                "cell_recall": 0.0,
                "cell_f1": 0.0,
                "structural_match": 0.0,
                "composite_score": 0.0,
                "error": "Failed to convert to DataFrame"
            }
    else:
        extracted_df = extracted_table

    # Calculate cell-level metrics
    cell_metrics = calculate_cell_metrics(extracted_df, ground_truth_table)

    # Calculate structural metrics
    structural_metrics = calculate_structural_metrics(extracted_df, ground_truth_table)

    # Composite score
    composite = (
        cell_metrics["cell_f1"] * 0.6 +
        structural_metrics["structural_match"] * 0.4
    )

    return {
        **cell_metrics,
        **structural_metrics,
        "composite_score": composite
    }


def calculate_cell_metrics(
    extracted: pd.DataFrame,
    ground_truth: pd.DataFrame
) -> dict[str, float]:
    """Calculate cell-level precision/recall/F1.

    Args:
        extracted: Extracted table
        ground_truth: Ground truth table

    Returns:
        Cell-level metrics
    """
    # Build cell dictionaries (row, col) -> value
    extracted_cells = _build_cell_dict(extracted)
    gt_cells = _build_cell_dict(ground_truth)

    # Calculate matches
    true_positives = 0
    for pos, value in gt_cells.items():
        if pos in extracted_cells:
            # Fuzzy match for cell content
            similarity = fuzz.ratio(
                str(extracted_cells[pos]),
                str(value)
            ) / 100.0
            if similarity >= 0.8:  # 80% threshold
                true_positives += 1

    # Calculate precision and recall
    extracted_count = len(extracted_cells)
    gt_count = len(gt_cells)

    precision = true_positives / extracted_count if extracted_count > 0 else 0.0
    recall = true_positives / gt_count if gt_count > 0 else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "cell_precision": precision,
        "cell_recall": recall,
        "cell_f1": f1
    }


def calculate_structural_metrics(
    extracted: pd.DataFrame,
    ground_truth: pd.DataFrame
) -> dict[str, float]:
    """Calculate structural accuracy (shape, headers).

    Args:
        extracted: Extracted table
        ground_truth: Ground truth table

    Returns:
        Structural metrics
    """
    # Row/column count match
    row_match = 1.0 if extracted.shape[0] == ground_truth.shape[0] else 0.0
    col_match = 1.0 if extracted.shape[1] == ground_truth.shape[1] else 0.0

    # Header match (if first row treated as header)
    header_match = 0.0
    if len(extracted.columns) == len(ground_truth.columns):
        header_similarities = []
        for ext_col, gt_col in zip(extracted.columns, ground_truth.columns):
            sim = fuzz.ratio(str(ext_col), str(gt_col)) / 100.0
            header_similarities.append(sim)
        header_match = sum(header_similarities) / len(header_similarities)

    # Structural composite
    structural_match = (row_match + col_match + header_match) / 3.0

    return {
        "row_match": row_match,
        "col_match": col_match,
        "header_match": header_match,
        "structural_match": structural_match
    }


def _build_cell_dict(df: pd.DataFrame) -> dict[tuple[int, int], str]:
    """Build dictionary of (row, col) -> value.

    Args:
        df: DataFrame

    Returns:
        Cell dictionary
    """
    cells = {}
    for row_idx in range(len(df)):
        for col_idx in range(len(df.columns)):
            value = df.iloc[row_idx, col_idx]
            cells[(row_idx, col_idx)] = str(value).strip()
    return cells


def calculate_merged_cell_penalty(
    extracted: pd.DataFrame,
    ground_truth: pd.DataFrame
) -> float:
    """Calculate penalty for unexpected merged cells.

    This is a heuristic based on empty cells and shape mismatches.

    Args:
        extracted: Extracted table
        ground_truth: Ground truth table

    Returns:
        Penalty score (0-1, lower is worse)
    """
    # Count empty cells
    extracted_empty = (extracted == "").sum().sum()
    gt_empty = (ground_truth == "").sum().sum()

    # Penalize if extracted has significantly more empty cells
    if gt_empty == 0:
        penalty = 1.0 if extracted_empty == 0 else 0.5
    else:
        ratio = extracted_empty / gt_empty
        penalty = 1.0 if ratio <= 1.5 else max(0.0, 1.0 - (ratio - 1.5) * 0.2)

    return penalty


def calculate_table_batch_metrics(
    extracted_tables: list[Any],
    ground_truth_tables: Optional[list[pd.DataFrame]] = None
) -> dict[str, Any]:
    """Calculate metrics across multiple tables.

    Args:
        extracted_tables: List of extracted tables
        ground_truth_tables: Optional list of ground truth tables

    Returns:
        Batch metrics dictionary
    """
    if not ground_truth_tables:
        return {
            "table_count": len(extracted_tables),
            "has_ground_truth": False
        }

    accuracies = []
    for ext_table, gt_table in zip(extracted_tables, ground_truth_tables):
        metrics = calculate_table_accuracy(ext_table, gt_table)
        accuracies.append(metrics["composite_score"])

    return {
        "table_count": len(extracted_tables),
        "has_ground_truth": True,
        "per_table_scores": accuracies,
        "mean_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0.0,
        "min_accuracy": min(accuracies) if accuracies else 0.0,
        "max_accuracy": max(accuracies) if accuracies else 0.0,
    }
