"""Comprehensive tests for CLI service commands."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call
from cli.commands.service import ServiceManager


class TestServiceManagerInitialization:
    """Test ServiceManager initialization and basic methods."""
    
    def test_service_manager_initialization(self):
        """Test ServiceManager initializes correctly."""
        manager = ServiceManager()
        assert manager.workspace_path == Path(".")
        assert manager.main_service is not None
    
    def test_service_manager_with_custom_path(self):
        """Test ServiceManager with custom workspace path."""
        custom_path = Path("/custom/path")
        manager = ServiceManager(custom_path)
        assert manager.workspace_path == custom_path
        assert manager.main_service is not None
    
    def test_manage_service_default(self):
        """Test manage_service with default parameters."""
        manager = ServiceManager()
        result = manager.manage_service()
        assert result is True
    
    def test_manage_service_named(self):
        """Test manage_service with named service."""
        manager = ServiceManager()
        result = manager.manage_service("test_service")
        assert result is True
    
    def test_execute(self):
        """Test execute method."""
        manager = ServiceManager()
        result = manager.execute()
        assert result is True
    
    def test_status(self):
        """Test status method."""
        with patch.object(ServiceManager, 'docker_status', return_value={"test": "running"}):
            manager = ServiceManager()
            status = manager.status()
            assert isinstance(status, dict)
            assert "status" in status
            assert "healthy" in status
            assert "docker_services" in status

    def test_manage_service_exception_handling(self):
        """Test manage_service handles exceptions gracefully."""
        manager = ServiceManager()
        
        # Mock an exception scenario
        with patch('builtins.print', side_effect=Exception("Print error")):
            # Should still return True for legacy compatibility
            result = manager.manage_service("error_service")
            assert result is True


class TestServiceManagerLocalServe:
    """Test local development server functionality."""
    
    def test_serve_local_success(self):
        """Test successful local server startup."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = None
            
            manager = ServiceManager()
            result = manager.serve_local(host="127.0.0.1", port=8080, reload=False)
            
            assert result is True
            mock_run.assert_called_once()
            
            # Check command construction
            call_args = mock_run.call_args[0][0]
            assert "uv" in call_args
            assert "run" in call_args
            assert "uvicorn" in call_args
            assert "--host" in call_args
            assert "127.0.0.1" in call_args
            assert "--port" in call_args
            assert "8080" in call_args

    def test_serve_local_with_reload(self):
        """Test local server with reload enabled."""
        with patch('subprocess.run') as mock_run:
            manager = ServiceManager()
            result = manager.serve_local(reload=True)
            
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "--reload" in call_args

    def test_serve_local_keyboard_interrupt(self):
        """Test handling of KeyboardInterrupt during local serve."""
        with patch('subprocess.run', side_effect=KeyboardInterrupt()):
            manager = ServiceManager()
            result = manager.serve_local()
            
            assert result is True  # Should handle gracefully

    def test_serve_local_os_error(self):
        """Test handling of OSError during local serve."""
        with patch('subprocess.run', side_effect=OSError("Port in use")):
            manager = ServiceManager()
            result = manager.serve_local()
            
            assert result is False


class TestServiceManagerDockerOperations:
    """Test Docker operations functionality."""
    
    def test_serve_docker_success(self):
        """Test successful Docker startup."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.serve_main.return_value = True
            
            manager = ServiceManager()
            result = manager.serve_docker("./test")
            
            assert result is True
            mock_main.serve_main.assert_called_once_with("./test")

    def test_serve_docker_keyboard_interrupt(self):
        """Test Docker startup with KeyboardInterrupt."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.serve_main.side_effect = KeyboardInterrupt()
            
            manager = ServiceManager()
            result = manager.serve_docker()
            
            assert result is True  # Should handle gracefully

    def test_serve_docker_exception(self):
        """Test Docker startup with generic exception."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.serve_main.side_effect = Exception("Docker error")
            
            manager = ServiceManager()
            result = manager.serve_docker()
            
            assert result is False

    def test_stop_docker_success(self):
        """Test successful Docker stop."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.stop_main.return_value = True
            
            manager = ServiceManager()
            result = manager.stop_docker("./test")
            
            assert result is True
            mock_main.stop_main.assert_called_once_with("./test")

    def test_stop_docker_exception(self):
        """Test Docker stop with exception."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.stop_main.side_effect = Exception("Stop error")
            
            manager = ServiceManager()
            result = manager.stop_docker()
            
            assert result is False

    def test_restart_docker_success(self):
        """Test successful Docker restart."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.restart_main.return_value = True
            
            manager = ServiceManager()
            result = manager.restart_docker("./test")
            
            assert result is True
            mock_main.restart_main.assert_called_once_with("./test")

    def test_restart_docker_exception(self):
        """Test Docker restart with exception."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.restart_main.side_effect = Exception("Restart error")
            
            manager = ServiceManager()
            result = manager.restart_docker()
            
            assert result is False

    def test_docker_status_success(self):
        """Test successful Docker status retrieval."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            expected_status = {"main-postgres": "🟢 Running", "main-app": "🟢 Running"}
            mock_main.get_main_status.return_value = expected_status
            
            manager = ServiceManager()
            result = manager.docker_status("./test")
            
            assert result == expected_status
            mock_main.get_main_status.assert_called_once_with("./test")

    def test_docker_status_exception(self):
        """Test Docker status with exception."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.get_main_status.side_effect = Exception("Status error")
            
            manager = ServiceManager()
            result = manager.docker_status()
            
            expected_default = {"main-postgres": "🛑 Stopped", "main-app": "🛑 Stopped"}
            assert result == expected_default

    def test_docker_logs_success(self):
        """Test successful Docker logs retrieval."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.show_main_logs.return_value = True
            
            manager = ServiceManager()
            result = manager.docker_logs("./test", tail=100)
            
            assert result is True
            mock_main.show_main_logs.assert_called_once_with("./test", 100)

    def test_docker_logs_exception(self):
        """Test Docker logs with exception."""
        with patch.object(ServiceManager, 'main_service') as mock_main:
            mock_main.show_main_logs.side_effect = Exception("Logs error")
            
            manager = ServiceManager()
            result = manager.docker_logs()
            
            assert result is False


class TestServiceManagerEnvironmentSetup:
    """Test environment setup and configuration."""
    
    def test_install_full_environment_success(self):
        """Test successful full environment installation."""
        with patch.object(ServiceManager, '_setup_env_file', return_value=True):
            with patch.object(ServiceManager, '_setup_postgresql_interactive', return_value=True):
                with patch.object(ServiceManager, 'main_service') as mock_main:
                    mock_main.install_main_environment.return_value = True
                    
                    manager = ServiceManager()
                    result = manager.install_full_environment("./test")
                    
                    assert result is True
                    mock_main.install_main_environment.assert_called_once_with("./test")

    def test_install_full_environment_env_setup_fails(self):
        """Test environment installation when env setup fails."""
        with patch.object(ServiceManager, '_setup_env_file', return_value=False):
            manager = ServiceManager()
            result = manager.install_full_environment()
            
            assert result is False

    def test_install_full_environment_postgres_setup_fails(self):
        """Test environment installation when PostgreSQL setup fails."""
        with patch.object(ServiceManager, '_setup_env_file', return_value=True):
            with patch.object(ServiceManager, '_setup_postgresql_interactive', return_value=False):
                manager = ServiceManager()
                result = manager.install_full_environment()
                
                assert result is False

    def test_install_full_environment_exception(self):
        """Test environment installation with exception."""
        with patch.object(ServiceManager, '_setup_env_file', side_effect=Exception("Setup error")):
            manager = ServiceManager()
            result = manager.install_full_environment()
            
            assert result is False


class TestServiceManagerEnvFileSetup:
    """Test .env file setup functionality."""
    
    def test_setup_env_file_creates_from_example(self):
        """Test .env creation from .env.example."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            env_example = workspace_path / ".env.example"
            env_file = workspace_path / ".env"
            
            # Create example file
            env_example.write_text("EXAMPLE_VAR=value")
            
            with patch('lib.auth.cli.regenerate_key'):
                manager = ServiceManager()
                result = manager._setup_env_file(str(workspace_path))
                
                assert result is True
                assert env_file.exists()
                assert env_file.read_text() == "EXAMPLE_VAR=value"

    def test_setup_env_file_already_exists(self):
        """Test .env setup when file already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            env_file = workspace_path / ".env"
            
            # Create existing file
            env_file.write_text("EXISTING_VAR=value")
            
            with patch('lib.auth.cli.regenerate_key'):
                manager = ServiceManager()
                result = manager._setup_env_file(str(workspace_path))
                
                assert result is True
                assert env_file.read_text() == "EXISTING_VAR=value"

    def test_setup_env_file_no_example(self):
        """Test .env setup when .env.example doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ServiceManager()
            result = manager._setup_env_file(str(temp_dir))
            
            assert result is False

    def test_setup_env_file_api_key_generation_fails(self):
        """Test .env setup when API key generation fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            env_example = workspace_path / ".env.example"
            
            # Create example file
            env_example.write_text("EXAMPLE_VAR=value")
            
            with patch('lib.auth.cli.regenerate_key', side_effect=Exception("Key error")):
                manager = ServiceManager()
                result = manager._setup_env_file(str(workspace_path))
                
                assert result is True  # Should continue despite key error

    def test_setup_env_file_exception(self):
        """Test .env setup with general exception."""
        with patch('shutil.copy', side_effect=Exception("Copy error")):
            manager = ServiceManager()
            result = manager._setup_env_file("./nonexistent")
            
            assert result is False


class TestServiceManagerPostgreSQLSetup:
    """Test PostgreSQL setup functionality."""
    
    def test_setup_postgresql_interactive_yes(self):
        """Test PostgreSQL setup with 'yes' response."""
        with patch('builtins.input', return_value='y'):
            with patch.object(ServiceManager, '_generate_postgres_credentials', return_value=True):
                manager = ServiceManager()
                result = manager._setup_postgresql_interactive("./test")
                
                assert result is True

    def test_setup_postgresql_interactive_no(self):
        """Test PostgreSQL setup with 'no' response."""
        with patch('builtins.input', return_value='n'):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")
            
            assert result is True

    def test_setup_postgresql_interactive_eof(self):
        """Test PostgreSQL setup with EOF (defaults to yes)."""
        with patch('builtins.input', side_effect=EOFError()):
            with patch.object(ServiceManager, '_generate_postgres_credentials', return_value=True):
                manager = ServiceManager()
                result = manager._setup_postgresql_interactive("./test")
                
                assert result is True

    def test_setup_postgresql_interactive_keyboard_interrupt(self):
        """Test PostgreSQL setup with KeyboardInterrupt (defaults to yes)."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            with patch.object(ServiceManager, '_generate_postgres_credentials', return_value=True):
                manager = ServiceManager()
                result = manager._setup_postgresql_interactive("./test")
                
                assert result is True

    def test_setup_postgresql_interactive_credentials_fail(self):
        """Test PostgreSQL setup when credential generation fails."""
        with patch('builtins.input', return_value='y'):
            with patch.object(ServiceManager, '_generate_postgres_credentials', return_value=False):
                manager = ServiceManager()
                result = manager._setup_postgresql_interactive("./test")
                
                assert result is False

    def test_setup_postgresql_interactive_exception(self):
        """Test PostgreSQL setup with exception."""
        with patch('builtins.input', side_effect=Exception("Input error")):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")
            
            assert result is False


class TestServiceManagerPostgreSQLCredentials:
    """Test PostgreSQL credential generation."""
    
    def test_generate_postgres_credentials_success(self):
        """Test successful PostgreSQL credential generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("EXAMPLE_VAR=value\n")
            
            with patch('pathlib.Path', return_value=Path(temp_dir)):
                manager = ServiceManager()
                result = manager._generate_postgres_credentials()
                
                assert result is True
                
                # Check that credentials were added
                env_content = env_file.read_text()
                assert "HIVE_DATABASE_URL=" in env_content
                assert "postgresql+psycopg://" in env_content

    def test_generate_postgres_credentials_existing_valid(self):
        """Test credential generation with existing valid credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("HIVE_DATABASE_URL=postgresql://existing_user:existing_pass@localhost:5532/hive\n")
            
            with patch('pathlib.Path', return_value=Path(temp_dir)):
                manager = ServiceManager()
                result = manager._generate_postgres_credentials()
                
                assert result is True
                
                # Should not change existing valid credentials
                env_content = env_file.read_text()
                assert "existing_user" in env_content
                assert "existing_pass" in env_content

    def test_generate_postgres_credentials_existing_placeholder(self):
        """Test credential generation with placeholder credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("HIVE_DATABASE_URL=postgresql://hive_user:your-secure-password-here@localhost:5532/hive\n")
            
            with patch('pathlib.Path', return_value=Path(temp_dir)):
                manager = ServiceManager()
                result = manager._generate_postgres_credentials()
                
                assert result is True
                
                # Should replace placeholder credentials
                env_content = env_file.read_text()
                assert "your-secure-password-here" not in env_content
                assert "hive_user" not in env_content

    def test_generate_postgres_credentials_no_env_file(self):
        """Test credential generation when .env file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path', return_value=Path(temp_dir)):
                manager = ServiceManager()
                result = manager._generate_postgres_credentials()
                
                assert result is False

    def test_generate_postgres_credentials_exception(self):
        """Test credential generation with exception."""
        with patch('pathlib.Path.read_text', side_effect=Exception("Read error")):
            manager = ServiceManager()
            result = manager._generate_postgres_credentials()
            
            assert result is False


class TestServiceManagerUninstall:
    """Test environment uninstall functionality."""
    
    def test_uninstall_environment_preserve_data(self):
        """Test environment uninstall with data preservation."""
        with patch('builtins.input', return_value='y'):
            with patch.object(ServiceManager, 'main_service') as mock_main:
                mock_main.uninstall_preserve_data.return_value = True
                
                manager = ServiceManager()
                result = manager.uninstall_environment("./test")
                
                assert result is True
                mock_main.uninstall_preserve_data.assert_called_once_with("./test")

    def test_uninstall_environment_wipe_data_confirmed(self):
        """Test environment uninstall with data wipe (confirmed)."""
        with patch('builtins.input', side_effect=['n', 'yes']):
            with patch.object(ServiceManager, 'main_service') as mock_main:
                mock_main.uninstall_wipe_data.return_value = True
                
                manager = ServiceManager()
                result = manager.uninstall_environment("./test")
                
                assert result is True
                mock_main.uninstall_wipe_data.assert_called_once_with("./test")

    def test_uninstall_environment_wipe_data_cancelled(self):
        """Test environment uninstall with data wipe (cancelled)."""
        with patch('builtins.input', side_effect=['n', 'no']):
            manager = ServiceManager()
            result = manager.uninstall_environment("./test")
            
            assert result is False

    def test_uninstall_environment_eof_defaults(self):
        """Test environment uninstall with EOF (defaults to preserve)."""
        with patch('builtins.input', side_effect=EOFError()):
            with patch.object(ServiceManager, 'main_service') as mock_main:
                mock_main.uninstall_preserve_data.return_value = True
                
                manager = ServiceManager()
                result = manager.uninstall_environment("./test")
                
                assert result is True
                mock_main.uninstall_preserve_data.assert_called_once_with("./test")

    def test_uninstall_environment_exception(self):
        """Test environment uninstall with exception."""
        with patch('builtins.input', side_effect=Exception("Input error")):
            manager = ServiceManager()
            result = manager.uninstall_environment("./test")
            
            assert result is False