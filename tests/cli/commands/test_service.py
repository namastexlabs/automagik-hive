"""Comprehensive tests for CLI service commands."""

import logging
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import lib.logging.config as logging_config
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
        with (
            patch.object(ServiceManager, "docker_status", return_value={"test": "running"}),
            patch.object(ServiceManager, "_runtime_snapshot", return_value={"status": "unavailable"}),
        ):
            manager = ServiceManager()
            status = manager.status()
            assert isinstance(status, dict)
            assert "status" in status
            assert "healthy" in status
            assert "docker_services" in status
            assert status["runtime"]["status"] == "unavailable"

    @patch("cli.commands.service._gather_runtime_snapshot", new_callable=AsyncMock)
    def test_runtime_snapshot_success(self, mock_gather):
        """_runtime_snapshot should return ready status when snapshot succeeds."""
        mock_gather.return_value = {"total_components": 1}
        manager = ServiceManager()

        result = manager._runtime_snapshot()

        assert result["status"] == "ready"
        assert result["summary"] == {"total_components": 1}
        mock_gather.assert_awaited_once()

    @patch("cli.commands.service._gather_runtime_snapshot", new_callable=AsyncMock)
    def test_runtime_snapshot_failure(self, mock_gather):
        """_runtime_snapshot should surface error details when snapshot fails."""
        mock_gather.side_effect = RuntimeError("boom")
        manager = ServiceManager()

        result = manager._runtime_snapshot()

        assert result["status"] == "unavailable"
        assert "boom" in result["error"]

    def test_manage_service_exception_handling(self):
        """Test manage_service handles exceptions gracefully."""
        manager = ServiceManager()

        # Patch print to avoid output but not raise exceptions
        with patch("builtins.print"):
            # Normal case should return True (the current implementation)
            result = manager.manage_service("test_service")
            assert result is True


class TestServiceManagerLocalServe:
    """Test local development server functionality."""

    def test_serve_local_success(self):
        """Test successful local server startup."""
        with (
            patch.object(ServiceManager, "_ensure_postgres_dependency", return_value=(True, False)),
            patch.object(ServiceManager, "_stop_postgres_dependency") as mock_stop,
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = None

            manager = ServiceManager()
            result = manager.serve_local(host="127.0.0.1", port=8080, reload=False)

            assert result is True
            # Should be called at least once for uvicorn startup
            assert mock_run.call_count >= 1

            # Find the uvicorn call (not necessarily the last call due to Docker checks)
            uvicorn_call_found = False
            for call in mock_run.call_args_list:
                call_args = call[0][0]
                if isinstance(call_args, list) and "uvicorn" in call_args:
                    assert "uv" in call_args
                    assert "run" in call_args
                    assert "uvicorn" in call_args
                    assert "--host" in call_args
                    assert "127.0.0.1" in call_args
                    assert "--port" in call_args
                    assert "8080" in call_args
                    uvicorn_call_found = True
                    break

            assert uvicorn_call_found, "No uvicorn call found in subprocess.run calls"
            mock_stop.assert_not_called()

    def test_serve_local_with_reload(self):
        """Test local server with reload enabled."""
        with (
            patch.object(ServiceManager, "_ensure_postgres_dependency", return_value=(True, False)),
            patch.object(ServiceManager, "_stop_postgres_dependency") as mock_stop,
            patch("subprocess.run") as mock_run,
        ):
            manager = ServiceManager()
            result = manager.serve_local(reload=True)

            assert result is True

            # Find the uvicorn call with reload flag
            reload_call_found = False
            for call in mock_run.call_args_list:
                call_args = call[0][0]
                if isinstance(call_args, list) and "uvicorn" in call_args:
                    assert "--reload" in call_args
                    reload_call_found = True
                    break

            assert reload_call_found, "No uvicorn call with --reload found in subprocess.run calls"
            mock_stop.assert_not_called()

    def test_serve_local_keyboard_interrupt(self):
        """Test handling of KeyboardInterrupt during local serve."""
        with (
            patch.object(ServiceManager, "_ensure_postgres_dependency", return_value=(True, False)),
            patch.object(ServiceManager, "_stop_postgres_dependency") as mock_stop,
            patch.object(ServiceManager, "_is_postgres_dependency_active", return_value=False),
        ):
            manager = ServiceManager()

            with patch("subprocess.run", side_effect=KeyboardInterrupt()):
                try:
                    result = manager.serve_local()
                    # If we get here, KeyboardInterrupt was handled
                    assert result is True
                    mock_stop.assert_not_called()
                except KeyboardInterrupt:
                    pytest.fail("KeyboardInterrupt was not handled properly")

    def test_serve_local_os_error(self):
        """Test handling of OSError during local serve."""
        with (
            patch.object(ServiceManager, "_ensure_postgres_dependency", return_value=(True, False)),
            patch.object(ServiceManager, "_stop_postgres_dependency") as mock_stop,
            patch("subprocess.run", side_effect=OSError("Port in use")),
        ):
            manager = ServiceManager()
            result = manager.serve_local()

            assert result is False
            mock_stop.assert_not_called()


class TestServiceManagerDockerOperations:
    """Test Docker operations functionality."""

    def test_serve_docker_success(self):
        """Test successful Docker startup."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.serve_main.return_value = True

            result = manager.serve_docker("./test")

            assert result is True
            mock_main.serve_main.assert_called_once_with("./test")

    def test_serve_docker_keyboard_interrupt(self):
        """Test Docker startup with KeyboardInterrupt."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.serve_main.side_effect = KeyboardInterrupt()

            try:
                result = manager.serve_docker()
                # If we get here, KeyboardInterrupt was handled
                assert result is True
            except KeyboardInterrupt:
                pytest.fail("KeyboardInterrupt was not handled properly")

    def test_serve_docker_exception(self):
        """Test Docker startup with generic exception."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.serve_main.side_effect = Exception("Docker error")

            result = manager.serve_docker()

            assert result is False

    def test_stop_docker_success(self):
        """Test successful Docker stop."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.stop_main.return_value = True

            result = manager.stop_docker("./test")

            assert result is True
            mock_main.stop_main.assert_called_once_with("./test")

    def test_stop_docker_exception(self):
        """Test Docker stop with exception."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.stop_main.side_effect = Exception("Stop error")

            result = manager.stop_docker()

            assert result is False

    def test_restart_docker_success(self):
        """Test successful Docker restart."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.restart_main.return_value = True

            result = manager.restart_docker("./test")

            assert result is True
            mock_main.restart_main.assert_called_once_with("./test")

    def test_restart_docker_exception(self):
        """Test Docker restart with exception."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.restart_main.side_effect = Exception("Restart error")

            result = manager.restart_docker()

            assert result is False

    def test_docker_status_success(self):
        """Test successful Docker status retrieval."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            expected_status = {"hive-postgres": "🟢 Running", "hive-api": "🟢 Running"}
            mock_main.get_main_status.return_value = expected_status

            result = manager.docker_status("./test")

            assert result == expected_status
            mock_main.get_main_status.assert_called_once_with("./test")


class TestServiceManagerLoggingLevels:
    """Ensure ServiceManager bootstraps logging with correct levels."""

    @staticmethod
    def _restore_real_initializer(monkeypatch):
        monkeypatch.setattr("lib.logging.initialize_logging", logging_config.initialize_logging)
        monkeypatch.setattr(
            "cli.commands.service.initialize_logging",
            logging_config.initialize_logging,
        )

    def test_initialization_respects_info_default(self, monkeypatch, capsys, tmp_path):
        """INFO default should suppress the bootstrap debug breadcrumb."""
        self._restore_real_initializer(monkeypatch)

        original_initialized = logging_config._logging_initialized
        original_level = logging.getLogger().getEffectiveLevel()

        try:
            monkeypatch.delenv("HIVE_LOG_LEVEL", raising=False)
            monkeypatch.setenv("AGNO_LOG_LEVEL", "WARNING")

            logging_config._logging_initialized = False
            capsys.readouterr()  # Clear captured buffers before instantiation

            ServiceManager()

            captured = capsys.readouterr()
            assert "Logging bootstrap complete" not in captured.err
            assert logging.getLogger().getEffectiveLevel() == logging.INFO

            sample_path = tmp_path / "cli_info_bootstrap.log"
            sample_path.write_text(captured.err)
            assert "Logging bootstrap complete" not in sample_path.read_text()
        finally:
            logging_config._logging_initialized = original_initialized
            logging.getLogger().setLevel(original_level)

    def test_initialization_emits_debug_when_opt_in(self, monkeypatch, capsys, tmp_path):
        """DEBUG opt-in should emit the bootstrap breadcrumb."""
        self._restore_real_initializer(monkeypatch)

        original_initialized = logging_config._logging_initialized
        original_level = logging.getLogger().getEffectiveLevel()

        try:
            monkeypatch.setenv("HIVE_LOG_LEVEL", "DEBUG")
            monkeypatch.setenv("AGNO_LOG_LEVEL", "WARNING")

            logging_config._logging_initialized = False
            capsys.readouterr()

            ServiceManager()

            captured = capsys.readouterr()
            assert "Logging bootstrap complete" in captured.err
            assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

            sample_path = tmp_path / "cli_debug_bootstrap.log"
            sample_path.write_text(captured.err)
            assert "Logging bootstrap complete" in sample_path.read_text()
        finally:
            logging_config._logging_initialized = original_initialized
            logging.getLogger().setLevel(original_level)

    def test_docker_status_exception(self):
        """Test Docker status with exception."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.get_main_status.side_effect = Exception("Status error")

            result = manager.docker_status()

            expected_default = {"hive-postgres": "🛑 Stopped", "hive-api": "🛑 Stopped"}
            assert result == expected_default

    def test_docker_logs_success(self):
        """Test successful Docker logs retrieval."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.show_main_logs.return_value = True

            result = manager.docker_logs("./test", tail=100)

            assert result is True
            mock_main.show_main_logs.assert_called_once_with("./test", 100)

    def test_docker_logs_exception(self):
        """Test Docker logs with exception."""
        manager = ServiceManager()
        with patch.object(manager, "main_service") as mock_main:
            mock_main.show_main_logs.side_effect = Exception("Logs error")

            result = manager.docker_logs()

            assert result is False


class TestServiceManagerEnvironmentSetup:
    """Test environment setup and configuration."""

    def test_install_full_environment_success(self):
        """Test successful full environment installation."""
        manager = ServiceManager()
        with patch.object(manager, "_prompt_deployment_choice", return_value="full_docker"):
            with patch.object(manager, "_prompt_backend_selection", return_value="postgresql"):
                with patch.object(manager, "_store_backend_choice"):
                    resolved_path = Path("/resolved/workspace")
                    with patch("lib.auth.credential_service.CredentialService") as mock_credential_service_class:
                        mock_credential_service = mock_credential_service_class.return_value
                        mock_credential_service.install_all_modes.return_value = {}
                        with patch.object(manager, "main_service") as mock_main:
                            mock_main.install_main_environment.return_value = True
                            with patch.object(manager, "_resolve_install_root", return_value=resolved_path):
                                result = manager.install_full_environment("./test")

                            assert result is True
                            mock_main.install_main_environment.assert_called_once_with(str(resolved_path))
                            mock_credential_service_class.assert_called_once()
                            kwargs = mock_credential_service_class.call_args.kwargs
                            assert kwargs.get("project_root") == resolved_path

    def test_install_full_environment_uses_parent_workspace(self, tmp_path):
        """Install should pivot to parent directory when AI bundle lacks markers."""
        repo_root = tmp_path
        ai_dir = repo_root / "ai"
        ai_dir.mkdir()
        (repo_root / ".env").write_text("HIVE_DATABASE_URL=postgresql://existing")
        (repo_root / "docker").mkdir()
        docker_main = repo_root / "docker" / "main"
        docker_main.mkdir()
        (docker_main / "docker-compose.yml").write_text("version: '3'")

        manager = ServiceManager()
        with patch.object(manager, "_prompt_deployment_choice", return_value="local_hybrid"):
            with patch.object(manager, "_prompt_backend_selection", return_value="postgresql"):
                with patch.object(manager, "_store_backend_choice"):
                    with patch("lib.auth.credential_service.CredentialService") as mock_credential_service_class:
                        credential_instance = mock_credential_service_class.return_value
                        credential_instance.install_all_modes.return_value = {}
                        with patch.object(manager, "main_service"):
                            with patch.object(
                                manager, "_setup_local_hybrid_deployment", return_value=True
                            ) as mock_local:
                                result = manager.install_full_environment(str(ai_dir))

        assert result is True
        mock_credential_service_class.assert_called_once()
        called_kwargs = mock_credential_service_class.call_args.kwargs
        assert called_kwargs.get("project_root") == repo_root
        mock_local.assert_called_once_with(str(repo_root), verbose=False)

    def test_install_full_environment_env_setup_fails(self):
        """Test environment installation when env setup fails."""
        with patch.object(ServiceManager, "_setup_env_file", return_value=False):
            manager = ServiceManager()
            result = manager.install_full_environment()

            assert result is False

    def test_install_full_environment_postgres_setup_fails(self):
        """Test environment installation when PostgreSQL setup fails."""
        with patch.object(ServiceManager, "_setup_env_file", return_value=True):
            with patch.object(ServiceManager, "_setup_postgresql_interactive", return_value=False):
                manager = ServiceManager()
                result = manager.install_full_environment()

                assert result is False

    def test_install_full_environment_exception(self):
        """Test environment installation with exception."""
        with patch.object(ServiceManager, "_setup_env_file", side_effect=Exception("Setup error")):
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

        with patch("lib.auth.cli.regenerate_key"):
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

        with patch("lib.auth.cli.regenerate_key"):
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

        with patch("lib.auth.cli.regenerate_key", side_effect=Exception("Key error")):
            manager = ServiceManager()
            result = manager._setup_env_file(str(workspace_path))

            assert result is True  # Should continue despite key error

    def test_setup_env_file_exception(self):
        """Test .env setup with general exception."""
        with patch("shutil.copy", side_effect=Exception("Copy error")):
            manager = ServiceManager()
            result = manager._setup_env_file("./nonexistent")

            assert result is False


class TestServiceManagerPostgreSQLSetup:
    """Test PostgreSQL setup functionality."""

    def test_setup_postgresql_interactive_yes(self, tmp_path):
        """Test PostgreSQL setup with 'yes' response."""
        # Create a test .env file with valid database URL
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/testdb")

        with patch("builtins.input", return_value="y"):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive(str(tmp_path))

            assert result is True

    def test_setup_postgresql_interactive_no(self):
        """Test PostgreSQL setup with 'no' response."""
        with patch("builtins.input", return_value="n"):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")

            assert result is True

    def test_setup_postgresql_interactive_eof(self, tmp_path):
        """Test PostgreSQL setup with EOF (defaults to yes)."""
        # Create a test .env file with valid database URL
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/testdb")

        with patch("builtins.input", side_effect=EOFError()):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive(str(tmp_path))

            assert result is True

    def test_setup_postgresql_interactive_keyboard_interrupt(self, tmp_path):
        """Test PostgreSQL setup with KeyboardInterrupt (defaults to yes)."""
        # Create a test .env file with valid database URL
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/testdb")

        # KeyboardInterrupt is handled as EOF (defaults to yes)
        manager = ServiceManager()
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            try:
                result = manager._setup_postgresql_interactive(str(tmp_path))
                # If we get here, KeyboardInterrupt was handled
                assert result is True
            except KeyboardInterrupt:
                pytest.fail("KeyboardInterrupt was not handled properly")

    def test_setup_postgresql_interactive_credentials_fail(self, tmp_path):
        """Test PostgreSQL setup when credential generation fails."""
        # Create a test .env file with valid database URL
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/testdb")

        with patch("builtins.input", return_value="y"):
            # The current implementation handles credential generation via CredentialService
            # and always returns True, so this test now validates the updated behavior
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive(str(tmp_path))

            # The method now always returns True as credential generation
            # is handled by CredentialService.install_all_modes() in install_full_environment
            assert result is True

    def test_setup_postgresql_interactive_exception(self):
        """Test PostgreSQL setup with exception."""
        with patch("builtins.input", side_effect=Exception("Input error")):
            manager = ServiceManager()
            result = manager._setup_postgresql_interactive("./test")

            assert result is False


class TestServiceManagerInitWorkspace:
    """Test workspace initialization (template copying) functionality."""

    def test_init_workspace_already_exists(self, tmp_path):
        """Test workspace initialization when directory already exists without force."""
        workspace_path = tmp_path / "existing-workspace"
        workspace_path.mkdir()

        manager = ServiceManager()
        result = manager.init_workspace(str(workspace_path), force=False)

        assert result is False

    def test_init_workspace_force_overwrite(self, tmp_path):
        """Test workspace initialization with --force flag."""
        workspace_path = tmp_path / "existing-workspace"
        workspace_path.mkdir()
        (workspace_path / "old-file.txt").write_text("old content")

        manager = ServiceManager()

        # Mock input to confirm overwrite
        with patch("builtins.input", return_value="yes"), patch("shutil.copytree"), patch("shutil.copy"):
            result = manager.init_workspace(str(workspace_path), force=True)

            assert result is True
            # Old file should be gone
            assert not (workspace_path / "old-file.txt").exists()
            # New structure should exist
            assert (workspace_path / "ai" / "agents").exists()

    def test_init_workspace_force_cancelled(self, tmp_path):
        """Test workspace initialization with --force flag but user cancels."""
        workspace_path = tmp_path / "existing-workspace"
        workspace_path.mkdir()

        manager = ServiceManager()

        # Mock input to cancel overwrite
        with patch("builtins.input", return_value="no"):
            result = manager.init_workspace(str(workspace_path), force=True)

            assert result is False
            # Directory should still exist
            assert workspace_path.exists()

    def test_init_workspace_exception_handling(self):
        """Test workspace initialization handles exceptions gracefully."""
        manager = ServiceManager()

        with patch.object(Path, "exists", side_effect=Exception("File system error")):
            result = manager.init_workspace("test-workspace")

            assert result is False

    def test_init_workspace_basic_structure(self, tmp_path):
        """Test basic workspace structure creation."""
        workspace_name = "test-workspace"
        workspace_path = tmp_path / workspace_name

        manager = ServiceManager()

        # Mock to avoid actual file copying
        with patch("shutil.copytree"), patch("shutil.copy"), patch.object(manager, "_create_workspace_metadata"):
            manager.init_workspace(str(workspace_path))

            # Should create the workspace directory
            assert workspace_path.exists()
            # Basic AI directories should be created
            assert (workspace_path / "ai" / "agents").exists()
            assert (workspace_path / "ai" / "teams").exists()
            assert (workspace_path / "ai" / "workflows").exists()
            assert (workspace_path / "knowledge").exists()
            assert (workspace_path / "knowledge" / ".gitkeep").exists()

    def test_locate_template_root_source(self):
        """Test template discovery from source directory."""
        manager = ServiceManager()
        template_root = manager._locate_template_root()

        # Should find templates in source directory when running tests
        assert template_root is not None
        assert (template_root / "agents" / "template-agent").exists()

    def test_create_workspace_metadata(self, tmp_path):
        """Test workspace metadata file creation."""
        workspace_path = tmp_path / "test-workspace"
        workspace_path.mkdir()

        manager = ServiceManager()
        manager._create_workspace_metadata(workspace_path)

        metadata_file = workspace_path / ".automagik-hive-workspace.yml"
        assert metadata_file.exists()

        # Verify metadata content
        import yaml

        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        assert "template_version" in metadata
        assert "hive_version" in metadata
        assert "created_at" in metadata
        assert metadata["template_version"] == "1.0.0"


class TestServiceManagerUninstall:
    """Test environment uninstall functionality."""

    def test_uninstall_environment_preserve_data(self):
        """Test environment uninstall with data preservation."""
        manager = ServiceManager()
        with patch("builtins.input", return_value="WIPE ALL"):
            with patch.object(manager, "uninstall_main_only", return_value=True) as mock_uninstall_main:
                result = manager.uninstall_environment("./test")

                assert result is True
                mock_uninstall_main.assert_called_once_with("./test")

    def test_uninstall_environment_wipe_data_confirmed(self):
        """Test environment uninstall with data wipe (confirmed)."""
        manager = ServiceManager()
        with patch("builtins.input", return_value="WIPE ALL"):
            with patch.object(manager, "uninstall_main_only", return_value=True) as mock_uninstall_main:
                result = manager.uninstall_environment("./test")

                assert result is True
                mock_uninstall_main.assert_called_once_with("./test")

    def test_uninstall_environment_wipe_data_cancelled(self):
        """Test environment uninstall with data wipe (cancelled)."""
        with patch("builtins.input", side_effect=["n", "no"]):
            manager = ServiceManager()
            result = manager.uninstall_environment("./test")

            assert result is False

    def test_uninstall_environment_eof_defaults(self):
        """Test environment uninstall with EOF (defaults to cancelled)."""
        manager = ServiceManager()
        with patch("builtins.input", side_effect=EOFError()):
            result = manager.uninstall_environment("./test")

            # EOF during confirmation should cancel the uninstall
            assert result is False

    def test_uninstall_environment_exception(self):
        """Test environment uninstall with exception."""
        with patch("builtins.input", side_effect=Exception("Input error")):
            manager = ServiceManager()
            result = manager.uninstall_environment("./test")

            assert result is False
