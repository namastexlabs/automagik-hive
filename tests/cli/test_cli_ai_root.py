"""
Comprehensive test suite for CLI external AI folder functionality.

Tests the setup_ai_root() function integration with CLI argument parsing,
environment variable propagation, command routing, and service integration.
All tests designed to FAIL initially for TDD RED phase implementation.

Key test scenarios:
1. setup_ai_root() precedence logic with CLI arguments
2. Environment variable side effects (os.environ["HIVE_AI_ROOT"])
3. Command counting and mutual exclusion validation
4. Service integration (ServiceManager, PostgreSQLCommands)
5. Exception handling (AIRootError, KeyboardInterrupt, SystemExit)
6. Argument parsing edge cases and routing
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

import pytest

from cli.main import main, create_parser, setup_ai_root
from lib.utils.ai_root import AIRootError


class TestSetupAIRootFunction:
    """Test setup_ai_root() function with CLI integration scenarios."""

    def test_setup_ai_root_with_explicit_path(self, monkeypatch, tmp_path):
        """Test setup_ai_root() with explicit AI root path."""
        # Given: A valid AI root directory
        ai_root = tmp_path / "test_ai"
        ai_root.mkdir()

        # When: setup_ai_root() is called with explicit path
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = ai_root
            result = setup_ai_root(str(ai_root))

        # Then: Should call resolve_ai_root with explicit path and set environment
        mock_resolve.assert_called_once_with(explicit_path=str(ai_root))
        assert os.environ["HIVE_AI_ROOT"] == str(ai_root)
        assert result == ai_root

    def test_setup_ai_root_with_empty_string(self, monkeypatch):
        """Test setup_ai_root() converts empty string to None."""
        # Given: Empty string argument (CLI flag provided without value)
        ai_root_arg = ""

        # When: setup_ai_root() is called with empty string
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = Path("ai")
            setup_ai_root(ai_root_arg)

        # Then: Should convert empty string to None for resolve_ai_root
        mock_resolve.assert_called_once_with(explicit_path=None)
        assert os.environ["HIVE_AI_ROOT"] == "ai"

    def test_setup_ai_root_with_none(self, monkeypatch):
        """Test setup_ai_root() with None argument."""
        # Given: None argument (CLI flag not provided)
        ai_root_arg = None

        # When: setup_ai_root() is called with None
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = Path("ai")
            setup_ai_root(ai_root_arg)

        # Then: Should pass None to resolve_ai_root
        mock_resolve.assert_called_once_with(explicit_path=None)
        assert os.environ["HIVE_AI_ROOT"] == "ai"

    def test_setup_ai_root_ai_root_error_handling(self, capsys):
        """Test setup_ai_root() handles AIRootError with sys.exit(1)."""
        # Given: resolve_ai_root raises AIRootError
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.side_effect = AIRootError("Invalid AI root directory")

            # When: setup_ai_root() is called
            # Then: Should exit with code 1 and print error
            with pytest.raises(SystemExit) as exc_info:
                setup_ai_root("/invalid/path")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Invalid AI root: Invalid AI root directory" in captured.err

    def test_setup_ai_root_environment_variable_persistence(self, monkeypatch):
        """Test that HIVE_AI_ROOT environment variable persists."""
        # Given: Initial environment state
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)

        # When: setup_ai_root() sets environment variable
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = Path("/test/ai/root")
            setup_ai_root("test_path")

        # Then: Environment variable should be set and persist
        assert "HIVE_AI_ROOT" in os.environ
        assert os.environ["HIVE_AI_ROOT"] == "/test/ai/root"


class TestCLIArgumentParsing:
    """Test CLI argument parsing with AI root scenarios."""

    def test_parser_serve_flag_with_ai_root(self):
        """Test --serve flag with AI root argument."""
        # Given: CLI arguments with --serve and AI root
        parser = create_parser()

        # When: Parsing --serve with AI root argument
        args = parser.parse_args(["--serve", "/path/to/ai"])

        # Then: Should capture AI root argument correctly
        assert args.serve == "/path/to/ai"
        assert getattr(args, 'dev', None) is None
        assert getattr(args, 'ai_root', None) is None

    def test_parser_serve_flag_without_ai_root(self):
        """Test --serve flag without AI root argument (empty string sentinel)."""
        # Given: CLI arguments with --serve flag only
        parser = create_parser()

        # When: Parsing --serve without argument
        args = parser.parse_args(["--serve"])

        # Then: Should use empty string sentinel
        assert args.serve == ""
        assert getattr(args, 'dev', None) is None
        assert getattr(args, 'ai_root', None) is None

    def test_parser_rejects_dev_flag(self):
        """Test that --dev flag is rejected in favor of dev subcommand."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--dev"])

    def test_parser_postgres_commands_with_ai_root(self):
        """Test PostgreSQL commands with AI root arguments."""
        parser = create_parser()

        # Test all PostgreSQL commands with AI root
        postgres_commands = [
            "postgres-status", "postgres-start", "postgres-stop",
            "postgres-restart", "postgres-logs", "postgres-health"
        ]

        for cmd in postgres_commands:
            args = parser.parse_args([f"--{cmd}", "/workspace/path"])
            assert getattr(args, cmd.replace("-", "_")) == "/workspace/path"

    def test_parser_subcommand_ai_root_handling(self):
        """Test subcommand AI root argument handling."""
        parser = create_parser()

        # Test install subcommand with AI root
        args1 = parser.parse_args(["install", "/install/ai/root"])
        assert args1.command == "install"
        assert args1.ai_root == "/install/ai/root"

        # Test dev subcommand with AI root
        args2 = parser.parse_args(["dev", "/dev/ai/root"])
        assert args2.command == "dev"
        assert args2.ai_root == "/dev/ai/root"

        # Test uninstall subcommand without AI root
        args3 = parser.parse_args(["uninstall"])
        assert args3.command == "uninstall"
        assert args3.ai_root is None

    def test_parser_positional_ai_root(self):
        """Test positional AI root argument."""
        parser = create_parser()

        # When: Providing positional AI root argument
        args = parser.parse_args(["/positional/ai/root"])

        # Then: Should capture as ai_root
        assert getattr(args, 'positional_ai_root', None) == "/positional/ai/root"
        assert args.serve is None
        assert getattr(args, 'dev', None) is None


class TestCommandCounting:
    """Test command counting and mutual exclusion logic."""

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_single_command_allowed(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test that single command executes successfully."""
        # Given: Single --serve command
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])
        mock_setup.return_value = Path("/test/ai")
        mock_service_mgr.return_value.serve_docker.return_value = True

        # When: Running main()
        result = main()

        # Then: Should execute successfully
        assert result == 0
        mock_setup.assert_called_once_with("")
        mock_service_mgr.return_value.serve_docker.assert_called_once()

    def test_multiple_commands_rejected(self, monkeypatch, capsys):
        """Test that multiple commands are rejected."""
        # Given: Multiple commands provided
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve', '--postgres-status'])

        # When: Running main()
        result = main()

        # Then: Should return error code 1
        assert result == 1
        captured = capsys.readouterr()
        assert "❌ Only one command allowed at a time" in captured.err

    def test_no_commands_shows_help(self, monkeypatch, capsys):
        """Test that no commands shows help."""
        # Given: No commands provided
        monkeypatch.setattr(sys, 'argv', ['cli'])

        # When: Running main()
        result = main()

        # Then: Should show help and return 0
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out or "Automagik Hive" in captured.out

    def test_command_detection_patterns(self):
        """Test command detection logic for various argument patterns."""
        parser = create_parser()

        # Test all flag commands with arguments
        flag_args = parser.parse_args(["--serve", "/path"])
        commands = [
            flag_args.serve is not None,
            flag_args.postgres_status is not None,
        ]
        assert sum(1 for cmd in commands if cmd) == 1

        # Test subcommands
        sub_args = parser.parse_args(["install"])
        assert sub_args.command == "install"

        # Test positional
        pos_args = parser.parse_args(["/path"])
        assert getattr(pos_args, 'positional_ai_root', None) is not None


class TestServiceIntegration:
    """Test integration with ServiceManager and PostgreSQLCommands."""

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_serve_command_integration(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test --serve command integration with ServiceManager."""
        # Given: --serve command with AI root
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve', '/ai/root'])
        mock_setup.return_value = Path("/resolved/ai")
        mock_service_mgr.return_value.serve_docker.return_value = True

        # When: Running main()
        result = main()

        # Then: Should call setup_ai_root and serve_docker
        assert result == 0
        mock_setup.assert_called_once_with('/ai/root')
        mock_service_mgr.assert_called_once()
        mock_service_mgr.return_value.serve_docker.assert_called_once_with('/ai/root')

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_dev_command_integration(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test dev subcommand integration with ServiceManager."""
        # Given: dev subcommand invoked without explicit AI root
        monkeypatch.setattr(sys, 'argv', ['cli', 'dev'])
        mock_setup.return_value = Path("/resolved/ai")
        mock_service_mgr.return_value.serve_local.return_value = True

        # When: Running main()
        result = main()

        # Then: Should call setup_ai_root with None and serve_local
        assert result == 0
        mock_setup.assert_called_once_with(None)
        mock_service_mgr.return_value.serve_local.assert_called_once_with("0.0.0.0", None, reload=True)

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_install_subcommand_integration(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test install subcommand integration."""
        # Given: install subcommand with AI root
        monkeypatch.setattr(sys, 'argv', ['cli', 'install', '/install/ai'])
        mock_setup.return_value = Path("/resolved/ai")
        mock_service_mgr.return_value.install_full_environment.return_value = True

        # When: Running main()
        result = main()

        # Then: Should call install_full_environment
        assert result == 0
        mock_setup.assert_called_once_with('/install/ai')
        mock_service_mgr.return_value.install_full_environment.assert_called_once_with("/resolved/ai")

    @patch('cli.main.PostgreSQLCommands')
    def test_postgres_commands_integration(self, mock_postgres_cmd, monkeypatch):
        """Test PostgreSQL commands integration."""
        # Given: postgres-status command
        monkeypatch.setattr(sys, 'argv', ['cli', '--postgres-status', 'workspace'])
        mock_postgres_cmd.return_value.postgres_status.return_value = True

        # When: Running main()
        result = main()

        # Then: Should call postgres_status
        assert result == 0
        mock_postgres_cmd.assert_called_once()
        mock_postgres_cmd.return_value.postgres_status.assert_called_once_with('workspace')

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_service_failure_handling(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test service method failure handling."""
        # Given: Service method returns False (failure)
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])
        mock_setup.return_value = Path("/ai")
        mock_service_mgr.return_value.serve_docker.return_value = False

        # When: Running main()
        result = main()

        # Then: Should return error code 1
        assert result == 1


class TestSubcommandAIRootHandling:
    """Test AI root handling for subcommands vs flags."""

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_dev_subcommand_vs_flag(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test dev subcommand vs --dev flag AI root handling."""
        mock_service_mgr.return_value.serve_local.return_value = True

        # Test dev subcommand with AI root
        monkeypatch.setattr(sys, 'argv', ['cli', 'dev', '/sub/ai'])
        mock_setup.return_value = Path("/resolved")
        main()
        mock_setup.assert_called_with('/sub/ai')

        mock_setup.reset_mock()

        # Legacy --dev flag should be rejected by parser without calling setup_ai_root
        with pytest.raises(SystemExit):
            parser = create_parser()
            parser.parse_args(["--dev", "/flag/ai"])
        mock_setup.assert_not_called()

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_getattr_fallback_pattern(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test getattr(args, 'ai_root', None) pattern for subcommands."""
        # Given: Subcommand without AI root argument
        monkeypatch.setattr(sys, 'argv', ['cli', 'install'])
        mock_setup.return_value = Path("/default")
        mock_service_mgr.return_value.install_full_environment.return_value = True

        # When: Running main()
        main()

        # Then: Should call setup_ai_root with None (getattr fallback)
        mock_setup.assert_called_once_with(None)

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_positional_ai_root_handling(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test positional AI root argument handling."""
        # Given: Positional AI root argument
        monkeypatch.setattr(sys, 'argv', ['cli', '/positional/ai/root'])
        mock_setup.return_value = Path("/resolved")
        mock_service_mgr.return_value.serve_local.return_value = True

        # When: Running main()
        result = main()

        # Then: Should call setup_ai_root with positional argument
        assert result == 0
        mock_setup.assert_called_once_with('/positional/ai/root')


class TestEnvironmentVariableSideEffects:
    """Test environment variable side effects and cleanup."""

    def test_hive_ai_root_environment_setting(self, monkeypatch):
        """Test that HIVE_AI_ROOT environment variable is set correctly."""
        # Given: Clean environment
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)

        # When: setup_ai_root() is called
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = Path("/test/ai/root")
            setup_ai_root("/explicit/path")

        # Then: Environment variable should be set
        assert os.environ["HIVE_AI_ROOT"] == "/test/ai/root"

    def test_environment_variable_persistence_across_calls(self, monkeypatch):
        """Test environment variable persistence across multiple calls."""
        monkeypatch.delenv("HIVE_AI_ROOT", raising=False)

        # First call
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = Path("/first/path")
            setup_ai_root("/first")
        assert os.environ["HIVE_AI_ROOT"] == "/first/path"

        # Second call should overwrite
        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.return_value = Path("/second/path")
            setup_ai_root("/second")
        assert os.environ["HIVE_AI_ROOT"] == "/second/path"

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_environment_propagation_to_services(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test that environment variable is available to service classes."""
        # Given: CLI command that sets AI root
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve', '/test/ai'])
        def _setup(path):
            os.environ["HIVE_AI_ROOT"] = str(Path("/resolved/ai"))
            return Path("/resolved/ai")

        mock_setup.side_effect = _setup
        mock_service_mgr.return_value.serve_docker.return_value = True

        # When: Running command
        main()

        # Then: Environment should be set before service instantiation
        mock_setup.assert_called_once()
        assert "HIVE_AI_ROOT" in os.environ


class TestExceptionHandling:
    """Test exception handling patterns in main()."""

    def test_keyboard_interrupt_handling(self, monkeypatch, capsys):
        """Test KeyboardInterrupt is re-raised with message."""
        # Given: Command that raises KeyboardInterrupt
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])

        with patch('cli.main.setup_ai_root') as mock_setup:
            mock_setup.side_effect = KeyboardInterrupt()

            # When: Running main()
            # Then: Should re-raise KeyboardInterrupt
            with pytest.raises(KeyboardInterrupt):
                main()

        captured = capsys.readouterr()
        assert "🛑 Interrupted by user" in captured.out

    def test_system_exit_handling(self, monkeypatch):
        """Test SystemExit is re-raised."""
        # Given: Command that raises SystemExit
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])

        with patch('cli.main.setup_ai_root') as mock_setup:
            mock_setup.side_effect = SystemExit(2)

            # When: Running main()
            # Then: Should re-raise SystemExit
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 2

    def test_general_exception_handling(self, monkeypatch, capsys):
        """Test general exception handling returns error code."""
        # Given: Command that raises general exception
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])

        with patch('cli.main.setup_ai_root') as mock_setup:
            mock_setup.side_effect = ValueError("Test error")

            # When: Running main()
            result = main()

            # Then: Should return error code 1 and print error
            assert result == 1
            captured = capsys.readouterr()
            assert "❌ Error: Test error" in captured.err

    def test_ai_root_error_from_setup(self, monkeypatch, capsys):
        """Test AIRootError from setup_ai_root causes sys.exit(1)."""
        # Given: setup_ai_root raises AIRootError
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])

        with patch('cli.main.resolve_ai_root') as mock_resolve:
            mock_resolve.side_effect = AIRootError("Invalid AI root")

            # When: Running main()
            # Then: Should exit with code 1
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "❌ Invalid AI root: Invalid AI root" in captured.err


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_empty_string_vs_none_ai_root_arguments(self):
        """Test distinction between empty string and None for AI root."""
        parser = create_parser()

        # Empty string for flag provided without argument
        args1 = parser.parse_args(["--serve"])
        assert args1.serve == ""

        # Subcommand captures AI root separately
        args2 = parser.parse_args(["dev", "/path"])
        assert args2.command == "dev"
        assert args2.ai_root == "/path"

    @patch('cli.main.ServiceManager')
    def test_service_instantiation_patterns(self, mock_service_mgr, monkeypatch):
        """Test service instantiation patterns across commands."""
        mock_service_mgr.return_value.serve_docker.return_value = True

        # Test that ServiceManager is instantiated for each command
        with patch('cli.main.setup_ai_root') as mock_setup:
            mock_setup.return_value = Path("/ai")

            monkeypatch.setattr(sys, 'argv', ['cli', '--serve'])
            main()

            # Should instantiate ServiceManager once per command
            assert mock_service_mgr.call_count == 1

    def test_argument_parsing_edge_cases(self):
        """Test edge cases in argument parsing."""
        parser = create_parser()

        # Test with special characters in AI root path
        args1 = parser.parse_args(["--serve", "/path/with spaces/ai-root"])
        assert args1.serve == "/path/with spaces/ai-root"

        # Test with relative paths using dev subcommand
        args2 = parser.parse_args(["dev", "relative/ai/path"])
        assert args2.command == "dev"
        assert args2.ai_root == "relative/ai/path"

        # Test with current directory
        args3 = parser.parse_args(["--serve", "."])
        assert args3.serve == "."

    @patch('cli.main.PostgreSQLCommands')
    def test_postgres_tail_argument_handling(self, mock_postgres_cmd, monkeypatch):
        """Test PostgreSQL logs command with --tail argument."""
        # Given: postgres-logs with --tail argument
        monkeypatch.setattr(sys, 'argv', ['cli', '--postgres-logs', 'workspace', '--tail', '100'])
        mock_postgres_cmd.return_value.postgres_logs.return_value = True

        # When: Running main()
        main()

        # Then: Should pass tail argument to postgres_logs
        mock_postgres_cmd.return_value.postgres_logs.assert_called_once_with('workspace', 100)

    def test_status_command_special_handling(self, monkeypatch, capsys):
        """Test --status command special output handling."""
        # Given: --status command
        monkeypatch.setattr(sys, 'argv', ['cli', '--status', 'workspace'])

        with patch('cli.main.ServiceManager') as mock_service_mgr:
            mock_service_mgr.return_value.docker_status.return_value = {
                'app': 'running',
                'postgres': 'stopped'
            }

            # When: Running main()
            result = main()

            # Then: Should print status and return 0
            assert result == 0
            captured = capsys.readouterr()
            assert "🔍 Production environment status in: workspace" in captured.out
            assert "app: running" in captured.out
            assert "postgres: stopped" in captured.out


class TestCLIIntegrationScenarios:
    """Test end-to-end CLI integration scenarios."""

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_full_serve_workflow(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test complete --serve workflow with AI root setup."""
        # Given: Full --serve command with custom AI root
        monkeypatch.setattr(sys, 'argv', ['cli', '--serve', '/custom/ai/root'])
        def _setup(path):
            os.environ["HIVE_AI_ROOT"] = str(Path("/resolved/ai/root"))
            return Path("/resolved/ai/root")

        mock_setup.side_effect = _setup
        mock_service_mgr.return_value.serve_docker.return_value = True

        # When: Running complete workflow
        result = main()

        # Then: Should execute full workflow successfully
        assert result == 0
        mock_setup.assert_called_once_with('/custom/ai/root')
        mock_service_mgr.assert_called_once()
        mock_service_mgr.return_value.serve_docker.assert_called_once_with('/custom/ai/root')
        assert os.environ["HIVE_AI_ROOT"] == "/resolved/ai/root"

    @patch('cli.main.ServiceManager')
    @patch('cli.main.setup_ai_root')
    def test_install_uninstall_workflow(self, mock_setup, mock_service_mgr, monkeypatch):
        """Test install and uninstall workflow with AI root."""
        mock_setup.return_value = Path("/ai/root")

        # Test install
        mock_service_mgr.return_value.install_full_environment.return_value = True
        monkeypatch.setattr(sys, 'argv', ['cli', 'install', '/install/ai'])
        result1 = main()
        assert result1 == 0

        # Reset mocks
        mock_setup.reset_mock()
        mock_service_mgr.reset_mock()

        # Test uninstall
        mock_service_mgr.return_value.uninstall_environment.return_value = True
        monkeypatch.setattr(sys, 'argv', ['cli', 'uninstall', '/uninstall/ai'])
        result2 = main()
        assert result2 == 0

    @patch('cli.main.PostgreSQLCommands')
    def test_postgres_command_sequence(self, mock_postgres_cmd, monkeypatch):
        """Test sequence of PostgreSQL commands."""
        mock_postgres_cmd.return_value.postgres_start.return_value = True
        mock_postgres_cmd.return_value.postgres_status.return_value = True
        mock_postgres_cmd.return_value.postgres_stop.return_value = True

        # Test start -> status -> stop sequence
        commands = [
            (['cli', '--postgres-start', 'workspace'], 'postgres_start'),
            (['cli', '--postgres-status', 'workspace'], 'postgres_status'),
            (['cli', '--postgres-stop', 'workspace'], 'postgres_stop')
        ]

        for argv, method_name in commands:
            mock_postgres_cmd.reset_mock()
            monkeypatch.setattr(sys, 'argv', argv)
            result = main()
            assert result == 0
            getattr(mock_postgres_cmd.return_value, method_name).assert_called_once_with('workspace')
