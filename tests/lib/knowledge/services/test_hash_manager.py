#!/usr/bin/env python3
"""
Tests for HashManager service - extracted from SmartIncrementalLoader
Validates row hashing and hash comparison logic.
"""

import pandas as pd

from lib.knowledge.services.hash_manager import HashManager


class TestHashManager:
    """Test suite for HashManager service."""

    def setup_method(self):
        """Setup test configuration matching SmartIncrementalLoader."""
        self.config = {
            "knowledge": {
                "csv_reader": {"content_column": "answer", "metadata_columns": ["question", "category", "tags"]}
            }
        }
        self.hash_manager = HashManager(self.config)

    def test_hash_row_basic(self):
        """Test basic row hashing functionality."""
        # Create test row similar to SmartIncrementalLoader test data
        row = pd.Series(
            {
                "question": "What is AI?",
                "answer": "Artificial Intelligence is...",
                "category": "technology",
                "tags": "ai,tech",
            },
            name=0,
        )  # name=0 simulates first row for debug logging

        result = self.hash_manager.hash_row(row)

        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hash length
        assert result != ""

    def test_hash_row_consistent(self):
        """Test that identical rows produce identical hashes."""
        row1 = pd.Series({"question": "Test question", "answer": "Test answer", "category": "test", "tags": "testing"})

        row2 = pd.Series({"question": "Test question", "answer": "Test answer", "category": "test", "tags": "testing"})

        hash1 = self.hash_manager.hash_row(row1)
        hash2 = self.hash_manager.hash_row(row2)

        assert hash1 == hash2

    def test_hash_row_different_content(self):
        """Test that different content produces different hashes."""
        row1 = pd.Series({"question": "Question 1", "answer": "Answer 1", "category": "cat1", "tags": "tag1"})

        row2 = pd.Series({"question": "Question 2", "answer": "Answer 2", "category": "cat2", "tags": "tag2"})

        hash1 = self.hash_manager.hash_row(row1)
        hash2 = self.hash_manager.hash_row(row2)

        assert hash1 != hash2

    def test_hash_row_missing_columns(self):
        """Test hashing with missing columns (should use empty strings)."""
        row = pd.Series(
            {
                "question": "Test question",
                "answer": "Test answer",
                # Missing category and tags
            }
        )

        result = self.hash_manager.hash_row(row)

        assert isinstance(result, str)
        assert len(result) == 32

    def test_hash_row_column_order_consistency(self):
        """Test that hash is consistent regardless of column order in Series."""
        # This tests the deterministic ordering in hash calculation
        data = {"tags": "tag1,tag2", "question": "Test question", "category": "test", "answer": "Test answer"}

        row1 = pd.Series(data)
        # Create same data but different Series creation order
        row2 = pd.Series(
            {"question": data["question"], "answer": data["answer"], "category": data["category"], "tags": data["tags"]}
        )

        hash1 = self.hash_manager.hash_row(row1)
        hash2 = self.hash_manager.hash_row(row2)

        assert hash1 == hash2

    def test_compare_hashes_equal(self):
        """Test hash comparison for equal hashes."""
        hash1 = "abc123def456"
        hash2 = "abc123def456"

        result = self.hash_manager.compare_hashes(hash1, hash2)

        assert result is True

    def test_compare_hashes_different(self):
        """Test hash comparison for different hashes."""
        hash1 = "abc123def456"
        hash2 = "xyz789uvw012"

        result = self.hash_manager.compare_hashes(hash1, hash2)

        assert result is False

    def test_hash_with_custom_config(self):
        """Test hashing with different configuration."""
        custom_config = {"knowledge": {"csv_reader": {"content_column": "content", "metadata_columns": ["title"]}}}

        custom_hash_manager = HashManager(custom_config)

        row = pd.Series({"title": "Test Title", "content": "Test Content"})

        result = custom_hash_manager.hash_row(row)

        assert isinstance(result, str)
        assert len(result) == 32

    def test_hash_row_debug_logging_first_row(self):
        """Test that debug logging is triggered for first row (name=0)."""
        row = pd.Series(
            {"question": "Debug test", "answer": "Debug answer", "category": "debug", "tags": "test"}, name=0
        )  # First row triggers debug logging

        # This should not raise an exception and should complete successfully
        result = self.hash_manager.hash_row(row)

        assert isinstance(result, str)
        assert len(result) == 32
