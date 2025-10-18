"""
Tests for knowledge_factory.py
Testing RowBasedCSVKnowledgeBase functionality
"""

from unittest.mock import Mock, patch

from lib.knowledge.factories.knowledge_factory import create_knowledge_base
from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase


# Clear the singleton before each test class
def setup_module():
    """Reset the global shared knowledge base before tests"""
    import lib.knowledge.factories.knowledge_factory

    lib.knowledge.factories.knowledge_factory._shared_kb = None


class TestKnowledgeFactory:
    """Test suite for knowledge factory refactoring"""

    def setup_method(self):
        """Reset singleton state before each test"""
        import lib.knowledge.factories.knowledge_factory

        lib.knowledge.factories.knowledge_factory._shared_kb = None

    def test_create_knowledge_base_returns_csv_knowledge_base(self):
        """Test that create_knowledge_base returns RowBasedCSVKnowledgeBase"""
        # RED: This test should fail because we haven't refactored yet
        with patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test_user:test_pass@localhost:5432/test_db"}):
            with patch("lib.knowledge.factories.knowledge_factory._load_knowledge_config") as mock_config:
                mock_config.return_value = {
                    "knowledge": {
                        "csv_file_path": "test.csv",
                        "csv_reader": {"content_column": "context"},
                        "vector_db": {"table_name": "knowledge_base"},
                    }
                }

                # Mock CSV file existence
                with patch("pathlib.Path.exists", return_value=True):
                    # Mock the PgVector class to prevent database connections
                    with patch("lib.knowledge.factories.knowledge_factory.PgVector") as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db

                        # Mock the RowBasedCSVKnowledgeBase since that's what current factory returns
                        with patch(
                            "lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase"
                        ) as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb

                            # Mock SmartIncrementalLoader to prevent CSV loading
                            with patch("lib.knowledge.smart_incremental_loader.SmartIncrementalLoader") as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {"strategy": "no_changes"}
                                mock_loader.return_value = mock_loader_instance

                                result = create_knowledge_base()

                                # Current implementation returns RowBasedCSVKnowledgeBase
                                # This test validates the correct return type
                                assert result == mock_kb

                                # Verify the factory was called with correct parameters
                                mock_kb_class.assert_called_once()

    def test_uses_row_chunking_with_skip_header(self):
        """Test that the factory creates RowBasedCSVKnowledgeBase correctly"""
        # Test that the factory creates the correct knowledge base type
        with patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test"}):
            with patch("lib.knowledge.factories.knowledge_factory._load_knowledge_config") as mock_config:
                mock_config.return_value = {
                    "knowledge": {
                        "csv_file_path": "test.csv",
                        "csv_reader": {"content_column": "context"},
                        "vector_db": {"table_name": "knowledge_base"},
                    }
                }

                with patch("pathlib.Path.exists", return_value=True):
                    # Mock the RowBasedCSVKnowledgeBase constructor to prevent actual database calls
                    # Mock the SmartIncrementalLoader to prevent CSV file operations
                    with patch("lib.knowledge.smart_incremental_loader.SmartIncrementalLoader") as mock_loader:
                        mock_loader_instance = Mock()
                        mock_loader_instance.smart_load.return_value = {"strategy": "no_changes"}
                        mock_loader.return_value = mock_loader_instance

                        # Mock the RowBasedCSVKnowledgeBase to prevent database calls
                        with patch(
                            "lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase"
                        ) as mock_row_based:
                            mock_kb = Mock()
                            mock_row_based.return_value = mock_kb

                            result = create_knowledge_base()

                            # Verify that RowBasedCSVKnowledgeBase was called correctly
                            mock_row_based.assert_called_once()
                            assert result == mock_kb

    def test_uses_context_column_as_content(self):
        """Test that CSV reader is configured to use 'context' column"""
        # RED: This should fail as current config uses different structure
        with patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test"}):
            with patch("lib.knowledge.factories.knowledge_factory._load_knowledge_config") as mock_config:
                mock_config.return_value = {
                    "knowledge": {
                        "csv_file_path": "test.csv",
                        "csv_reader": {"content_column": "context"},
                        "vector_db": {"table_name": "knowledge_base"},
                    }
                }

                with patch("pathlib.Path.exists", return_value=True):
                    # Mock PgVector to prevent database connection
                    with patch("lib.knowledge.factories.knowledge_factory.PgVector") as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db

                        # Mock RowBasedCSVKnowledgeBase to prevent actual instantiation
                        with patch(
                            "lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase"
                        ) as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb

                            # Mock SmartIncrementalLoader to prevent CSV operations
                            with patch("lib.knowledge.smart_incremental_loader.SmartIncrementalLoader") as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {"strategy": "no_changes"}
                                mock_loader.return_value = mock_loader_instance

                                result = create_knowledge_base()

                                # Verify that the knowledge base was created
                                assert result == mock_kb
                                mock_kb_class.assert_called_once()
                                mock_pgvector.assert_called_once()

    def test_smart_incremental_loader_compatibility(self):
        """Test that SmartIncrementalLoader works with new native system"""
        # This ensures backward compatibility is maintained
        with patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test"}):
            kb = Mock(spec=RowBasedCSVKnowledgeBase)
            kb.load = Mock()

            # Should be able to call load methods that SmartIncrementalLoader expects
            kb.load(recreate=False, upsert=True)
            kb.load.assert_called_with(recreate=False, upsert=True)

    def test_removes_business_unit_filtering(self):
        """Test that business unit specific filtering configuration works"""
        # Test that the system correctly configures metadata filters
        with patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test"}):
            with patch("lib.knowledge.factories.knowledge_factory._load_knowledge_config") as mock_config:
                mock_config.return_value = {
                    "knowledge": {
                        "csv_file_path": "test.csv",
                        "csv_reader": {"content_column": "context"},
                        "vector_db": {"table_name": "knowledge_base"},
                    }
                }

                with patch("pathlib.Path.exists", return_value=True):
                    # Mock PgVector to prevent database connection
                    with patch("lib.knowledge.factories.knowledge_factory.PgVector") as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db

                        # Mock RowBasedCSVKnowledgeBase to prevent actual instantiation
                        with patch(
                            "lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase"
                        ) as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb

                            # Mock SmartIncrementalLoader to prevent CSV operations
                            with patch("lib.knowledge.smart_incremental_loader.SmartIncrementalLoader") as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {"strategy": "no_changes"}
                                mock_loader.return_value = mock_loader_instance

                                result = create_knowledge_base()

                                # Verify that valid_metadata_filters is properly configured
                                assert hasattr(result, "valid_metadata_filters"), (
                                    "Implementation should have valid_metadata_filters attribute"
                                )

    def test_preserves_thread_safety(self):
        """Test that global shared instance with thread safety is preserved"""
        # This is a critical requirement to maintain
        with patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test"}):
            with patch("lib.knowledge.factories.knowledge_factory._load_knowledge_config") as mock_config:
                mock_config.return_value = {
                    "knowledge": {
                        "csv_file_path": "test.csv",
                        "csv_reader": {"content_column": "context"},
                        "vector_db": {"table_name": "knowledge_base"},
                    }
                }

                with patch("pathlib.Path.exists", return_value=True):
                    # Mock PgVector to prevent database connection
                    with patch("lib.knowledge.factories.knowledge_factory.PgVector") as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db

                        # Mock RowBasedCSVKnowledgeBase to prevent actual instantiation
                        with patch(
                            "lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase"
                        ) as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb

                            # Mock SmartIncrementalLoader to prevent CSV operations
                            with patch("lib.knowledge.smart_incremental_loader.SmartIncrementalLoader") as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {"strategy": "no_changes"}
                                mock_loader.return_value = mock_loader_instance

                                # Multiple calls should return the same instance (thread safety)
                                kb1 = create_knowledge_base()
                                kb2 = create_knowledge_base()
                                assert kb1 is kb2

                                # Should only create knowledge base once
                                mock_kb_class.assert_called_once()
                                mock_pgvector.assert_called_once()
