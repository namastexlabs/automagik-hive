"""Tests for hash-based incremental loader."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.knowledge.incremental import IncrementalCSVLoader


@pytest.fixture
def mock_vector_db() -> MagicMock:
    """Create a mock PgVector database."""
    db = MagicMock()
    db.table_name = "test_knowledge"
    db.Session = MagicMock()
    return db


@pytest.fixture
def incremental_loader(mock_vector_db: MagicMock) -> IncrementalCSVLoader:
    """Create an incremental loader instance."""
    return IncrementalCSVLoader(
        vector_db=mock_vector_db,
        hash_columns=["question", "answer"],
    )


def test_compute_row_hash(incremental_loader: IncrementalCSVLoader) -> None:
    """Test row hash computation."""
    row = pd.Series({"question": "What is AI?", "answer": "Artificial Intelligence", "category": "tech"})

    hash1 = incremental_loader._compute_row_hash(row)
    assert isinstance(hash1, str)
    assert len(hash1) == 32  # MD5 hex length

    # Same data should produce same hash
    hash2 = incremental_loader._compute_row_hash(row)
    assert hash1 == hash2

    # Different data should produce different hash
    row2 = pd.Series({"question": "What is ML?", "answer": "Machine Learning", "category": "tech"})
    hash3 = incremental_loader._compute_row_hash(row2)
    assert hash1 != hash3


def test_detect_changes_initial(incremental_loader: IncrementalCSVLoader, tmp_path: Path) -> None:
    """Test change detection on initial load."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1", "Q2"], "answer": ["A1", "A2"]})
    df.to_csv(csv_path, index=False)

    # Mock database returns empty (no existing hashes)
    with patch.object(incremental_loader, "_load_existing_hashes", return_value={}):
        with patch.object(incremental_loader, "_ensure_hash_table"):
            changes = incremental_loader.detect_changes(csv_path)

    # All rows should be "added"
    assert len(changes["added"]) == 2
    assert len(changes["changed"]) == 0
    assert len(changes["deleted"]) == 0
    assert len(changes["current_hashes"]) == 2


def test_detect_changes_with_modifications(incremental_loader: IncrementalCSVLoader, tmp_path: Path) -> None:
    """Test change detection with row modifications."""
    # Create test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"question": ["Q1", "Q2", "Q3"], "answer": ["A1", "A2", "A3"]})
    df.to_csv(csv_path, index=False)

    # Compute hashes for original data
    original_hashes = {}
    for idx, row in df.iterrows():
        original_hashes[idx] = incremental_loader._compute_row_hash(row)

    # Modify row 1, add row 3, delete row 0
    existing_hashes = {0: original_hashes[0], 1: "different_hash"}  # Changed row 1, missing row 2

    with patch.object(incremental_loader, "_load_existing_hashes", return_value=existing_hashes):
        with patch.object(incremental_loader, "_ensure_hash_table"):
            changes = incremental_loader.detect_changes(csv_path)

    # Row 0: unchanged (hash matches)
    # Row 1: changed (hash different)
    # Row 2: added (new row)
    assert 1 in changes["changed"]
    assert 2 in changes["added"]
    assert len(changes["deleted"]) == 0


def test_update_hashes(incremental_loader: IncrementalCSVLoader, mock_vector_db: MagicMock) -> None:
    """Test hash storage in database."""
    hashes = {0: "hash0", 1: "hash1", 2: "hash2"}

    # Mock session
    mock_session = MagicMock()
    mock_vector_db.Session.return_value.__enter__.return_value = mock_session

    incremental_loader.update_hashes(hashes)

    # Should have executed 3 upserts
    assert mock_session.execute.call_count == 3
    mock_session.commit.assert_called_once()


def test_delete_hashes(incremental_loader: IncrementalCSVLoader, mock_vector_db: MagicMock) -> None:
    """Test hash deletion from database."""
    row_ids = [5, 7, 9]

    # Mock session
    mock_session = MagicMock()
    mock_vector_db.Session.return_value.__enter__.return_value = mock_session

    incremental_loader.delete_hashes(row_ids)

    # Should have executed delete
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_delete_hashes_empty_list(incremental_loader: IncrementalCSVLoader, mock_vector_db: MagicMock) -> None:
    """Test that empty delete list is a no-op."""
    mock_session = MagicMock()
    mock_vector_db.Session.return_value.__enter__.return_value = mock_session

    incremental_loader.delete_hashes([])

    # Should not execute anything
    mock_session.execute.assert_not_called()
    mock_session.commit.assert_not_called()
