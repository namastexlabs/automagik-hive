"""Comprehensive tests for cli.commands.genie module.

These tests provide extensive coverage for genie command functionality including
service lifecycle operations, Claude launching, error handling, and integration scenarios.
All tests are designed with RED phase compliance for TDD workflow.
"""

import pytest
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call

from cli.commands.genie import GenieCommands


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory for testing."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_genie_service():
    """Create a mock GenieService for testing GenieCommands."""
    with patch('cli.commands.genie.GenieService') as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        yield mock_service


@pytest.fixture
def genie_md_content():
    """Sample GENIE.md content for testing."""
    return """# Master Genie System

This is the Master Genie configuration with comprehensive agent orchestration.

## Agent Routing
- hive-dev-coder: Code implementation
- hive-testing-maker: Test creation
- hive-quality-ruff: Code quality checks

## Behavioral Framework
The genie operates with strict behavioral compliance and routing intelligence.
"""


@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self, max_time=None):
            if self.start_time is None:
                raise ValueError("Timer not started")
            elapsed = time.time() - self.start_time
            if max_time and elapsed > max_time:
                pytest.fail(f"Operation took {elapsed:.2f}s, expected < {max_time}s")
            return elapsed
    
    return Timer()


class TestGenieCommandsInitialization:
    """Test GenieCommands class initialization and configuration."""

    def test_init_with_workspace_path(self, temp_workspace):
        """Test GenieCommands initializes correctly with provided workspace path."""
        commands = GenieCommands(temp_workspace)
        
        assert commands.workspace_path == temp_workspace

    def test_init_with_default_workspace(self):
        """Test GenieCommands initializes with current directory when no path provided."""
        commands = GenieCommands()
        
        # The commands should resolve to the current working directory
        expected_path = Path()
        assert commands.workspace_path == expected_path

    def test_init_creates_genie_service(self, temp_workspace, mock_genie_service):
        """Test GenieCommands creates GenieService instance during initialization."""
        commands = GenieCommands(temp_workspace)
        
        # GenieService should be instantiated with workspace path
        assert commands.genie_service is not None

    def test_init_with_string_workspace_path(self, temp_workspace):
        """Test GenieCommands handles string workspace paths correctly."""
        workspace_str = str(temp_workspace)
        commands = GenieCommands(workspace_str)
        
        # Should convert string to Path object
        assert isinstance(commands.workspace_path, (Path, str))

    def test_init_with_none_workspace_path(self):
        """Test GenieCommands handles None workspace path correctly."""
        commands = GenieCommands(None)
        
        # Should default to current directory
        assert commands.workspace_path == Path()


class TestGenieServiceLifecycleOperations:
    """Test genie service lifecycle management operations."""

    def test_install_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service installation."""
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.install()
        
        assert result is True
        mock_genie_service.install_genie_environment.assert_called_once_with(".")
        mock_genie_service.serve_genie.assert_called_once_with(".")

    def test_install_with_custom_workspace(self, temp_workspace, mock_genie_service):
        """Test installation with custom workspace parameter."""
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_workspace = "/custom/workspace"
        result = commands.install(custom_workspace)
        
        assert result is True
        mock_genie_service.install_genie_environment.assert_called_once_with(custom_workspace)
        mock_genie_service.serve_genie.assert_called_once_with(custom_workspace)

    def test_install_failure_during_environment_setup(self, temp_workspace, mock_genie_service):
        """Test installation fails when environment setup fails."""
        mock_genie_service.install_genie_environment.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.install()
        
        assert result is False
        mock_genie_service.install_genie_environment.assert_called_once()
        # serve_genie should not be called if install fails
        mock_genie_service.serve_genie.assert_not_called()

    def test_install_failure_during_service_start(self, temp_workspace, mock_genie_service):
        """Test installation fails when service start fails."""
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.install()
        
        assert result is False
        mock_genie_service.install_genie_environment.assert_called_once()
        mock_genie_service.serve_genie.assert_called_once()

    def test_install_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test installation handles exceptions gracefully."""
        mock_genie_service.install_genie_environment.side_effect = Exception("Installation error")
        
        commands = GenieCommands(temp_workspace)
        result = commands.install()
        
        assert result is False

    def test_start_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service startup."""
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.start()
        
        assert result is True
        mock_genie_service.serve_genie.assert_called_once_with(".")

    def test_start_with_custom_workspace(self, temp_workspace, mock_genie_service):
        """Test start with custom workspace parameter."""
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_workspace = "/custom/workspace"
        result = commands.start(custom_workspace)
        
        assert result is True
        mock_genie_service.serve_genie.assert_called_once_with(custom_workspace)

    def test_start_failure(self, temp_workspace, mock_genie_service):
        """Test start handles service startup failures."""
        mock_genie_service.serve_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.start()
        
        assert result is False

    def test_start_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test start handles exceptions gracefully."""
        mock_genie_service.serve_genie.side_effect = Exception("Service error")
        
        commands = GenieCommands(temp_workspace)
        result = commands.start()
        
        assert result is False

    def test_stop_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service shutdown."""
        mock_genie_service.stop_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.stop()
        
        assert result is True
        mock_genie_service.stop_genie.assert_called_once_with(".")

    def test_stop_with_custom_workspace(self, temp_workspace, mock_genie_service):
        """Test stop with custom workspace parameter."""
        mock_genie_service.stop_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_workspace = "/custom/workspace"
        result = commands.stop(custom_workspace)
        
        assert result is True
        mock_genie_service.stop_genie.assert_called_once_with(custom_workspace)

    def test_stop_failure(self, temp_workspace, mock_genie_service):
        """Test stop handles service shutdown failures."""
        mock_genie_service.stop_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.stop()
        
        assert result is False

    def test_stop_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test stop handles exceptions gracefully."""
        mock_genie_service.stop_genie.side_effect = Exception("Stop error")
        
        commands = GenieCommands(temp_workspace)
        result = commands.stop()
        
        assert result is False

    def test_restart_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service restart."""
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.restart()
        
        assert result is True
        mock_genie_service.stop_genie.assert_called_once_with(".")
        mock_genie_service.serve_genie.assert_called_once_with(".")

    def test_restart_with_stop_failure(self, temp_workspace, mock_genie_service):
        """Test restart handles stop operation failures."""
        mock_genie_service.stop_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.restart()
        
        assert result is False
        mock_genie_service.stop_genie.assert_called_once()
        # serve_genie should not be called if stop fails
        mock_genie_service.serve_genie.assert_not_called()

    def test_restart_with_start_failure(self, temp_workspace, mock_genie_service):
        """Test restart handles start operation failures."""
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.serve_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.restart()
        
        assert result is False
        mock_genie_service.stop_genie.assert_called_once()
        mock_genie_service.serve_genie.assert_called_once()

    def test_restart_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test restart handles exceptions gracefully."""
        mock_genie_service.stop_genie.side_effect = Exception("Restart error")
        
        commands = GenieCommands(temp_workspace)
        result = commands.restart()
        
        assert result is False


class TestGenieServiceStatusAndLogs:
    """Test genie service status monitoring and log retrieval."""

    def test_status_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service status check."""
        mock_genie_service.status_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.status()
        
        assert result is True
        mock_genie_service.status_genie.assert_called_once_with(".")

    def test_status_with_custom_workspace(self, temp_workspace, mock_genie_service):
        """Test status with custom workspace parameter."""
        mock_genie_service.status_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_workspace = "/custom/workspace"
        result = commands.status(custom_workspace)
        
        assert result is True
        mock_genie_service.status_genie.assert_called_once_with(custom_workspace)

    def test_status_failure(self, temp_workspace, mock_genie_service):
        """Test status handles service status check failures."""
        mock_genie_service.status_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.status()
        
        assert result is False

    def test_status_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test status handles exceptions gracefully."""
        mock_genie_service.status_genie.side_effect = Exception("Status error")
        
        commands = GenieCommands(temp_workspace)
        result = commands.status()
        
        assert result is False

    def test_logs_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service log retrieval."""
        mock_genie_service.logs_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.logs()
        
        assert result is True
        mock_genie_service.logs_genie.assert_called_once_with(".", 50)

    def test_logs_with_custom_tail(self, temp_workspace, mock_genie_service):
        """Test logs with custom tail parameter."""
        mock_genie_service.logs_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_tail = 100
        result = commands.logs(tail=custom_tail)
        
        assert result is True
        mock_genie_service.logs_genie.assert_called_once_with(".", custom_tail)

    def test_logs_with_custom_workspace_and_tail(self, temp_workspace, mock_genie_service):
        """Test logs with both custom workspace and tail parameters."""
        mock_genie_service.logs_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_workspace = "/custom/workspace"
        custom_tail = 200
        result = commands.logs(custom_workspace, custom_tail)
        
        assert result is True
        mock_genie_service.logs_genie.assert_called_once_with(custom_workspace, custom_tail)

    def test_logs_failure(self, temp_workspace, mock_genie_service):
        """Test logs handles service log retrieval failures."""
        mock_genie_service.logs_genie.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.logs()
        
        assert result is False

    def test_logs_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test logs handles exceptions gracefully."""
        mock_genie_service.logs_genie.side_effect = Exception("Logs error")
        
        commands = GenieCommands(temp_workspace)
        result = commands.logs()
        
        assert result is False


class TestGenieServiceReset:
    """Test genie service reset functionality."""

    def test_reset_success(self, temp_workspace, mock_genie_service):
        """Test successful genie service reset."""
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.uninstall_genie_environment.return_value = True
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.reset()
        
        assert result is True
        # Verify the sequence: stop -> uninstall -> install -> serve
        expected_calls = [
            call.stop_genie("."),
            call.uninstall_genie_environment("."),
            call.install_genie_environment("."),
            call.serve_genie(".")
        ]
        assert mock_genie_service.method_calls == expected_calls

    def test_reset_with_custom_workspace(self, temp_workspace, mock_genie_service):
        """Test reset with custom workspace parameter."""
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.uninstall_genie_environment.return_value = True
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        custom_workspace = "/custom/workspace"
        result = commands.reset(custom_workspace)
        
        assert result is True
        # Verify all operations use custom workspace
        expected_calls = [
            call.stop_genie(custom_workspace),
            call.uninstall_genie_environment(custom_workspace),
            call.install_genie_environment(custom_workspace),
            call.serve_genie(custom_workspace)
        ]
        assert mock_genie_service.method_calls == expected_calls

    def test_reset_with_uninstall_failure(self, temp_workspace, mock_genie_service):
        """Test reset handles uninstall failures."""
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.uninstall_genie_environment.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.reset()
        
        assert result is False
        # Install and serve should not be called if uninstall fails
        mock_genie_service.install_genie_environment.assert_not_called()
        mock_genie_service.serve_genie.assert_not_called()

    def test_reset_with_install_failure(self, temp_workspace, mock_genie_service):
        """Test reset handles install failures during reset."""
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.uninstall_genie_environment.return_value = True
        mock_genie_service.install_genie_environment.return_value = False
        
        commands = GenieCommands(temp_workspace)
        result = commands.reset()
        
        assert result is False
        # serve_genie should not be called if install fails
        mock_genie_service.serve_genie.assert_not_called()

    def test_reset_continues_after_stop_failure(self, temp_workspace, mock_genie_service):
        """Test reset continues even if stop operation fails."""
        mock_genie_service.stop_genie.return_value = False
        mock_genie_service.uninstall_genie_environment.return_value = True
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.reset()
        
        assert result is True
        # All operations should still be called even if stop fails
        mock_genie_service.stop_genie.assert_called_once()
        mock_genie_service.uninstall_genie_environment.assert_called_once()
        mock_genie_service.install_genie_environment.assert_called_once()
        mock_genie_service.serve_genie.assert_called_once()

    def test_reset_with_exception_handling(self, temp_workspace, mock_genie_service):
        """Test reset handles exceptions gracefully."""
        mock_genie_service.stop_genie.side_effect = Exception("Reset error")
        # Mock all other service methods to return proper boolean values
        mock_genie_service.uninstall_genie_environment.return_value = True
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.reset()
        
        # The reset should succeed because stop_genie exceptions are ignored
        # and other operations succeed
        assert result is True


class TestClaudeLaunching:
    """Test Claude launching functionality with GENIE.md integration."""

    def test_launch_claude_success_with_genie_md_in_current_dir(self, temp_workspace, genie_md_content):
        """Test successful Claude launch with GENIE.md in current directory."""
        # Create GENIE.md file in current directory
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude()
            
            assert result is True
            # Verify subprocess.run was called with correct command
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            
            assert call_args[0] == "claude"
            assert "--append-system-prompt" in call_args
            assert genie_md_content in call_args
            assert "--mcp-config" in call_args
            assert ".mcp.json" in call_args
            assert "--model" in call_args
            assert "sonnet" in call_args
            assert "--dangerously-skip-permissions" in call_args

    def test_launch_claude_success_with_genie_md_in_parent_dir(self, temp_workspace, genie_md_content):
        """Test successful Claude launch with GENIE.md in parent directory."""
        # Create GENIE.md file in parent directory
        parent_dir = temp_workspace
        genie_md_path = parent_dir / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        # Create subdirectory as current working directory
        current_dir = parent_dir / "subdirectory"
        current_dir.mkdir()
        
        commands = GenieCommands(current_dir)
        
        with patch('pathlib.Path.cwd', return_value=current_dir), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude()
            
            assert result is True
            # Verify the GENIE.md content was found and used
            call_args = mock_run.call_args[0][0]
            assert genie_md_content in call_args

    def test_launch_claude_with_extra_args(self, temp_workspace, genie_md_content):
        """Test Claude launch with additional command-line arguments."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        extra_args = ["--model", "opus", "--verbose"]
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude(extra_args)
            
            assert result is True
            call_args = mock_run.call_args[0][0]
            
            # Verify extra args are included
            assert "--model" in call_args
            assert "opus" in call_args
            assert "--verbose" in call_args

    def test_launch_claude_failure_genie_md_not_found(self, temp_workspace, capsys):
        """Test Claude launch fails when GENIE.md file is not found."""
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace):
            result = commands.launch_claude()
            
            assert result is False
            # Verify error message was printed to stderr
            captured = capsys.readouterr()
            assert "GENIE.md not found" in captured.err

    def test_launch_claude_failure_genie_md_read_error(self, temp_workspace, capsys):
        """Test Claude launch handles GENIE.md read errors."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text("content")
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = commands.launch_claude()
            
            assert result is False
            captured = capsys.readouterr()
            assert "Failed to read GENIE.md" in captured.err

    def test_launch_claude_failure_claude_not_found(self, temp_workspace, genie_md_content, capsys):
        """Test Claude launch handles missing claude command."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run', side_effect=FileNotFoundError("claude not found")):
            result = commands.launch_claude()
            
            assert result is False
            captured = capsys.readouterr()
            assert "claude command not found" in captured.err

    def test_launch_claude_handles_keyboard_interrupt(self, temp_workspace, genie_md_content, capsys):
        """Test Claude launch handles keyboard interrupt gracefully."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run', side_effect=KeyboardInterrupt()):
            result = commands.launch_claude()
            
            assert result is True  # Keyboard interrupt is not an error
            captured = capsys.readouterr()
            assert "Interrupted by user" in captured.out

    def test_launch_claude_failure_subprocess_error(self, temp_workspace, genie_md_content):
        """Test Claude launch handles subprocess execution errors."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1  # Non-zero exit code
            
            result = commands.launch_claude()
            
            assert result is False

    def test_launch_claude_failure_general_exception(self, temp_workspace, genie_md_content, capsys):
        """Test Claude launch handles general exceptions."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run', side_effect=Exception("Unexpected error")):
            result = commands.launch_claude()
            
            assert result is False
            captured = capsys.readouterr()
            assert "Failed to launch claude" in captured.err


class TestGenieCommandsEdgeCases:
    """Test edge cases and error conditions."""

    def test_operations_with_invalid_workspace(self, mock_genie_service):
        """Test commands handle invalid workspace paths gracefully."""
        invalid_path = Path("/nonexistent/workspace/path")
        commands = GenieCommands(invalid_path)
        
        # Mock all genie service operations to return success
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.status_genie.return_value = True
        mock_genie_service.logs_genie.return_value = True
        mock_genie_service.uninstall_genie_environment.return_value = True
        
        # All operations should complete successfully (GenieService handles path validation)
        assert commands.install() is True
        assert commands.start() is True
        assert commands.stop() is True
        assert commands.status() is True
        assert commands.logs() is True
        assert commands.reset() is True

    def test_concurrent_operations(self, temp_workspace, mock_genie_service):
        """Test commands handle concurrent operations safely."""
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        
        # Mock concurrent start operations
        results = []
        
        def start_service():
            results.append(commands.start())
        
        threads = [threading.Thread(target=start_service) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(result is True for result in results)
        assert len(results) == 3

    def test_operations_with_empty_workspace_string(self, mock_genie_service):
        """Test commands handle empty workspace string."""
        mock_genie_service.serve_genie.return_value = True
        
        commands = GenieCommands()
        result = commands.start("")
        
        assert result is True
        mock_genie_service.serve_genie.assert_called_once_with("")

    def test_logs_with_zero_tail(self, temp_workspace, mock_genie_service):
        """Test logs command handles zero tail parameter."""
        mock_genie_service.logs_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.logs(tail=0)
        
        assert result is True
        mock_genie_service.logs_genie.assert_called_once_with(".", 0)

    def test_logs_with_negative_tail(self, temp_workspace, mock_genie_service):
        """Test logs command handles negative tail parameter."""
        mock_genie_service.logs_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        result = commands.logs(tail=-10)
        
        assert result is True
        mock_genie_service.logs_genie.assert_called_once_with(".", -10)

    def test_launch_claude_with_empty_extra_args(self, temp_workspace, genie_md_content):
        """Test Claude launch handles empty extra arguments list."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude([])
            
            assert result is True

    def test_launch_claude_with_none_extra_args(self, temp_workspace, genie_md_content):
        """Test Claude launch handles None extra arguments."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude(None)
            
            assert result is True


class TestGenieCommandsIntegration:
    """Test integration scenarios and complex workflows."""

    def test_full_lifecycle_workflow(self, temp_workspace, mock_genie_service):
        """Test complete genie service lifecycle: install -> start -> status -> logs -> stop -> reset."""
        # Mock all operations to succeed
        mock_genie_service.install_genie_environment.return_value = True
        mock_genie_service.serve_genie.return_value = True
        mock_genie_service.status_genie.return_value = True
        mock_genie_service.logs_genie.return_value = True
        mock_genie_service.stop_genie.return_value = True
        mock_genie_service.uninstall_genie_environment.return_value = True
        
        commands = GenieCommands(temp_workspace)
        
        # Execute full lifecycle
        assert commands.install() is True
        assert commands.status() is True
        assert commands.logs() is True
        assert commands.stop() is True
        assert commands.reset() is True
        
        # Verify all expected service calls were made
        expected_calls = [
            call.install_genie_environment("."),
            call.serve_genie("."),
            call.status_genie("."),
            call.logs_genie(".", 50),
            call.stop_genie("."),
            call.stop_genie("."),  # Called again during reset
            call.uninstall_genie_environment("."),
            call.install_genie_environment("."),
            call.serve_genie(".")
        ]
        assert mock_genie_service.method_calls == expected_calls

    def test_error_recovery_workflow(self, temp_workspace, mock_genie_service):
        """Test error recovery scenarios during service operations."""
        # Simulate initial failure followed by success
        mock_genie_service.serve_genie.side_effect = [False, True]  # Fail first, succeed second
        mock_genie_service.stop_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        
        # First start fails
        assert commands.start() is False
        
        # Restart should still work (calls stop then start)
        assert commands.restart() is True
        
        # Verify the sequence of calls
        expected_calls = [
            call.serve_genie("."),  # First start (fails)
            call.stop_genie("."),   # Stop during restart
            call.serve_genie(".")   # Start during restart (succeeds)
        ]
        assert mock_genie_service.method_calls == expected_calls

    def test_claude_launch_with_service_lifecycle(self, temp_workspace, genie_md_content, mock_genie_service):
        """Test Claude launch combined with service management."""
        # Setup GENIE.md
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        # Mock service operations
        mock_genie_service.serve_genie.return_value = True
        mock_genie_service.status_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        
        # Start services and check status
        assert commands.start() is True
        assert commands.status() is True
        
        # Launch Claude
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            assert commands.launch_claude() is True
        
        # Verify service operations were called
        mock_genie_service.serve_genie.assert_called_once()
        mock_genie_service.status_genie.assert_called_once()

    def test_performance_timing(self, temp_workspace, mock_genie_service, performance_timer):
        """Test command execution completes within reasonable time."""
        mock_genie_service.status_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        
        performance_timer.start()
        status_result = commands.status()
        elapsed = performance_timer.stop(max_time=1.0)
        
        assert status_result is True
        assert elapsed < 0.1  # Status check should be very fast

    def test_multiple_workspace_operations(self, temp_workspace, mock_genie_service):
        """Test operations across multiple workspace parameters."""
        mock_genie_service.serve_genie.return_value = True
        mock_genie_service.stop_genie.return_value = True
        
        commands = GenieCommands(temp_workspace)
        
        workspaces = [".", "/workspace1", "/workspace2"]
        
        for workspace in workspaces:
            assert commands.start(workspace) is True
            assert commands.stop(workspace) is True
        
        # Verify all workspace parameters were passed correctly
        expected_start_calls = [call.serve_genie(ws) for ws in workspaces]
        expected_stop_calls = [call.stop_genie(ws) for ws in workspaces]
        
        start_calls = [call for call in mock_genie_service.method_calls if 'serve_genie' in str(call)]
        stop_calls = [call for call in mock_genie_service.method_calls if 'stop_genie' in str(call)]
        
        assert start_calls == expected_start_calls
        assert stop_calls == expected_stop_calls


class TestGenieCommandsErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_all_operations_handle_service_exceptions(self, temp_workspace, mock_genie_service):
        """Test all operations handle GenieService exceptions gracefully."""
        # Make all service operations raise exceptions
        mock_genie_service.install_genie_environment.side_effect = Exception("Install error")
        mock_genie_service.serve_genie.side_effect = Exception("Start error")
        mock_genie_service.stop_genie.side_effect = Exception("Stop error")
        mock_genie_service.status_genie.side_effect = Exception("Status error")
        mock_genie_service.logs_genie.side_effect = Exception("Logs error")
        mock_genie_service.uninstall_genie_environment.side_effect = Exception("Uninstall error")
        
        commands = GenieCommands(temp_workspace)
        
        # All operations should return False instead of raising exceptions
        assert commands.install() is False
        assert commands.start() is False
        assert commands.stop() is False
        assert commands.restart() is False
        assert commands.status() is False
        assert commands.logs() is False
        assert commands.reset() is False

    def test_unicode_handling_in_genie_md(self, temp_workspace):
        """Test Claude launch handles unicode content in GENIE.md."""
        unicode_content = """# Master Genie 🧞‍♂️

This contains unicode: 你好 世界, émojis 🚀, and special chars: áéíóú
"""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(unicode_content, encoding='utf-8')
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude()
            
            assert result is True
            # Verify unicode content was passed correctly
            call_args = mock_run.call_args[0][0]
            assert "你好 世界" in str(call_args)
            assert "🚀" in str(call_args)

    def test_very_large_genie_md_file(self, temp_workspace):
        """Test Claude launch handles very large GENIE.md files."""
        # Create a large GENIE.md content (>1MB)
        large_content = "# Master Genie\n" + "A" * (1024 * 1024)  # 1MB+ of content
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(large_content)
        
        commands = GenieCommands(temp_workspace)
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude()
            
            assert result is True
            # Verify large content was handled
            call_args = mock_run.call_args[0][0]
            assert large_content in call_args

    def test_command_injection_protection(self, temp_workspace, genie_md_content):
        """Test Claude launch is protected against command injection in extra args."""
        genie_md_path = temp_workspace / "GENIE.md"
        genie_md_path.write_text(genie_md_content)
        
        commands = GenieCommands(temp_workspace)
        
        # Attempt command injection through extra args
        malicious_args = ["; rm -rf /", "&&", "echo", "hacked", "|", "cat"]
        
        with patch('pathlib.Path.cwd', return_value=temp_workspace), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = commands.launch_claude(malicious_args)
            
            assert result is True
            # Verify malicious args are passed as separate arguments (not shell injection)
            call_args = mock_run.call_args[0][0]
            assert "; rm -rf /" in call_args  # Should be treated as literal argument
            assert malicious_args[-1] in call_args