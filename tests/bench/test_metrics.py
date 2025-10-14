"""Tests for metrics calculation modules."""

import sys
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from bench.scripts.metrics import text_metrics, table_metrics, utils


class TestTextMetrics:
    """Test text quality metrics."""

    def test_character_similarity_identical(self) -> None:
        """Test character similarity with identical texts."""
        text1 = "This is a test document."
        text2 = "This is a test document."

        result = text_metrics.calculate_text_quality(text1, text2)

        assert result["character_similarity"] >= 0.99

    def test_character_similarity_different(self) -> None:
        """Test character similarity with different texts."""
        text1 = "This is a test document."
        text2 = "This is completely different."

        result = text_metrics.calculate_text_quality(text1, text2)

        assert 0.0 <= result["character_similarity"] < 1.0

    def test_paragraph_consistency(self) -> None:
        """Test paragraph break consistency."""
        text1 = "Para 1\n\nPara 2\n\nPara 3"
        text2 = "Para 1\n\nPara 2\n\nPara 3"

        consistency = text_metrics.calculate_paragraph_consistency(text1, text2)

        assert consistency == 1.0

    def test_unicode_preservation_pt_br(self) -> None:
        """Test Brazilian Portuguese Unicode preservation."""
        ground_truth = "São Paulo: ação, coração, informação"
        extracted = "Sao Paulo: acao, coracao, informacao"  # Missing diacritics

        preservation = text_metrics.calculate_unicode_preservation(
            extracted, ground_truth
        )

        assert preservation < 1.0  # Should detect missing diacritics

    def test_unicode_preservation_perfect(self) -> None:
        """Test perfect Unicode preservation."""
        text = "São Paulo: ação, coração, informação"

        preservation = text_metrics.calculate_unicode_preservation(text, text)

        assert preservation == 1.0

    def test_formatting_metrics(self) -> None:
        """Test formatting metrics calculation."""
        text = """HEADING 1

This is a paragraph.

- List item 1
- List item 2
* Another item

1. Numbered item
2. Another numbered
"""
        metrics = text_metrics.calculate_formatting_metrics(text)

        assert metrics["heading_markers"] >= 0
        assert metrics["list_markers"] >= 3  # At least 3 list items

    def test_per_page_metrics(self) -> None:
        """Test per-page metrics calculation."""
        extracted_pages = ["Page 1 content", "Page 2 content"]
        ground_truth_pages = ["Page 1 content", "Page 2 different"]

        result = text_metrics.calculate_per_page_metrics(
            extracted_pages, ground_truth_pages
        )

        assert "page_similarities" in result
        assert len(result["page_similarities"]) == 2
        assert "mean_similarity" in result


class TestTableMetrics:
    """Test table accuracy metrics."""

    def test_identical_tables(self) -> None:
        """Test metrics with identical tables."""
        table = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"]
        })

        result = table_metrics.calculate_table_accuracy(table, table)

        assert result["cell_precision"] == 1.0
        assert result["cell_recall"] == 1.0
        assert result["cell_f1"] == 1.0

    def test_different_tables(self) -> None:
        """Test metrics with different tables."""
        table1 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"]
        })
        table2 = pd.DataFrame({
            "A": [4, 5, 6],
            "B": ["a", "b", "c"]
        })

        result = table_metrics.calculate_table_accuracy(table1, table2)

        assert result["cell_f1"] < 1.0

    def test_structural_metrics(self) -> None:
        """Test structural metrics calculation."""
        table1 = pd.DataFrame({
            "Col1": [1, 2],
            "Col2": [3, 4]
        })
        table2 = pd.DataFrame({
            "Col1": [5, 6],
            "Col2": [7, 8]
        })

        result = table_metrics.calculate_structural_metrics(table1, table2)

        assert result["row_match"] == 1.0  # Same shape
        assert result["col_match"] == 1.0
        assert result["header_match"] == 1.0  # Same headers

    def test_mismatched_structure(self) -> None:
        """Test with mismatched table structure."""
        table1 = pd.DataFrame({
            "A": [1, 2]
        })
        table2 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6]
        })

        result = table_metrics.calculate_structural_metrics(table1, table2)

        assert result["row_match"] == 0.0  # Different rows
        assert result["col_match"] == 0.0  # Different cols

    def test_merged_cell_penalty(self) -> None:
        """Test merged cell penalty calculation."""
        table1 = pd.DataFrame({
            "A": [1, "", 3],
            "B": ["x", "y", "z"]
        })
        table2 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": ["x", "y", "z"]
        })

        penalty = table_metrics.calculate_merged_cell_penalty(table1, table2)

        assert 0.0 <= penalty <= 1.0

    def test_batch_metrics(self) -> None:
        """Test batch table metrics."""
        tables = [
            pd.DataFrame({"A": [1, 2]}),
            pd.DataFrame({"B": [3, 4]})
        ]

        result = table_metrics.calculate_table_batch_metrics(tables)

        assert result["table_count"] == 2
        assert result["has_ground_truth"] is False

    def test_batch_metrics_with_ground_truth(self) -> None:
        """Test batch metrics with ground truth."""
        extracted = [pd.DataFrame({"A": [1, 2]})]
        ground_truth = [pd.DataFrame({"A": [1, 2]})]

        result = table_metrics.calculate_table_batch_metrics(
            extracted, ground_truth
        )

        assert result["has_ground_truth"] is True
        assert result["mean_accuracy"] >= 0.0


class TestMetricsUtils:
    """Test metrics utility functions."""

    def test_confidence_interval(self) -> None:
        """Test confidence interval calculation."""
        values = [0.8, 0.85, 0.9, 0.75, 0.88]

        lower, upper = utils.calculate_confidence_interval(values)

        assert lower < upper
        assert lower >= 0.0
        assert upper <= 1.0

    def test_confidence_interval_insufficient_data(self) -> None:
        """Test CI with insufficient data."""
        values: list[float] = []

        lower, upper = utils.calculate_confidence_interval(values)

        assert lower == 0.0
        assert upper == 0.0

    def test_aggregate_metrics(self) -> None:
        """Test metrics aggregation."""
        metric_dicts = [
            {"score": 0.8, "time": 1.0},
            {"score": 0.9, "time": 1.5},
            {"score": 0.85, "time": 1.2}
        ]

        result = utils.aggregate_metrics(metric_dicts)

        assert "score" in result
        assert "time" in result
        assert result["score"]["mean"] == pytest.approx(0.85, rel=0.01)
        assert "stdev" in result["score"]

    def test_composite_score(self) -> None:
        """Test composite score calculation."""
        metrics = {
            "quality": 0.9,
            "speed": 0.8,
            "memory": 0.7
        }
        weights = {
            "quality": 0.5,
            "speed": 0.3,
            "memory": 0.2
        }

        score = utils.calculate_composite_score(metrics, weights)

        expected = 0.9 * 0.5 + 0.8 * 0.3 + 0.7 * 0.2
        assert score == pytest.approx(expected, rel=0.01)

    def test_composite_score_normalization(self) -> None:
        """Test composite score with non-normalized weights."""
        metrics = {"a": 0.5, "b": 0.5}
        weights = {"a": 2.0, "b": 2.0}  # Sum to 4.0

        score = utils.calculate_composite_score(metrics, weights)

        assert score == 0.5  # Should normalize

    def test_normalize_score(self) -> None:
        """Test score normalization."""
        # Value in middle of range
        score = utils.normalize_score(5.0, min_val=0.0, max_val=10.0)
        assert score == 0.5

        # Value at min
        score = utils.normalize_score(0.0, min_val=0.0, max_val=10.0)
        assert score == 0.0

        # Value at max
        score = utils.normalize_score(10.0, min_val=0.0, max_val=10.0)
        assert score == 1.0

        # Value beyond range (should clip)
        score = utils.normalize_score(15.0, min_val=0.0, max_val=10.0)
        assert score == 1.0

    def test_format_metrics_report(self) -> None:
        """Test metrics report formatting."""
        metrics = {
            "score": 0.85,
            "nested": {
                "value": 0.9
            },
            "list": [0.8, 0.9, 0.7]
        }

        report = utils.format_metrics_report(metrics)

        assert "score: 0.8500" in report
        assert "nested:" in report
        assert "value: 0.9000" in report
