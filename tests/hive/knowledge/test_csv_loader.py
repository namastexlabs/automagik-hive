"""Tests for CSV knowledge loader."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.knowledge.csv_loader import CSVKnowledgeLoader


@pytest.fixture
def mock_vector_db() -> MagicMock:
    """Create a mock PgVector database."""
    db = MagicMock()
    db.table_name = "test_knowledge"
    db.upsert = MagicMock()
    db.delete = MagicMock()
    return db


@pytest.fixture
def csv_loader(mock_vector_db: MagicMock) -> CSVKnowledgeLoader:
    """Create a CSV loader instance."""
    return CSVKnowledgeLoader(
        vector_db=mock_vector_db,
        content_column="answer",
        hash_columns=["question", "answer"],
    )


def test_row_to_document(csv_loader: CSVKnowledgeLoader) -> None:
    """Test conversion of CSV row to Agno Document."""
    row = pd.Series({"question": "What is AI?", "answer": "Artificial Intelligence", "category": "tech"})

    doc = csv_loader._row_to_document(row, row_id=42)

    assert doc.name == "csv_row_42"
    assert doc.content == "Artificial Intelligence"
    assert doc.meta_data["row_id"] == 42
    assert doc.meta_data["question"] == "What is AI?"
    assert doc.meta_data["category"] == "tech"
    assert "answer" not in doc.meta_data  # Content column excluded from metadata


def test_load_full(csv_loader: CSVKnowledgeLoader, tmp_path: Path, mock_vector_db: MagicMock) -> None:
    """Test full CSV load."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1", "Q2"], "answer": ["A1", "A2"]})
    df.to_csv(csv_path, index=False)

    # Mock incremental loader
    with patch.object(csv_loader.incremental_loader, "update_hashes"):
        count = csv_loader.load_full(csv_path)

    assert count == 2
    mock_vector_db.upsert.assert_called_once()

    # Check documents passed to upsert
    upserted_docs = mock_vector_db.upsert.call_args[1]["documents"]
    assert len(upserted_docs) == 2
    assert upserted_docs[0].content == "A1"
    assert upserted_docs[1].content == "A2"


def test_load_incremental_additions(csv_loader: CSVKnowledgeLoader, tmp_path: Path, mock_vector_db: MagicMock) -> None:
    """Test incremental load with additions."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1", "Q2"], "answer": ["A1", "A2"]})
    df.to_csv(csv_path, index=False)

    # Mock change detection
    changes = {
        "dataframe": df,
        "current_hashes": {0: "hash0", 1: "hash1"},
        "added": [1],  # Row 1 is new
        "changed": [],
        "deleted": [],
    }
    with patch.object(csv_loader.incremental_loader, "detect_changes", return_value=changes):
        with patch.object(csv_loader.incremental_loader, "update_hashes"):
            stats = csv_loader.load_incremental(csv_path)

    assert stats["added"] == 1
    assert stats["changed"] == 0
    assert stats["deleted"] == 0
    mock_vector_db.upsert.assert_called_once()


def test_load_incremental_changes(csv_loader: CSVKnowledgeLoader, tmp_path: Path, mock_vector_db: MagicMock) -> None:
    """Test incremental load with changes."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1", "Q2"], "answer": ["A1", "A2"]})
    df.to_csv(csv_path, index=False)

    # Mock change detection
    changes = {
        "dataframe": df,
        "current_hashes": {0: "hash0", 1: "hash1"},
        "added": [],
        "changed": [0],  # Row 0 changed
        "deleted": [],
    }
    with patch.object(csv_loader.incremental_loader, "detect_changes", return_value=changes):
        with patch.object(csv_loader.incremental_loader, "update_hashes"):
            stats = csv_loader.load_incremental(csv_path)

    assert stats["added"] == 0
    assert stats["changed"] == 1
    assert stats["deleted"] == 0
    mock_vector_db.upsert.assert_called_once()


def test_load_incremental_deletions(csv_loader: CSVKnowledgeLoader, tmp_path: Path, mock_vector_db: MagicMock) -> None:
    """Test incremental load with deletions."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1"], "answer": ["A1"]})
    df.to_csv(csv_path, index=False)

    # Mock change detection
    changes = {
        "dataframe": df,
        "current_hashes": {0: "hash0"},
        "added": [],
        "changed": [],
        "deleted": [5, 7],  # Rows 5 and 7 deleted
    }
    with patch.object(csv_loader.incremental_loader, "detect_changes", return_value=changes):
        with patch.object(csv_loader.incremental_loader, "update_hashes"):
            with patch.object(csv_loader.incremental_loader, "delete_hashes"):
                stats = csv_loader.load_incremental(csv_path)

    assert stats["added"] == 0
    assert stats["changed"] == 0
    assert stats["deleted"] == 2
    # Should call delete for each deleted row
    assert mock_vector_db.delete.call_count == 2


def test_load_auto_full(csv_loader: CSVKnowledgeLoader, tmp_path: Path) -> None:
    """Test auto-detection of full load."""
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1"], "answer": ["A1"]})
    df.to_csv(csv_path, index=False)

    # Mock no existing hashes (first load)
    with patch.object(csv_loader.incremental_loader, "_load_existing_hashes", return_value={}):
        with patch.object(csv_loader, "load_full", return_value=1) as mock_full:
            result = csv_loader.load(csv_path)

    assert result["mode"] == "full"
    assert result["documents"] == 1
    mock_full.assert_called_once_with(csv_path)


def test_load_auto_incremental(csv_loader: CSVKnowledgeLoader, tmp_path: Path) -> None:
    """Test auto-detection of incremental load."""
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1"], "answer": ["A1"]})
    df.to_csv(csv_path, index=False)

    # Mock existing hashes (subsequent load)
    with patch.object(csv_loader.incremental_loader, "_load_existing_hashes", return_value={0: "hash0"}):
        with patch.object(
            csv_loader, "load_incremental", return_value={"added": 0, "changed": 0, "deleted": 0}
        ) as mock_inc:
            result = csv_loader.load(csv_path)

    assert result["mode"] == "incremental"
    mock_inc.assert_called_once_with(csv_path)
