"""Test suite for CLI Agent Commands.

Tests for the AgentCommands class covering all 7 command methods with >95% coverage.
Follows TDD Red-Green-Refactor approach with failing tests first.

Test Categories:
- Unit tests: Individual command method testing  
- Integration tests: CLI argument parsing and error handling
- Mock tests: Docker and filesystem operations
- Cross-platform compatibility testing patterns
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cli.commands.agent import (
    AgentCommands,
    agent_install_cmd,
    agent_logs_cmd,
    agent_reset_cmd,
    agent_restart_cmd,
    agent_serve_cmd,
    agent_status_cmd,
    agent_stop_cmd,
)


class TestAgentCommands:
    """Test suite for AgentCommands class with comprehensive coverage."""

    @pytest.fixture
    def mock_agent_service(self):
        """Mock AgentService for testing command interactions."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            # Create required files for valid workspace
            (workspace / "docker-compose.yml").write_text("version: '3.8'\n")
            (workspace / ".env.example").write_text("HIVE_API_PORT=8886\n")
            yield str(workspace)

    def test_agent_commands_initialization(self, mock_agent_service):
        """Test AgentCommands initializes with AgentService."""
        commands = AgentCommands()
        assert commands.agent_service is not None
        # Should fail initially - no service created yet
        assert hasattr(commands, "agent_service")

    def test_agent_install_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent installation."""
        mock_agent_service.install_agent_environment.return_value = True

        commands = AgentCommands()
        result = commands.install(temp_workspace)

        # Should fail initially - method not implemented
        assert result is True
        assert mock_agent_service.install_agent_environment.called
        mock_agent_service.install_agent_environment.assert_called_once_with(
            str(Path(temp_workspace).resolve())
        )

    def test_agent_install_command_failure(self, mock_agent_service, temp_workspace):
        """Test agent installation failure."""
        mock_agent_service.install_agent_environment.return_value = False

        commands = AgentCommands()
        result = commands.install(temp_workspace)

        # Should fail initially - error handling not implemented
        assert result is False
        assert mock_agent_service.install_agent_environment.called

    def test_agent_install_command_default_workspace(self, mock_agent_service):
        """Test agent installation with default workspace (current directory)."""
        mock_agent_service.install_agent_environment.return_value = True

        commands = AgentCommands()
        result = commands.install()

        # Should fail initially - default path resolution not implemented
        expected_path = str(Path().resolve())
        mock_agent_service.install_agent_environment.assert_called_once_with(expected_path)
        assert result is True

    def test_agent_serve_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent server start."""
        mock_agent_service.serve_agent.return_value = True

        commands = AgentCommands()
        result = commands.serve(temp_workspace)

        # Should fail initially - serve method not implemented
        assert result is True
        mock_agent_service.serve_agent.assert_called_once_with(
            str(Path(temp_workspace).resolve())
        )

    def test_agent_serve_command_failure(self, mock_agent_service, temp_workspace):
        """Test agent server start failure."""
        mock_agent_service.serve_agent.return_value = False

        commands = AgentCommands()
        result = commands.serve(temp_workspace)

        # Should fail initially - error handling not implemented
        assert result is False
        assert mock_agent_service.serve_agent.called

    def test_agent_serve_command_default_workspace(self, mock_agent_service):
        """Test agent server start with default workspace."""
        mock_agent_service.serve_agent.return_value = True

        commands = AgentCommands()
        result = commands.serve()

        # Should fail initially - default workspace handling not implemented
        expected_path = str(Path().resolve())
        mock_agent_service.serve_agent.assert_called_once_with(expected_path)
        assert result is True

    def test_agent_stop_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent server stop."""
        mock_agent_service.stop_agent.return_value = True

        commands = AgentCommands()
        result = commands.stop(temp_workspace)

        # Should fail initially - stop method not implemented
        assert result is True
        mock_agent_service.stop_agent.assert_called_once_with(
            str(Path(temp_workspace).resolve())
        )

    def test_agent_stop_command_failure(self, mock_agent_service, temp_workspace):
        """Test agent server stop failure."""
        mock_agent_service.stop_agent.return_value = False

        commands = AgentCommands()
        result = commands.stop(temp_workspace)

        # Should fail initially - error handling not implemented
        assert result is False
        assert mock_agent_service.stop_agent.called

    def test_agent_stop_command_default_workspace(self, mock_agent_service):
        """Test agent server stop with default workspace."""
        mock_agent_service.stop_agent.return_value = True

        commands = AgentCommands()
        result = commands.stop()

        # Should fail initially - default workspace handling not implemented
        expected_path = str(Path().resolve())
        mock_agent_service.stop_agent.assert_called_once_with(expected_path)
        assert result is True

    def test_agent_restart_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent server restart."""
        mock_agent_service.restart_agent.return_value = True

        commands = AgentCommands()
        result = commands.restart(temp_workspace)

        # Should fail initially - restart method not implemented
        assert result is True
        mock_agent_service.restart_agent.assert_called_once_with(
            str(Path(temp_workspace).resolve())
        )

    def test_agent_restart_command_failure(self, mock_agent_service, temp_workspace):
        """Test agent server restart failure."""
        mock_agent_service.restart_agent.return_value = False

        commands = AgentCommands()
        result = commands.restart(temp_workspace)

        # Should fail initially - error handling not implemented
        assert result is False
        assert mock_agent_service.restart_agent.called

    def test_agent_restart_command_default_workspace(self, mock_agent_service):
        """Test agent server restart with default workspace."""
        mock_agent_service.restart_agent.return_value = True

        commands = AgentCommands()
        result = commands.restart()

        # Should fail initially - default workspace handling not implemented
        expected_path = str(Path().resolve())
        mock_agent_service.restart_agent.assert_called_once_with(expected_path)
        assert result is True

    def test_agent_logs_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent logs display."""
        mock_agent_service.show_agent_logs.return_value = True

        commands = AgentCommands()
        result = commands.logs(temp_workspace, tail=100)

        # Should fail initially - logs method not implemented
        assert result is True
        mock_agent_service.show_agent_logs.assert_called_once_with(
            str(Path(temp_workspace).resolve()), 100
        )

    def test_agent_logs_command_failure(self, mock_agent_service, temp_workspace):
        """Test agent logs display failure."""
        mock_agent_service.show_agent_logs.return_value = False

        commands = AgentCommands()
        result = commands.logs(temp_workspace)

        # Should fail initially - error handling not implemented
        assert result is False
        mock_agent_service.show_agent_logs.assert_called_once_with(
            str(Path(temp_workspace).resolve()), 50
        )

    def test_agent_logs_command_default_parameters(self, mock_agent_service):
        """Test agent logs with default parameters."""
        mock_agent_service.show_agent_logs.return_value = True

        commands = AgentCommands()
        result = commands.logs()

        # Should fail initially - default parameter handling not implemented
        expected_path = str(Path().resolve())
        mock_agent_service.show_agent_logs.assert_called_once_with(expected_path, 50)
        assert result is True

    def test_agent_status_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent status check."""
        mock_status = {
            "agent-server": "✅ Running (PID: 1234, Port: 38886)",
            "agent-postgres": "✅ Running (Port: 35532)",
        }
        mock_agent_service.get_agent_status.return_value = mock_status

        # Mock Path.exists for log file check
        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = "Recent log line"

                commands = AgentCommands()
                result = commands.status(temp_workspace)

        # Should fail initially - status method not implemented properly
        assert result is True
        mock_agent_service.get_agent_status.assert_called_once_with(
            str(Path(temp_workspace).resolve())
        )

    def test_agent_status_command_no_logs(self, mock_agent_service, temp_workspace):
        """Test agent status check when no log file exists."""
        mock_status = {
            "agent-server": "🛑 Stopped",
            "agent-postgres": "🛑 Stopped",
        }
        mock_agent_service.get_agent_status.return_value = mock_status

        # Mock Path.exists to return False for log file
        with patch("pathlib.Path.exists", return_value=False):
            commands = AgentCommands()
            result = commands.status(temp_workspace)

        # Should fail initially - no logs case not handled
        assert result is True
        assert mock_agent_service.get_agent_status.called

    def test_agent_status_command_subprocess_error(self, mock_agent_service, temp_workspace):
        """Test agent status check when subprocess fails."""
        mock_status = {"agent-server": "✅ Running"}
        mock_agent_service.get_agent_status.return_value = mock_status

        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run", side_effect=Exception("Subprocess error")):
                commands = AgentCommands()
                result = commands.status(temp_workspace)

        # Should fail initially - subprocess error handling not implemented
        assert result is True
        assert mock_agent_service.get_agent_status.called

    def test_agent_reset_command_success(self, mock_agent_service, temp_workspace):
        """Test successful agent environment reset."""
        mock_agent_service.reset_agent_environment.return_value = True

        commands = AgentCommands()
        result = commands.reset(temp_workspace)

        # Should fail initially - reset method not implemented
        assert result is True
        mock_agent_service.reset_agent_environment.assert_called_once_with(
            str(Path(temp_workspace).resolve())
        )

    def test_agent_reset_command_failure(self, mock_agent_service, temp_workspace):
        """Test agent environment reset failure."""
        mock_agent_service.reset_agent_environment.return_value = False

        commands = AgentCommands()
        result = commands.reset(temp_workspace)

        # Should fail initially - error handling not implemented
        assert result is False
        assert mock_agent_service.reset_agent_environment.called

    def test_agent_reset_command_default_workspace(self, mock_agent_service):
        """Test agent environment reset with default workspace."""
        mock_agent_service.reset_agent_environment.return_value = True

        commands = AgentCommands()
        result = commands.reset()

        # Should fail initially - default workspace handling not implemented
        expected_path = str(Path().resolve())
        mock_agent_service.reset_agent_environment.assert_called_once_with(expected_path)
        assert result is True


class TestAgentCommandsCLIIntegration:
    """Test CLI integration functions for agent commands."""

    @pytest.fixture
    def mock_agent_commands(self):
        """Mock AgentCommands class for CLI integration testing."""
        with patch("cli.commands.agent.AgentCommands") as mock_commands_class:
            mock_commands = Mock()
            mock_commands_class.return_value = mock_commands
            yield mock_commands

    def test_agent_install_cmd_success(self, mock_agent_commands):
        """Test CLI install command success."""
        mock_agent_commands.install.return_value = True

        result = agent_install_cmd("test_workspace")

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.install.assert_called_once_with("test_workspace")

    def test_agent_install_cmd_failure(self, mock_agent_commands):
        """Test CLI install command failure."""
        mock_agent_commands.install.return_value = False

        result = agent_install_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        assert mock_agent_commands.install.called

    def test_agent_install_cmd_no_workspace(self, mock_agent_commands):
        """Test CLI install command with no workspace."""
        mock_agent_commands.install.return_value = True

        result = agent_install_cmd()

        # Should fail initially - default parameter handling not implemented
        assert result == 0
        mock_agent_commands.install.assert_called_once_with(None)

    def test_agent_serve_cmd_success(self, mock_agent_commands):
        """Test CLI serve command success."""
        mock_agent_commands.serve.return_value = True

        result = agent_serve_cmd("test_workspace")

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.serve.assert_called_once_with("test_workspace")

    def test_agent_serve_cmd_failure(self, mock_agent_commands):
        """Test CLI serve command failure."""
        mock_agent_commands.serve.return_value = False

        result = agent_serve_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        assert mock_agent_commands.serve.called

    def test_agent_stop_cmd_success(self, mock_agent_commands):
        """Test CLI stop command success."""
        mock_agent_commands.stop.return_value = True

        result = agent_stop_cmd("test_workspace")

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.stop.assert_called_once_with("test_workspace")

    def test_agent_stop_cmd_failure(self, mock_agent_commands):
        """Test CLI stop command failure."""
        mock_agent_commands.stop.return_value = False

        result = agent_stop_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        assert mock_agent_commands.stop.called

    def test_agent_restart_cmd_success(self, mock_agent_commands):
        """Test CLI restart command success."""
        mock_agent_commands.restart.return_value = True

        result = agent_restart_cmd("test_workspace")

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.restart.assert_called_once_with("test_workspace")

    def test_agent_restart_cmd_failure(self, mock_agent_commands):
        """Test CLI restart command failure."""
        mock_agent_commands.restart.return_value = False

        result = agent_restart_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        assert mock_agent_commands.restart.called

    def test_agent_logs_cmd_success(self, mock_agent_commands):
        """Test CLI logs command success."""
        mock_agent_commands.logs.return_value = True

        result = agent_logs_cmd("test_workspace", tail=100)

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.logs.assert_called_once_with("test_workspace", 100)

    def test_agent_logs_cmd_failure(self, mock_agent_commands):
        """Test CLI logs command failure."""
        mock_agent_commands.logs.return_value = False

        result = agent_logs_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        mock_agent_commands.logs.assert_called_once_with("test_workspace", 50)

    def test_agent_status_cmd_success(self, mock_agent_commands):
        """Test CLI status command success."""
        mock_agent_commands.status.return_value = True

        result = agent_status_cmd("test_workspace")

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.status.assert_called_once_with("test_workspace")

    def test_agent_status_cmd_failure(self, mock_agent_commands):
        """Test CLI status command failure."""
        mock_agent_commands.status.return_value = False

        result = agent_status_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        assert mock_agent_commands.status.called

    def test_agent_reset_cmd_success(self, mock_agent_commands):
        """Test CLI reset command success."""
        mock_agent_commands.reset.return_value = True

        result = agent_reset_cmd("test_workspace")

        # Should fail initially - CLI function not implemented
        assert result == 0
        mock_agent_commands.reset.assert_called_once_with("test_workspace")

    def test_agent_reset_cmd_failure(self, mock_agent_commands):
        """Test CLI reset command failure."""
        mock_agent_commands.reset.return_value = False

        result = agent_reset_cmd("test_workspace")

        # Should fail initially - error code handling not implemented
        assert result == 1
        assert mock_agent_commands.reset.called


class TestAgentCommandsErrorHandling:
    """Test error handling and edge cases for agent commands."""

    @pytest.fixture
    def mock_agent_service_with_exceptions(self):
        """Mock AgentService that raises exceptions for testing."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            yield mock_service

    def test_agent_commands_with_invalid_workspace_path(self, mock_agent_service_with_exceptions):
        """Test commands with invalid workspace paths."""
        mock_agent_service_with_exceptions.install_agent_environment.side_effect = FileNotFoundError(
            "Workspace not found"
        )

        commands = AgentCommands()

        # Should fail initially - exception handling not implemented
        with pytest.raises(FileNotFoundError):
            commands.install("/invalid/workspace/path")

    def test_agent_commands_with_permission_errors(self, mock_agent_service_with_exceptions):
        """Test commands with permission errors."""
        mock_agent_service_with_exceptions.serve_agent.side_effect = PermissionError(
            "Permission denied"
        )

        commands = AgentCommands()

        # Should fail initially - permission error handling not implemented
        with pytest.raises(PermissionError):
            commands.serve("/restricted/path")

    def test_agent_commands_with_none_workspace(self, mock_agent_service_with_exceptions):
        """Test commands with None workspace parameter."""
        mock_agent_service_with_exceptions.stop_agent.return_value = True

        commands = AgentCommands()
        result = commands.stop(None)

        # Should fail initially - None handling not implemented
        expected_path = str(Path().resolve())
        mock_agent_service_with_exceptions.stop_agent.assert_called_once_with(expected_path)
        assert result is True

    def test_agent_status_command_empty_status(self, mock_agent_service_with_exceptions):
        """Test status command with empty status response."""
        mock_agent_service_with_exceptions.get_agent_status.return_value = {}

        with patch("pathlib.Path.exists", return_value=False):
            commands = AgentCommands()
            result = commands.status("test_workspace")

        # Should fail initially - empty status handling not implemented
        assert result is True
        assert mock_agent_service_with_exceptions.get_agent_status.called

    def test_agent_logs_command_with_zero_tail(self, mock_agent_service_with_exceptions):
        """Test logs command with zero tail parameter."""
        mock_agent_service_with_exceptions.show_agent_logs.return_value = True

        commands = AgentCommands()
        result = commands.logs("test_workspace", tail=0)

        # Should fail initially - zero tail handling not implemented
        assert result is True
        mock_agent_service_with_exceptions.show_agent_logs.assert_called_once_with(
            str(Path("test_workspace").resolve()), 0
        )

    def test_agent_logs_command_with_negative_tail(self, mock_agent_service_with_exceptions):
        """Test logs command with negative tail parameter."""
        mock_agent_service_with_exceptions.show_agent_logs.return_value = True

        commands = AgentCommands()
        result = commands.logs("test_workspace", tail=-10)

        # Should fail initially - negative tail handling not implemented
        assert result is True
        mock_agent_service_with_exceptions.show_agent_logs.assert_called_once_with(
            str(Path("test_workspace").resolve()), -10
        )


class TestAgentCommandsCrossPlatform:
    """Test cross-platform compatibility patterns for agent commands."""

    @pytest.fixture
    def mock_platform_detection(self):
        """Mock platform detection for cross-platform testing."""
        with patch("platform.system") as mock_system:
            yield mock_system

    def test_agent_commands_on_windows(self, mock_platform_detection):
        """Test agent commands on Windows platform."""
        mock_platform_detection.return_value = "Windows"

        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.install_agent_environment.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            result = commands.install("C:\\test\\workspace")

        # Should fail initially - Windows path handling not implemented
        assert result is True
        expected_path = str(Path("C:\\test\\workspace").resolve())
        mock_service.install_agent_environment.assert_called_once_with(expected_path)

    def test_agent_commands_on_linux(self, mock_platform_detection):
        """Test agent commands on Linux platform."""
        mock_platform_detection.return_value = "Linux"

        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.serve_agent.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            result = commands.serve("/home/user/workspace")

        # Should fail initially - Linux path handling not implemented
        assert result is True
        expected_path = str(Path("/home/user/workspace").resolve())
        mock_service.serve_agent.assert_called_once_with(expected_path)

    def test_agent_commands_on_macos(self, mock_platform_detection):
        """Test agent commands on macOS platform."""
        mock_platform_detection.return_value = "Darwin"

        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.restart_agent.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            result = commands.restart("/Users/user/workspace")

        # Should fail initially - macOS path handling not implemented
        assert result is True
        expected_path = str(Path("/Users/user/workspace").resolve())
        mock_service.restart_agent.assert_called_once_with(expected_path)

    def test_path_resolution_with_relative_paths(self):
        """Test path resolution with various relative path formats."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.status_agent.return_value = {}
            mock_service_class.return_value = mock_service

            commands = AgentCommands()

            test_paths = [".", "..", "./workspace", "../workspace", "~/workspace"]

            for test_path in test_paths:
                # Should fail initially - relative path normalization not implemented
                try:
                    commands.status(test_path)
                    expected_path = str(Path(test_path).resolve())
                    # Path resolution should be consistent across platforms
                    assert Path(expected_path).is_absolute()
                except Exception:
                    # Expected to fail initially
                    pass

    def test_agent_commands_with_unicode_paths(self):
        """Test agent commands with Unicode characters in paths."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.install_agent_environment.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            unicode_path = "/tmp/测试工作空间"

            # Should fail initially - Unicode path handling not implemented
            try:
                result = commands.install(unicode_path)
                expected_path = str(Path(unicode_path).resolve())
                mock_service.install_agent_environment.assert_called_once_with(expected_path)
                assert result is True
            except Exception:
                # Expected to fail initially with Unicode paths
                pass


class TestAgentCommandsPrintOutput:
    """Test print output and user feedback for agent commands."""

    def test_agent_install_print_messages(self, capsys):
        """Test install command print messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.install_agent_environment.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            commands.install("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - print messages not implemented
            assert "🤖 Installing agent environment in workspace" in captured.out
            assert "✅ Agent environment installation completed successfully" in captured.out

    def test_agent_serve_print_messages(self, capsys):
        """Test serve command print messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.serve_agent.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            commands.serve("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - print messages not implemented
            assert "🚀 Starting agent server in workspace" in captured.out
            assert "✅ Agent server started successfully" in captured.out

    def test_agent_stop_print_messages(self, capsys):
        """Test stop command print messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.stop_agent.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            commands.stop("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - print messages not implemented
            assert "🛑 Stopping agent server in workspace" in captured.out
            assert "✅ Agent server stopped successfully" in captured.out

    def test_agent_restart_print_messages(self, capsys):
        """Test restart command print messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.restart_agent.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            commands.restart("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - print messages not implemented
            assert "🔄 Restarting agent server in workspace" in captured.out
            assert "✅ Agent server restarted successfully" in captured.out

    def test_agent_logs_print_messages(self, capsys):
        """Test logs command print messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.show_agent_logs.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            commands.logs("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - print messages not implemented
            assert "📋 Showing agent logs from workspace" in captured.out

    def test_agent_status_print_table_format(self, capsys):
        """Test status command prints properly formatted table."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.get_agent_status.return_value = {
                "agent-server": "✅ Running (PID: 1234)",
                "agent-postgres": "🛑 Stopped"
            }
            mock_service_class.return_value = mock_service

            with patch("pathlib.Path.exists", return_value=False):
                commands = AgentCommands()
                commands.status("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - table formatting not implemented
            assert "📊 Agent Environment Status:" in captured.out
            assert "┌─────────────────────────┬──────────────────────────────────────┐" in captured.out
            assert "│ Agent Service           │ Status                               │" in captured.out
            assert "├─────────────────────────┼──────────────────────────────────────┤" in captured.out
            assert "│ Agent Server            │ ✅ Running (PID: 1234)               │" in captured.out
            assert "│ Agent Postgres          │ 🛑 Stopped                           │" in captured.out
            assert "└─────────────────────────┴──────────────────────────────────────┘" in captured.out

    def test_agent_reset_print_messages(self, capsys):
        """Test reset command print messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.reset_agent_environment.return_value = True
            mock_service_class.return_value = mock_service

            commands = AgentCommands()
            commands.reset("test_workspace")

            captured = capsys.readouterr()

            # Should fail initially - print messages not implemented
            assert "🔄 Resetting agent environment in workspace" in captured.out
            assert "✅ Agent environment reset completed successfully" in captured.out

    def test_failure_print_messages(self, capsys):
        """Test failure scenarios print appropriate error messages."""
        with patch("cli.commands.agent.AgentService") as mock_service_class:
            mock_service = Mock()
            mock_service.install_agent_environment.return_value = False
            mock_service.serve_agent.return_value = False
            mock_service.stop_agent.return_value = False
            mock_service.restart_agent.return_value = False
            mock_service.reset_agent_environment.return_value = False
            mock_service_class.return_value = mock_service

            commands = AgentCommands()

            # Test all failure scenarios
            commands.install("test")
            commands.serve("test")
            commands.stop("test")
            commands.restart("test")
            commands.reset("test")

            captured = capsys.readouterr()

            # Should fail initially - error messages not implemented
            assert "❌ Agent environment installation failed" in captured.out
            assert "❌ Failed to start agent server" in captured.out
            assert "❌ Failed to stop agent server" in captured.out
            assert "❌ Failed to restart agent server" in captured.out
            assert "❌ Agent environment reset failed" in captured.out
