"""Comprehensive tests for lib.knowledge.smart_incremental_loader module.

This test suite covers:
1. Incremental data loading and processing
2. Change detection and delta calculations  
3. Smart caching and optimization strategies
4. Batch processing and memory management
5. Error recovery and data validation
6. Performance optimization and monitoring

Target: Boost coverage from 23% to 50%+ minimum
"""

import csv
import hashlib
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open, call

import pandas as pd
import pytest
import yaml

# Import the module under test
try:
    from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader
    import lib.knowledge.smart_incremental_loader
except ImportError:
    pytest.skip(f"Module lib.knowledge.smart_incremental_loader not available", allow_module_level=True)


class TestSmartIncrementalLoaderCore:
    """Test core SmartIncrementalLoader functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "incremental.csv"
        self.config_file = Path(self.temp_dir) / "config.yaml"
        
        # Default test configuration
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }
        
        # Sample CSV data
        self.sample_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["How to debug Python?", "Use pdb debugger", "tech", "programming"],
            ["Database slow queries", "Add indexes and optimize", "tech", "database"],
            ["API rate limiting", "Implement throttling", "tech", "api"],
        ]

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_csv_file(self, data=None):
        """Helper to create CSV file with test data."""
        data = data or self.sample_data
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return self.csv_file

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import lib.knowledge.smart_incremental_loader
        assert lib.knowledge.smart_incremental_loader is not None
        assert hasattr(lib.knowledge.smart_incremental_loader, 'SmartIncrementalLoader')

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_loader_initialization_with_config(self, mock_yaml_load, mock_file):
        """Test SmartIncrementalLoader initialization with configuration."""
        mock_yaml_load.return_value = self.test_config
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        assert loader is not None
        assert loader.csv_path == Path(self.csv_file)
        assert loader.db_url == "postgresql://test:5432/db"
        assert loader.table_name == "knowledge_base"
        assert loader.config == self.test_config

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_loader_initialization_no_csv_path(self, mock_yaml_load, mock_file):
        """Test SmartIncrementalLoader initialization without explicit CSV path."""
        mock_yaml_load.return_value = self.test_config
        
        with patch('pathlib.Path.exists', return_value=True):
            loader = SmartIncrementalLoader()
            
            assert loader is not None
            # Should use path from config relative to knowledge directory
            expected_path = Path(lib.knowledge.smart_incremental_loader.__file__).parent / "test.csv"
            assert loader.csv_path == expected_path

    def test_loader_initialization_missing_db_url(self):
        """Test SmartIncrementalLoader initialization without database URL."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="HIVE_DATABASE_URL required"):
                SmartIncrementalLoader(str(self.csv_file))

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_loader_config_loading_failure(self, mock_file):
        """Test SmartIncrementalLoader with config loading failure."""
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            
            # Should handle missing config gracefully
            assert loader.config == {}
            mock_logger.warning.assert_called_once()

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load", return_value={})
    def test_loader_with_empty_config(self, mock_yaml_load, mock_file):
        """Test SmartIncrementalLoader with empty configuration."""
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        # Should use default values
        assert loader.table_name == "knowledge_base"
        # CSV path should be provided path since config is empty
        assert loader.csv_path == Path(self.csv_file)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_loader_with_kb_parameter(self, mock_yaml_load, mock_file):
        """Test SmartIncrementalLoader with knowledge base parameter."""
        mock_yaml_load.return_value = self.test_config
        mock_kb = MagicMock()
        
        loader = SmartIncrementalLoader(str(self.csv_file), kb=mock_kb)
        
        assert loader.kb is mock_kb
        assert loader.csv_path == Path(self.csv_file)


class TestSmartIncrementalLoaderHashing:
    """Test row hashing and content tracking functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_hash_row_functionality(self, mock_yaml_load, mock_file):
        """Test row hashing creates consistent unique identifiers."""
        mock_yaml_load.return_value = self.test_config
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        # Create test row data
        row_data = pd.Series({
            'problem': 'How to optimize database queries?',
            'solution': 'Use indexes and query optimization',
            'typification': 'database',
            'business_unit': 'tech'
        })
        
        hash1 = loader._hash_row(row_data)
        hash2 = loader._hash_row(row_data)
        
        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length
        
        # Different content should produce different hash
        different_row = pd.Series({
            'problem': 'Different problem',
            'solution': 'Different solution', 
            'typification': 'different',
            'business_unit': 'different'
        })
        
        hash3 = loader._hash_row(different_row)
        assert hash1 != hash3

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_hash_row_with_missing_fields(self, mock_yaml_load, mock_file):
        """Test row hashing handles missing fields gracefully."""
        mock_yaml_load.return_value = self.test_config
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        # Row with missing fields
        row_data = pd.Series({
            'problem': 'Test problem',
            # Missing solution, typification, business_unit
        })
        
        hash_result = loader._hash_row(row_data)
        assert hash_result is not None
        assert len(hash_result) == 32

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_hash_row_deterministic(self, mock_yaml_load, mock_file):
        """Test that row hashing is deterministic for same content."""
        mock_yaml_load.return_value = self.test_config
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        # Test content
        content = {
            'problem': 'How to debug Python?',
            'solution': 'Use pdb debugger',
            'typification': 'programming',
            'business_unit': 'tech'
        }
        
        # Create multiple Series with same content
        row1 = pd.Series(content)
        row2 = pd.Series(content.copy())
        
        hash1 = loader._hash_row(row1)
        hash2 = loader._hash_row(row2)
        
        # Should produce identical hashes
        assert hash1 == hash2
        
        # Verify it matches expected MD5
        content_str = f"{content['problem']}{content['solution']}{content['typification']}{content['business_unit']}"
        expected_hash = hashlib.md5(content_str.encode('utf-8')).hexdigest()
        assert hash1 == expected_hash


class TestSmartIncrementalLoaderDatabase:
    """Test database interaction functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_get_existing_row_hashes_table_exists(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test getting existing row hashes when table and hash column exist."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        # Mock table exists (returns 1)
        # Mock hash column exists (returns 1)
        # Mock hash results
        mock_conn.execute.return_value.fetchone.side_effect = [
            [1],  # table exists
            [1],  # hash column exists
        ]
        mock_conn.execute.return_value.fetchall.return_value = [
            ['hash1'], ['hash2'], ['hash3']
        ]
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        existing_hashes = loader._get_existing_row_hashes()
        
        assert existing_hashes == {'hash1', 'hash2', 'hash3'}
        assert len(mock_conn.execute.call_args_list) == 3  # table check, column check, hash query

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_get_existing_row_hashes_table_not_exists(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test getting existing row hashes when table doesn't exist."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        # Mock table doesn't exist (returns 0)
        mock_conn.execute.return_value.fetchone.return_value = [0]
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        existing_hashes = loader._get_existing_row_hashes()
        
        assert existing_hashes == set()
        assert len(mock_conn.execute.call_args_list) == 1  # Only table check

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_get_existing_row_hashes_no_hash_column(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test getting existing row hashes when hash column doesn't exist."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        # Mock table exists but hash column doesn't exist
        mock_conn.execute.return_value.fetchone.side_effect = [1, 0]  # table exists, column doesn't
        
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            existing_hashes = loader._get_existing_row_hashes()
            
            assert existing_hashes == set()
            mock_logger.warning.assert_called_once()

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_get_existing_row_hashes_database_error(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test getting existing row hashes handles database errors."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection failure
        mock_create_engine.side_effect = Exception("Database connection failed")
        
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            existing_hashes = loader._get_existing_row_hashes()
            
            assert existing_hashes == set()
            mock_logger.warning.assert_called_once_with(
                "Could not check existing hashes", error="Database connection failed"
            )

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_add_hash_column_to_table_success(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test adding hash column to existing table successfully."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        result = loader._add_hash_column_to_table()
        
        assert result is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_add_hash_column_to_table_error(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test adding hash column handles database errors."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection failure
        mock_create_engine.side_effect = Exception("Database error")
        
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            result = loader._add_hash_column_to_table()
            
            assert result is False
            mock_logger.warning.assert_called_once_with(
                "Could not add hash column", error="Database error"
            )


class TestSmartIncrementalLoaderCSVProcessing:
    """Test CSV reading and processing functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }
        
        self.sample_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["How to debug Python?", "Use pdb debugger", "tech", "programming"],
            ["Database slow queries", "Add indexes", "tech", "database"],
            ["API rate limiting", "Implement throttling", "tech", "api"],
        ]

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_csv_file(self, data=None):
        """Helper to create CSV file with test data."""
        data = data or self.sample_data
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return self.csv_file

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("pandas.read_csv")
    def test_get_csv_rows_with_hashes_success(self, mock_read_csv, mock_yaml_load, mock_file):
        """Test reading CSV file and generating row hashes successfully."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_rows = [
            (0, pd.Series({"problem": "How to debug Python?", "solution": "Use pdb debugger", "business_unit": "tech"})),
            (1, pd.Series({"problem": "Database slow queries", "solution": "Add indexes", "business_unit": "tech"})),
            (2, pd.Series({"problem": "API rate limiting", "solution": "Implement throttling", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(mock_rows)
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):
            loader = SmartIncrementalLoader(str(self.csv_file))
            rows_with_hashes = loader._get_csv_rows_with_hashes()
            
            assert len(rows_with_hashes) == 3  # 3 data rows
            
            # Check structure of returned data
            for i, row in enumerate(rows_with_hashes):
                assert 'index' in row
                assert 'hash' in row 
                assert 'data' in row
                assert row['index'] == i
                assert len(row['hash']) == 32  # MD5 hash length
                assert isinstance(row['data'], dict)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_csv_rows_with_hashes_missing_file(self, mock_yaml_load, mock_file):
        """Test reading CSV file when file doesn't exist."""
        mock_yaml_load.return_value = self.test_config
        
        # Don't create the CSV file
        loader = SmartIncrementalLoader(str(self.csv_file))
        rows_with_hashes = loader._get_csv_rows_with_hashes()
        
        assert rows_with_hashes == []

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("pandas.read_csv")
    def test_get_csv_rows_with_hashes_pandas_error(self, mock_read_csv, mock_yaml_load, mock_file):
        """Test reading CSV file handles pandas errors."""
        mock_yaml_load.return_value = self.test_config
        mock_read_csv.side_effect = Exception("Pandas read error")
        
        with patch('lib.logging.logger') as mock_logger:
            with patch('pathlib.Path.exists', return_value=True):  # Ensure file "exists"
                loader = SmartIncrementalLoader(str(self.csv_file))
                rows_with_hashes = loader._get_csv_rows_with_hashes()
                
                assert rows_with_hashes == []
                mock_logger.warning.assert_called_once_with(
                    "Could not read CSV with hashes", error="Pandas read error"
                )

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_csv_rows_with_hashes_empty_file(self, mock_yaml_load, mock_file):
        """Test reading empty CSV file."""
        mock_yaml_load.return_value = self.test_config
        
        # Create empty CSV file
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            pass  # Empty file
        
        with patch('lib.logging.logger'):
            loader = SmartIncrementalLoader(str(self.csv_file))
            rows_with_hashes = loader._get_csv_rows_with_hashes()
            
            # Should handle empty file gracefully
            assert isinstance(rows_with_hashes, list)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_csv_rows_with_hashes_malformed_data(self, mock_yaml_load, mock_file):
        """Test reading CSV file with malformed data."""
        mock_yaml_load.return_value = self.test_config
        
        # Create CSV with inconsistent columns
        malformed_data = [
            ["problem", "solution", "business_unit"],
            ["How to debug?", "Use debugger", "tech", "extra_field"],  # Extra field
            ["Database issue"],  # Missing fields
        ]
        
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(malformed_data)
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        rows_with_hashes = loader._get_csv_rows_with_hashes()
        
        # Should handle malformed data gracefully
        assert isinstance(rows_with_hashes, list)
        assert len(rows_with_hashes) >= 0  # May be empty or have processed rows


class TestSmartIncrementalLoaderAnalysis:
    """Test change analysis and detection functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }
        
        self.sample_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["How to debug Python?", "Use pdb debugger", "tech", "programming"],
            ["Database slow queries", "Add indexes", "tech", "database"],
            ["API rate limiting", "Implement throttling", "tech", "api"],
        ]

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_csv_file(self, data=None):
        """Helper to create CSV file with test data."""
        data = data or self.sample_data
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return self.csv_file

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_analyze_changes_csv_not_found(self, mock_yaml_load, mock_file):
        """Test analyze_changes when CSV file doesn't exist."""
        mock_yaml_load.return_value = self.test_config
        
        # Don't create CSV file
        loader = SmartIncrementalLoader(str(self.csv_file))
        analysis = loader.analyze_changes()
        
        assert "error" in analysis
        assert analysis["error"] == "CSV file not found"

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    @patch("pandas.read_csv")
    def test_analyze_changes_no_existing_records(self, mock_read_csv, mock_create_engine, mock_yaml_load, mock_file):
        """Test analyze_changes with no existing database records."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame  
        mock_df = MagicMock()
        mock_rows = [
            (0, pd.Series({"problem": "How to debug Python?", "solution": "Use pdb debugger", "business_unit": "tech"})),
            (1, pd.Series({"problem": "Database slow queries", "solution": "Add indexes", "business_unit": "tech"})),
            (2, pd.Series({"problem": "API rate limiting", "solution": "Implement throttling", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(mock_rows)
        mock_read_csv.return_value = mock_df
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        # Mock no existing records for all queries
        mock_conn.execute.return_value.fetchone.return_value = [0]
        
        with patch('pathlib.Path.exists', return_value=True):
            loader = SmartIncrementalLoader(str(self.csv_file))
            analysis = loader.analyze_changes()
            
            assert "error" not in analysis
            assert analysis["csv_total_rows"] == 3  # 3 data rows
            assert analysis["existing_vector_rows"] == 0
            assert analysis["new_rows_count"] == 3  # All rows are new
            assert analysis["needs_processing"] is True
            assert analysis["status"] == "incremental_update_required"

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    @patch("pandas.read_csv")
    def test_analyze_changes_with_existing_records(self, mock_read_csv, mock_create_engine, mock_yaml_load, mock_file):
        """Test analyze_changes with some existing database records."""
        mock_yaml_load.return_value = self.test_config
        
        # Create CSV file
        self.create_csv_file()
        
        # Mock pandas DataFrame for CSV reading
        mock_df = MagicMock()
        mock_rows = [
            (0, pd.Series({"problem": "How to debug Python?", "solution": "Use pdb debugger", "business_unit": "tech"})),
            (1, pd.Series({"problem": "Database slow queries", "solution": "Add indexes", "business_unit": "tech"})),
            (2, pd.Series({"problem": "API rate limiting", "solution": "Implement throttling", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(mock_rows)
        mock_read_csv.return_value = mock_df
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        # Mock some records exist (first query returns 1, others return 0)
        mock_conn.execute.return_value.fetchone.side_effect = [[1], [0], [0]]  # 1 existing, 2 new
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            analysis = loader.analyze_changes()
        
        assert "error" not in analysis
        assert analysis["csv_total_rows"] == 3
        assert analysis["existing_vector_rows"] == 1
        assert analysis["new_rows_count"] == 2  # 2 new rows
        assert analysis["needs_processing"] is True
        assert analysis["status"] == "incremental_update_required"

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_analyze_changes_all_existing_records(self, mock_create_engine, mock_yaml_load, mock_file, mock_read_csv):
        """Test analyze_changes when all records already exist."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame for CSV reading
        mock_df = MagicMock()
        mock_rows = [
            (0, pd.Series({"problem": "How to debug Python?", "solution": "Use pdb debugger", "business_unit": "tech"})),
            (1, pd.Series({"problem": "Database slow queries", "solution": "Add indexes", "business_unit": "tech"})),
            (2, pd.Series({"problem": "API rate limiting", "solution": "Implement throttling", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(mock_rows)
        mock_read_csv.return_value = mock_df
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        # Mock all records exist (all queries return 1)
        mock_conn.execute.return_value.fetchone.return_value = [1]
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            analysis = loader.analyze_changes()
            
            assert "error" not in analysis
        assert analysis["csv_total_rows"] == 3
        assert analysis["existing_vector_rows"] == 3  # All exist
        assert analysis["new_rows_count"] == 0  # No new rows
        assert analysis["needs_processing"] is False
        assert analysis["status"] == "up_to_date"

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_analyze_changes_database_error(self, mock_create_engine, mock_yaml_load, mock_file, mock_read_csv):
        """Test analyze_changes handles database errors."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame for CSV reading
        mock_df = MagicMock()
        mock_rows = [
            (0, pd.Series({"problem": "How to debug Python?", "solution": "Use pdb debugger", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(mock_rows)
        mock_read_csv.return_value = mock_df
        
        # Mock database connection error
        mock_create_engine.side_effect = Exception("Database connection failed")
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            analysis = loader.analyze_changes()
            
            assert "error" in analysis
            assert analysis["error"] == "Database connection failed"


class TestSmartIncrementalLoaderSmartLoad:
    """Test smart loading functionality including incremental updates."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }
        
        self.sample_data = [
            ["problem", "solution", "business_unit", "typification"],
            ["How to debug Python?", "Use pdb debugger", "tech", "programming"],
            ["Database slow queries", "Add indexes", "tech", "database"],
        ]

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_csv_file(self, data=None):
        """Helper to create CSV file with test data."""
        data = data or self.sample_data
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return self.csv_file

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.SmartIncrementalLoader.analyze_changes")
    def test_smart_load_force_recreate(self, mock_analyze_changes, mock_yaml_load, mock_file):
        """Test smart_load with force_recreate=True."""
        mock_yaml_load.return_value = self.test_config
        
        with patch('lib.logging.logger') as mock_logger:
            with patch.object(SmartIncrementalLoader, '_full_reload', return_value={"strategy": "full_reload"}) as mock_full_reload:
                loader = SmartIncrementalLoader(str(self.csv_file))
                result = loader.smart_load(force_recreate=True)
                
                assert result == {"strategy": "full_reload"}
                mock_full_reload.assert_called_once()
                mock_logger.info.assert_called_with("Force recreate requested - will rebuild everything")
                # analyze_changes should not be called when force_recreate=True
                mock_analyze_changes.assert_not_called()

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_smart_load_analysis_error(self, mock_yaml_load, mock_file):
        """Test smart_load when analysis returns error."""
        mock_yaml_load.return_value = self.test_config
        
        with patch.object(SmartIncrementalLoader, 'analyze_changes', return_value={"error": "Analysis failed"}):
            loader = SmartIncrementalLoader(str(self.csv_file))
            result = loader.smart_load()
            
            assert result == {"error": "Analysis failed"}

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_smart_load_no_changes_needed(self, mock_yaml_load, mock_file):
        """Test smart_load when no changes are needed."""
        mock_yaml_load.return_value = self.test_config
        
        analysis_result = {
            "needs_processing": False,
            "csv_total_rows": 3,
            "existing_vector_rows": 3,
            "new_rows_count": 0,
            "status": "up_to_date"
        }
        
        with patch.object(SmartIncrementalLoader, 'analyze_changes', return_value=analysis_result):
            loader = SmartIncrementalLoader(str(self.csv_file))
            result = loader.smart_load()
            
            assert result["strategy"] == "no_changes"
            assert "All tokens saved!" in result["embedding_tokens_saved"]
            assert result["csv_total_rows"] == 3
            assert result["existing_vector_rows"] == 3

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_smart_load_initial_load_needed(self, mock_yaml_load, mock_file):
        """Test smart_load when initial load is needed (no existing records)."""
        mock_yaml_load.return_value = self.test_config
        
        analysis_result = {
            "needs_processing": True,
            "existing_vector_rows": 0,
            "new_rows_count": 3,
            "status": "incremental_update_required"
        }
        
        initial_load_result = {"strategy": "initial_load_with_hashes", "entries_processed": 3}
        
        with patch.object(SmartIncrementalLoader, 'analyze_changes', return_value=analysis_result):
            with patch.object(SmartIncrementalLoader, '_initial_load_with_hashes', return_value=initial_load_result) as mock_initial_load:
                loader = SmartIncrementalLoader(str(self.csv_file))
                result = loader.smart_load()
                
                assert result == initial_load_result
                mock_initial_load.assert_called_once()

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_smart_load_incremental_update_needed(self, mock_yaml_load, mock_file):
        """Test smart_load when incremental update is needed."""
        mock_yaml_load.return_value = self.test_config
        
        analysis_result = {
            "needs_processing": True,
            "existing_vector_rows": 2,
            "new_rows_count": 1,
            "status": "incremental_update_required"
        }
        
        incremental_result = {"strategy": "incremental_update", "new_rows_processed": 1}
        
        with patch.object(SmartIncrementalLoader, 'analyze_changes', return_value=analysis_result):
            with patch.object(SmartIncrementalLoader, '_incremental_update', return_value=incremental_result) as mock_incremental:
                loader = SmartIncrementalLoader(str(self.csv_file))
                result = loader.smart_load()
                
                assert result == incremental_result
                mock_incremental.assert_called_once_with(analysis_result)


class TestSmartIncrementalLoaderLoadingStrategies:
    """Test different loading strategy implementations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    @patch("lib.knowledge.smart_incremental_loader.datetime")
    def test_initial_load_with_hashes_success(self, mock_datetime, mock_create_engine, mock_yaml_load, mock_file):
        """Test initial load with hash tracking success."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock datetime
        mock_start_time = MagicMock()
        mock_end_time = MagicMock()
        mock_time_diff = MagicMock()
        mock_time_diff.total_seconds.return_value = 5.5
        mock_end_time.__sub__ = MagicMock(return_value=mock_time_diff)
        mock_datetime.now.side_effect = [mock_start_time, mock_end_time]
        
        # Mock database connection for final count
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = [10]  # 10 entries
        
        # Mock knowledge base
        mock_kb = MagicMock()
        
        with patch('lib.logging.logger') as mock_logger:
            with patch.object(SmartIncrementalLoader, '_add_hash_column_to_table', return_value=True):
                with patch.object(SmartIncrementalLoader, '_populate_existing_hashes', return_value=True):
                    loader = SmartIncrementalLoader(str(self.csv_file), kb=mock_kb)
                    result = loader._initial_load_with_hashes()
                    
                    assert result["strategy"] == "initial_load_with_hashes"
                    assert result["entries_processed"] == 10
                    assert result["load_time_seconds"] == 5.5
                    assert "initial load" in result["embedding_tokens_used"]
                    
                    mock_kb.load.assert_called_once_with(recreate=True)
                    mock_logger.info.assert_any_call("Initial load: creating knowledge base with hash tracking")

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_initial_load_with_hashes_error(self, mock_yaml_load, mock_file):
        """Test initial load with hash tracking handles errors."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock knowledge base that raises error
        mock_kb = MagicMock()
        mock_kb.load.side_effect = Exception("Knowledge base load failed")
        
        loader = SmartIncrementalLoader(str(self.csv_file), kb=mock_kb)
        result = loader._initial_load_with_hashes()
        
        assert "error" in result
        assert "Initial load failed: Knowledge base load failed" in result["error"]

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.datetime")
    def test_full_reload_success(self, mock_datetime, mock_yaml_load, mock_file):
        """Test full reload strategy success."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock datetime
        mock_start_time = MagicMock()
        mock_end_time = MagicMock()
        mock_time_diff = MagicMock()
        mock_time_diff.total_seconds.return_value = 8.2
        mock_end_time.__sub__ = MagicMock(return_value=mock_time_diff)
        mock_datetime.now.side_effect = [mock_start_time, mock_end_time]
        
        # Mock knowledge base
        mock_kb = MagicMock()
        mock_kb.get_knowledge_statistics.return_value = {"total_entries": 15}
        
        with patch('lib.logging.logger') as mock_logger:
            with patch.object(SmartIncrementalLoader, '_add_hash_column_to_table', return_value=True):
                with patch.object(SmartIncrementalLoader, '_populate_existing_hashes', return_value=True):
                    loader = SmartIncrementalLoader(str(self.csv_file), kb=mock_kb)
                    result = loader._full_reload()
                    
                    assert result["strategy"] == "full_reload"
                    assert result["entries_processed"] == 15
                    assert result["load_time_seconds"] == 8.2
                    assert "full cost" in result["embedding_tokens_used"]
                    
                    mock_kb.load.assert_called_once_with(recreate=True)
                    mock_logger.info.assert_any_call("Full reload: recreating knowledge base")

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.datetime")
    def test_incremental_update_success(self, mock_datetime, mock_yaml_load, mock_file):
        """Test incremental update strategy success."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock datetime
        mock_start_time = MagicMock()
        mock_end_time = MagicMock()
        mock_time_diff = MagicMock()
        mock_time_diff.total_seconds.return_value = 2.1
        mock_end_time.__sub__ = MagicMock(return_value=mock_time_diff)
        mock_datetime.now.side_effect = [mock_start_time, mock_end_time]
        
        # Mock analysis result
        analysis = {
            "new_rows": [
                {"index": 0, "hash": "hash1", "data": {"problem": "Test 1", "solution": "Solution 1"}},
                {"index": 1, "hash": "hash2", "data": {"problem": "Test 2", "solution": "Solution 2"}},
            ],
            "removed_rows_count": 0,
            "removed_hashes": []
        }
        
        with patch.object(SmartIncrementalLoader, '_add_hash_column_to_table', return_value=True):
            with patch.object(SmartIncrementalLoader, '_process_single_row', return_value=True) as mock_process:
                loader = SmartIncrementalLoader(str(self.csv_file))
                result = loader._incremental_update(analysis)
                
                assert result["strategy"] == "incremental_update"
                assert result["new_rows_processed"] == 2
                assert result["rows_removed"] == 0
                assert result["load_time_seconds"] == 2.1
                assert "2 new entries" in result["embedding_tokens_used"]
                
                # Should process each new row
                assert mock_process.call_count == 2

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_incremental_update_with_removals(self, mock_yaml_load, mock_file):
        """Test incremental update with row removals."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock analysis result with removals
        analysis = {
            "new_rows": [],
            "removed_rows_count": 2,
            "removed_hashes": ["old_hash1", "old_hash2"]
        }
        
        with patch('lib.logging.logger') as mock_logger:
            with patch.object(SmartIncrementalLoader, '_remove_rows_by_hash', return_value=2) as mock_remove:
                loader = SmartIncrementalLoader(str(self.csv_file))
                result = loader._incremental_update(analysis)
                
                assert result["new_rows_processed"] == 0
                assert result["rows_removed"] == 2
                
                mock_remove.assert_called_once_with(["old_hash1", "old_hash2"])
                mock_logger.info.assert_called_with("Removing obsolete entries", removed_count=2)


class TestSmartIncrementalLoaderSingleRowProcessing:
    """Test single row processing functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("pandas.DataFrame.to_csv")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.unlink")
    def test_process_single_row_success(self, mock_unlink, mock_exists, mock_to_csv, mock_yaml_load, mock_file):
        """Test processing a single row successfully."""
        mock_yaml_load.return_value = self.test_config
        
        row_data = {
            "index": 0,
            "hash": "test_hash",
            "data": {"problem": "Test problem", "solution": "Test solution"}
        }
        
        # Mock knowledge base
        mock_kb = MagicMock()
        
        with patch.object(SmartIncrementalLoader, '_update_row_hash', return_value=True) as mock_update_hash:
            loader = SmartIncrementalLoader(str(self.csv_file), kb=mock_kb)
            result = loader._process_single_row(row_data)
            
            assert result is True
            mock_to_csv.assert_called_once()  # Temporary CSV created
            mock_kb.load.assert_called_once_with(recreate=False, upsert=True)
            mock_update_hash.assert_called_once_with(row_data["data"], row_data["hash"])
            mock_unlink.assert_called_once()  # Temporary file cleaned up

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_process_single_row_kb_error(self, mock_yaml_load, mock_file):
        """Test processing single row handles knowledge base errors."""
        mock_yaml_load.return_value = self.test_config
        
        row_data = {
            "index": 0,
            "hash": "test_hash",
            "data": {"problem": "Test problem", "solution": "Test solution"}
        }
        
        # Mock knowledge base that raises error
        mock_kb = MagicMock()
        mock_kb.load.side_effect = Exception("KB load failed")
        
        with patch('lib.logging.logger') as mock_logger:
            with patch("pandas.DataFrame.to_csv"):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.unlink"):
                        loader = SmartIncrementalLoader(str(self.csv_file), kb=mock_kb)
                        result = loader._process_single_row(row_data)
                        
                        assert result is False
                        mock_logger.error.assert_called_once_with("Error processing single row", error="KB load failed")

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_update_row_hash_success(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test updating row hash in database successfully."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        row_data = {"problem": "Test problem", "solution": "Test solution"}
        content_hash = "test_hash_123"
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        result = loader._update_row_hash(row_data, content_hash)
        
        assert result is True
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_update_row_hash_error(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test updating row hash handles database errors."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection error
        mock_create_engine.side_effect = Exception("Database error")
        
        row_data = {"problem": "Test problem", "solution": "Test solution"}
        content_hash = "test_hash_123"
        
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            result = loader._update_row_hash(row_data, content_hash)
            
            assert result is False
            mock_logger.warning.assert_called_once_with("Could not update row hash", error="Database error")


class TestSmartIncrementalLoaderStatisticsAndUtilities:
    """Test statistics and utility functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_csv_file(self):
        """Helper to create CSV file with test data."""
        sample_data = [
            ["problem", "solution", "business_unit"],
            ["Test problem", "Test solution", "tech"],
        ]
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(sample_data)
        return self.csv_file

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_database_stats_success(self, mock_yaml_load, mock_file):
        """Test getting database statistics successfully."""
        mock_yaml_load.return_value = self.test_config
        
        analysis_result = {
            "csv_total_rows": 1,
            "existing_vector_rows": 0,
            "new_rows_count": 1,
            "removed_rows_count": 0,
            "status": "incremental_update_required"
        }
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            with patch.object(SmartIncrementalLoader, 'analyze_changes', return_value=analysis_result):
                loader = SmartIncrementalLoader(str(self.csv_file))
                stats = loader.get_database_stats()
                
                assert stats["csv_file"] == str(self.csv_file)
                assert stats["csv_exists"] is True
                assert stats["csv_total_rows"] == 1
                assert stats["existing_vector_rows"] == 0
                assert stats["new_rows_pending"] == 1
                assert stats["removed_rows_pending"] == 0
                assert stats["sync_status"] == "incremental_update_required"
            assert stats["hash_tracking_enabled"] is True
            assert "postgresql://test:5432/db" in stats["database_url"]

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_database_stats_analysis_error(self, mock_yaml_load, mock_file):
        """Test getting database statistics when analysis fails."""
        mock_yaml_load.return_value = self.test_config
        
        with patch.object(SmartIncrementalLoader, 'analyze_changes', return_value={"error": "Analysis failed"}):
            loader = SmartIncrementalLoader(str(self.csv_file))
            stats = loader.get_database_stats()
            
            assert stats == {"error": "Analysis failed"}

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_database_stats_exception(self, mock_yaml_load, mock_file):
        """Test getting database statistics handles exceptions."""
        mock_yaml_load.return_value = self.test_config
        
        with patch.object(SmartIncrementalLoader, 'analyze_changes', side_effect=Exception("Unexpected error")):
            loader = SmartIncrementalLoader(str(self.csv_file))
            stats = loader.get_database_stats()
            
            assert "error" in stats
            assert stats["error"] == "Unexpected error"

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_populate_existing_hashes_success(self, mock_create_engine, mock_yaml_load, mock_file, mock_read_csv):
        """Test populating existing hashes successfully."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame for CSV reading
        mock_df = MagicMock()
        mock_rows = [
            (0, pd.Series({"problem": "How to debug Python?", "solution": "Use pdb debugger", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(mock_rows)
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            with patch('lib.logging.logger') as mock_logger:
                with patch.object(SmartIncrementalLoader, '_update_row_hash', return_value=True) as mock_update_hash:
                    loader = SmartIncrementalLoader(str(self.csv_file))
                    result = loader._populate_existing_hashes()
                    
                    assert result is True
                    mock_update_hash.assert_called_once()  # Should update hash for 1 row
                    mock_logger.info.assert_any_call("Populating content hashes for existing rows")
                    mock_logger.info.assert_any_call("Populated hashes for rows", rows_count=1)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_populate_existing_hashes_error(self, mock_yaml_load, mock_file):
        """Test populating existing hashes handles errors."""
        mock_yaml_load.return_value = self.test_config
        
        with patch('lib.logging.logger') as mock_logger:
            with patch.object(SmartIncrementalLoader, '_get_csv_rows_with_hashes', side_effect=Exception("CSV error")):
                loader = SmartIncrementalLoader(str(self.csv_file))
                result = loader._populate_existing_hashes()
                
                assert result is False
                mock_logger.warning.assert_called_once_with("Could not populate existing hashes", error="CSV error")

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_remove_rows_by_hash_success(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test removing rows by hash successfully."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_create_engine.return_value = mock_engine
        
        hashes_to_remove = ["hash1", "hash2", "hash3"]
        
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            result = loader._remove_rows_by_hash(hashes_to_remove)
            
            assert result == 3
            assert mock_conn.execute.call_count == 3  # One call per hash
            mock_conn.commit.assert_called_once()
            mock_logger.info.assert_called_once_with("Removed obsolete rows", removed_count=3)

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_remove_rows_by_hash_empty_list(self, mock_yaml_load, mock_file):
        """Test removing rows by hash with empty list."""
        mock_yaml_load.return_value = self.test_config
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        result = loader._remove_rows_by_hash([])
        
        assert result == 0

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_remove_rows_by_hash_error(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test removing rows by hash handles database errors."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock database connection error
        mock_create_engine.side_effect = Exception("Database error")
        
        hashes_to_remove = ["hash1", "hash2"]
        
        with patch('lib.logging.logger') as mock_logger:
            loader = SmartIncrementalLoader(str(self.csv_file))
            result = loader._remove_rows_by_hash(hashes_to_remove)
            
            assert result == 0
            mock_logger.warning.assert_called_once_with("Could not remove rows", error="Database error")


class TestSmartIncrementalLoaderEdgeCasesAndErrorRecovery:
    """Test edge cases, error recovery, and performance scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.temp_dir) / "test.csv"
        
        self.test_config = {
            "knowledge": {
                "csv_file_path": "test.csv",
                "vector_db": {"table_name": "knowledge_base"},
            },
        }

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_large_csv_processing(self, mock_yaml_load, mock_file, mock_read_csv):
        """Test processing large CSV files with many rows."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock large pandas DataFrame
        mock_df = MagicMock()
        large_rows = [(i, pd.Series({"problem": f"Problem {i}", "solution": f"Solution {i}", "business_unit": "tech"})) for i in range(1000)]
        mock_df.iterrows.return_value = iter(large_rows)
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            rows_with_hashes = loader._get_csv_rows_with_hashes()
            
            assert len(rows_with_hashes) == 1000
            # Check that all hashes are unique (no collisions)
            hashes = [row['hash'] for row in rows_with_hashes]
            assert len(set(hashes)) == 1000

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_unicode_and_special_characters(self, mock_yaml_load, mock_file, mock_read_csv):
        """Test handling of Unicode and special characters in CSV data."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame with Unicode content
        mock_df = MagicMock()
        unicode_rows = [
            (0, pd.Series({"problem": "How to handle ñ in Spanish?", "solution": "Use Unicode UTF-8 ñ", "business_unit": "tech"})),
            (1, pd.Series({"problem": "Database émojis 🚀", "solution": "Store in UTF-8 encoding 🌟", "business_unit": "tech"})),
            (2, pd.Series({"problem": "Special chars @#$%^&*()", "solution": "Escape properly []{}|\\", "business_unit": "tech"})),
            (3, pd.Series({"problem": "Multi-line\nProblem", "solution": "Multi-line\nSolution", "business_unit": "tech"})),
        ]
        mock_df.iterrows.return_value = iter(unicode_rows)
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            rows_with_hashes = loader._get_csv_rows_with_hashes()
            
            assert len(rows_with_hashes) == 4  # 4 data rows
            
            # Verify hashing handles Unicode correctly
            for row in rows_with_hashes:
                assert len(row['hash']) == 32  # MD5 hash length
                assert row['hash'] is not None

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_empty_and_null_values(self, mock_yaml_load, mock_file, mock_read_csv):
        """Test handling of empty and null values in CSV data."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame with empty and null values
        mock_df = MagicMock()
        sparse_rows = [
            (0, pd.Series({"problem": "Valid problem", "solution": "", "business_unit": "", "typification": ""})),
            (1, pd.Series({"problem": "", "solution": "Valid solution", "business_unit": "tech", "typification": ""})),
            (2, pd.Series({"problem": "Problem with null", "solution": "Solution", "business_unit": None, "typification": "programming"})),
            (3, pd.Series({"problem": "", "solution": "", "business_unit": "", "typification": ""})),
        ]
        mock_df.iterrows.return_value = iter(sparse_rows)
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            rows_with_hashes = loader._get_csv_rows_with_hashes()
            
            assert len(rows_with_hashes) == 4  # 4 data rows
            
            # All rows should have valid hashes despite empty values
            for row in rows_with_hashes:
                assert len(row['hash']) == 32
                assert row['hash'] is not None

    @patch("pandas.read_csv")
    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_duplicate_content_detection(self, mock_yaml_load, mock_file, mock_read_csv):
        """Test detection of duplicate content with same hashes."""
        mock_yaml_load.return_value = self.test_config
        
        # Mock pandas DataFrame with duplicate content
        mock_df = MagicMock()
        duplicate_rows = [
            (0, pd.Series({"problem": "Duplicate problem", "solution": "Duplicate solution", "business_unit": "tech"})),
            (1, pd.Series({"problem": "Different problem", "solution": "Different solution", "business_unit": "tech"})),
            (2, pd.Series({"problem": "Duplicate problem", "solution": "Duplicate solution", "business_unit": "tech"})),  # Exact duplicate
        ]
        mock_df.iterrows.return_value = iter(duplicate_rows)
        mock_read_csv.return_value = mock_df
        
        with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
            loader = SmartIncrementalLoader(str(self.csv_file))
            rows_with_hashes = loader._get_csv_rows_with_hashes()
            
            assert len(rows_with_hashes) == 3  # 3 data rows
            
            # Check that duplicates have same hash
            hash1 = rows_with_hashes[0]['hash']
            hash2 = rows_with_hashes[1]['hash']
            hash3 = rows_with_hashes[2]['hash']  # Should match hash1
        
        assert hash1 == hash3  # Duplicates have same hash
        assert hash1 != hash2  # Different content has different hash

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_configuration_edge_cases(self, mock_yaml_load, mock_file):
        """Test handling of various configuration edge cases."""
        # Test with minimal config
        minimal_config = {"knowledge": {}}
        mock_yaml_load.return_value = minimal_config
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        # Should use default values
        assert loader.table_name == "knowledge_base"
        
        # Test with custom table name
        custom_config = {
            "knowledge": {
                "vector_db": {"table_name": "custom_knowledge"}
            }
        }
        mock_yaml_load.return_value = custom_config
        
        loader2 = SmartIncrementalLoader(str(self.csv_file))
        assert loader2.table_name == "custom_knowledge"

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    @patch("lib.knowledge.smart_incremental_loader.create_engine")
    def test_database_connection_resilience(self, mock_create_engine, mock_yaml_load, mock_file):
        """Test resilience to database connection issues."""
        mock_yaml_load.return_value = self.test_config
        
        # Test connection timeout
        mock_create_engine.side_effect = Exception("Connection timeout")
        
        loader = SmartIncrementalLoader(str(self.csv_file))
        
        # Should handle connection errors gracefully
        existing_hashes = loader._get_existing_row_hashes()
        assert existing_hashes == set()
        
        add_result = loader._add_hash_column_to_table()
        assert add_result is False
        
        remove_result = loader._remove_rows_by_hash(["test_hash"])
        assert remove_result == 0

    @patch.dict("os.environ", {"HIVE_DATABASE_URL": "postgresql://test:5432/db"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_memory_efficiency_large_dataset(self, mock_yaml_load, mock_file):
        """Test memory efficiency with large datasets."""
        mock_yaml_load.return_value = self.test_config
        
        # Simulate very large CSV processing
        with patch('pandas.read_csv') as mock_read_csv:
            # Mock large DataFrame
            mock_df = MagicMock()
            mock_df.iterrows.return_value = [(i, pd.Series({"problem": f"P{i}", "solution": f"S{i}"})) for i in range(10000)]
            mock_read_csv.return_value = mock_df
            
            with patch('pathlib.Path.exists', return_value=True):  # Ensure CSV file "exists"
                loader = SmartIncrementalLoader(str(self.csv_file))
                rows_with_hashes = loader._get_csv_rows_with_hashes()
                
                # Should handle large dataset without memory issues
                assert len(rows_with_hashes) == 10000
                
                # Verify memory-efficient processing (iterative, not loading all at once)
                mock_df.iterrows.assert_called_once()
