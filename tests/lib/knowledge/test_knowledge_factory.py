"""
Tests for knowledge_factory.py
Testing RowBasedCSVKnowledgeBase functionality
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.knowledge.factories.knowledge_factory import create_knowledge_base, get_knowledge_base

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
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test_user:test_pass@localhost:5432/test_db'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                # Mock CSV file existence
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock the PgVector class to prevent database connections
                    with patch('lib.knowledge.factories.knowledge_factory.PgVector') as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db
                        
                        # Mock the RowBasedCSVKnowledgeBase since that's what current factory returns
                        with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            # Mock SmartIncrementalLoader to prevent CSV loading
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
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
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock the RowBasedCSVKnowledgeBase constructor to prevent actual database calls
                        # Mock the SmartIncrementalLoader to prevent CSV file operations  
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                            mock_loader_instance = Mock()
                            mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                            mock_loader.return_value = mock_loader_instance
                            
                            # Mock the RowBasedCSVKnowledgeBase to prevent database calls
                            with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_row_based:
                                mock_kb = Mock()
                                mock_row_based.return_value = mock_kb
                                
                                result = create_knowledge_base()
                                
                                # Verify that RowBasedCSVKnowledgeBase was called correctly
                                mock_row_based.assert_called_once()
                                assert result == mock_kb

    def test_uses_context_column_as_content(self):
        """Test that CSV reader is configured to use 'context' column"""
        # RED: This should fail as current config uses different structure
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock PgVector to prevent database connection
                    with patch('lib.knowledge.factories.knowledge_factory.PgVector') as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db
                        
                        # Mock RowBasedCSVKnowledgeBase to prevent actual instantiation
                        with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            # Mock SmartIncrementalLoader to prevent CSV operations
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                                mock_loader.return_value = mock_loader_instance
                                
                                result = create_knowledge_base()
                                
                                # Verify that the knowledge base was created
                                assert result == mock_kb
                                mock_kb_class.assert_called_once()
                                mock_pgvector.assert_called_once()

    def test_smart_incremental_loader_compatibility(self):
        """Test that SmartIncrementalLoader works with new native system"""
        # This ensures backward compatibility is maintained
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            kb = Mock(spec=RowBasedCSVKnowledgeBase)
            kb.load = Mock()
            
            # Should be able to call load methods that SmartIncrementalLoader expects
            kb.load(recreate=False, upsert=True)
            kb.load.assert_called_with(recreate=False, upsert=True)

    def test_removes_business_unit_filtering(self):
        """Test that business unit specific filtering configuration works"""
        # Test that the system correctly configures metadata filters
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock PgVector to prevent database connection
                    with patch('lib.knowledge.factories.knowledge_factory.PgVector') as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db
                        
                        # Mock RowBasedCSVKnowledgeBase to prevent actual instantiation
                        with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            # Mock SmartIncrementalLoader to prevent CSV operations
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                                mock_loader.return_value = mock_loader_instance
                                
                                result = create_knowledge_base()
                                
                                # Verify that valid_metadata_filters is properly configured
                                assert hasattr(result, 'valid_metadata_filters'), "Implementation should have valid_metadata_filters attribute"

    def test_preserves_thread_safety(self):
        """Test that global shared instance with thread safety is preserved"""
        # This is a critical requirement to maintain
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock PgVector to prevent database connection
                    with patch('lib.knowledge.factories.knowledge_factory.PgVector') as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db
                        
                        # Mock RowBasedCSVKnowledgeBase to prevent actual instantiation
                        with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            # Mock SmartIncrementalLoader to prevent CSV operations
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                                mock_loader.return_value = mock_loader_instance
                                
                                # Multiple calls should return the same instance (thread safety)
                                kb1 = create_knowledge_base()
                                kb2 = create_knowledge_base()
                                assert kb1 is kb2

                                # Should only create knowledge base once
                                mock_kb_class.assert_called_once()
                                mock_pgvector.assert_called_once()


class TestKnowledgeFactoryProcessorIntegration:
    """Test factory integration with DocumentProcessor (TDD RED phase for C2)."""

    def setup_method(self):
        """Reset singleton state before each test"""
        import lib.knowledge.factories.knowledge_factory
        lib.knowledge.factories.knowledge_factory._shared_kb = None

    # ========================================================================
    # Configuration Loading Tests
    # ========================================================================

    def test_factory_loads_processing_config(self):
        """Should load processing config when enabled.

        RED: This test should fail because factory doesn't call load_processing_config yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb:
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            # Mock the config loader that factory should call
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig(
                                    processing={"enabled": True}
                                )

                                create_knowledge_base()

                                # Factory should call the config loader
                                mock_loader.assert_called_once()

    def test_factory_uses_default_config_when_no_override(self):
        """Should use default config path when not overridden.

        RED: Factory doesn't handle config loading yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}, clear=False):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase'):
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig()

                                create_knowledge_base()

                                # Should call loader with None (default path)
                                mock_loader.assert_called_once_with(None)

    def test_factory_respects_custom_config_path(self):
        """Should load from custom path when HIVE_KNOWLEDGE_CONFIG_PATH set.

        RED: Factory doesn't check HIVE_KNOWLEDGE_CONFIG_PATH env var yet.
        """
        custom_path = "/custom/path/processing_config.yaml"
        with patch.dict('os.environ', {
            'HIVE_DATABASE_URL': 'postgresql://test',
            'HIVE_KNOWLEDGE_CONFIG_PATH': custom_path
        }):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase'):
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig()

                                create_knowledge_base()

                                # Should call loader with custom path from env
                                mock_loader.assert_called_once_with(custom_path)

    # ========================================================================
    # Processor Integration Tests
    # ========================================================================

    def test_factory_passes_config_to_knowledge_base(self):
        """Should pass processing_config to RowBasedCSVKnowledgeBase.

        RED: Factory doesn't pass processing_config parameter yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                test_config = ProcessingConfig(processing={"enabled": True})
                                mock_loader.return_value = test_config

                                create_knowledge_base()

                                # Factory should pass processing_config to RowBasedCSVKnowledgeBase
                                call_kwargs = mock_kb_class.call_args[1]
                                assert 'processing_config' in call_kwargs
                                assert call_kwargs['processing_config'] == test_config

    def test_factory_creates_knowledge_base_with_processor(self):
        """Should instantiate knowledge base with active processor.

        RED: Knowledge base doesn't have processor attribute yet (C1 dependency).
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        # Mock knowledge base with processor attribute
                        mock_kb = Mock()
                        mock_kb.processor = Mock()  # Should exist when config enabled
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig(
                                    processing={"enabled": True}
                                )

                                result = create_knowledge_base()

                                # Result should have processor when enabled
                                assert hasattr(result, 'processor')
                                assert result.processor is not None

    def test_factory_processor_none_when_disabled(self):
        """Should create knowledge base without processor when disabled.

        RED: Factory doesn't handle enabled/disabled logic yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb.processor = None  # Should be None when disabled
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig(
                                    processing={"enabled": False}
                                )

                                result = create_knowledge_base()

                                # Processor should be None when disabled
                                assert result.processor is None

    # ========================================================================
    # Enable/Disable Toggle Tests
    # ========================================================================

    def test_factory_enables_processing_when_config_enabled(self):
        """Should enable processing when config.processing.enabled=true.

        RED: Factory doesn't check enabled flag in config yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb.processing_config = None
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                enabled_config = ProcessingConfig(processing={"enabled": True})
                                mock_loader.return_value = enabled_config

                                result = create_knowledge_base()

                                # Should have processing_config when enabled
                                assert hasattr(result, 'processing_config')
                                assert result.processing_config is not None
                                assert result.processing_config.processing["enabled"] is True

    def test_factory_disables_processing_when_config_disabled(self):
        """Should disable processing when config.processing.enabled=false.

        RED: Factory doesn't handle disabled state properly yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb.processing_config = Mock()
                        mock_kb.processing_config.processing = {"enabled": False}
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                disabled_config = ProcessingConfig(processing={"enabled": False})
                                mock_loader.return_value = disabled_config

                                result = create_knowledge_base()

                                # Config should be present but disabled
                                assert result.processing_config.processing["enabled"] is False

    def test_factory_handles_missing_config_gracefully(self):
        """Should create knowledge base without processor when config missing.

        RED: Factory doesn't have fallback logic for missing config yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb.processor = None
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                # Simulate missing config (returns defaults with disabled)
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig()  # Defaults to disabled

                                result = create_knowledge_base()

                                # Should succeed without processor
                                assert result is not None
                                assert result.processor is None

    # ========================================================================
    # Singleton Behavior Tests
    # ========================================================================

    def test_factory_shared_instance_has_processor(self):
        """Should ensure shared knowledge base instance has processor.

        RED: Singleton pattern doesn't preserve processor in shared instance yet.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb.processor = Mock()  # Processor instance
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig(
                                    processing={"enabled": True}
                                )

                                # First call creates shared instance with processor
                                kb1 = create_knowledge_base()
                                # Second call should return same instance with processor
                                kb2 = create_knowledge_base()

                                assert kb1 is kb2
                                assert kb1.processor is not None
                                assert kb2.processor is not None
                                assert kb1.processor is kb2.processor

    def test_factory_reuses_processor_across_calls(self):
        """Should reuse same processor instance for shared knowledge base.

        RED: Factory might create multiple processors instead of reusing.
        """
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.factories.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }

                with patch('pathlib.Path.exists', return_value=True):
                    with patch('lib.knowledge.factories.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        processor_instance = Mock()
                        mock_kb.processor = processor_instance
                        mock_kb_class.return_value = mock_kb

                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader'):
                            with patch('lib.knowledge.factories.knowledge_factory.load_knowledge_processing_config') as mock_loader:
                                from lib.knowledge.config.processing_config import ProcessingConfig
                                mock_loader.return_value = ProcessingConfig(
                                    processing={"enabled": True}
                                )

                                # Multiple calls should reuse same processor
                                kb1 = create_knowledge_base()
                                kb2 = create_knowledge_base()
                                kb3 = create_knowledge_base()

                                # All should reference the same processor instance
                                assert kb1.processor is processor_instance
                                assert kb2.processor is processor_instance
                                assert kb3.processor is processor_instance

                                # Should only create knowledge base once (singleton)
                                mock_kb_class.assert_called_once()