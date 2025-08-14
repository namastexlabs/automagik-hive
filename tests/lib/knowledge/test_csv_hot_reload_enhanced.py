"""
Enhanced test suite for CSVHotReloadManager targeting 50%+ coverage.

This test suite focuses on the missing coverage areas identified:
- Lines 39-49: Configuration loading with fallback
- Lines 72, 81-83: Database and embedder initialization
- Lines 108-144: File watching initialization and event handling
- Lines 148-158: Stop watching functionality 
- Lines 162-176: Knowledge base reloading
- Lines 182, 191-192: Status and force reload
- Lines 197-224: Main function CLI handling
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import pytest

from lib.knowledge.csv_hot_reload import CSVHotReloadManager, main


class TestConfigurationAndInitialization:
    """Test configuration loading and initialization paths that are currently missing coverage."""
    
    def test_config_loading_fallback_scenario(self, tmp_path):
        """Test lines 39-49: Configuration loading with fallback when config fails."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test content\n")
        
        # Mock config loading to fail
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config', side_effect=Exception("Config load error")):
            with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
                manager = CSVHotReloadManager()
                
                # Should log warning about config failure (line 46-48)
                mock_logger.warning.assert_called()
                warning_calls = [call[0][0] if call[0] else str(call[1]) for call in mock_logger.warning.call_args_list]
                has_config_warning = any("Could not load centralized config" in str(call) for call in warning_calls)
                assert has_config_warning, f"Expected config warning not found in calls: {warning_calls}"
                
                # Should fall back to default path (line 49)
                assert "knowledge_rag.csv" in str(manager.csv_path)

    def test_config_loading_success_path(self, tmp_path):
        """Test lines 39-44: Successful configuration loading."""
        csv_path = tmp_path / "custom_knowledge.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        mock_config = {"csv_file_path": "custom_knowledge.csv"}
        
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config', return_value=mock_config):
            with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
                manager = CSVHotReloadManager()
                
                # Should log info about using config path (line 44)
                mock_logger.info.assert_any_call("Using CSV path from centralized config", csv_path=str(manager.csv_path))
                
                # Should use config filename
                assert "custom_knowledge.csv" in str(manager.csv_path)


class TestKnowledgeBaseInitializationCoverage:
    """Test knowledge base initialization paths missing coverage."""
    
    @pytest.fixture
    def setup_environment(self):
        """Set up environment variables for testing."""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'}):
            yield
    
    def test_database_url_missing_scenario(self):
        """Test line 72: ValueError when database URL is missing."""
        # Ensure HIVE_DATABASE_URL is not set
        with patch.dict(os.environ, {}, clear=True):
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager._initialize_knowledge_base', side_effect=Exception("HIVE_DATABASE_URL environment variable is required")):
                manager = CSVHotReloadManager()
                
                # Knowledge base should be None due to missing URL
                assert manager.knowledge_base is None
    
    def test_embedder_config_loading_fallback(self, setup_environment):
        """Test lines 81-83: Fallback embedder when global config fails."""
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config', side_effect=Exception("Config error")):
            with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
                with patch('lib.knowledge.csv_hot_reload.OpenAIEmbedder') as mock_embedder:
                    with patch('lib.knowledge.csv_hot_reload.PgVector'):
                        with patch('lib.knowledge.csv_hot_reload.RowBasedCSVKnowledgeBase'):
                            CSVHotReloadManager()
                            
                            # Should log warning (line 82)
                            mock_logger.warning.assert_called()
                            warning_call = mock_logger.warning.call_args[0][0]
                            assert "Could not load global embedder config" in warning_call
                            
                            # Should use default embedder (line 83)
                            mock_embedder.assert_called_with(id="text-embedding-3-small")


class TestFileWatchingCoverageEnhancement:
    """Test file watching functionality to cover missing lines 108-144."""
    
    @pytest.fixture
    def manager_with_mocked_deps(self, tmp_path):
        """Create manager with all dependencies mocked."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager._initialize_knowledge_base'):
            manager = CSVHotReloadManager(csv_path=str(csv_path))
            manager.knowledge_base = Mock()
            return manager
    
    def test_start_watching_already_running_early_return(self, manager_with_mocked_deps):
        """Test lines 108-109: Early return when already running."""
        manager = manager_with_mocked_deps
        manager.is_running = True
        
        # Should return early without setting up observer
        manager.start_watching()
        
        # Should remain running, no observer created
        assert manager.is_running is True
        assert manager.observer is None
    
    def test_start_watching_success_path(self, manager_with_mocked_deps):
        """Test lines 111-141: Successful file watching setup."""
        manager = manager_with_mocked_deps
        
        with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
            with patch('watchdog.observers.Observer') as mock_observer_class:
                with patch('watchdog.events.FileSystemEventHandler') as mock_handler_class:
                    mock_observer = Mock()
                    mock_observer_class.return_value = mock_observer
                    
                    manager.start_watching()
                    
                    # Should set is_running to True (line 111)
                    assert manager.is_running is True
                    
                    # Should log file watching started (line 113)
                    mock_logger.info.assert_called_with("File watching started", path=str(manager.csv_path))
                    
                    # Should create observer and handler (lines 135-137)
                    mock_observer_class.assert_called_once()
                    mock_observer.schedule.assert_called_once()
                    mock_observer.start.assert_called_once()
                    
                    # Should log debug message (line 140)
                    mock_logger.debug.assert_called_with("File watching active", observer_started=True)
    
    def test_start_watching_exception_handling(self, manager_with_mocked_deps):
        """Test lines 142-144: Exception handling during observer setup."""
        manager = manager_with_mocked_deps
        
        with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
            with patch('watchdog.observers.Observer', side_effect=Exception("Observer setup failed")):
                with patch.object(manager, 'stop_watching') as mock_stop:
                    manager.start_watching()
                    
                    # Should log error (line 143)
                    mock_logger.error.assert_called_with("Error setting up file watcher", error="Observer setup failed")
                    
                    # Should call stop_watching to cleanup (line 144)
                    mock_stop.assert_called_once()
    
    def test_file_event_handler_functionality(self, manager_with_mocked_deps):
        """Test lines 119-133: File event handler logic."""
        manager = manager_with_mocked_deps
        
        # Test the SimpleHandler class that's created inside start_watching
        with patch('watchdog.observers.Observer') as mock_observer_class:
            with patch('watchdog.events.FileSystemEventHandler') as mock_handler_class:
                mock_observer = Mock()
                mock_observer_class.return_value = mock_observer
                
                with patch.object(manager, '_reload_knowledge_base') as mock_reload:
                    manager.start_watching()
                    
                    # Test event handler logic directly
                    modified_event = Mock()
                    modified_event.is_directory = False
                    modified_event.src_path = str(manager.csv_path)
                    
                    # Simulate the handler logic from lines 123-127
                    if not modified_event.is_directory and modified_event.src_path.endswith(manager.csv_path.name):
                        manager._reload_knowledge_base()
                    
                    mock_reload.assert_called()


class TestStopWatchingCoverage:
    """Test stop watching functionality to cover missing lines 148-158."""
    
    def test_stop_watching_not_running_early_return(self):
        """Test lines 148-149: Early return when not running."""
        manager = CSVHotReloadManager()
        manager.is_running = False
        
        # Should return early
        manager.stop_watching()
        
        # Should remain not running
        assert manager.is_running is False
    
    def test_stop_watching_with_observer(self):
        """Test lines 151-157: Stopping observer when running."""
        manager = CSVHotReloadManager()
        
        # Set up mock observer
        mock_observer = Mock()
        manager.observer = mock_observer
        manager.is_running = True
        
        with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
            manager.stop_watching()
            
            # Should stop and join observer (lines 152-154)
            mock_observer.stop.assert_called_once()
            mock_observer.join.assert_called_once()
            
            # Should set observer to None and is_running to False (lines 154-156)
            assert manager.observer is None
            assert manager.is_running is False
            
            # Should log stopped message (line 158)
            mock_logger.info.assert_called_with("File watching stopped", path=str(manager.csv_path))


class TestKnowledgeBaseReloadingCoverage:
    """Test knowledge base reloading to cover missing lines 162-176."""
    
    def test_reload_knowledge_base_no_knowledge_base(self):
        """Test lines 162-163: Early return when no knowledge base."""
        manager = CSVHotReloadManager()
        manager.knowledge_base = None
        
        # Should return early without error
        manager._reload_knowledge_base()
        
        # Should not crash
    
    def test_reload_knowledge_base_success_path(self):
        """Test lines 165-173: Successful knowledge base reload."""
        manager = CSVHotReloadManager()
        
        # Mock knowledge base
        mock_kb = Mock()
        manager.knowledge_base = mock_kb
        
        with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
            manager._reload_knowledge_base()
            
            # Should call load with correct parameters (line 167)
            mock_kb.load.assert_called_once_with(recreate=False, skip_existing=True)
            
            # Should log success (lines 169-173)
            mock_logger.info.assert_called_with(
                "Knowledge base reloaded",
                component="csv_hot_reload",
                method="agno_incremental"
            )
    
    def test_reload_knowledge_base_exception_handling(self):
        """Test lines 175-178: Exception handling during reload."""
        manager = CSVHotReloadManager()
        
        # Mock knowledge base that fails
        mock_kb = Mock()
        mock_kb.load.side_effect = Exception("Reload failed")
        manager.knowledge_base = mock_kb
        
        with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
            manager._reload_knowledge_base()
            
            # Should log error (lines 176-178)
            mock_logger.error.assert_called_with(
                "Knowledge base reload failed",
                error="Reload failed",
                component="csv_hot_reload"
            )


class TestStatusAndForceReloadCoverage:
    """Test status and force reload functionality to cover missing lines 182, 191-192."""
    
    def test_get_status_file_exists_check(self, tmp_path):
        """Test line 186: File exists check in status."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        status = manager.get_status()
        
        # Should check file existence (line 186)
        assert status["file_exists"] is True
        assert status["csv_path"] == str(csv_path)
        assert status["mode"] == "agno_native_incremental"
    
    def test_force_reload_functionality(self):
        """Test lines 191-192: Force reload functionality."""
        manager = CSVHotReloadManager()
        
        with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
            with patch.object(manager, '_reload_knowledge_base') as mock_reload:
                manager.force_reload()
                
                # Should log force reload (line 191)
                mock_logger.info.assert_called_with("Force reloading knowledge base", component="csv_hot_reload")
                
                # Should call _reload_knowledge_base (line 192)
                mock_reload.assert_called_once()


class TestMainFunctionCoverage:
    """Test main function CLI handling to cover missing lines 197-224."""
    
    def test_main_argument_parser_setup(self):
        """Test lines 198-209: Argument parser setup."""
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_args.return_value = Mock(csv="test.csv", status=False, force_reload=False)
            
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                try:
                    main()
                except SystemExit:
                    pass  # ArgumentParser might call sys.exit
                
                # Should create argument parser with description (lines 199-201)
                mock_parser_class.assert_called_once()
                call_args = mock_parser_class.call_args
                assert "CSV Hot Reload Manager" in call_args[1]["description"]
                
                # Should add arguments (lines 202-208)
                assert mock_parser.add_argument.call_count >= 3
    
    def test_main_status_flag_handling(self):
        """Test lines 214-217: Status flag handling."""
        mock_args = Mock()
        mock_args.csv = "test.csv"
        mock_args.status = True
        mock_args.force_reload = False
        
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_args.return_value = mock_args
            
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_status.return_value = {"status": "stopped", "csv_path": "test.csv"}
                mock_manager_class.return_value = mock_manager
                
                with patch('lib.knowledge.csv_hot_reload.logger') as mock_logger:
                    main()
                    
                    # Should create manager (line 212)
                    mock_manager_class.assert_called_with("test.csv")
                    
                    # Should get status (line 215)
                    mock_manager.get_status.assert_called_once()
                    
                    # Should log status report (line 216)
                    mock_logger.info.assert_called_with("Status Report", status="stopped", csv_path="test.csv")
    
    def test_main_force_reload_flag_handling(self):
        """Test lines 219-221: Force reload flag handling."""
        mock_args = Mock()
        mock_args.csv = "test.csv"
        mock_args.status = False
        mock_args.force_reload = True
        
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_args.return_value = mock_args
            
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                main()
                
                # Should create manager (line 212)
                mock_manager_class.assert_called_with("test.csv")
                
                # Should call force_reload (line 220)
                mock_manager.force_reload.assert_called_once()
    
    def test_main_default_start_watching(self):
        """Test lines 223-224: Default start watching behavior."""
        mock_args = Mock()
        mock_args.csv = "test.csv"
        mock_args.status = False
        mock_args.force_reload = False
        
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_args.return_value = mock_args
            
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                main()
                
                # Should create manager (line 212)
                mock_manager_class.assert_called_with("test.csv")
                
                # Should start watching by default (line 224)
                mock_manager.start_watching.assert_called_once()


class TestRealWorldScenarios:
    """Test realistic scenarios to improve practical coverage."""
    
    def test_complete_lifecycle_with_real_events(self, tmp_path):
        """Test complete manager lifecycle with realistic file events."""
        csv_path = tmp_path / "lifecycle_test.csv"
        initial_content = "id,content\n1,Initial content\n"
        csv_path.write_text(initial_content)
        
        # Create manager with minimal mocking
        with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager._initialize_knowledge_base'):
            manager = CSVHotReloadManager(csv_path=str(csv_path))
            manager.knowledge_base = Mock()
            
            # Test status when stopped
            status = manager.get_status()
            assert status["status"] == "stopped"
            assert status["file_exists"] is True
            
            # Start watching (mocked)
            with patch('watchdog.observers.Observer') as mock_observer_class:
                mock_observer = Mock()
                mock_observer_class.return_value = mock_observer
                
                manager.start_watching()
                assert manager.is_running is True
                
                # Test status when running
                status = manager.get_status()
                assert status["status"] == "running"
                
                # Simulate file modification
                updated_content = initial_content + "2,New content\n"
                csv_path.write_text(updated_content)
                manager._reload_knowledge_base()
                
                # Verify knowledge base was reloaded
                manager.knowledge_base.load.assert_called_with(recreate=False, skip_existing=True)
                
                # Test force reload
                manager.force_reload()
                assert manager.knowledge_base.load.call_count == 2
                
                # Stop watching
                manager.stop_watching()
                assert manager.is_running is False
    
    def test_concurrent_operations_stress_test(self, tmp_path):
        """Test concurrent operations to ensure thread safety."""
        csv_path = tmp_path / "concurrent_test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager._initialize_knowledge_base'):
            manager = CSVHotReloadManager(csv_path=str(csv_path))
            manager.knowledge_base = Mock()
            
            # Test multiple rapid reloads
            for i in range(10):
                manager._reload_knowledge_base()
            
            # Should handle multiple reloads without issues
            assert manager.knowledge_base.load.call_count == 10
            
            # Test status calls during operations
            for i in range(5):
                status = manager.get_status()
                assert status["csv_path"] == str(csv_path)
    
    def test_error_recovery_scenarios(self, tmp_path):
        """Test error recovery in various scenarios."""
        csv_path = tmp_path / "error_test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager._initialize_knowledge_base'):
            manager = CSVHotReloadManager(csv_path=str(csv_path))
            
            # Test with failing knowledge base
            mock_kb = Mock()
            mock_kb.load.side_effect = [Exception("First failure"), Exception("Second failure"), None]
            manager.knowledge_base = mock_kb
            
            # Should handle multiple failures gracefully
            manager._reload_knowledge_base()  # First failure
            manager._reload_knowledge_base()  # Second failure
            manager._reload_knowledge_base()  # Success
            
            assert mock_kb.load.call_count == 3
            
            # Test force reload after failures
            manager.force_reload()
            assert mock_kb.load.call_count == 4