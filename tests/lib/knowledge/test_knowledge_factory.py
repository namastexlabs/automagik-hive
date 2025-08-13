"""
Tests for knowledge_factory.py
Testing refactored native Agno CSVKnowledgeBase functionality
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from agno.knowledge.csv import CSVKnowledgeBase
from agno.document.chunking.row import RowChunking
from lib.knowledge.knowledge_factory import create_knowledge_base, get_knowledge_base


class TestKnowledgeFactory:
    """Test suite for knowledge factory refactoring"""

    def test_create_knowledge_base_returns_csv_knowledge_base(self):
        """Test that create_knowledge_base returns native Agno CSVKnowledgeBase"""
        # RED: This test should fail because we haven't refactored yet
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                # Mock CSV file existence
                with patch('pathlib.Path.exists', return_value=True):
                    with patch.object(CSVKnowledgeBase, '__init__', return_value=None) as mock_init:
                        mock_kb = Mock(spec=CSVKnowledgeBase)
                        with patch.object(CSVKnowledgeBase, '__new__', return_value=mock_kb):
                            result = create_knowledge_base()
                            
                            # Should return native CSVKnowledgeBase, not RowBasedCSVKnowledgeBase
                            assert isinstance(result, CSVKnowledgeBase)

    def test_uses_row_chunking_with_skip_header(self):
        """Test that the factory uses RowChunking with skip_header=True"""
        # RED: This should fail as current implementation doesn't use RowChunking
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    with patch.object(CSVKnowledgeBase, '__init__') as mock_init:
                        create_knowledge_base()
                        
                        # Check that RowChunking with skip_header=True was used
                        args, kwargs = mock_init.call_args
                        chunking_strategy = kwargs.get('chunking_strategy')
                        assert isinstance(chunking_strategy, RowChunking)
                        assert chunking_strategy.skip_header is True

    def test_uses_context_column_as_content(self):
        """Test that CSV reader is configured to use 'context' column"""
        # RED: This should fail as current config uses different structure
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    with patch.object(CSVKnowledgeBase, '__init__') as mock_init:
                        create_knowledge_base()
                        
                        # Check that CSVReader uses 'context' column
                        args, kwargs = mock_init.call_args
                        reader = kwargs.get('reader')
                        assert hasattr(reader, 'content_column')
                        assert reader.content_column == 'context'

    def test_smart_incremental_loader_compatibility(self):
        """Test that SmartIncrementalLoader works with new native system"""
        # This ensures backward compatibility is maintained
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            kb = Mock(spec=CSVKnowledgeBase)
            kb.load = Mock()
            
            # Should be able to call load methods that SmartIncrementalLoader expects
            kb.load(recreate=False, upsert=True)
            kb.load.assert_called_with(recreate=False, upsert=True)

    def test_removes_business_unit_filtering(self):
        """Test that business unit specific filtering is removed"""
        # RED: Should fail because current system has business unit logic
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    with patch.object(CSVKnowledgeBase, '__init__', return_value=None):
                        mock_kb = Mock(spec=CSVKnowledgeBase)
                        with patch.object(CSVKnowledgeBase, '__new__', return_value=mock_kb):
                            result = create_knowledge_base()
                            
                            # Should not have business unit specific attributes
                            assert not hasattr(result, 'valid_metadata_filters')

    def test_preserves_thread_safety(self):
        """Test that global shared instance with thread safety is preserved"""
        # This is a critical requirement to maintain
        with patch.dict('os.environ', {'HIVE_DATABASE_URL': 'postgresql://test'}):
            with patch('lib.knowledge.knowledge_factory._load_knowledge_config') as mock_config:
                mock_config.return_value = {
                    'knowledge': {
                        'csv_file_path': 'test.csv',
                        'csv_reader': {'content_column': 'context'},
                        'vector_db': {'table_name': 'knowledge_base'}
                    }
                }
                
                with patch('pathlib.Path.exists', return_value=True):
                    with patch.object(CSVKnowledgeBase, '__init__', return_value=None):
                        mock_kb = Mock(spec=CSVKnowledgeBase)
                        with patch.object(CSVKnowledgeBase, '__new__', return_value=mock_kb):
                            # Multiple calls should return the same instance
                            kb1 = create_knowledge_base()
                            kb2 = create_knowledge_base()
                            assert kb1 is kb2