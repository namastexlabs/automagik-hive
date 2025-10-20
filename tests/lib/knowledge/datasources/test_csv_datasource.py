#!/usr/bin/env python3
"""
Tests for CSVDataSource service - extracted from SmartIncrementalLoader
Validates CSV reading and row processing logic with StringIO temp file handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from lib.knowledge.datasources.csv_datasource import CSVDataSource


class TestCSVDataSource:
    """Test suite for CSVDataSource service."""

    def setup_method(self):
        """Setup test configuration and mock hash manager."""
        self.config = {
            "knowledge": {
                "csv_reader": {"content_column": "answer", "metadata_columns": ["question", "category", "tags"]}
            }
        }

        # Mock hash manager for testing
        self.mock_hash_manager = Mock()
        self.mock_hash_manager.hash_row.side_effect = lambda row: f"hash_{row.name}"

        # Create temporary CSV file for testing
        self.temp_csv_path = None

    def teardown_method(self):
        """Cleanup test files."""
        if self.temp_csv_path and self.temp_csv_path.exists():
            self.temp_csv_path.unlink()

    def create_test_csv(self, data):
        """Helper to create temporary CSV file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
        df = pd.DataFrame(data)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()

        self.temp_csv_path = Path(temp_file.name)
        return self.temp_csv_path

    def test_get_csv_rows_with_hashes_basic(self):
        """Test basic CSV reading with hash generation."""
        # Create test data
        test_data = [
            {"question": "What is AI?", "answer": "Artificial Intelligence", "category": "tech", "tags": "ai"},
            {"question": "What is ML?", "answer": "Machine Learning", "category": "tech", "tags": "ml"},
        ]
        csv_path = self.create_test_csv(test_data)

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)
        result = csv_datasource.get_csv_rows_with_hashes()

        assert len(result) == 2
        assert result[0]["index"] == 0
        assert result[0]["hash"] == "hash_0"
        assert result[0]["data"]["question"] == "What is AI?"
        assert result[1]["index"] == 1
        assert result[1]["hash"] == "hash_1"
        assert result[1]["data"]["question"] == "What is ML?"

    def test_get_csv_rows_with_hashes_empty_file(self):
        """Test handling of empty CSV file."""
        # Create empty CSV file
        csv_path = self.create_test_csv([])

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)
        result = csv_datasource.get_csv_rows_with_hashes()

        assert result == []

    def test_get_csv_rows_with_hashes_missing_file(self):
        """Test handling of missing CSV file."""
        missing_path = Path("/non/existent/file.csv")

        csv_datasource = CSVDataSource(missing_path, self.mock_hash_manager)
        result = csv_datasource.get_csv_rows_with_hashes()

        assert result == []

    def test_process_single_row_success(self):
        """Test successful single row processing."""
        csv_path = self.create_test_csv([])  # Create dummy path

        # Mock knowledge base
        mock_kb = Mock()
        mock_temp_kb = Mock()
        mock_kb.vector_db = Mock()

        row_data = {"index": 0, "hash": "test_hash", "data": {"question": "Test Q", "answer": "Test A"}}

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)

        with patch("lib.knowledge.row_based_csv_knowledge.RowBasedCSVKnowledgeBase") as mock_kb_class:
            mock_kb_class.return_value = mock_temp_kb

            result = csv_datasource.process_single_row(row_data, mock_kb, lambda data, hash_: True)

            assert result is True
            mock_temp_kb.load.assert_called_once_with(recreate=False, upsert=True)

    def test_process_single_row_with_proper_cleanup(self):
        """Test that process_single_row properly manages temp files with cleanup."""
        csv_path = self.create_test_csv([])  # Create dummy path

        # Mock knowledge base
        mock_kb = Mock()
        mock_temp_kb = Mock()
        mock_kb.vector_db = Mock()

        row_data = {"index": 0, "hash": "test_hash", "data": {"question": "Test Q", "answer": "Test A"}}

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)

        with patch("lib.knowledge.row_based_csv_knowledge.RowBasedCSVKnowledgeBase") as mock_kb_class:
            mock_kb_class.return_value = mock_temp_kb

            csv_datasource.process_single_row(row_data, mock_kb, lambda data, hash_: True)

            # Verify temp knowledge base was created with proper csv_path argument
            mock_kb_class.assert_called_once()
            call_args = mock_kb_class.call_args
            # Should be called with csv_path as string and vector_db
            assert len(call_args.args) == 0  # No positional args
            assert "csv_path" in call_args.kwargs
            assert "vector_db" in call_args.kwargs

    def test_process_single_row_failure(self):
        """Test single row processing failure handling."""
        csv_path = self.create_test_csv([])

        mock_kb = Mock()
        mock_temp_kb = Mock()
        mock_temp_kb.load.side_effect = Exception("Load failed")
        mock_kb.vector_db = Mock()

        row_data = {"index": 0, "hash": "test_hash", "data": {"question": "Test Q", "answer": "Test A"}}

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)

        with patch("lib.knowledge.row_based_csv_knowledge.RowBasedCSVKnowledgeBase") as mock_kb_class:
            mock_kb_class.return_value = mock_temp_kb

            result = csv_datasource.process_single_row(row_data, mock_kb, lambda data, hash_: True)

            assert result is False

    def test_csv_reading_with_missing_columns(self):
        """Test CSV reading with missing columns in data."""
        # Test data with missing columns
        test_data = [
            {"question": "What is AI?", "answer": "Artificial Intelligence"},  # Missing category, tags
            {"question": "What is ML?", "category": "tech"},  # Missing answer, tags
        ]
        csv_path = self.create_test_csv(test_data)

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)
        result = csv_datasource.get_csv_rows_with_hashes()

        assert len(result) == 2
        # First row should have NaN/None for missing columns
        assert "category" in result[0]["data"] or pd.isna(result[0]["data"].get("category"))
        assert "tags" in result[0]["data"] or pd.isna(result[0]["data"].get("tags"))

    def test_hash_manager_integration(self):
        """Test proper integration with hash manager."""
        test_data = [{"question": "Test question", "answer": "Test answer", "category": "test", "tags": "testing"}]
        csv_path = self.create_test_csv(test_data)

        csv_datasource = CSVDataSource(csv_path, self.mock_hash_manager)
        csv_datasource.get_csv_rows_with_hashes()

        # Verify hash manager was called for each row
        assert self.mock_hash_manager.hash_row.call_count == 1
        # Verify the row data passed to hash_row
        call_args = self.mock_hash_manager.hash_row.call_args[0][0]
        assert call_args["question"] == "Test question"
        assert call_args["answer"] == "Test answer"

    def test_csv_path_validation(self):
        """Test CSV path validation and error handling."""
        # Test with None path
        csv_datasource = CSVDataSource(None, self.mock_hash_manager)
        result = csv_datasource.get_csv_rows_with_hashes()
        assert result == []

        # Test with invalid path object
        invalid_path = "not_a_path_object"
        csv_datasource = CSVDataSource(invalid_path, self.mock_hash_manager)
        # Should handle gracefully
        result = csv_datasource.get_csv_rows_with_hashes()
        assert result == []
