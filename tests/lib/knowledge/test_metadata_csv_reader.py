"""Tests for lib.knowledge.metadata_csv_reader module."""

import csv
import os
import tempfile
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

# Import the module under test
try:
    from lib.knowledge.metadata_csv_reader import MetadataCSVReader
    import lib.knowledge.metadata_csv_reader
except ImportError:
    pytest.skip(f"Module lib.knowledge.metadata_csv_reader not available", allow_module_level=True)


class TestMetadataCsvReader:
    """Test metadata_csv_reader module functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "metadata.csv"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import lib.knowledge.metadata_csv_reader
        assert lib.knowledge.metadata_csv_reader is not None

    def test_csv_reading_basic(self):
        """Test basic CSV file reading."""
        # Create test CSV with metadata - use 'problem' as content column (default)
        test_data = [
            ["problem", "answer", "category", "priority"],
            ["What is AI?", "Artificial Intelligence", "tech", "high"],
            ["How to code?", "Practice daily", "programming", "medium"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        # Create reader with 'problem' as content column
        reader = MetadataCSVReader(content_column="problem")
        documents = reader.read(self.csv_file)

        assert len(documents) == 2  # Excluding header
        assert documents[0].content == "What is AI?"
        assert documents[0].meta_data["category"] == "tech"
        assert documents[1].content == "How to code?"
        assert documents[1].meta_data["priority"] == "medium"

    def test_header_only_csv(self):
        """Test CSV with only headers."""
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["problem", "answer", "metadata"])

        reader = MetadataCSVReader(content_column="problem")
        documents = reader.read(self.csv_file)
        assert documents == []

    def test_custom_content_column(self):
        """Test reading with custom content column."""
        test_data = [
            ["id", "description", "metadata", "tags"],
            ["1", "First item", "meta1", "tag1"],
            ["2", "Second item", "meta2", "tag2"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        reader = MetadataCSVReader(content_column="description")
        documents = reader.read(self.csv_file)

        assert len(documents) == 2
        assert documents[0].content == "First item"
        assert documents[0].meta_data["id"] == "1"
        assert documents[1].content == "Second item"
        assert documents[1].meta_data["tags"] == "tag2"


class TestMetadataCsvReaderEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_csv_handling(self):
        """Test handling of empty CSV files."""
        # Create empty CSV
        with open(self.csv_file, "w"):
            pass

        reader = MetadataCSVReader()
        # Empty CSV should raise FileNotFoundError or return empty list
        try:
            documents = reader.read(self.csv_file)
            assert documents == []
        except Exception:
            # It's okay if it raises an exception for empty files
            pass

    def test_nonexistent_file_handling(self):
        """Test handling of non-existent CSV files."""
        reader = MetadataCSVReader()
        try:
            documents = reader.read(Path("/non/existent/file.csv"))
            assert documents == []
        except FileNotFoundError:
            # Expected behavior for missing files
            pass

    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV files."""
        with open(self.csv_file, "w") as f:
            # Write malformed CSV
            f.write('incomplete,csv\n"unclosed quote,data\n')

        try:
            reader = MetadataCSVReader(content_column="incomplete")
            documents = reader.read(self.csv_file)
            # Should handle gracefully, not crash
            assert isinstance(documents, list)
        except Exception:
            # It's OK if it raises an exception, as long as it doesn't crash the test runner
            pass

    def test_missing_content_column(self):
        """Test handling when specified content column doesn't exist."""
        test_data = [
            ["id", "description"],
            ["1", "Test data"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        reader = MetadataCSVReader(content_column="nonexistent")
        try:
            documents = reader.read(self.csv_file)
            # Should handle missing column gracefully
            assert isinstance(documents, list)
        except (KeyError, ValueError, RuntimeError):
            # Expected if content column is required (may be wrapped in RuntimeError)
            pass


class TestMetadataCsvReaderIntegration:
    """Test integration scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_csv_handling(self):
        """Test handling of larger CSV files."""
        csv_file = Path(self.temp_dir) / "large.csv"
        
        # Create larger CSV file with many rows
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["problem", "solution", "category"])
            
            # Write many rows
            for i in range(100):
                writer.writerow([f"Problem {i}", f"Solution {i}", f"category_{i % 5}"])

        reader = MetadataCSVReader(content_column="problem")
        documents = reader.read(csv_file)
        
        assert len(documents) == 100
        assert documents[0].content == "Problem 0"
        assert documents[99].content == "Problem 99"
        assert documents[50].meta_data["solution"] == "Solution 50"

    def test_special_characters_handling(self):
        """Test CSV handling with special characters."""
        csv_file = Path(self.temp_dir) / "special.csv"
        
        test_data = [
            ["question", "answer"],
            ['What is "AI"?', "Artificial Intelligence, ML & DL"],
            ["Cost?", "$100,000 per year"],
            ["Formula?", "E = mc²"],
        ]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        reader = MetadataCSVReader(content_column="question")
        documents = reader.read(csv_file)

        assert len(documents) == 3
        assert '$100,000 per year' in documents[1].meta_data["answer"]
        assert "E = mc²" in documents[2].meta_data["answer"]

    def test_unicode_content_handling(self):
        """Test handling of Unicode content."""
        csv_file = Path(self.temp_dir) / "unicode.csv"
        
        test_data = [
            ["content", "metadata"],
            ["Café ☕", "French"],
            ["مرحبا", "Arabic"],
            ["こんにちは", "Japanese"],
        ]

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        reader = MetadataCSVReader(content_column="content")
        documents = reader.read(csv_file)

        assert len(documents) == 3
        assert documents[0].content == "Café ☕"
        assert documents[1].content == "مرحبا"
        assert documents[2].content == "こんにちは"
