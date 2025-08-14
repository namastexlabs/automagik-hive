"""
Comprehensive test suite for knowledge_factory.py to boost coverage from 47% to 50%+

Tests focus on:
1. Knowledge base factory pattern implementation
2. Configuration loading and handling
3. Thread-safe singleton behavior
4. Error handling scenarios
5. Database connectivity checks
6. Smart loading integration
7. CSV path resolution logic
"""

import os
import pytest
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Import the functions we want to test
from lib.knowledge.knowledge_factory import (
    create_knowledge_base,
    get_knowledge_base,
    _check_knowledge_base_exists,
    _load_knowledge_config,
    _shared_kb,
    _kb_lock
)


class TestKnowledgeFactoryComprehensive:
    """Comprehensive test suite for knowledge_factory functionality"""
    
    def setup_method(self):
        """Reset global state before each test"""
        import lib.knowledge.knowledge_factory
        lib.knowledge.knowledge_factory._shared_kb = None

    def test_load_knowledge_config_success(self):
        """Test successful config loading from YAML file"""
        config_data = {
            'knowledge': {
                'csv_file_path': 'test.csv',
                'vector_db': {'table_name': 'knowledge_base'},
                'filters': {'valid_metadata_fields': ['category', 'tags']}
            }
        }
        
        yaml_content = "knowledge:\n  csv_file_path: test.csv\n  vector_db:\n    table_name: knowledge_base"
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load', return_value=config_data):
                with patch('pathlib.Path.exists', return_value=True):
                    result = _load_knowledge_config()
                    
                    assert result == config_data
                    assert 'knowledge' in result
                    assert result['knowledge']['csv_file_path'] == 'test.csv'

    def test_load_knowledge_config_file_not_found(self):
        """Test config loading when file doesn't exist"""
        with patch('builtins.open', side_effect=FileNotFoundError("Config file not found")):
            with patch('lib.knowledge.knowledge_factory.logger') as mock_logger:
                result = _load_knowledge_config()
                
                assert result == {}
                mock_logger.warning.assert_called_once()

    def test_load_knowledge_config_invalid_yaml(self):
        """Test config loading with invalid YAML content"""
        with patch('builtins.open', mock_open(read_data="invalid: yaml: content: [")):
            with patch('yaml.safe_load', side_effect=Exception("Invalid YAML")):
                with patch('lib.knowledge.knowledge_factory.logger') as mock_logger:
                    result = _load_knowledge_config()
                    
                    assert result == {}
                    mock_logger.warning.assert_called_once()

    def test_check_knowledge_base_exists_table_exists_with_data(self):
        """Test database check when table exists and has data"""
        mock_engine = Mock()
        mock_conn = Mock()
        mock_result = Mock()
        
        # Mock table exists query
        table_exists_result = Mock()
        table_exists_result.fetchone.return_value = [1]  # Table exists
        
        # Mock data count query
        data_count_result = Mock()
        data_count_result.fetchone.return_value = [5]  # Has data
        
        mock_conn.execute.side_effect = [table_exists_result, data_count_result]
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        
        with patch('sqlalchemy.create_engine', return_value=mock_engine):
            result = _check_knowledge_base_exists("postgresql://test:test@localhost:5432/test")
            
            assert result is True
            assert mock_conn.execute.call_count == 2

    def test_check_knowledge_base_exists_table_not_exists(self):
        """Test database check when table doesn't exist"""
        mock_engine = Mock()
        mock_conn = Mock()
        
        # Mock table doesn't exist
        table_exists_result = Mock()
        table_exists_result.fetchone.return_value = [0]  # Table doesn't exist
        
        mock_conn.execute.return_value = table_exists_result
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        
        with patch('sqlalchemy.create_engine', return_value=mock_engine):
            result = _check_knowledge_base_exists("postgresql://test:test@localhost:5432/test")
            
            assert result is False
            assert mock_conn.execute.call_count == 1

    def test_check_knowledge_base_exists_table_exists_no_data(self):
        """Test database check when table exists but has no data"""
        mock_engine = Mock()
        mock_conn = Mock()
        
        # Mock table exists
        table_exists_result = Mock()
        table_exists_result.fetchone.return_value = [1]  # Table exists
        
        # Mock no data
        data_count_result = Mock()
        data_count_result.fetchone.return_value = [0]  # No data
        
        mock_conn.execute.side_effect = [table_exists_result, data_count_result]
        mock_engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        
        with patch('sqlalchemy.create_engine', return_value=mock_engine):
            result = _check_knowledge_base_exists("postgresql://test:test@localhost:5432/test")
            
            assert result is False
            assert mock_conn.execute.call_count == 2

    def test_check_knowledge_base_exists_database_error(self):
        """Test database check when database connection fails"""
        with patch('sqlalchemy.create_engine', side_effect=SQLAlchemyError("Connection failed")):
            with patch('lib.knowledge.knowledge_factory.logger') as mock_logger:
                result = _check_knowledge_base_exists("postgresql://invalid:invalid@localhost:5432/invalid")
                
                assert result is False
                mock_logger.warning.assert_called_once()

    def test_create_knowledge_base_missing_db_url(self):
        """Test knowledge base creation when HIVE_DATABASE_URL is missing"""
        with patch.dict(os.environ, {}, clear=True):  # Clear all env vars
            with pytest.raises(RuntimeError, match="HIVE_DATABASE_URL environment variable required"):
                create_knowledge_base()

    def test_create_knowledge_base_custom_db_url(self):
        """Test knowledge base creation with custom database URL"""
        custom_db_url = "postgresql://custom:pass@localhost:5432/custom"
        
        with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
            mock_config.return_value = {
                'knowledge': {
                    'csv_file_path': 'test.csv',
                    'vector_db': {'table_name': 'knowledge_base'},
                    'filters': {'valid_metadata_fields': ['category', 'tags']}
                }
            }
            
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
                        
                        result = create_knowledge_base(db_url=custom_db_url)
                        
                        assert result == mock_kb
                        # Verify PgVector was created with custom URL
                        mock_pgvector.assert_called_once()
                        args, kwargs = mock_pgvector.call_args
                        assert kwargs['db_url'] == custom_db_url

    def test_create_knowledge_base_custom_csv_path_absolute(self):
        """Test knowledge base creation with custom absolute CSV path"""
        custom_csv_path = "/absolute/path/to/custom.csv"
        
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
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
                            
                            result = create_knowledge_base(csv_path=custom_csv_path)
                            
                            assert result == mock_kb
                            # Verify RowBasedCSVKnowledgeBase was created with custom path
                            mock_kb_class.assert_called_once()
                            args, kwargs = mock_kb_class.call_args
                            # Check csv_path in kwargs since it's passed as keyword argument
                            assert kwargs['csv_path'] == custom_csv_path

    def test_create_knowledge_base_custom_csv_path_relative_with_lib_prefix(self):
        """Test knowledge base creation with relative CSV path that includes lib/knowledge/"""
        relative_csv_path = "lib/knowledge/custom.csv"
        
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
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
                            
                            with patch('pathlib.Path.resolve') as mock_resolve:
                                mock_resolve.return_value = Path("/resolved/path/custom.csv")
                                
                                result = create_knowledge_base(csv_path=relative_csv_path)
                                
                                assert result == mock_kb
                                mock_kb_class.assert_called_once()

    def test_create_knowledge_base_custom_csv_path_relative_without_lib_prefix(self):
        """Test knowledge base creation with relative CSV path without lib/knowledge/ prefix"""
        relative_csv_path = "custom.csv"
        
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
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
                            
                            result = create_knowledge_base(csv_path=relative_csv_path)
                            
                            assert result == mock_kb
                            mock_kb_class.assert_called_once()
                            # Should combine knowledge directory with relative path
                            args, kwargs = mock_kb_class.call_args
                            csv_path_used = kwargs['csv_path']
                            assert "custom.csv" in csv_path_used

    def test_create_knowledge_base_smart_loader_error_fallback(self):
        """Test knowledge base creation when smart loader fails and falls back to basic loading"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector') as mock_pgvector:
                    mock_vector_db = Mock()
                    mock_pgvector.return_value = mock_vector_db
                    
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb
                        
                        # Mock smart loader to return error
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                            mock_loader_instance = Mock()
                            mock_loader_instance.smart_load.return_value = {'error': 'Failed to load'}
                            mock_loader.return_value = mock_loader_instance
                            
                            with patch('lib.knowledge.knowledge_factory.logger') as mock_logger:
                                result = create_knowledge_base()
                                
                                assert result == mock_kb
                                # Verify fallback to basic loading was called
                                mock_kb.load.assert_called_once_with(recreate=False, upsert=True)
                                mock_logger.warning.assert_called_once()
                                mock_logger.info.assert_any_call("Falling back to basic knowledge base loading")

    def test_create_knowledge_base_smart_loader_exception_fallback(self):
        """Test knowledge base creation when smart loader raises exception"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
                with patch('lib.knowledge.knowledge_factory.PgVector') as mock_pgvector:
                    mock_vector_db = Mock()
                    mock_pgvector.return_value = mock_vector_db
                    
                    with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                        mock_kb = Mock()
                        mock_kb_class.return_value = mock_kb
                        
                        # Mock smart loader to raise exception
                        with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader', side_effect=Exception("Import error")):
                            with patch('lib.knowledge.knowledge_factory.logger') as mock_logger:
                                result = create_knowledge_base()
                                
                                assert result == mock_kb
                                # Verify fallback to basic loading was called
                                mock_kb.load.assert_called_once_with(recreate=False, upsert=True)
                                mock_logger.warning.assert_called_once()

    def test_create_knowledge_base_different_smart_loading_strategies(self):
        """Test different smart loading strategies are handled correctly"""
        strategies = [
            ('no_changes', 'No changes needed (all documents already exist)'),
            ('incremental_update', 'Added new documents (incremental)'),
            ('initial_load_with_hashes', 'Initial load completed'),
            ('unknown_strategy', 'Completed')
        ]
        
        for strategy, expected_log_message in strategies:
            # Reset global state for each strategy test
            import lib.knowledge.knowledge_factory
            lib.knowledge.knowledge_factory._shared_kb = None
            with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
                with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                    mock_config.return_value = {
                        'knowledge': {
                            'csv_file_path': 'test.csv',
                            'vector_db': {'table_name': 'knowledge_base'},
                            'filters': {'valid_metadata_fields': ['category', 'tags']}
                        }
                    }
                    
                    with patch('lib.knowledge.knowledge_factory.PgVector') as mock_pgvector:
                        mock_vector_db = Mock()
                        mock_pgvector.return_value = mock_vector_db
                        
                        with patch('lib.knowledge.knowledge_factory.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            # Create result based on strategy
                            smart_load_result = {'strategy': strategy}
                            if strategy == 'incremental_update':
                                smart_load_result['new_rows_processed'] = 5
                            elif strategy == 'initial_load_with_hashes':
                                smart_load_result['entries_processed'] = 100
                            
                            with patch('lib.knowledge.smart_incremental_loader.SmartIncrementalLoader') as mock_loader:
                                mock_loader_instance = Mock()
                                mock_loader_instance.smart_load.return_value = smart_load_result
                                mock_loader.return_value = mock_loader_instance
                                
                                with patch('lib.knowledge.knowledge_factory.logger') as mock_logger:
                                    result = create_knowledge_base()
                                    
                                    assert result == mock_kb
                                    # Check that appropriate log message was called
                                    found_expected_log = any(
                                        expected_log_message in str(call) 
                                        for call in mock_logger.info.call_args_list
                                    )
                                    assert found_expected_log, f"Expected log message '{expected_log_message}' not found for strategy '{strategy}'"

    def test_thread_safety_multiple_calls(self):
        """Test thread safety with multiple simultaneous calls"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
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
                            
                            results = []
                            exceptions = []
                            
                            def create_kb():
                                try:
                                    kb = create_knowledge_base()
                                    results.append(kb)
                                except Exception as e:
                                    exceptions.append(e)
                            
                            # Create multiple threads
                            threads = [threading.Thread(target=create_kb) for _ in range(5)]
                            
                            # Start all threads
                            for thread in threads:
                                thread.start()
                            
                            # Wait for all threads to complete
                            for thread in threads:
                                thread.join()
                            
                            # Check results
                            assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
                            assert len(results) == 5
                            # All results should be the same instance (singleton pattern)
                            for result in results:
                                assert result is results[0]
                            
                            # Knowledge base should only be created once
                            mock_kb_class.assert_called_once()

    def test_get_knowledge_base_delegates_to_create(self):
        """Test that get_knowledge_base properly delegates to create_knowledge_base"""
        with patch('lib.knowledge.knowledge_factory.create_knowledge_base') as mock_create:
            mock_kb = Mock()
            mock_create.return_value = mock_kb
            
            config = {'test': 'config'}
            db_url = "postgresql://test:test@localhost:5432/test"
            num_documents = 15
            csv_path = "test.csv"
            
            result = get_knowledge_base(config, db_url, num_documents, csv_path)
            
            assert result == mock_kb
            mock_create.assert_called_once_with(config, db_url, num_documents, csv_path)

    def test_vector_db_configuration_parameters(self):
        """Test that vector database is configured with correct parameters"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            custom_config = {
                'knowledge': {
                    'csv_file_path': 'test.csv',
                    'vector_db': {
                        'table_name': 'custom_knowledge',
                        'embedder': 'text-embedding-ada-002',
                        'distance': 'euclidean'
                    },
                    'filters': {'valid_metadata_fields': ['domain', 'type']}
                }
            }
            
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
                        
                        result = create_knowledge_base(config=custom_config)
                        
                        assert result == mock_kb
                        # Verify PgVector was configured with custom parameters
                        mock_pgvector.assert_called_once()
                        args, kwargs = mock_pgvector.call_args
                        assert kwargs['table_name'] == 'custom_knowledge'
                        assert kwargs['schema'] == 'agno'
                        assert kwargs['distance'] == 'euclidean'

    def test_metadata_filters_configuration(self):
        """Test that metadata filters are properly configured"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            custom_config = {
                'knowledge': {
                    'csv_file_path': 'test.csv',
                    'vector_db': {'table_name': 'knowledge_base'},
                    'filters': {'valid_metadata_fields': ['domain', 'type', 'priority']}
                }
            }
            
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
                        
                        result = create_knowledge_base(config=custom_config)
                        
                        assert result == mock_kb
                        # Verify metadata filters were set
                        expected_filters = {'domain', 'type', 'priority'}
                        assert mock_kb.valid_metadata_filters == expected_filters

    def test_num_documents_parameter_handling(self):
        """Test that num_documents parameter is properly handled"""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
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
                            
                            custom_num_docs = 25
                            result = create_knowledge_base(num_documents=custom_num_docs)
                            
                            assert result == mock_kb
                            # Verify num_documents was set on the knowledge base
                            assert mock_kb.num_documents == custom_num_docs

    def test_existing_shared_kb_num_documents_update(self):
        """Test that existing shared KB gets updated num_documents"""
        # First create a knowledge base
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'vector_db': {'table_name': 'knowledge_base'},
                        'filters': {'valid_metadata_fields': ['category', 'tags']}
                    }
                }
                
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
                            
                            # First call creates KB with 10 documents
                            kb1 = create_knowledge_base(num_documents=10)
                            assert kb1.num_documents == 10
                            
                            # Second call should return same instance but update num_documents
                            kb2 = create_knowledge_base(num_documents=20)
                            assert kb2 is kb1  # Same instance
                            assert kb2.num_documents == 20  # Updated value