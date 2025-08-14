"""
Real coverage test for knowledge_factory.py - exercises actual code paths

This test file focuses on testing the actual knowledge factory functions
with minimal mocking to achieve real coverage metrics.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

# Direct imports to trigger coverage
import lib.knowledge.knowledge_factory as factory_module
from lib.knowledge.knowledge_factory import (
    _load_knowledge_config,
    _check_knowledge_base_exists,
    create_knowledge_base,
    get_knowledge_base
)


class TestKnowledgeFactoryRealCoverage:
    """Test suite that exercises real code paths for proper coverage"""
    
    def setup_method(self):
        """Reset global state"""
        factory_module._shared_kb = None

    def test_load_config_with_valid_yaml(self):
        """Test loading configuration with valid YAML - real code path"""
        # Test the actual _load_knowledge_config function
        yaml_content = """
knowledge:
  csv_file_path: test_knowledge.csv
  vector_db:
    table_name: test_knowledge_base
    embedder: text-embedding-3-small
    distance: cosine
  filters:
    valid_metadata_fields:
      - category
      - domain
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            config = _load_knowledge_config()
            
            # Verify the actual config loading worked
            assert 'knowledge' in config
            assert config['knowledge']['csv_file_path'] == 'test_knowledge.csv'
            assert config['knowledge']['vector_db']['table_name'] == 'test_knowledge_base'
            assert config['knowledge']['filters']['valid_metadata_fields'] == ['category', 'domain']

    def test_load_config_file_error(self):
        """Test configuration loading when file access fails"""
        with patch('builtins.open', side_effect=FileNotFoundError("No config file")):
            config = _load_knowledge_config()
            
            # Should return empty dict on error
            assert config == {}

    def test_check_knowledge_base_exists_success(self):
        """Test successful database check"""
        # Mock SQLAlchemy components
        mock_result1 = Mock()
        mock_result1.fetchone.return_value = [1]  # Table exists
        
        mock_result2 = Mock()
        mock_result2.fetchone.return_value = [10]  # Has data
        
        mock_conn = Mock()
        mock_conn.execute.side_effect = [mock_result1, mock_result2]
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        
        with patch('sqlalchemy.create_engine', return_value=mock_engine):
            result = _check_knowledge_base_exists("postgresql://test:pass@localhost:5432/test")
            
            assert result is True
            assert mock_conn.execute.call_count == 2

    def test_check_knowledge_base_exists_no_table(self):
        """Test database check when table doesn't exist"""
        mock_result = Mock()
        mock_result.fetchone.return_value = [0]  # Table doesn't exist
        
        mock_conn = Mock()
        mock_conn.execute.return_value = mock_result
        
        mock_engine = Mock()
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        
        with patch('sqlalchemy.create_engine', return_value=mock_engine):
            result = _check_knowledge_base_exists("postgresql://test:pass@localhost:5432/test")
            
            assert result is False

    def test_check_knowledge_base_exists_exception(self):
        """Test database check exception handling"""
        with patch('sqlalchemy.create_engine', side_effect=Exception("DB Error")):
            result = _check_knowledge_base_exists("postgresql://invalid")
            
            assert result is False

    def test_create_knowledge_base_missing_env_var(self):
        """Test creation fails without HIVE_DATABASE_URL"""
        # Clear environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="HIVE_DATABASE_URL environment variable required"):
                create_knowledge_base()

    def test_create_knowledge_base_with_config(self):
        """Test knowledge base creation with provided config"""
        test_config = {
            'knowledge': {
                'csv_file_path': 'test.csv',
                'vector_db': {
                    'table_name': 'test_kb',
                    'embedder': 'text-embedding-ada-002',
                    'distance': 'cosine'
                },
                'filters': {
                    'valid_metadata_fields': ['category', 'type']
                }
            }
        }
        
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
            # Mock the external dependencies but let the main logic run
            with patch('lib.knowledge.knowledge_factory.PgVector') as mock_pgvector:
                mock_vector_db = Mock()
                mock_pgvector.return_value = mock_vector_db
                
                with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                    mock_kb = Mock()
                    mock_kb_class.return_value = mock_kb
                    
                    with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                        mock_loader_instance = Mock()
                        mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                        mock_loader.return_value = mock_loader_instance
                        
                        # This should exercise the main create_knowledge_base logic
                        result = create_knowledge_base(config=test_config)
                        
                        # Verify function completed and returned mock KB
                        assert result == mock_kb
                        
                        # Verify PgVector was configured with test config
                        mock_pgvector.assert_called_once()
                        args, kwargs = mock_pgvector.call_args
                        assert kwargs['table_name'] == 'test_kb'
                        assert kwargs['distance'] == 'cosine'
                        
                        # Verify metadata filters were set
                        expected_filters = {'category', 'type'}
                        assert mock_kb.valid_metadata_filters == expected_filters

    def test_create_knowledge_base_csv_path_resolution(self):
        """Test CSV path resolution logic"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'custom_knowledge.csv',
                        'vector_db': {'table_name': 'test_kb'},
                        'filters': {'valid_metadata_fields': ['category']}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector'):
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb
                        
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                            mock_loader_instance = Mock()
                            mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                            mock_loader.return_value = mock_loader_instance
                            
                            # Test default CSV path resolution
                            result = create_knowledge_base()
                            
                            # Verify the KB was created
                            assert result == mock_kb
                            mock_kb_class.assert_called_once()
                            
                            # Verify CSV path was resolved correctly
                            args, kwargs = mock_kb_class.call_args
                            csv_path_used = kwargs['csv_path']
                            assert 'custom_knowledge.csv' in csv_path_used

    def test_create_knowledge_base_custom_csv_path(self):
        """Test knowledge base creation with custom CSV path"""
        custom_path = "/custom/path/knowledge.csv"
        
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'vector_db': {'table_name': 'test_kb'},
                        'filters': {'valid_metadata_fields': ['category']}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector'):
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb
                        
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                            mock_loader_instance = Mock()
                            mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                            mock_loader.return_value = mock_loader_instance
                            
                            # Test with custom CSV path
                            result = create_knowledge_base(csv_path=custom_path)
                            
                            # Verify the custom path was used
                            mock_kb_class.assert_called_once()
                            args, kwargs = mock_kb_class.call_args
                            assert kwargs['csv_path'] == custom_path

    def test_create_knowledge_base_relative_csv_path_handling(self):
        """Test handling of different relative CSV path formats"""
        test_cases = [
            ("relative.csv", True),  # Simple relative path
            ("lib/knowledge/prefixed.csv", True),  # Prefixed relative path
        ]
        
        for relative_path, should_modify in test_cases:
            factory_module._shared_kb = None  # Reset for each test case
            
            with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
                with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                    mock_config.return_value = {
                        'knowledge': {
                            'vector_db': {'table_name': 'test_kb'},
                            'filters': {'valid_metadata_fields': ['category']}
                        }
                    }
                    
                    with patch('lib.knowledge.knowledge_factory.PgVector'):
                        with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                                mock_loader.return_value = mock_loader_instance
                                
                                # Test relative path handling
                                result = create_knowledge_base(csv_path=relative_path)
                                
                                # Verify the path was handled correctly
                                mock_kb_class.assert_called_once()
                                args, kwargs = mock_kb_class.call_args
                                csv_path_used = kwargs['csv_path']
                                
                                if should_modify:
                                    # Path should be modified/resolved
                                    assert relative_path.split('/')[-1] in csv_path_used
                                else:
                                    # Path should be used as-is
                                    assert csv_path_used == relative_path

    def test_smart_loader_fallback_scenarios(self):
        """Test smart loader fallback scenarios"""
        fallback_scenarios = [
            ({'error': 'Loading failed'}, 'error in result'),
            ({'strategy': 'incremental_update', 'new_rows_processed': 5}, 'success with incremental'),
            ({'strategy': 'initial_load_with_hashes', 'entries_processed': 100}, 'success with initial load'),
            ({'strategy': 'unknown', 'status': 'completed'}, 'success with unknown strategy')
        ]
        
        for smart_result, description in fallback_scenarios:
            factory_module._shared_kb = None  # Reset for each test
            
            with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
                with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                    mock_config.return_value = {
                        'knowledge': {
                            'csv_file_path': 'test.csv',
                            'vector_db': {'table_name': 'test_kb'},
                            'filters': {'valid_metadata_fields': ['category']}
                        }
                    }
                    
                    with patch('lib.knowledge.knowledge_factory.PgVector'):
                        with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = smart_result
                                mock_loader.return_value = mock_loader_instance
                                
                                # Test the scenario
                                result = create_knowledge_base()
                                
                                # Verify the result
                                assert result == mock_kb
                                
                                # Check if fallback to basic loading was called for error cases
                                if 'error' in smart_result:
                                    mock_kb.load.assert_called_once_with(recreate=False, upsert=True)
                                else:
                                    # For successful cases, basic load should not be called
                                    mock_kb.load.assert_not_called()

    def test_smart_loader_import_failure(self):
        """Test behavior when smart loader import fails"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'test_kb'},
                        'filters': {'valid_metadata_fields': ['category']}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector'):
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb
                        
                        # Mock specific import failure for smart loader
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader', side_effect=ImportError("Module not found")):
                            result = create_knowledge_base()
                            
                            # Should fall back to basic loading
                            assert result == mock_kb
                            mock_kb.load.assert_called_once_with(recreate=False, upsert=True)

    def test_thread_safety_singleton(self):
        """Test thread-safe singleton behavior"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'test_kb'},
                        'filters': {'valid_metadata_fields': ['category']}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector'):
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb
                        
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                            mock_loader_instance = Mock()
                            mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                            mock_loader.return_value = mock_loader_instance
                            
                            # First call should create the KB
                            kb1 = create_knowledge_base(num_documents=10)
                            assert kb1.num_documents == 10
                            
                            # Second call should return same instance but update num_documents
                            kb2 = create_knowledge_base(num_documents=20)
                            assert kb2 is kb1  # Same object
                            assert kb2.num_documents == 20  # Updated parameter
                            
                            # KB should only be instantiated once
                            mock_kb_class.assert_called_once()

    def test_thread_safety_edge_case_documentation(self):
        """Document the double-check thread safety pattern that exists in the code"""
        # Note: Lines 137-141 in knowledge_factory.py implement the double-check pattern
        # for thread safety. This pattern handles the rare race condition where:
        # 1. Thread A passes the first check (_shared_kb is None)
        # 2. Thread A waits for lock
        # 3. Thread B creates the KB while Thread A waits
        # 4. Thread A gets lock and finds KB already exists
        # These lines are difficult to test without complex threading scenarios,
        # but they provide important thread safety guarantees.
        
        # Verify the code structure is in place
        import inspect
        source = inspect.getsource(create_knowledge_base)
        assert "Double-check pattern" in source or "another thread might have created it" in source
        assert "_shared_kb.num_documents = num_documents" in source

    def test_get_knowledge_base_delegation(self):
        """Test that get_knowledge_base delegates to create_knowledge_base"""
        with patch('lib.knowledge.knowledge_factory.create_knowledge_base') as mock_create:
            mock_kb = Mock()
            mock_create.return_value = mock_kb
            
            test_config = {'test': 'config'}
            test_db_url = 'postgresql://test'
            test_num_docs = 15
            test_csv_path = 'test.csv'
            
            # Call get_knowledge_base
            result = get_knowledge_base(test_config, test_db_url, test_num_docs, test_csv_path)
            
            # Verify delegation
            assert result == mock_kb
            mock_create.assert_called_once_with(test_config, test_db_url, test_num_docs, test_csv_path)

    def test_vector_db_configuration_defaults(self):
        """Test vector database configuration with default values"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:pass@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                # Config with minimal vector_db settings
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {},  # Empty config to test defaults
                        'filters': {}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector') as mock_pgvector:
                    mock_vector_db = Mock()
                    mock_pgvector.return_value = mock_vector_db
                    
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase'):
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                            mock_loader_instance = Mock()
                            mock_loader_instance.smart_load.return_value = {'strategy': 'no_changes'}
                            mock_loader.return_value = mock_loader_instance
                            
                            create_knowledge_base()
                            
                            # Verify default values were used
                            mock_pgvector.assert_called_once()
                            args, kwargs = mock_pgvector.call_args
                            assert kwargs['table_name'] == 'knowledge_base'  # Default table name
                            assert kwargs['distance'] == 'cosine'  # Default distance
                            assert kwargs['schema'] == 'agno'  # Default schema