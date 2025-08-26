"""Tests for CTE Data Monitor

Test suite for hot reload system that monitors CTE JSON files.
"""

import pytest
import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from ai.agents.jack_retrieval.cte_data_monitor import (
    CTEDataMonitor,
    CTEDataHandler,
    initialize_cte_monitoring
)


class TestCTEDataMonitor:
    """Test cases for CTE Data Monitor."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = CTEDataMonitor(cte_directory=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        if self.monitor.is_monitoring:
            self.monitor.stop_monitoring()
    
    def test_monitor_initialization(self):
        """Test CTE monitor initialization."""
        assert self.monitor.cte_dir == Path(self.temp_dir)
        assert not self.monitor.is_monitoring
        assert len(self.monitor.vector_update_callbacks) == 0
    
    def test_add_vector_update_callback(self):
        """Test adding vector update callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        self.monitor.add_vector_update_callback(callback1)
        self.monitor.add_vector_update_callback(callback2)
        
        assert len(self.monitor.vector_update_callbacks) == 2
        assert callback1 in self.monitor.vector_update_callbacks
        assert callback2 in self.monitor.vector_update_callbacks
    
    def test_load_cte_data_valid(self):
        """Test loading valid CTE data."""
        # Create test CTE file
        test_data = {
            "batch_info": {
                "batch_id": "test_batch",
                "total_ctes": 2
            },
            "orders": [
                {
                    "po_number": "600714860",
                    "status": "PENDING",
                    "ctes": [{"NF/CTE": "12345", "valor_chave": "100.00"}],
                    "po_total_value": 100.0
                }
            ],
            "summary": {
                "total_orders": 1,
                "total_ctes": 1,
                "total_value": 100.0
            }
        }
        
        test_file = Path(self.temp_dir) / "test_cte.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        loaded_data = self.monitor.load_cte_data(test_file)
        
        assert loaded_data is not None
        assert loaded_data['batch_info']['batch_id'] == 'test_batch'
        assert len(loaded_data['orders']) == 1
        assert loaded_data['orders'][0]['po_number'] == '600714860'
    
    def test_load_cte_data_invalid_json(self):
        """Test loading invalid JSON data."""
        test_file = Path(self.temp_dir) / "invalid.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        loaded_data = self.monitor.load_cte_data(test_file)
        assert loaded_data is None
    
    def test_load_cte_data_missing_orders(self):
        """Test loading CTE data without orders."""
        test_data = {"batch_info": {"batch_id": "test"}}
        
        test_file = Path(self.temp_dir) / "no_orders.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        loaded_data = self.monitor.load_cte_data(test_file)
        assert loaded_data is None
    
    def test_get_latest_cte_file_empty_dir(self):
        """Test getting latest CTE file from empty directory."""
        latest = self.monitor.get_latest_cte_file()
        assert latest is None
    
    def test_get_latest_cte_file_with_files(self):
        """Test getting latest CTE file with multiple files."""
        # Create test files with different timestamps
        file1 = Path(self.temp_dir) / "consolidated_ctes_daily_20250824_120000.json"
        file2 = Path(self.temp_dir) / "consolidated_ctes_daily_20250824_140000.json"
        file3 = Path(self.temp_dir) / "other_file.json"  # Should be ignored
        
        file1.write_text('{"orders": []}')
        file2.write_text('{"orders": []}')
        file3.write_text('{"data": []}')
        
        # file2 should be latest based on name pattern
        latest = self.monitor.get_latest_cte_file()
        assert latest is not None
        assert "consolidated_ctes_daily_" in latest.name
    
    def test_get_all_cte_files(self):
        """Test getting all CTE files."""
        # Create test files
        file1 = Path(self.temp_dir) / "consolidated_ctes_daily_20250824_120000.json"
        file2 = Path(self.temp_dir) / "consolidated_ctes_daily_20250824_140000.json"
        file3 = Path(self.temp_dir) / "other_file.json"  # Should be ignored
        
        file1.write_text('{"orders": []}')
        file2.write_text('{"orders": []}')
        file3.write_text('{"data": []}')
        
        all_files = self.monitor.get_all_cte_files()
        assert len(all_files) == 2
        assert all(("consolidated_ctes_daily_" in f.name) for f in all_files)
    
    @pytest.mark.asyncio
    async def test_handle_cte_file_change(self):
        """Test handling CTE file changes."""
        # Create test file
        test_data = {
            "batch_info": {"batch_id": "test", "total_ctes": 1},
            "orders": [{"po_number": "123", "status": "PENDING"}],
            "summary": {"total_orders": 1, "total_ctes": 1, "total_value": 100.0}
        }
        
        test_file = Path(self.temp_dir) / "consolidated_ctes_daily_test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Add mock callback
        callback = AsyncMock()
        self.monitor.add_vector_update_callback(callback)
        
        # Handle file change
        await self.monitor.handle_cte_file_change(test_file)
        
        # Verify callback was called
        callback.assert_called_once_with(test_file, test_data)
    
    @pytest.mark.asyncio
    async def test_get_current_cte_data(self):
        """Test getting current CTE data."""
        # Create test file
        test_data = {
            "batch_info": {"batch_id": "current"},
            "orders": [{"po_number": "current_po"}],
            "summary": {"total_orders": 1}
        }
        
        test_file = Path(self.temp_dir) / "consolidated_ctes_daily_current.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        current_data = await self.monitor.get_current_cte_data()
        
        assert current_data is not None
        assert current_data['batch_info']['batch_id'] == 'current'
        assert current_data['orders'][0]['po_number'] == 'current_po'


class TestCTEDataHandler:
    """Test cases for CTE Data Handler."""
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        callback = Mock()
        handler = CTEDataHandler(callback)
        
        assert handler.callback_func == callback
        assert handler.debounce_time == 2.0
        assert len(handler.last_modified) == 0
    
    def test_handler_ignores_directories(self):
        """Test handler ignores directory events."""
        callback = Mock()
        handler = CTEDataHandler(callback)
        
        # Mock directory event
        event = Mock()
        event.is_directory = True
        event.src_path = "/path/to/directory"
        
        handler.on_modified(event)
        handler.on_created(event)
        
        # Callback should not be called
        callback.assert_not_called()
    
    def test_handler_ignores_non_cte_files(self):
        """Test handler ignores non-CTE files."""
        callback = Mock()
        handler = CTEDataHandler(callback)
        
        # Mock non-CTE file event
        event = Mock()
        event.is_directory = False
        event.src_path = "/path/to/other_file.json"
        
        handler.on_modified(event)
        handler.on_created(event)
        
        # Callback should not be called
        callback.assert_not_called()


class TestInitializeCTEMonitoring:
    """Test cases for CTE monitoring initialization."""
    
    @pytest.mark.asyncio
    @patch('ai.agents.jack_retrieval.cte_data_monitor.cte_monitor')
    async def test_initialize_cte_monitoring_with_data(self, mock_monitor):
        """Test initialization with existing CTE data."""
        # Mock current data
        mock_data = {
            "summary": {
                "total_orders": 5,
                "total_ctes": 10,
                "total_value": 1000.0
            }
        }
        
        mock_monitor.get_current_cte_data = AsyncMock(return_value=mock_data)
        mock_monitor.start_monitoring = Mock()
        
        result = await initialize_cte_monitoring()
        
        assert result == mock_monitor
        mock_monitor.get_current_cte_data.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('ai.agents.jack_retrieval.cte_data_monitor.cte_monitor')
    async def test_initialize_cte_monitoring_no_data(self, mock_monitor):
        """Test initialization without existing CTE data."""
        mock_monitor.get_current_cte_data = AsyncMock(return_value=None)
        mock_monitor.start_monitoring = Mock()
        
        result = await initialize_cte_monitoring()
        
        assert result == mock_monitor
        mock_monitor.get_current_cte_data.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()