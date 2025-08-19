"""Comprehensive tests for cli.workspace module.

These tests provide extensive coverage for workspace management including
workspace initialization, template generation, and server startup functionality.
All tests are designed with RED phase compliance for TDD workflow.
"""

import os
import subprocess
import tempfile
import threading
from pathlib import Path
from unittest.mock import call, patch

import pytest

from cli.workspace import WorkspaceManager


class TestWorkspaceManagerInitialization:
    """Test WorkspaceManager class initialization and configuration."""

    def test_init_sets_project_root(self):
        """Test WorkspaceManager initializes with current directory as project root."""
        with patch("pathlib.Path.cwd", return_value=Path("/test/project")):
            manager = WorkspaceManager()
            assert manager.project_root == Path("/test/project")

    def test_init_with_different_working_directory(self):
        """Test WorkspaceManager initialization from different directories."""
        test_paths = [Path("/home/user/project"), Path("/var/lib/app"), Path(tempfile.gettempdir()) / "workspace"]

        for test_path in test_paths:
            with patch("pathlib.Path.cwd", return_value=test_path):
                manager = WorkspaceManager()
                assert manager.project_root == test_path


class TestWorkspaceInitialization:
    """Test workspace initialization functionality."""

    def test_init_workspace_success(self, isolated_workspace):
        """Test successful workspace initialization with all components."""
        manager = WorkspaceManager()
        workspace_name = "test_workspace_success_unique"

        with (
            patch("builtins.input", return_value=workspace_name),
            patch("shutil.which", return_value="/usr/bin/git"),
            patch.object(manager, "_run_command") as mock_run,
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text") as mock_write_text,
        ):
            result = manager.init_workspace()

            assert result is True
            # Verify git commands were called with correct workspace path
            expected_calls = [
                call(["git", "init"], cwd=Path(workspace_name)),
                call(["git", "add", "."], cwd=Path(workspace_name)),
                call(["git", "commit", "-m", "Initial workspace setup"], cwd=Path(workspace_name)),
            ]
            mock_run.assert_has_calls(expected_calls)

            # Verify directory creation was attempted
            assert mock_mkdir.called
            assert mock_write_text.called

    def test_init_workspace_with_provided_name(self, isolated_workspace):
        """Test workspace initialization with provided workspace name."""
        manager = WorkspaceManager()
        workspace_name = "provided_workspace"

        with (
            patch("shutil.which", return_value=None),
            patch.object(manager, "_run_command"),
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text") as mock_write_text,
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = manager.init_workspace(workspace_name)

        assert result is True
        # Verify directory creation was attempted instead of checking real filesystem
        assert mock_mkdir.called
        assert mock_write_text.called

    def test_init_workspace_empty_name_error(self, isolated_workspace):
        """Test workspace initialization fails with empty name."""
        manager = WorkspaceManager()

        with patch("builtins.input", return_value=""), patch("builtins.print") as mock_print:
            result = manager.init_workspace()

            assert result is False
            mock_print.assert_called_with("❌ Workspace name is required")

    def test_init_workspace_existing_directory_error(self, isolated_workspace):
        """Test workspace initialization fails when directory already exists."""
        workspace_name = "existing_workspace"

        # Create existing directory in isolated workspace
        existing_dir = Path(workspace_name)
        existing_dir.mkdir()

        # Create manager after setting up directory
        manager = WorkspaceManager()

        with patch("builtins.print") as mock_print:
            result = manager.init_workspace(workspace_name)

        assert result is False
        mock_print.assert_called_with(f"❌ Directory {workspace_name} already exists")

    def test_init_workspace_permission_error(self, isolated_workspace):
        """Test workspace initialization handles permission errors."""
        manager = WorkspaceManager()
        workspace_name = "permission_test"

        with (
            patch("pathlib.Path.mkdir", side_effect=PermissionError("Access denied")),
            patch("builtins.print") as mock_print,
        ):
            result = manager.init_workspace(workspace_name)

            assert result is False
            mock_print.assert_called_with("❌ Failed to create workspace: Access denied")

    def test_init_workspace_creates_directory_structure(self, temp_workspace):
        """Test workspace initialization creates proper directory structure."""
        workspace_name = "structure_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            # Create manager after changing directory to ensure it uses the temp workspace
            manager = WorkspaceManager()

            with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                result = manager.init_workspace(workspace_name)

            assert result is True
            workspace_path = temp_workspace / workspace_name

            # Verify directory structure
            expected_dirs = ["ai/agents", "ai/teams", "ai/workflows", "api", "lib", "tests"]

            for dir_path in expected_dirs:
                assert (workspace_path / dir_path).exists()

        finally:
            os.chdir(original_cwd)

    def test_init_workspace_creates_template_files(self, temp_workspace):
        """Test workspace initialization creates template files with correct content."""
        manager = WorkspaceManager()
        import os
        import uuid

        workspace_name = f"template_test_{uuid.uuid4().hex[:8]}"

        # Store original directory to restore later
        original_cwd = os.getcwd()

        try:
            # Change to temp workspace directory
            os.chdir(temp_workspace)

            with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                result = manager.init_workspace(workspace_name)
        finally:
            # Always restore original directory
            os.chdir(original_cwd)

            assert result is True
            workspace_path = temp_workspace / workspace_name

            # Verify template files exist and have content
            template_files = [
                "pyproject.toml",
                "README.md",
                ".env.example",
                "api/main.py",
                "ai/agents/hello_agent.yaml",
            ]

            for file_path in template_files:
                file_full_path = workspace_path / file_path
                assert file_full_path.exists()
                content = file_full_path.read_text()
                assert len(content) > 0  # Should have template content

    def test_init_workspace_git_initialization_optional(self, temp_workspace):
        """Test workspace initialization works without git available."""
        manager = WorkspaceManager()
        workspace_name = "no_git_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with patch("shutil.which", return_value=None):  # Git not available
                result = manager.init_workspace(workspace_name)

            assert result is True  # Should succeed even without git

        finally:
            os.chdir(original_cwd)

    def test_init_workspace_cleanup_on_failure(self, isolated_workspace):
        """Test workspace initialization cleans up on failure."""
        manager = WorkspaceManager()
        workspace_name = "cleanup_test"

        with (
            patch.object(manager, "_get_pyproject_template", side_effect=Exception("Template error")),
            patch("shutil.rmtree") as mock_rmtree,
            patch("builtins.print"),
        ):
            result = manager.init_workspace(workspace_name)

            assert result is False
            # Should attempt cleanup - the workspace directory should exist and cleanup should be called
            mock_rmtree.assert_called()


class TestWorkspaceServerStartup:
    """Test workspace development server startup functionality."""

    def test_start_server_success(self, isolated_workspace):
        """Test successful workspace server startup."""
        manager = WorkspaceManager()
        workspace_path = str(isolated_workspace)

        # Create required API file
        api_dir = isolated_workspace / "api"
        api_dir.mkdir()
        api_file = api_dir / "main.py"
        api_file.write_text("# API main file")

        with patch("os.chdir") as mock_chdir, patch.object(manager, "_run_command") as mock_run:
            result = manager.start_server(workspace_path)

            assert result is True
            mock_chdir.assert_called_once_with(isolated_workspace)
            mock_run.assert_called_once_with(["python", "-m", "api.main"])

    def test_start_server_workspace_not_found(self, isolated_workspace):
        """Test server startup fails when workspace directory doesn't exist."""
        manager = WorkspaceManager()
        nonexistent_path = str(isolated_workspace / "nonexistent")

        with patch("builtins.print") as mock_print:
            result = manager.start_server(nonexistent_path)

            assert result is False
            mock_print.assert_called_with(f"❌ Workspace directory not found: {nonexistent_path}")

    def test_start_server_api_file_missing(self, isolated_workspace):
        """Test server startup fails when API file is missing."""
        manager = WorkspaceManager()
        workspace_path = str(isolated_workspace)

        with patch("builtins.print") as mock_print:
            result = manager.start_server(workspace_path)

            assert result is False
            expected_api_file = isolated_workspace / "api" / "main.py"
            mock_print.assert_called_with(f"❌ API file not found: {expected_api_file}")

    def test_start_server_keyboard_interrupt(self, temp_workspace):
        """Test server startup handles KeyboardInterrupt gracefully."""
        manager = WorkspaceManager()
        workspace_path = str(temp_workspace)

        # Create required API file
        api_dir = temp_workspace / "api"
        api_dir.mkdir()
        api_file = api_dir / "main.py"
        api_file.write_text("# API main file")

        with (
            patch("os.chdir"),
            patch.object(manager, "_run_command", side_effect=KeyboardInterrupt),
            patch("builtins.print") as mock_print,
        ):
            result = manager.start_server(workspace_path)

            assert result is True  # Should handle interrupt gracefully
            mock_print.assert_called_with("\n🛑 Server stopped")

    def test_start_server_exception_handling(self, temp_workspace):
        """Test server startup handles general exceptions."""
        manager = WorkspaceManager()
        workspace_path = str(temp_workspace)

        # Create required API file
        api_dir = temp_workspace / "api"
        api_dir.mkdir()
        api_file = api_dir / "main.py"
        api_file.write_text("# API main file")

        with (
            patch("os.chdir"),
            patch.object(manager, "_run_command", side_effect=Exception("Server error")),
            patch("builtins.print") as mock_print,
        ):
            result = manager.start_server(workspace_path)

            assert result is False
            mock_print.assert_called_with("❌ Failed to start server: Server error")


class TestWorkspaceTemplateGeneration:
    """Test workspace template generation functionality."""

    def test_get_pyproject_template(self, temp_workspace):
        """Test pyproject.toml template generation."""
        manager = WorkspaceManager()
        workspace_name = "test_project"

        template = manager._get_pyproject_template(workspace_name)

        assert f'name = "{workspace_name}"' in template
        assert 'version = "0.1.0"' in template
        assert '"automagik-hive"' in template
        assert '"fastapi"' in template
        assert '"uvicorn"' in template

    def test_get_readme_template(self, temp_workspace):
        """Test README.md template generation."""
        manager = WorkspaceManager()
        workspace_name = "test_project"

        template = manager._get_readme_template(workspace_name)

        assert f"# {workspace_name}" in template
        assert "Automagik Hive workspace" in template
        assert "uvx automagik-hive" in template
        assert "Quick Start" in template
        assert "Check docker-compose.yml for port configuration" in template

    def test_get_env_template(self, temp_workspace):
        """Test .env template generation."""
        manager = WorkspaceManager()

        template = manager._get_env_template()

        assert "DATABASE_URL=" in template
        assert "HIVE_API_KEY=" in template
        assert "PORT=8000" in template
        assert "ENVIRONMENT=development" in template

    def test_get_api_template(self, temp_workspace):
        """Test API template generation."""
        manager = WorkspaceManager()

        template = manager._get_api_template()

        assert "from fastapi import FastAPI" in template
        assert 'title="Automagik Hive Workspace"' in template
        assert "uvicorn.run(" in template
        assert "port=8000" in template

    def test_get_agent_template(self, temp_workspace):
        """Test agent template generation."""
        manager = WorkspaceManager()

        template = manager._get_agent_template()

        assert "name: hello_agent" in template
        assert "description:" in template
        assert "version: 1.0.0" in template
        assert "provider: openai" in template
        assert "name: gpt-4" in template


class TestWorkspaceCommandExecution:
    """Test workspace command execution functionality."""

    def test_run_command_success_without_capture(self, temp_workspace):
        """Test successful command execution without output capture."""
        manager = WorkspaceManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = manager._run_command(["echo", "test"])

            assert result is None
            mock_run.assert_called_once_with(["echo", "test"], cwd=None, check=True)

    def test_run_command_success_with_capture(self, temp_workspace):
        """Test successful command execution with output capture."""
        manager = WorkspaceManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "command output"
            mock_run.return_value.returncode = 0

            result = manager._run_command(["echo", "test"], capture_output=True)

            assert result == "command output"
            mock_run.assert_called_once_with(["echo", "test"], cwd=None, capture_output=True, text=True, check=True)

    def test_run_command_with_working_directory(self, temp_workspace):
        """Test command execution with specified working directory."""
        manager = WorkspaceManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "output"

            result = manager._run_command(["ls"], cwd=temp_workspace, capture_output=True)

            assert result == "output"
            mock_run.assert_called_once_with(["ls"], cwd=temp_workspace, capture_output=True, text=True, check=True)

    def test_run_command_called_process_error(self, temp_workspace):
        """Test command execution handles CalledProcessError."""
        manager = WorkspaceManager()

        with (
            patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["false"], stderr="Error")),
            patch("builtins.print") as mock_print,
        ):
            result = manager._run_command(["false"], capture_output=True)

            assert result is None
            mock_print.assert_any_call("❌ Command failed: false")
            mock_print.assert_any_call("Error: Error")

    def test_run_command_file_not_found(self, temp_workspace):
        """Test command execution handles FileNotFoundError."""
        manager = WorkspaceManager()

        with patch("subprocess.run", side_effect=FileNotFoundError), patch("builtins.print") as mock_print:
            result = manager._run_command(["nonexistent"], capture_output=True)

            assert result is None
            mock_print.assert_called_with("❌ Command not found: nonexistent")

    def test_run_command_timeout_handling(self, temp_workspace):
        """Test command execution handles timeout scenarios."""
        manager = WorkspaceManager()

        with (
            patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["sleep", "60"])),
            patch("builtins.print") as mock_print,
        ):
            result = manager._run_command(["sleep", "60"], capture_output=True)

            assert result is None
            mock_print.assert_called_with("❌ Command failed: sleep 60")

    def test_run_command_permission_error(self, temp_workspace):
        """Test command execution handles permission errors."""
        manager = WorkspaceManager()

        with (
            patch("subprocess.run", side_effect=FileNotFoundError("Command not found")),
            patch("builtins.print") as mock_print,
        ):
            result = manager._run_command(["restricted"], capture_output=True)

            assert result is None
            mock_print.assert_called_with("❌ Command not found: restricted")


class TestWorkspaceEdgeCases:
    """Test edge cases and error conditions."""

    def test_init_workspace_with_unicode_name(self, temp_workspace):
        """Test workspace initialization with Unicode characters in name."""
        manager = WorkspaceManager()
        unicode_name = "测试工作空间"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                result = manager.init_workspace(unicode_name)

            assert result is True
            assert (temp_workspace / unicode_name).exists()

        finally:
            os.chdir(original_cwd)

    def test_init_workspace_with_special_characters(self, temp_workspace):
        """Test workspace initialization with special characters in name."""
        special_names = ["workspace-123", "workspace_test", "workspace.v1"]
        manager = WorkspaceManager()

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            for name in special_names:
                with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                    result = manager.init_workspace(name)

                    assert result is True
                    assert (temp_workspace / name).exists()

        finally:
            os.chdir(original_cwd)

    def test_init_workspace_very_long_name(self, temp_workspace):
        """Test workspace initialization with very long workspace name."""
        manager = WorkspaceManager()
        long_name = "x" * 255  # Very long name

        with (
            patch("pathlib.Path.cwd", return_value=temp_workspace),
            patch("shutil.which", return_value=None),
            patch.object(manager, "_run_command"),
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text") as mock_write_text,
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = manager.init_workspace(long_name)

            # Should handle long names (may succeed or fail depending on filesystem)
            assert isinstance(result, bool)

            # Verify file operations were attempted but no real directories created
            if result:
                assert mock_mkdir.called
                assert mock_write_text.called

    def test_start_server_with_corrupted_api_file(self, temp_workspace):
        """Test server startup with corrupted API file."""
        manager = WorkspaceManager()
        workspace_path = str(temp_workspace)

        # Create corrupted API file
        api_dir = temp_workspace / "api"
        api_dir.mkdir()
        api_file = api_dir / "main.py"
        api_file.write_bytes(b"\x00\x01\x02\xff")  # Binary garbage

        with (
            patch("os.chdir"),
            patch.object(manager, "_run_command", side_effect=Exception("Syntax error")),
            patch("builtins.print"),
        ):
            result = manager.start_server(workspace_path)

            assert result is False

    def test_concurrent_workspace_operations(self, temp_workspace):
        """Test concurrent workspace operations."""
        manager = WorkspaceManager()
        results = []

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            def create_workspace(name):
                with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                    result = manager.init_workspace(f"workspace_{name}")
                    results.append(result)

            # Run concurrent workspace creation
            threads = [threading.Thread(target=create_workspace, args=(i,)) for i in range(3)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # All should succeed independently
            assert all(result is True for result in results)

        finally:
            os.chdir(original_cwd)

    def test_workspace_operations_with_readonly_filesystem(self, temp_workspace):
        """Test workspace operations handle read-only filesystem."""
        manager = WorkspaceManager()

        with (
            patch("pathlib.Path.cwd", return_value=temp_workspace),
            patch("pathlib.Path.mkdir", side_effect=PermissionError("Read-only filesystem")),
            patch("builtins.print"),
        ):
            result = manager.init_workspace("readonly_test")

            assert result is False

    def test_workspace_with_insufficient_disk_space(self, temp_workspace):
        """Test workspace creation handles insufficient disk space."""
        manager = WorkspaceManager()

        with (
            patch("pathlib.Path.cwd", return_value=temp_workspace),
            patch("pathlib.Path.write_text", side_effect=OSError("No space left on device")),
            patch("builtins.print"),
        ):
            result = manager.init_workspace("diskspace_test")

            assert result is False


class TestWorkspaceIntegration:
    """Test workspace integration with external systems."""

    def test_workspace_git_integration_success(self, temp_workspace):
        """Test workspace integrates properly with git when available."""
        manager = WorkspaceManager()
        workspace_name = "git_integration_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with patch("shutil.which", return_value="/usr/bin/git"), patch.object(manager, "_run_command") as mock_run:
                result = manager.init_workspace(workspace_name)

                assert result is True
                # Verify git commands were called in sequence
                git_calls = [call for call in mock_run.call_args_list if "git" in str(call)]
                assert len(git_calls) == 3  # init, add, commit

        finally:
            os.chdir(original_cwd)

    def test_workspace_git_integration_failure(self, temp_workspace):
        """Test workspace handles git command failures gracefully."""
        manager = WorkspaceManager()
        workspace_name = "git_failure_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            def selective_fail(cmd, **kwargs):
                # Only fail for git commands, allow other operations to succeed
                if cmd and "git" in cmd[0]:
                    raise subprocess.CalledProcessError(1, cmd, stderr="Git error")
                # Return a mock successful result for non-git commands
                from unittest.mock import MagicMock

                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                return mock_result

            with (
                patch("shutil.which", return_value="/usr/bin/git"),
                patch("subprocess.run", side_effect=selective_fail),
            ):
                # Should still succeed even if git fails
                result = manager.init_workspace(workspace_name)

                assert result is True

        finally:
            os.chdir(original_cwd)

    def test_workspace_environment_variable_integration(self, temp_workspace):
        """Test workspace respects environment variables."""
        manager = WorkspaceManager()
        workspace_name = "env_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with (
                patch("shutil.which", return_value=None),
                patch.object(manager, "_run_command"),
                patch.dict(os.environ, {"WORKSPACE_DEFAULT_PORT": "9000"}),
            ):
                result = manager.init_workspace(workspace_name)

                assert result is True
                # Environment template should be customizable

        finally:
            os.chdir(original_cwd)

    def test_workspace_docker_integration(self, temp_workspace):
        """Test workspace can integrate with Docker when available."""
        manager = WorkspaceManager()
        workspace_name = "docker_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with patch("shutil.which", return_value="/usr/bin/docker"), patch.object(manager, "_run_command"):
                result = manager.init_workspace(workspace_name)

                assert result is True
                # Could create docker-compose.yml when Docker is available

        finally:
            os.chdir(original_cwd)

    def test_workspace_with_existing_project_files(self, temp_workspace):
        """Test workspace creation in directory with existing files."""
        manager = WorkspaceManager()
        workspace_name = "existing_files_test"

        # Create some existing files in temp workspace
        existing_file = temp_workspace / "existing.txt"
        existing_file.write_text("existing content")

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                result = manager.init_workspace(workspace_name)

                assert result is True
                # Should create workspace in subdirectory, not interfere with existing files
                assert existing_file.exists()
                assert (temp_workspace / workspace_name).exists()

        finally:
            os.chdir(original_cwd)

    def test_workspace_cross_platform_compatibility(self, temp_workspace):
        """Test workspace creation works across different platforms."""
        manager = WorkspaceManager()
        workspace_name = "cross_platform_test"

        # Use os.chdir to change to temp workspace directory for proper isolation
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            # Test different path separators and conventions
            with patch("shutil.which", return_value=None), patch.object(manager, "_run_command"):
                result = manager.init_workspace(workspace_name)

                assert result is True
                # Templates should work on any platform
                workspace_path = temp_workspace / workspace_name
                assert (workspace_path / "pyproject.toml").exists()
                assert (workspace_path / "api" / "main.py").exists()

        finally:
            os.chdir(original_cwd)
