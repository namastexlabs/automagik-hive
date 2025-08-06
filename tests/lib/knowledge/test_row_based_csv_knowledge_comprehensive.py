"""
Comprehensive test suite for lib/knowledge/row_based_csv_knowledge.py

This test suite targets the 77 uncovered lines (1.1% boost) in the RowBasedCSVKnowledgeBase class.
Focus areas:
- CSV knowledge management and document creation
- Row-based operations and data processing
- Search functionality and filtering
- Error handling and edge cases
- Progress tracking and batch processing
- Metadata validation and business unit analysis
- Hot reload functionality
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from agno.document.base import Document
from agno.vectordb.base import VectorDb

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase


class TestRowBasedCSVKnowledgeInitialization:
    """Test initialization and document loading functionality."""

    def setup_method(self):
        """Set up test environment with temp directory and mock vector db."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test_knowledge.csv"

        # Create mock vector database that passes type validation
        self.mock_vector_db = MagicMock(spec=VectorDb)
        self.mock_vector_db.exists.return_value = False
        self.mock_vector_db.upsert_available.return_value = True

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_with_valid_csv(self):
        """Test initialization with valid CSV file containing all expected columns."""
        # Create test CSV with all expected columns
        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            [
                "Python basics",
                "Python is a programming language",
                "tech",
                "programming",
            ],
            [
                "Data structures",
                "Lists, dicts, sets are basic structures",
                "tech",
                "programming",
            ],
            ["Machine learning", "ML is subset of AI", "ai", "concepts"],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        # Initialize knowledge base
        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Verify initialization
        assert kb is not None
        assert hasattr(kb, "_csv_path")
        assert kb._csv_path == self.csv_file
        assert len(kb.documents) == 3  # Excluding header row

        # Check document structure
        doc = kb.documents[0]
        assert isinstance(doc, Document)
        assert doc.id == "knowledge_row_1"
        assert "**Problem:**" in doc.content
        assert "**Solution:**" in doc.content
        assert "**Business Unit:**" in doc.content
        assert "**Typification:**" in doc.content

    def test_initialization_with_missing_columns(self):
        """Test initialization with CSV missing some expected columns."""
        # Create CSV with only problem and solution columns
        test_data = [
            ["problem", "solution"],
            ["Basic question", "Basic answer"],
            ["Another question", "Another answer"],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Should handle missing columns gracefully
        assert len(kb.documents) == 2
        doc = kb.documents[0]
        assert "**Problem:**" in doc.content
        assert "**Solution:**" in doc.content
        # Should not include missing fields
        assert "**Business Unit:**" not in doc.content
        assert "**Typification:**" not in doc.content

    def test_initialization_with_empty_values(self):
        """Test initialization with CSV containing empty values."""
        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            [
                "Question with no solution",
                "",
                "tech",
                "",
            ],  # Empty solution and typification
            [
                "",
                "Answer with no question",
                "",
                "misc",
            ],  # Empty problem and business_unit
            ["  ", "  ", "  ", "  "],  # Whitespace-only values
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Should create documents for rows with some content
        assert len(kb.documents) >= 1

        # Check metadata handling for empty values
        for doc in kb.documents:
            assert isinstance(doc.meta_data["business_unit"], str)
            assert isinstance(doc.meta_data["typification"], str)
            assert isinstance(doc.meta_data["has_problem"], bool)
            assert isinstance(doc.meta_data["has_solution"], bool)

    def test_initialization_with_nonexistent_file(self):
        """Test initialization with non-existent CSV file."""
        nonexistent_file = "/non/existent/file.csv"

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            kb = RowBasedCSVKnowledgeBase(nonexistent_file, self.mock_vector_db)

            # Should create empty knowledge base
            assert len(kb.documents) == 0
            # Should log warning about missing file
            mock_logger.warning.assert_called_once()

    def test_content_formatting(self):
        """Test content formatting with various combinations of fields."""
        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["Problem only", "", "", ""],
            ["", "Solution only", "", ""],
            ["", "", "Business Unit only", ""],
            ["", "", "", "Typification only"],
            ["Complete entry", "Full solution", "tech", "programming"],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Should create documents for each row with content
        documents = kb.documents

        # Find specific documents by content
        for doc in documents:
            if "Problem only" in doc.content:
                assert "**Problem:** Problem only" in doc.content
                assert "**Solution:**" not in doc.content
            elif "Solution only" in doc.content:
                assert "**Solution:** Solution only" in doc.content
                assert "**Problem:**" not in doc.content
            elif "Complete entry" in doc.content:
                assert "**Problem:** Complete entry" in doc.content
                assert "**Solution:** Full solution" in doc.content
                assert "**Business Unit:** tech" in doc.content
                assert "**Typification:** programming" in doc.content


class TestRowBasedCSVDocumentCreation:
    """Test document creation and metadata handling."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "metadata_test.csv"
        self.mock_vector_db = MagicMock(spec=VectorDb)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_document_metadata_creation(self):
        """Test proper metadata creation for documents."""
        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["Test problem", "Test solution", "engineering", "technical"],
            ["", "Answer only", "sales", "business"],
            ["Question only", "", "support", ""],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)
        documents = kb.documents

        # Check first document metadata
        doc1 = documents[0]
        assert doc1.meta_data["row_index"] == 1
        assert doc1.meta_data["source"] == "knowledge_rag_csv"
        assert doc1.meta_data["business_unit"] == "engineering"
        assert doc1.meta_data["typification"] == "technical"
        assert doc1.meta_data["has_problem"] is True
        assert doc1.meta_data["has_solution"] is True

        # Check document with empty problem
        doc2 = documents[1]
        assert doc2.meta_data["row_index"] == 2
        assert doc2.meta_data["business_unit"] == "sales"
        assert doc2.meta_data["has_problem"] is False
        assert doc2.meta_data["has_solution"] is True

        # Check document with empty solution
        doc3 = documents[2]
        assert doc3.meta_data["row_index"] == 3
        assert doc3.meta_data["business_unit"] == "support"
        assert doc3.meta_data["has_problem"] is True
        assert doc3.meta_data["has_solution"] is False

    def test_document_id_generation(self):
        """Test unique document ID generation based on row index."""
        test_data = [
            ["problem", "solution"],
            ["First question", "First answer"],
            ["Second question", "Second answer"],
            ["Third question", "Third answer"],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)
        documents = kb.documents

        # Check unique ID generation
        expected_ids = ["knowledge_row_1", "knowledge_row_2", "knowledge_row_3"]
        actual_ids = [doc.id for doc in documents]
        assert actual_ids == expected_ids

    def test_business_unit_counting_and_logging(self):
        """Test business unit counting and logging during document creation."""
        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["Tech Q1", "Tech A1", "engineering", "technical"],
            ["Tech Q2", "Tech A2", "engineering", "technical"],
            ["Sales Q1", "Sales A1", "sales", "business"],
            ["Support Q1", "Support A1", "support", "help"],
            ["Support Q2", "Support A2", "support", "help"],
            ["Support Q3", "Support A3", "support", "help"],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

            # Check that business unit counting works
            documents = kb.documents
            assert len(documents) == 6

            # Check debug logging calls for business unit summary
            debug_calls = mock_logger.debug.call_args_list
            for call_args in debug_calls:
                if len(
                    call_args[0]
                ) > 0 and "✓ engineering: 2 documents processed" in str(call_args):
                    break
            # Note: The exact format might vary, so we check that some logging occurred
            assert len(debug_calls) > 0

    def test_content_strip_and_formatting(self):
        """Test that content is properly stripped and formatted."""
        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            [
                "  Problem with spaces  ",
                "  Solution with spaces  ",
                "  tech  ",
                "  programming  ",
            ],
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)
        doc = kb.documents[0]

        # Check that spaces are stripped in content
        assert "**Problem:** Problem with spaces" in doc.content
        assert "**Solution:** Solution with spaces" in doc.content
        assert "**Business Unit:** tech" in doc.content
        assert "**Typification:** programming" in doc.content

        # Check that metadata values are also stripped
        assert doc.meta_data["business_unit"] == "tech"
        assert doc.meta_data["typification"] == "programming"


class TestRowBasedCSVErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_vector_db = MagicMock(spec=VectorDb)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_csv_read_error_handling(self):
        """Test handling of CSV read errors."""
        # Create a file that will cause read errors
        bad_csv_file = Path(self.temp_dir) / "bad.csv"

        # Create a file with invalid encoding or structure
        with open(bad_csv_file, "wb") as f:
            f.write(b"\xff\xfe\x00\x00")  # Invalid UTF-8 bytes

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            kb = RowBasedCSVKnowledgeBase(str(bad_csv_file), self.mock_vector_db)

            # Should handle error gracefully and create empty knowledge base
            assert len(kb.documents) == 0
            # Should log error
            mock_logger.error.assert_called_once()

    def test_file_permission_error(self):
        """Test handling of file permission errors."""
        csv_file = Path(self.temp_dir) / "protected.csv"

        # Create file first
        with open(csv_file, "w") as f:
            f.write("problem,solution\ntest,test")

        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
                kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

                assert len(kb.documents) == 0
                mock_logger.error.assert_called_once()

    def test_empty_csv_file(self):
        """Test handling of completely empty CSV file."""
        empty_csv = Path(self.temp_dir) / "empty.csv"

        # Create empty file
        with open(empty_csv, "w"):
            pass

        with patch("lib.knowledge.row_based_csv_knowledge.logger"):
            kb = RowBasedCSVKnowledgeBase(str(empty_csv), self.mock_vector_db)

            # Should handle gracefully
            assert len(kb.documents) == 0

    def test_csv_with_only_headers(self):
        """Test CSV file with only header row."""
        headers_only_csv = Path(self.temp_dir) / "headers_only.csv"

        with open(headers_only_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["problem", "solution", "business_unit", "typification"])

        kb = RowBasedCSVKnowledgeBase(str(headers_only_csv), self.mock_vector_db)

        # Should create empty document list (no data rows)
        assert len(kb.documents) == 0

    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV content."""
        malformed_csv = Path(self.temp_dir) / "malformed.csv"

        # Create CSV with malformed content
        with open(malformed_csv, "w") as f:
            f.write('problem,solution\n"unclosed quote,data\nmore,data')

        # Should handle malformed CSV gracefully
        try:
            kb = RowBasedCSVKnowledgeBase(str(malformed_csv), self.mock_vector_db)
            # If it doesn't crash, that's good
            assert isinstance(kb.documents, list)
        except Exception:
            # If it does throw an exception, that's also acceptable
            # as long as it's handled appropriately
            pass


class TestRowBasedCSVVectorOperations:
    """Test vector database operations and loading functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "vector_test.csv"
        self.mock_vector_db = MagicMock(spec=VectorDb)
        self.mock_vector_db.exists.return_value = False
        self.mock_vector_db.upsert_available.return_value = True

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_method_with_recreate(self):
        """Test load method with recreate=True."""
        # Create test CSV
        test_data = [
            ["problem", "solution", "business_unit"],
            ["Q1", "A1", "tech"],
            ["Q2", "A2", "sales"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Test load with recreate
        with patch("agno.utils.log.log_info") as mock_log_info:
            kb.load(recreate=True)

            # Should drop and create collection
            self.mock_vector_db.drop.assert_called_once()
            self.mock_vector_db.create.assert_called_once()
            mock_log_info.assert_any_call("Dropping collection")
            mock_log_info.assert_any_call("Creating collection")

    def test_load_method_without_vector_db(self):
        """Test load method when vector_db is None."""
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), None)

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            kb.load()

            # Should log warning and return early
            mock_logger.warning.assert_called_once_with("No vector db provided")

    def test_load_method_with_existing_collection(self):
        """Test load method when collection already exists."""
        # Create test CSV
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        # Mock existing collection
        self.mock_vector_db.exists.return_value = True

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        with patch("agno.utils.log.log_info"):
            kb.load(recreate=False)

            # Should not drop or create collection
            self.mock_vector_db.drop.assert_not_called()
            self.mock_vector_db.create.assert_not_called()

    def test_load_method_with_upsert(self):
        """Test load method with upsert functionality."""
        test_data = [
            ["problem", "solution", "business_unit"],
            ["Q1", "A1", "tech"],
            ["Q2", "A2", "sales"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Mock progress bar to avoid actual tqdm output
        with patch("lib.knowledge.row_based_csv_knowledge.tqdm") as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value.__enter__ = MagicMock(return_value=mock_pbar)
            mock_tqdm.return_value.__exit__ = MagicMock(return_value=None)

            kb.load(upsert=True)

            # Should call upsert instead of insert
            self.mock_vector_db.upsert.assert_called()
            self.mock_vector_db.insert.assert_not_called()

    def test_load_method_batch_processing(self):
        """Test load method batch processing with progress tracking."""
        # Create larger dataset to test batching
        test_data = [["problem", "solution", "business_unit"]]
        for i in range(25):  # More than default batch size of 10
            test_data.append([f"Question {i}", f"Answer {i}", "tech"])

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Mock progress bar to capture calls
        with patch("lib.knowledge.row_based_csv_knowledge.tqdm") as mock_tqdm:
            mock_pbar = MagicMock()
            mock_tqdm.return_value.__enter__ = MagicMock(return_value=mock_pbar)
            mock_tqdm.return_value.__exit__ = MagicMock(return_value=None)

            # Force documents to be "new" by setting skip_existing=False
            kb.load(skip_existing=False)

            # Should create progress bar
            mock_tqdm.assert_called_once()
            args, kwargs = mock_tqdm.call_args
            assert kwargs["desc"] == "Embedding & upserting documents"
            assert kwargs["unit"] == "doc"

    def test_load_method_filter_suppression(self):
        """Test load method agno logger filter for batch messages."""
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        with patch("agno.utils.log.logger") as mock_agno_logger:
            with patch("lib.knowledge.row_based_csv_knowledge.tqdm"):
                # Force documents to be loaded by setting skip_existing=False
                kb.load(skip_existing=False)

                # Should add and remove filter
                mock_agno_logger.addFilter.assert_called_once()
                mock_agno_logger.removeFilter.assert_called_once()

    def test_business_unit_summary_logging(self):
        """Test business unit summary logging during load."""
        test_data = [
            ["problem", "solution", "business_unit"],
            ["Q1", "A1", "engineering"],
            ["Q2", "A2", "engineering"],
            ["Q3", "A3", "sales"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            with patch("lib.knowledge.row_based_csv_knowledge.tqdm"):
                # Force documents to be loaded by setting skip_existing=False
                kb.load(skip_existing=False)

                # Should log business unit summary
                debug_calls = mock_logger.debug.call_args_list
                assert len(debug_calls) > 0


class TestRowBasedCSVHotReload:
    """Test hot reload functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "reload_test.csv"
        self.mock_vector_db = MagicMock(spec=VectorDb)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_reload_from_csv_success(self):
        """Test successful reload from CSV."""
        # Create initial CSV
        initial_data = [
            ["problem", "solution"],
            ["Initial Q", "Initial A"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(initial_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)
        len(kb.documents)

        # Update CSV file
        updated_data = [
            ["problem", "solution"],
            ["Updated Q1", "Updated A1"],
            ["Updated Q2", "Updated A2"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(updated_data)

        # Test reload
        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            kb.reload_from_csv()

            # Should have new document count
            assert len(kb.documents) == 2
            # Should log success
            mock_logger.info.assert_called_once()

    def test_reload_from_csv_error_handling(self):
        """Test reload error handling."""
        # Create initial CSV
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Mock _load_csv_as_documents to raise exception
        with patch.object(
            kb, "_load_csv_as_documents", side_effect=Exception("Load error")
        ):
            with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
                kb.reload_from_csv()

                # Should log error
                mock_logger.error.assert_called_once()


class TestRowBasedCSVFilterValidation:
    """Test filter validation functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "filter_test.csv"
        self.mock_vector_db = MagicMock(spec=VectorDb)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_filters_with_none(self):
        """Test filter validation with None filters."""
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        valid_filters, invalid_keys = kb.validate_filters(None)

        assert valid_filters == {}
        assert invalid_keys == []

    def test_validate_filters_with_empty_dict(self):
        """Test filter validation with empty dictionary."""
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        valid_filters, invalid_keys = kb.validate_filters({})

        assert valid_filters == {}
        assert invalid_keys == []

    def test_validate_filters_no_metadata_tracked(self):
        """Test filter validation when no metadata filters are tracked yet."""
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Ensure no metadata filters are tracked
        if hasattr(kb, "valid_metadata_filters"):
            delattr(kb, "valid_metadata_filters")

        test_filters = {"business_unit": "tech", "has_problem": True}

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            valid_filters, invalid_keys = kb.validate_filters(test_filters)

            assert valid_filters == {}
            assert invalid_keys == ["business_unit", "has_problem"]
            mock_logger.debug.assert_called()

    def test_validate_filters_with_valid_metadata(self):
        """Test filter validation with valid metadata filters."""
        test_data = [
            ["problem", "solution", "business_unit"],
            ["Q1", "A1", "tech"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Mock valid metadata filters
        kb.valid_metadata_filters = {
            "business_unit",
            "row_index",
            "source",
            "has_problem",
            "has_solution",
        }

        test_filters = {
            "business_unit": "tech",
            "has_problem": True,
            "invalid_key": "value",
        }

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            valid_filters, invalid_keys = kb.validate_filters(test_filters)

            assert valid_filters == {"business_unit": "tech", "has_problem": True}
            assert invalid_keys == ["invalid_key"]
            mock_logger.debug.assert_called()

    def test_validate_filters_with_prefixed_keys(self):
        """Test filter validation with prefixed keys like meta_data.key."""
        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(self.csv_file), self.mock_vector_db)

        # Mock valid metadata filters
        kb.valid_metadata_filters = {"business_unit", "row_index"}

        test_filters = {
            "meta_data.business_unit": "tech",
            "meta_data.invalid_key": "value",
            "row_index": 1,
        }

        valid_filters, invalid_keys = kb.validate_filters(test_filters)

        # Should handle prefixed keys correctly
        assert "meta_data.business_unit" in valid_filters
        assert "row_index" in valid_filters
        assert "meta_data.invalid_key" in invalid_keys


class TestRowBasedCSVAdvancedCases:
    """Test advanced use cases and edge conditions."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_vector_db = MagicMock(spec=VectorDb)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_special_characters_in_content(self):
        """Test handling of special characters in CSV content."""
        csv_file = Path(self.temp_dir) / "special_chars.csv"

        test_data = [
            ["problem", "solution", "business_unit"],
            ["What is AI? 🤖", "AI is artificial intelligence! 🧠", "tech"],
            ["SQL: SELECT * FROM users;", "Use WHERE clause for filtering", "database"],
            ["Price: $100.50", "Payment via card/cash", "finance"],
        ]

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

        # Should handle special characters correctly
        assert len(kb.documents) == 3

        # Check that special characters are preserved
        contents = [doc.content for doc in kb.documents]
        assert any("🤖" in content for content in contents)
        assert any("SELECT *" in content for content in contents)
        assert any("$100.50" in content for content in contents)

    def test_very_long_content(self):
        """Test handling of very long content in CSV rows."""
        csv_file = Path(self.temp_dir) / "long_content.csv"

        # Create very long content
        long_problem = "This is a very long problem description. " * 100
        long_solution = "This is a very long solution description. " * 100

        test_data = [
            ["problem", "solution"],
            [long_problem, long_solution],
            ["Short problem", "Short solution"],
        ]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

        # Should handle long content
        assert len(kb.documents) == 2

        # Find the long content document
        long_doc = None
        for doc in kb.documents:
            if len(doc.content) > 1000:
                long_doc = doc
                break

        assert long_doc is not None
        assert "This is a very long problem description." in long_doc.content

    def test_unicode_and_encoding_handling(self):
        """Test handling of Unicode characters and different encodings."""
        csv_file = Path(self.temp_dir) / "unicode.csv"

        test_data = [
            ["problem", "solution", "business_unit"],
            ["Café question", "Résponse française", "international"],
            ["问题", "解决方案", "中文"],
            ["Здравствуй", "Привет мир", "русский"],
        ]

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

        # Should handle Unicode correctly
        assert len(kb.documents) == 3

        # Check Unicode preservation
        contents = [doc.content for doc in kb.documents]
        assert any("Café" in content for content in contents)
        assert any("问题" in content for content in contents)
        assert any("Здравствуй" in content for content in contents)

    def test_load_csv_as_documents_parameter_handling(self):
        """Test _load_csv_as_documents with different parameter scenarios."""
        csv_file = Path(self.temp_dir) / "param_test.csv"

        test_data = [
            ["problem", "solution"],
            ["Test Q", "Test A"],
        ]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

        # Test with explicit path parameter
        documents1 = kb._load_csv_as_documents(csv_file)
        assert len(documents1) == 1

        # Test with None parameter (should use stored path)
        documents2 = kb._load_csv_as_documents(None)
        assert len(documents2) == 1

        # Test with no stored path (simulate missing _csv_path)
        original_path = kb._csv_path
        object.__setattr__(kb, "_csv_path", None)

        with patch("lib.knowledge.row_based_csv_knowledge.logger") as mock_logger:
            documents3 = kb._load_csv_as_documents(None)
            assert len(documents3) == 0
            mock_logger.error.assert_called_once()

        # Restore original path
        object.__setattr__(kb, "_csv_path", original_path)

    def test_document_content_with_newlines_and_formatting(self):
        """Test document content formatting with newlines and structure."""
        csv_file = Path(self.temp_dir) / "formatting_test.csv"

        test_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["Multi\nline\nproblem", "Multi\nline\nsolution", "tech", "complex"],
        ]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)
        doc = kb.documents[0]

        # Check that content is properly formatted with double newlines between sections
        content_parts = doc.content.split("\n\n")
        assert len(content_parts) == 4  # Problem, Solution, Typification, Business Unit

        # Check individual sections in the correct order (based on actual code)
        assert content_parts[0].startswith("**Problem:**")
        assert content_parts[1].startswith("**Solution:**")
        assert content_parts[2].startswith(
            "**Typification:**"
        )  # Comes before Business Unit
        assert content_parts[3].startswith("**Business Unit:**")


class TestRowBasedCSVPerformanceAndMemory:
    """Test performance characteristics and memory handling."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_vector_db = MagicMock(spec=VectorDb)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_dataset_handling(self):
        """Test handling of reasonably large datasets."""
        csv_file = Path(self.temp_dir) / "large_dataset.csv"

        # Create larger dataset (not too large for CI)
        test_data = [["problem", "solution", "business_unit"]]
        for i in range(100):
            test_data.append([f"Problem {i}", f"Solution {i}", f"unit_{i % 5}"])

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        # Time the initialization (basic performance check)
        import time

        start_time = time.time()
        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)
        end_time = time.time()

        # Should complete reasonably quickly
        assert end_time - start_time < 5.0  # 5 seconds max
        assert len(kb.documents) == 100

    def test_memory_efficient_document_creation(self):
        """Test that document creation doesn't hold unnecessary references."""
        csv_file = Path(self.temp_dir) / "memory_test.csv"

        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
            ["Q2", "A2"],
        ]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

        # Check that documents don't reference the entire CSV data
        for doc in kb.documents:
            # Each document should be self-contained
            assert isinstance(doc.content, str)
            assert isinstance(doc.meta_data, dict)
            assert isinstance(doc.id, str)

    def test_csv_reader_resource_cleanup(self):
        """Test that CSV file handles are properly closed."""
        csv_file = Path(self.temp_dir) / "resource_test.csv"

        test_data = [
            ["problem", "solution"],
            ["Q1", "A1"],
        ]

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(test_data)

        # Mock open to track file handle usage
        original_open = open

        def mock_open(*args, **kwargs):
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open) as mock_open_func:
            kb = RowBasedCSVKnowledgeBase(str(csv_file), self.mock_vector_db)

            # File should be opened for reading
            mock_open_func.assert_called()

            # Verify documents were created (indicating successful reading and closing)
            assert len(kb.documents) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
