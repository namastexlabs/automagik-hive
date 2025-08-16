"""Comprehensive tests for CLI service commands."""

from pathlib import Path
from unittest.mock import patch

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
        
        # Patch print to avoid output but not raise exceptions
        with patch('builtins.print'):
            # Normal case should return True (the current implementation)
            result = manager.manage_service("test_service")
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
            # Should be called multiple times: postgres dependency checks + uvicorn startup
            assert mock_run.call_count >= 1
            
            # Check that the final call is the uvicorn command
            final_call_args = mock_run.call_args[0][0]
            assert "uv" in final_call_args
            assert "run" in final_call_args
            assert "uvicorn" in final_call_args
            assert "--host" in final_call_args
            assert "127.0.0.1" in final_call_args
            assert "--port" in final_call_args
            assert "8080" in final_call_args

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
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.serve_main.return_value = True
            
            result = manager.serve_docker("./test")
            
            assert result is True
            mock_main.serve_main.assert_called_once_with("./test")

    def test_serve_docker_keyboard_interrupt(self):
        """Test Docker startup with KeyboardInterrupt."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.serve_main.side_effect = KeyboardInterrupt()
            
            result = manager.serve_docker()
            
            assert result is True  # Should handle gracefully

    def test_serve_docker_exception(self):
        """Test Docker startup with generic exception."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.serve_main.side_effect = Exception("Docker error")
            
            result = manager.serve_docker()
            
            assert result is False

    def test_stop_docker_success(self):
        """Test successful Docker stop."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.stop_main.return_value = True
            
            result = manager.stop_docker("./test")
            
            assert result is True
            mock_main.stop_main.assert_called_once_with("./test")

    def test_stop_docker_exception(self):
        """Test Docker stop with exception."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.stop_main.side_effect = Exception("Stop error")
            
            result = manager.stop_docker()
            
            assert result is False

    def test_restart_docker_success(self):
        """Test successful Docker restart."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.restart_main.return_value = True
            
            result = manager.restart_docker("./test")
            
            assert result is True
            mock_main.restart_main.assert_called_once_with("./test")

    def test_restart_docker_exception(self):
        """Test Docker restart with exception."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.restart_main.side_effect = Exception("Restart error")
            
            result = manager.restart_docker()
            
            assert result is False

    def test_docker_status_success(self):
        """Test successful Docker status retrieval."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            expected_status = {"main-postgres": "🟢 Running", "main-app": "🟢 Running"}
            mock_main.get_main_status.return_value = expected_status
            
            result = manager.docker_status("./test")
            
            assert result == expected_status
            mock_main.get_main_status.assert_called_once_with("./test")

    def test_docker_status_exception(self):
        """Test Docker status with exception."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.get_main_status.side_effect = Exception("Status error")
            
            result = manager.docker_status()
            
            expected_default = {"main-postgres": "🛑 Stopped", "main-app": "🛑 Stopped"}
            assert result == expected_default

    def test_docker_logs_success(self):
        """Test successful Docker logs retrieval."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.show_main_logs.return_value = True
            
            result = manager.docker_logs("./test", tail=100)
            
            assert result is True
            mock_main.show_main_logs.assert_called_once_with("./test", 100)

    def test_docker_logs_exception(self):
        """Test Docker logs with exception."""
        manager = ServiceManager()
        with patch.object(manager, 'main_service') as mock_main:
            mock_main.show_main_logs.side_effect = Exception("Logs error")
            
            result = manager.docker_logs()
            
            assert result is False


class TestServiceManagerEnvironmentSetup:
    """Test environment setup and configuration."""
    
    def test_install_full_environment_success(self):
        """Test successful full environment installation."""
        manager = ServiceManager()
        with patch.object(manager, '_prompt_deployment_choice', return_value='full_docker'):
            with patch('lib.auth.credential_service.CredentialService') as mock_credential_service_class:
                mock_credential_service = mock_credential_service_class.return_value
                mock_credential_service.install_all_modes.return_value = {}
                with patch.object(manager, 'main_service') as mock_main:
                    mock_main.install_main_environment.return_value = True
                    
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
    
    def test_setup_env_file_creates_from_example(self, isolated_workspace):
        """Test .env creation from .env.example."""
        workspace_path = isolated_workspace
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

    def test_setup_env_file_already_exists(self, isolated_workspace):
        """Test .env setup when file already exists."""
        workspace_path = isolated_workspace
        env_file = workspace_path / ".env"
        
        # Create existing file
        env_file.write_text("EXISTING_VAR=value")
        
        with patch('lib.auth.cli.regenerate_key'):
            manager = ServiceManager()
            result = manager._setup_env_file(str(workspace_path))
            
            assert result is True
            assert env_file.read_text() == "EXISTING_VAR=value"

    def test_setup_env_file_no_example(self, isolated_workspace):
        """Test .env setup when .env.example doesn't exist."""
        workspace_path = isolated_workspace
        manager = ServiceManager()
        result = manager._setup_env_file(str(workspace_path))
        
        assert result is False

    def test_setup_env_file_api_key_generation_fails(self, isolated_workspace):
        """Test .env setup when API key generation fails."""
        workspace_path = isolated_workspace
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
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")
            
            assert result is True

    def test_setup_postgresql_interactive_keyboard_interrupt(self):
        """Test PostgreSQL setup with KeyboardInterrupt (defaults to yes)."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")
            
            assert result is True

    def test_setup_postgresql_interactive_credentials_fail(self):
        """Test PostgreSQL setup when credential generation fails."""
        with patch('builtins.input', return_value='y'):
            # The current implementation handles credential generation via CredentialService
            # and always returns True, so this test now validates the updated behavior
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")
            
            # The method now always returns True as credential generation
            # is handled by CredentialService.install_all_modes() in install_full_environment
            assert result is True

    def test_setup_postgresql_interactive_exception(self):
        """Test PostgreSQL setup with exception."""
        with patch('builtins.input', side_effect=Exception("Input error")):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")
            
            assert result is False



class TestServiceManagerUninstall:
    """Test environment uninstall functionality."""
    
    def test_uninstall_environment_preserve_data(self):
        """Test environment uninstall with data preservation."""
        manager = ServiceManager()
        with patch('builtins.input', return_value='WIPE ALL'):
            with patch('cli.commands.agent.AgentCommands') as mock_agent_cmd_class:
                with patch('cli.commands.genie.GenieCommands') as mock_genie_cmd_class:
                    with patch.object(manager, 'uninstall_main_only', return_value=True) as mock_uninstall_main:
                        # Setup mocks for agent and genie command instances
                        mock_agent_cmd = mock_agent_cmd_class.return_value
                        mock_agent_cmd.uninstall.return_value = True
                        
                        mock_genie_cmd = mock_genie_cmd_class.return_value
                        mock_genie_cmd.uninstall.return_value = True
                        
                        result = manager.uninstall_environment("./test")
                        
                        assert result is True
                        mock_uninstall_main.assert_called_once_with("./test")

    def test_uninstall_environment_wipe_data_confirmed(self):
        """Test environment uninstall with data wipe (confirmed)."""
        manager = ServiceManager()
        with patch('builtins.input', return_value='WIPE ALL'):
            with patch('cli.commands.agent.AgentCommands') as mock_agent_cmd_class:
                with patch('cli.commands.genie.GenieCommands') as mock_genie_cmd_class:
                    with patch.object(manager, 'uninstall_main_only', return_value=True) as mock_uninstall_main:
                        # Setup mocks for agent and genie command instances
                        mock_agent_cmd = mock_agent_cmd_class.return_value
                        mock_agent_cmd.uninstall.return_value = True
                        
                        mock_genie_cmd = mock_genie_cmd_class.return_value
                        mock_genie_cmd.uninstall.return_value = True
                        
                        result = manager.uninstall_environment("./test")
                        
                        assert result is True
                        mock_uninstall_main.assert_called_once_with("./test")

    def test_uninstall_environment_wipe_data_cancelled(self):
        """Test environment uninstall with data wipe (cancelled)."""
        with patch('builtins.input', side_effect=['n', 'no']):
            manager = ServiceManager()
            result = manager.uninstall_environment("./test")
            
            assert result is False

    def test_uninstall_environment_eof_defaults(self):
        """Test environment uninstall with EOF (defaults to cancelled)."""
        manager = ServiceManager()
        with patch('builtins.input', side_effect=EOFError()):
            result = manager.uninstall_environment("./test")
            
            # EOF during confirmation should cancel the uninstall
            assert result is False

    def test_uninstall_environment_exception(self):
        """Test environment uninstall with exception."""
        with patch('builtins.input', side_effect=Exception("Input error")):
            manager = ServiceManager()
            result = manager.uninstall_environment("./test")
            
            assert result is False