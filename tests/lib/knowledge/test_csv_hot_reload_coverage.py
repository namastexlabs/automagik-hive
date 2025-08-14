"""
Enhanced test suite for CSVHotReloadManager - targeting 50%+ coverage.

This test suite covers CSV hot reload functionality, file watching,
knowledge base management, and error handling scenarios.
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

from lib.knowledge.csv_hot_reload import CSVHotReloadManager, main


class TestCSVHotReloadManagerInitialization:
    """Test CSVHotReloadManager initialization and setup."""
    
    def test_init_with_explicit_csv_path(self, tmp_path):
        """Test initialization with explicit CSV path."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("header1,header2\nvalue1,value2\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        assert manager.csv_path == csv_path
        assert not manager.is_running
        assert manager.observer is None
        
    def test_init_without_csv_path_uses_global_config(self, tmp_path):
        """Test initialization without CSV path uses global configuration."""
        mock_config = {
            "csv_file_path": "custom_knowledge.csv"
        }
        
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config') as mock_load:
            mock_load.return_value = mock_config
            
            manager = CSVHotReloadManager()
            
            # Should construct path using config and current file directory
            expected_path = Path(__file__).parent.parent.parent / "lib/knowledge/custom_knowledge.csv"
            assert manager.csv_path.name == "custom_knowledge.csv"
            
    def test_init_fallback_when_config_fails(self):
        """Test initialization falls back when global config fails."""
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config', side_effect=Exception("Config error")):
            manager = CSVHotReloadManager()
            
            # Should fall back to default path
            assert "knowledge_rag.csv" in str(manager.csv_path)
            
    def test_init_initializes_knowledge_base(self, tmp_path):
        """Test initialization creates knowledge base."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test content\n")
        
        with patch.object(CSVHotReloadManager, '_initialize_knowledge_base') as mock_init:
            manager = CSVHotReloadManager(csv_path=str(csv_path))
            mock_init.assert_called_once()


class TestKnowledgeBaseInitialization:
    """Test knowledge base initialization functionality."""
    
    @pytest.fixture
    def mock_environment_setup(self):
        """Set up mock environment for knowledge base tests."""
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://user:pass@localhost:5432/test'}):
            yield
            
    def test_initialize_knowledge_base_success(self, tmp_path, mock_environment_setup):
        """Test successful knowledge base initialization."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test content\n")
        
        mock_config = {"vector_db": {"embedder": "text-embedding-ada-002"}}
        
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config') as mock_load_config:
            mock_load_config.return_value = mock_config
            
            with patch('lib.knowledge.csv_hot_reload.OpenAIEmbedder') as mock_embedder:
                with patch('lib.knowledge.csv_hot_reload.PgVector') as mock_vector_db:
                    with patch('lib.knowledge.csv_hot_reload.RowBasedCSVKnowledgeBase') as mock_kb:
                        mock_kb_instance = Mock()
                        mock_kb.return_value = mock_kb_instance
                        
                        manager = CSVHotReloadManager(csv_path=str(csv_path))
                        
                        # Should create embedder with configured model
                        mock_embedder.assert_called_with(id="text-embedding-ada-002")
                        
                        # Should create PgVector with correct parameters
                        mock_vector_db.assert_called_once()
                        call_kwargs = mock_vector_db.call_args.kwargs
                        assert call_kwargs["table_name"] == "knowledge_base"
                        assert call_kwargs["schema"] == "agno"
                        assert call_kwargs["db_url"] == "postgresql://user:pass@localhost:5432/test"
                        
                        # Should create knowledge base and load data
                        mock_kb.assert_called_once()
                        mock_kb_instance.load.assert_called_with(recreate=False, skip_existing=True)
                        
                        assert manager.knowledge_base is mock_kb_instance
                        
    def test_initialize_knowledge_base_no_database_url(self):
        """Test knowledge base initialization fails without database URL."""
        with patch.dict(os.environ, {}, clear=True):  # Clear all env vars including HIVE_DATABASE_URL
            manager = CSVHotReloadManager()
            
            # Should handle missing database URL gracefully
            assert manager.knowledge_base is None
        
    def test_initialize_knowledge_base_config_error(self, mock_environment_setup):
        """Test knowledge base initialization with config error."""
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config', side_effect=Exception("Config error")):
            with patch('lib.knowledge.csv_hot_reload.OpenAIEmbedder') as mock_embedder:
                with patch('lib.knowledge.csv_hot_reload.PgVector'):
                    with patch('lib.knowledge.csv_hot_reload.RowBasedCSVKnowledgeBase'):
                        manager = CSVHotReloadManager()
                        
                        # Should fall back to default embedder
                        mock_embedder.assert_called_with(id="text-embedding-3-small")
                        
    def test_initialize_knowledge_base_csv_not_exists(self, mock_environment_setup):
        """Test knowledge base initialization when CSV file doesn't exist."""
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config') as mock_config:
            mock_config.return_value = {"vector_db": {"embedder": "test-model"}}
            
            with patch('lib.knowledge.csv_hot_reload.OpenAIEmbedder'):
                with patch('lib.knowledge.csv_hot_reload.PgVector'):
                    with patch('lib.knowledge.csv_hot_reload.RowBasedCSVKnowledgeBase') as mock_kb:
                        mock_kb_instance = Mock()
                        mock_kb.return_value = mock_kb_instance
                        
                        manager = CSVHotReloadManager(csv_path="/nonexistent/file.csv")
                        
                        # Should create knowledge base but not load non-existent file
                        mock_kb_instance.load.assert_not_called()
                        
    def test_initialize_knowledge_base_exception_handling(self, mock_environment_setup):
        """Test knowledge base initialization handles exceptions gracefully."""
        with patch('lib.knowledge.csv_hot_reload.PgVector', side_effect=Exception("DB error")):
            manager = CSVHotReloadManager()
            
            # Should handle exceptions and set knowledge_base to None
            assert manager.knowledge_base is None


class TestFileWatching:
    """Test file watching functionality."""
    
    @pytest.fixture
    def manager_with_mock_knowledge_base(self, tmp_path):
        """Create manager with mocked knowledge base."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        manager.knowledge_base = Mock()  # Mock the knowledge base
        return manager
        
    def test_start_watching_initializes_observer(self, manager_with_mock_knowledge_base):
        """Test starting file watching initializes observer."""
        manager = manager_with_mock_knowledge_base
        
        with patch('watchdog.observers.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            
            manager.start_watching()
            
            assert manager.is_running is True
            assert manager.observer is mock_observer
            mock_observer.schedule.assert_called_once()
            mock_observer.start.assert_called_once()
            
    def test_start_watching_already_running(self, manager_with_mock_knowledge_base):
        """Test starting file watching when already running."""
        manager = manager_with_mock_knowledge_base
        manager.is_running = True
        
        with patch('watchdog.observers.Observer') as mock_observer_class:
            manager.start_watching()
            
            # Should not create new observer
            mock_observer_class.assert_not_called()
            
    def test_start_watching_import_error(self, manager_with_mock_knowledge_base):
        """Test starting file watching when watchdog import fails."""
        manager = manager_with_mock_knowledge_base
        
        with patch('watchdog.observers.Observer', side_effect=ImportError("No watchdog")):
            manager.start_watching()
            
            # Should handle import error gracefully and set running to False on error
            assert manager.is_running is False  # Should be False after error cleanup
            assert manager.observer is None
            
    def test_start_watching_observer_error(self, manager_with_mock_knowledge_base):
        """Test starting file watching when observer setup fails."""
        manager = manager_with_mock_knowledge_base
        
        with patch('watchdog.observers.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer.schedule.side_effect = Exception("Observer error")
            mock_observer_class.return_value = mock_observer
            
            manager.start_watching()
            
            # Should handle observer errors and clean up
            assert manager.is_running is False
            assert manager.observer is None
            
    def test_stop_watching_stops_observer(self, manager_with_mock_knowledge_base):
        """Test stopping file watching stops observer."""
        manager = manager_with_mock_knowledge_base
        
        mock_observer = Mock()
        manager.observer = mock_observer
        manager.is_running = True
        
        manager.stop_watching()
        
        assert manager.is_running is False
        assert manager.observer is None
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()
        
    def test_stop_watching_not_running(self, manager_with_mock_knowledge_base):
        """Test stopping file watching when not running."""
        manager = manager_with_mock_knowledge_base
        manager.is_running = False
        
        manager.stop_watching()
        
        # Should handle gracefully when not running
        assert manager.is_running is False
        
    def test_file_handler_on_modified(self, manager_with_mock_knowledge_base):
        """Test file system event handler on file modification."""
        manager = manager_with_mock_knowledge_base
        
        with patch('watchdog.observers.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            
            with patch.object(manager, '_reload_knowledge_base') as mock_reload:
                manager.start_watching()
                
                # Get the handler passed to schedule
                assert mock_observer.schedule.called
                handler = mock_observer.schedule.call_args[0][0]
                
                # Create mock event
                mock_event = Mock()
                mock_event.is_directory = False
                mock_event.src_path = str(manager.csv_path)
                
                # Test handler on_modified method
                handler.on_modified(mock_event)
                
                mock_reload.assert_called_once()
                        
    def test_file_handler_on_moved(self, manager_with_mock_knowledge_base):
        """Test file system event handler on file move."""
        manager = manager_with_mock_knowledge_base
        
        with patch('watchdog.observers.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            
            with patch.object(manager, '_reload_knowledge_base') as mock_reload:
                manager.start_watching()
                
                # Get the handler passed to schedule
                assert mock_observer.schedule.called
                handler = mock_observer.schedule.call_args[0][0]
                
                # Create mock event for moved file
                mock_event = Mock()
                mock_event.dest_path = str(manager.csv_path)
                
                # Test handler on_moved method
                handler.on_moved(mock_event)
                
                mock_reload.assert_called_once()


class TestKnowledgeBaseReloading:
    """Test knowledge base reloading functionality."""
    
    def test_reload_knowledge_base_success(self, tmp_path):
        """Test successful knowledge base reload."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Mock knowledge base
        mock_kb = Mock()
        manager.knowledge_base = mock_kb
        
        manager._reload_knowledge_base()
        
        # Should call load with incremental parameters
        mock_kb.load.assert_called_once_with(recreate=False, skip_existing=True)
        
    def test_reload_knowledge_base_no_knowledge_base(self):
        """Test reload when no knowledge base is initialized."""
        manager = CSVHotReloadManager()
        manager.knowledge_base = None
        
        # Should handle gracefully when no knowledge base
        manager._reload_knowledge_base()
        
        # Should not raise exception
        
    def test_reload_knowledge_base_exception(self, tmp_path):
        """Test reload handles exceptions gracefully."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Mock knowledge base that raises exception
        mock_kb = Mock()
        mock_kb.load.side_effect = Exception("Reload error")
        manager.knowledge_base = mock_kb
        
        # Should handle exception gracefully
        manager._reload_knowledge_base()
        
        # Should not raise exception
        
    def test_force_reload(self, tmp_path):
        """Test manual force reload."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        with patch.object(manager, '_reload_knowledge_base') as mock_reload:
            manager.force_reload()
            mock_reload.assert_called_once()


class TestStatusAndUtilities:
    """Test status reporting and utility methods."""
    
    def test_get_status_not_running(self, tmp_path):
        """Test status when manager is not running."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        status = manager.get_status()
        
        assert status["status"] == "stopped"
        assert status["csv_path"] == str(csv_path)
        assert status["mode"] == "agno_native_incremental"
        assert status["file_exists"] is True
        
    def test_get_status_running(self, tmp_path):
        """Test status when manager is running."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        manager.is_running = True
        
        status = manager.get_status()
        
        assert status["status"] == "running"
        assert status["file_exists"] is True
        
    def test_get_status_file_not_exists(self, tmp_path):
        """Test status when CSV file doesn't exist."""
        csv_path = tmp_path / "nonexistent.csv"
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        status = manager.get_status()
        
        assert status["file_exists"] is False


class TestMainFunction:
    """Test main function and CLI functionality."""
    
    def test_main_with_status_flag(self, tmp_path):
        """Test main function with status flag."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        test_args = ["--csv", str(csv_path), "--status"]
        
        with patch('sys.argv', ['csv_hot_reload.py'] + test_args):
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_status.return_value = {"status": "stopped", "csv_path": str(csv_path)}
                mock_manager_class.return_value = mock_manager
                
                main()
                
                # Should create manager and call get_status
                mock_manager_class.assert_called_with(str(csv_path))
                mock_manager.get_status.assert_called_once()
                
    def test_main_with_force_reload_flag(self, tmp_path):
        """Test main function with force reload flag."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        test_args = ["--csv", str(csv_path), "--force-reload"]
        
        with patch('sys.argv', ['csv_hot_reload.py'] + test_args):
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                main()
                
                # Should create manager and call force_reload
                mock_manager_class.assert_called_with(str(csv_path))
                mock_manager.force_reload.assert_called_once()
                
    def test_main_starts_watching(self, tmp_path):
        """Test main function starts watching by default."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        test_args = ["--csv", str(csv_path)]
        
        with patch('sys.argv', ['csv_hot_reload.py'] + test_args):
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                main()
                
                # Should create manager and start watching
                mock_manager_class.assert_called_with(str(csv_path))
                mock_manager.start_watching.assert_called_once()
                
    def test_main_default_csv_path(self):
        """Test main function with default CSV path."""
        test_args = ["--status"]
        
        with patch('sys.argv', ['csv_hot_reload.py'] + test_args):
            with patch('lib.knowledge.csv_hot_reload.CSVHotReloadManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_status.return_value = {"status": "stopped"}
                mock_manager_class.return_value = mock_manager
                
                main()
                
                # Should create manager with default path
                mock_manager_class.assert_called_with("knowledge/knowledge_rag.csv")


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    def test_concurrent_file_operations(self, tmp_path):
        """Test manager handles concurrent file operations."""
        csv_path = tmp_path / "concurrent_test.csv"
        csv_path.write_text("id,content\n1,initial\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        mock_kb = Mock()
        manager.knowledge_base = mock_kb
        
        # Simulate concurrent reloads
        def concurrent_reload():
            manager._reload_knowledge_base()
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=concurrent_reload)
            threads.append(thread)
            
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Should handle concurrent access without errors
        assert mock_kb.load.call_count == 5
        
    def test_large_csv_file_handling(self, tmp_path):
        """Test manager handles large CSV files appropriately."""
        csv_path = tmp_path / "large_test.csv"
        
        # Create a reasonably large CSV file for testing
        with open(csv_path, 'w') as f:
            f.write("id,content,metadata\n")
            for i in range(1000):  # 1000 rows
                f.write(f"{i},Content for row {i},metadata_{i}\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Should handle large files without issues during initialization
        assert manager.csv_path == csv_path
        assert manager.csv_path.exists()
        
        # Test file size detection
        file_size = csv_path.stat().st_size
        assert file_size > 10000  # Should be reasonably large
        
    def test_invalid_csv_content_handling(self, tmp_path):
        """Test manager handles invalid CSV content gracefully."""
        csv_path = tmp_path / "invalid.csv"
        csv_path.write_text("This is not valid CSV content\nMissing proper structure")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        mock_kb = Mock()
        mock_kb.load.side_effect = Exception("Invalid CSV format")
        manager.knowledge_base = mock_kb
        
        # Should handle invalid CSV content gracefully
        manager._reload_knowledge_base()
        
        # Should not raise exception
        mock_kb.load.assert_called_once()
        
    def test_file_permissions_error(self, tmp_path):
        """Test manager handles file permission errors."""
        csv_path = tmp_path / "restricted.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        # Make file read-only
        csv_path.chmod(0o444)
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Should handle permission restrictions gracefully
        assert manager.csv_path == csv_path
        
        # Clean up - make writable again for cleanup
        csv_path.chmod(0o644)
        
    def test_unicode_content_handling(self, tmp_path):
        """Test manager handles Unicode content correctly."""
        csv_path = tmp_path / "unicode.csv"
        
        # Write CSV with Unicode content
        unicode_content = "id,content\n1,Café são bôm ñoño\n2,こんにちは世界\n3,Здравствуй мир\n"
        csv_path.write_text(unicode_content, encoding='utf-8')
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Should handle Unicode content without issues
        assert manager.csv_path == csv_path
        assert manager.csv_path.exists()
        
    def test_missing_dependencies_handling(self):
        """Test manager handles missing dependencies gracefully."""
        with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config', side_effect=ImportError("Missing dependency")):
            # Should handle missing dependencies during config loading
            manager = CSVHotReloadManager()
            
            # Should fall back gracefully
            assert "knowledge_rag.csv" in str(manager.csv_path)
            
    def test_watchdog_import_error_handling(self, tmp_path):
        """Test manager handles missing watchdog gracefully."""
        csv_path = tmp_path / "test.csv" 
        csv_path.write_text("id,content\n1,test\n")
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Mock watchdog import failure
        with patch('watchdog.observers.Observer', side_effect=ImportError("No watchdog")):
            manager.start_watching()
            
            # Should handle import error gracefully and clean up
            assert manager.is_running is False
            assert manager.observer is None
                
    def test_database_connection_failure(self, tmp_path):
        """Test manager handles database connection failures."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        with patch.dict(os.environ, {'HIVE_DATABASE_URL': 'postgresql://invalid:connection@nonexistent:5432/db'}):
            with patch('lib.knowledge.csv_hot_reload.PgVector', side_effect=Exception("Connection failed")):
                manager = CSVHotReloadManager(csv_path=str(csv_path))
                
                # Should handle database connection failure
                assert manager.knowledge_base is None


class TestIntegrationScenarios:
    """Test integration scenarios with realistic usage."""
    
    def test_typical_usage_workflow(self, tmp_path):
        """Test typical usage workflow."""
        csv_path = tmp_path / "knowledge.csv"
        initial_content = "id,content\n1,Initial content\n"
        csv_path.write_text(initial_content)
        
        manager = CSVHotReloadManager(csv_path=str(csv_path))
        
        # Mock knowledge base
        mock_kb = Mock()
        manager.knowledge_base = mock_kb
        
        # Test initial status
        status = manager.get_status()
        assert status["status"] == "stopped"
        assert status["file_exists"] is True
        
        # Start watching
        with patch('watchdog.observers.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            
            manager.start_watching()
            
            assert manager.is_running is True
            mock_observer.start.assert_called_once()
            
            # Test status while running
            status = manager.get_status()
            assert status["status"] == "running"
            
            # Simulate file modification and reload
            updated_content = "id,content\n1,Initial content\n2,New content\n"
            csv_path.write_text(updated_content)
            
            manager._reload_knowledge_base()
            mock_kb.load.assert_called_with(recreate=False, skip_existing=True)
            
            # Stop watching
            manager.stop_watching()
            assert manager.is_running is False
            mock_observer.stop.assert_called_once()
            
    def test_production_environment_simulation(self, tmp_path):
        """Test simulation of production environment usage."""
        csv_path = tmp_path / "production_knowledge.csv"
        
        # Create realistic production-like CSV
        production_content = """id,question,answer,category,keywords
1,"How to make PIX transfer?","Use the PIX option in the app",payments,"pix,transfer,payment"
2,"Credit card limit","Check your limit in the cards section",cards,"credit,limit,card"
3,"Account balance","View balance in account overview",accounts,"balance,account,money"
"""
        csv_path.write_text(production_content)
        
        # Set up production-like environment
        with patch.dict(os.environ, {
            'HIVE_DATABASE_URL': 'postgresql://prod_user:prod_pass@prod_host:5432/prod_db',
            'HIVE_LOG_LEVEL': 'INFO'
        }):
            mock_config = {
                "csv_file_path": "production_knowledge.csv",
                "vector_db": {
                    "embedder": "text-embedding-3-large"
                }
            }
            
            with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config') as mock_load:
                mock_load.return_value = mock_config
                
                with patch('lib.knowledge.csv_hot_reload.OpenAIEmbedder') as mock_embedder:
                    with patch('lib.knowledge.csv_hot_reload.PgVector') as mock_vector_db:
                        with patch('lib.knowledge.csv_hot_reload.RowBasedCSVKnowledgeBase') as mock_kb_class:
                            mock_kb = Mock()
                            mock_kb_class.return_value = mock_kb
                            
                            manager = CSVHotReloadManager(csv_path=str(csv_path))
                            
                            # Should use production embedder
                            mock_embedder.assert_called_with(id="text-embedding-3-large")
                            
                            # Should use production database settings
                            vector_call_kwargs = mock_vector_db.call_args.kwargs
                            assert vector_call_kwargs["db_url"] == "postgresql://prod_user:prod_pass@prod_host:5432/prod_db"
                            assert vector_call_kwargs["schema"] == "agno"
                            
                            # Should load production data
                            mock_kb.load.assert_called_with(recreate=False, skip_existing=True)
                            
                            # Test production workflow
                            assert manager.knowledge_base is mock_kb
                            
                            # Force reload should work
                            manager.force_reload()
                            assert mock_kb.load.call_count == 2
                            
                            # Status should reflect production state
                            status = manager.get_status()
                            assert status["mode"] == "agno_native_incremental"
                            assert status["file_exists"] is True
                            
    def test_multi_manager_instances(self, tmp_path):
        """Test multiple manager instances don't interfere."""
        csv_path1 = tmp_path / "knowledge1.csv"
        csv_path2 = tmp_path / "knowledge2.csv"
        
        csv_path1.write_text("id,content\n1,Content 1\n")
        csv_path2.write_text("id,content\n1,Content 2\n")
        
        manager1 = CSVHotReloadManager(csv_path=str(csv_path1))
        manager2 = CSVHotReloadManager(csv_path=str(csv_path2))
        
        # Mock knowledge bases
        mock_kb1 = Mock()
        mock_kb2 = Mock()
        manager1.knowledge_base = mock_kb1
        manager2.knowledge_base = mock_kb2
        
        # Both should work independently
        manager1._reload_knowledge_base()
        manager2._reload_knowledge_base()
        
        mock_kb1.load.assert_called_once()
        mock_kb2.load.assert_called_once()
        
        # Status should be independent
        status1 = manager1.get_status()
        status2 = manager2.get_status()
        
        assert status1["csv_path"] == str(csv_path1)
        assert status2["csv_path"] == str(csv_path2)
        
    def test_configuration_driven_behavior(self, tmp_path):
        """Test behavior changes based on configuration."""
        csv_path = tmp_path / "configurable_knowledge.csv"
        csv_path.write_text("id,content\n1,test\n")
        
        # Test with different configurations
        configs = [
            {
                "csv_file_path": "knowledge_v1.csv",
                "vector_db": {"embedder": "text-embedding-ada-002"}
            },
            {
                "csv_file_path": "knowledge_v2.csv", 
                "vector_db": {"embedder": "text-embedding-3-small"}
            }
        ]
        
        for i, config in enumerate(configs):
            with patch('lib.knowledge.csv_hot_reload.load_global_knowledge_config') as mock_load:
                mock_load.return_value = config
                
                with patch('lib.knowledge.csv_hot_reload.OpenAIEmbedder') as mock_embedder:
                    with patch('lib.knowledge.csv_hot_reload.PgVector'):
                        with patch('lib.knowledge.csv_hot_reload.RowBasedCSVKnowledgeBase'):
                            # Create manager without explicit path (should use config)
                            manager = CSVHotReloadManager()
                            
                            # Should use embedder from config
                            expected_embedder = config["vector_db"]["embedder"]
                            mock_embedder.assert_called_with(id=expected_embedder)
                            
                            # Path should reflect config
                            expected_filename = config["csv_file_path"]
                            assert expected_filename in str(manager.csv_path)