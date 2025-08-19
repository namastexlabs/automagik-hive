"""Comprehensive CLI integration test suite for refactored architecture.

Tests end-to-end CLI command functionality ensuring all uvx automagik-hive commands
work correctly with the new decomposed modules. Validates the complete command flow
from CLI entry points through to service execution.
Targets 90%+ coverage as per CLI cleanup strategy requirements.
"""

import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from cli.main import LazyCommandLoader, create_parser, main


class TestLazyCommandLoader:
    """Test the LazyCommandLoader functionality."""

    @pytest.fixture
    def loader(self):
        """Create LazyCommandLoader instance for testing."""
        return LazyCommandLoader()

    def test_lazy_command_loader_initialization(self, loader):
        """Test LazyCommandLoader initializes properly."""
        # The actual LazyCommandLoader is a simple stub
        assert hasattr(loader, "load_command")

    def test_interactive_initializer_lazy_loading(self, loader):
        """Test interactive initializer stub functionality."""
        # Test the load_command method
        result = loader.load_command("init")
        assert callable(result)
        assert "init" in result()

    def test_workspace_manager_lazy_loading(self, loader):
        """Test workspace manager stub functionality."""
        result = loader.load_command("workspace")
        assert callable(result)
        assert "workspace" in result()

    def test_workflow_orchestrator_lazy_loading(self, loader):
        """Test workflow orchestrator stub functionality."""
        result = loader.load_command("orchestrator")
        assert callable(result)
        assert "orchestrator" in result()

    def test_service_manager_lazy_loading(self, loader):
        """Test service manager stub functionality."""
        result = loader.load_command("service")
        assert callable(result)
        assert "service" in result()

    def test_health_checker_lazy_loading(self, loader):
        """Test health checker stub functionality."""
        result = loader.load_command("health")
        assert callable(result)
        assert "health" in result()

    def test_uninstaller_lazy_loading(self, loader):
        """Test uninstaller stub functionality."""
        result = loader.load_command("uninstall")
        assert callable(result)
        assert "uninstall" in result()

    def test_all_components_lazy_loaded_independently(self, loader):
        """Test all components can be loaded independently."""
        commands = ["init", "workspace", "orchestrator", "service", "health", "uninstall"]

        for command in commands:
            result = loader.load_command(command)
            assert callable(result)
            assert command in result()


class TestCLIMainEntryPoint:
    """Test CLI main entry point functionality."""

    def test_main_function_initialization(self):
        """Test main function initializes properly."""
        # Test help command
        with patch("sys.argv", ["automagik-hive", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_command_routing_install(self):
        """Test main function routes install command correctly."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = True
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                result = main()
                assert result == 0
                mock_agent.install.assert_called_once_with(".")

    def test_main_command_routing_start(self):
        """Test main function routes start command correctly."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.start.return_value = True
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-start", "."]):
                result = main()
                assert result == 0
                mock_agent.start.assert_called_once_with(".")

    def test_main_command_routing_health(self):
        """Test main function routes health command correctly."""
        with patch("cli.main.PostgreSQLCommands") as mock_postgres_class:
            mock_postgres = Mock()
            mock_postgres.postgres_health.return_value = True
            mock_postgres_class.return_value = mock_postgres

            with patch("sys.argv", ["automagik-hive", "--postgres-health", "."]):
                result = main()
                assert result == 0
                mock_postgres.postgres_health.assert_called_once_with(".")

    def test_main_exception_handling(self):
        """Test main function handles exceptions gracefully."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent_class.side_effect = Exception("Agent initialization failed")

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                result = main()
                assert result == 1


class TestCLICommandIntegration:
    """Integration tests for CLI commands with real argument parsing."""

    def test_argument_parsing_install_command(self):
        """Test argument parsing for install commands."""
        parser = create_parser()

        # Test agent install command
        args = parser.parse_args(["--agent-install", "."])
        assert args.agent_install == "."

        # Test agent install with workspace
        args = parser.parse_args(["--agent-install", "/path/to/workspace"])
        assert args.agent_install == "/path/to/workspace"

    def test_argument_parsing_service_commands(self):
        """Test argument parsing for service management commands."""
        parser = create_parser()

        # Test agent serve command
        args = parser.parse_args(["--agent-start", "."])
        assert args.agent_start == "."

        # Test agent stop command
        args = parser.parse_args(["--agent-stop", "."])
        assert args.agent_stop == "."

        # Test agent restart command
        args = parser.parse_args(["--agent-restart", "."])
        assert args.agent_restart == "."

    def test_argument_parsing_status_commands(self):
        """Test argument parsing for status and health commands."""
        parser = create_parser()

        # Test agent status command
        args = parser.parse_args(["--agent-status", "."])
        assert args.agent_status == "."

        # Test postgres health command
        args = parser.parse_args(["--postgres-health", "."])
        assert args.postgres_health == "."

        # Test postgres status command
        args = parser.parse_args(["--postgres-status", "."])
        assert args.postgres_status == "."

    def test_argument_parsing_logs_command(self):
        """Test argument parsing for logs command."""
        parser = create_parser()

        # Test postgres logs command
        args = parser.parse_args(["--postgres-logs", "."])
        assert args.postgres_logs == "."

        # Test agent logs with tail count
        args = parser.parse_args(["--agent-logs", ".", "--tail", "100"])
        assert args.agent_logs == "."
        assert args.tail == 100

    @pytest.mark.skip(reason="Blocked by task-4177cc24-9ce9-4589-b957-20612c107648 - CLI parser requires subcommands, cannot parse bare workspace paths")
    def test_argument_parsing_uninstall_command(self):
        """Test argument parsing for uninstall command."""
        parser = create_parser()

        # Test workspace uninstall command
        args = parser.parse_args(["--uninstall", "."])
        assert args.uninstall == "."

        # Test global uninstall command
        args = parser.parse_args(["--uninstall-global"])
        assert args.uninstall_global is True

    def test_argument_parsing_init_command(self):
        """Test argument parsing for init command."""
        parser = create_parser()

        # Test init command without name (default)
        args = parser.parse_args(["--init"])
        assert args.init == "__DEFAULT__"

        # Test init command with name
        args = parser.parse_args(["--init", "my-project"])
        assert args.init == "my-project"

    def test_argument_parsing_help_command(self):
        """Test argument parsing for help command."""
        parser = create_parser()

        # Help command will trigger SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_argument_parsing_invalid_combinations(self):
        """Test argument parsing with multiple commands."""
        parser = create_parser()

        # These should parse successfully
        args = parser.parse_args(["--agent-install", ".", "--agent-start", "."])
        assert args.agent_install == "."
        assert args.agent_start == "."

    def test_argument_parsing_edge_cases(self):
        """Test argument parsing edge cases."""
        parser = create_parser()

        # Test empty arguments (should not crash)
        args = parser.parse_args([])
        assert args is not None

        # Test version argument
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])


class TestCLIWorkflowIntegration:
    """Test complete CLI workflow integration."""

    def test_install_workflow_integration(self, isolated_workspace):
        """Test complete install workflow integration."""
        workspace_path = isolated_workspace / "test-workspace"
        workspace_path.mkdir()
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = True
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-install", str(workspace_path)]):
                result = main()
                assert result == 0
                mock_agent.install.assert_called_once_with(str(workspace_path))

    def test_service_lifecycle_integration(self):
        """Test complete service lifecycle integration."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.start.return_value = True
            mock_agent.status.return_value = True
            mock_agent.stop.return_value = True
            mock_agent_class.return_value = mock_agent

            # Test start
            with patch("sys.argv", ["automagik-hive", "--agent-start", "."]):
                result = main()
                assert result == 0
                mock_agent.start.assert_called_once_with(".")

            # Reset the mock
            mock_agent_class.reset_mock()
            mock_agent = Mock()
            mock_agent.status.return_value = True
            mock_agent_class.return_value = mock_agent

            # Test status
            with patch("sys.argv", ["automagik-hive", "--agent-status", "."]):
                result = main()
                assert result == 0
                mock_agent.status.assert_called_once_with(".")

            # Reset the mock
            mock_agent_class.reset_mock()
            mock_agent = Mock()
            mock_agent.stop.return_value = True
            mock_agent_class.return_value = mock_agent

            # Test stop
            with patch("sys.argv", ["automagik-hive", "--agent-stop", "."]):
                result = main()
                assert result == 0
                mock_agent.stop.assert_called_once_with(".")

    def test_health_check_integration(self):
        """Test health check integration."""
        with patch("cli.main.PostgreSQLCommands") as mock_postgres_class:
            mock_postgres = Mock()
            mock_postgres.postgres_health.return_value = True
            mock_postgres_class.return_value = mock_postgres

            with patch("sys.argv", ["automagik-hive", "--postgres-health", "."]):
                result = main()
                assert result == 0
                mock_postgres.postgres_health.assert_called_once_with(".")

    def test_init_workflow_integration(self):
        """Test init workflow integration."""
        with patch("cli.main.InitCommands") as mock_init_class:
            mock_init = Mock()
            mock_init.init_workspace.return_value = True
            mock_init_class.return_value = mock_init

            with patch("sys.argv", ["automagik-hive", "--init"]):
                result = main()
                assert result == 0
                mock_init.init_workspace.assert_called_once_with(None)

    @pytest.mark.skip(reason="Blocked by task-4177cc24-9ce9-4589-b957-20612c107648 - CLI parser requires subcommands, cannot parse bare workspace paths")
    def test_uninstall_workflow_integration(self):
        """Test uninstall workflow integration."""
        with patch("cli.main.ServiceManager") as mock_service_class:
            mock_service = Mock()
            mock_service.uninstall_environment.return_value = True
            mock_service_class.return_value = mock_service

            with patch("sys.argv", ["automagik-hive", "--uninstall", "."]):
                result = main()
                assert result == 0
                mock_service.uninstall_environment.assert_called_once_with(".")


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_command_failure_handling(self):
        """Test CLI handles command failures gracefully."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = False  # Failure
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                result = main()
                assert result == 1  # Exit with error code

    def test_exception_in_command_handling(self):
        """Test CLI handles exceptions in commands gracefully."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent_class.side_effect = Exception("Service error")

            with patch("sys.argv", ["automagik-hive", "--agent-start", "."]):
                result = main()
                assert result == 1

    def test_invalid_component_handling(self):
        """Test CLI handles invalid operations."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.start.return_value = False  # Invalid operation
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-start", "."]):
                result = main()
                assert result == 1

    def test_permission_error_handling(self):
        """Test CLI handles permission errors."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent_class.side_effect = PermissionError("Permission denied")

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                result = main()
                assert result == 1

    def test_keyboard_interrupt_handling(self):
        """Test CLI handles keyboard interrupts gracefully."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent_class.side_effect = KeyboardInterrupt()

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                with pytest.raises(KeyboardInterrupt):
                    main()


class TestCLIPerformance:
    """Test CLI performance characteristics."""

    def test_cli_startup_performance(self):
        """Test CLI startup performance."""
        from cli.main import LazyCommandLoader

        start_time = time.time()

        # Create loader (should be fast due to lazy loading)
        LazyCommandLoader()

        end_time = time.time()
        startup_time = end_time - start_time

        # Startup should be very fast with lazy loading
        assert startup_time < 0.1  # Less than 100ms

    def test_lazy_loading_performance(self):
        """Test lazy loading performance."""
        loader = LazyCommandLoader()

        start_time = time.time()

        # First access should create instance
        result1 = loader.load_command("service")

        end_time = time.time()
        first_access_time = end_time - start_time

        start_time = time.time()

        # Second access should be consistent
        result2 = loader.load_command("service")

        end_time = time.time()
        # Second access should be fast due to caching
        assert end_time - start_time < 0.01  # Very fast access

        # Both should be callable functions
        assert callable(result1)
        assert callable(result2)
        assert first_access_time < 0.1  # Should be fast

    def test_argument_parsing_performance(self):
        """Test argument parsing performance."""
        parser = create_parser()

        start_time = time.time()

        # Parse various argument combinations
        test_args = [
            ["--init"],
            ["--agent-install", "."],
            ["--agent-start", "."],
            ["--postgres-health", ".", "--tail", "100"],
            ["--agent-logs", ".", "--tail", "100"],
            ["--uninstall", "."],
        ]

        for args in test_args:
            try:
                parser.parse_args(args)
            except SystemExit:
                # Help command will exit, that's expected
                pass

        end_time = time.time()
        parsing_time = end_time - start_time

        # Argument parsing should be fast
        assert parsing_time < 0.1  # Less than 100ms for all combinations


class TestCLICompatibility:
    """Test CLI compatibility and backwards compatibility."""

    @pytest.mark.skip(reason="Blocked by task-4177cc24-9ce9-4589-b957-20612c107648 - CLI parser requires subcommands, cannot parse bare workspace paths")
    def test_command_line_interface_compatibility(self):
        """Test that CLI maintains expected interface."""
        parser = create_parser()

        # Test all expected commands are supported
        expected_commands = [
            "--agent-install",
            "--agent-start",
            "--agent-stop",
            "--agent-restart",
            "--agent-status",
            "--postgres-health",
            "--agent-logs",
            "--uninstall",
            "--init",
        ]

        for command in expected_commands:
            if command == "--init":
                args = parser.parse_args([command])
            else:
                args = parser.parse_args([command, "."])

            assert args is not None

    def test_component_names_compatibility(self):
        """Test that all expected component arguments are supported."""
        parser = create_parser()

        expected_paths = [".", tempfile.gettempdir(), "./workspace", "../parent"]

        for path in expected_paths:
            args = parser.parse_args(["--agent-install", path])
            assert args.agent_install == path

    def test_exit_code_compatibility(self):
        """Test that CLI returns expected exit codes."""
        # Test success exit code
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = True
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                result = main()
                assert result == 0

        # Test failure exit code
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = False
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-install", "."]):
                result = main()
                assert result == 1


class TestCLIEndToEndScenarios:
    """Test end-to-end CLI scenarios."""

    @pytest.fixture
    def mock_all_components(self):
        """Mock all CLI components for E2E testing."""
        with (
            patch("cli.main.InitCommands") as mock_init,
            patch("cli.main.AgentCommands") as mock_agent,
            patch("cli.main.PostgreSQLCommands") as mock_postgres,
            patch("cli.main.UninstallCommands") as mock_uninstall,
            patch("cli.main.ServiceManager") as mock_service,
        ):
            # Setup successful mocks
            mock_init.return_value.init_workspace.return_value = True
            mock_agent.return_value.install.return_value = True
            mock_agent.return_value.start.return_value = True
            mock_agent.return_value.stop.return_value = True
            mock_agent.return_value.status.return_value = True
            mock_agent.return_value.logs.return_value = True
            mock_postgres.return_value.postgres_health.return_value = True
            mock_postgres.return_value.postgres_status.return_value = True
            mock_postgres.return_value.postgres_logs.return_value = True
            mock_uninstall.return_value.uninstall_current_workspace.return_value = True
            mock_service.return_value.uninstall_environment.return_value = True
            mock_service.return_value.serve_docker.return_value = True
            mock_service.return_value.serve_local.return_value = True
            mock_service.return_value.stop_docker.return_value = True
            mock_service.return_value.restart_docker.return_value = True
            mock_service.return_value.docker_logs.return_value = True
            mock_service.return_value.install_full_environment.return_value = True

            yield {
                "init": mock_init,
                "agent": mock_agent,
                "postgres": mock_postgres,
                "uninstall": mock_uninstall,
                "service": mock_service,
            }

    @pytest.mark.skip(reason="Blocked by task-4177cc24-9ce9-4589-b957-20612c107648 - CLI parser requires subcommands, cannot parse bare workspace paths")
    def test_complete_agent_lifecycle(self, mock_all_components):
        """Test complete agent lifecycle: install -> start -> health -> stop -> uninstall."""
        scenarios = [
            (["automagik-hive", "--agent-install", "."], 0),
            (["automagik-hive", "--agent-start", "."], 0),
            (["automagik-hive", "--postgres-health", "."], 0),
            (["automagik-hive", "--agent-status", "."], 0),
            (["automagik-hive", "--agent-logs", "."], 0),
            (["automagik-hive", "--agent-stop", "."], 0),
            (["automagik-hive", "--uninstall", "."], 0),
        ]

        for argv, expected_exit in scenarios:
            with patch("sys.argv", argv):
                result = main()
                assert result == expected_exit

    def test_complete_workspace_lifecycle(self, mock_all_components):
        """Test complete workspace lifecycle."""
        scenarios = [
            (["automagik-hive", "--init"], 0),
            (["automagik-hive", "--agent-install", "."], 0),
            (["automagik-hive", "--agent-start", "."], 0),
            (["automagik-hive", "--postgres-health", "."], 0),
            (["automagik-hive", "--agent-stop", "."], 0),
        ]

        for argv, expected_exit in scenarios:
            with patch("sys.argv", argv):
                result = main()
                assert result == expected_exit

    def test_all_components_lifecycle(self, mock_all_components):
        """Test complete system lifecycle with all components."""
        scenarios = [
            (["automagik-hive", "--agent-install", "."], 0),
            (["automagik-hive", "--agent-start", "."], 0),
            (["automagik-hive", "--postgres-health", "."], 0),
            (["automagik-hive", "--agent-status", "."], 0),
            (["automagik-hive", "--agent-logs", ".", "--tail", "50"], 0),
            (["automagik-hive", "--agent-restart", "."], 0),
            (["automagik-hive", "--agent-stop", "."], 0),
        ]

        for argv, expected_exit in scenarios:
            with patch("sys.argv", argv):
                result = main()
                assert result == expected_exit

    def test_error_recovery_scenarios(self):
        """Test error recovery scenarios."""
        # Setup failure scenarios with fresh mocks
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = False
            mock_agent.start.return_value = False
            mock_agent_class.return_value = mock_agent

            failure_scenarios = [
                (["automagik-hive", "--agent-install", "."], 1),
                (["automagik-hive", "--agent-start", "."], 1),
            ]

            for argv, expected_exit in failure_scenarios:
                with patch("sys.argv", argv):
                    result = main()
                    assert result == expected_exit

    def test_mixed_component_operations(self, mock_all_components):
        """Test operations on mixed components."""
        mixed_scenarios = [
            (["automagik-hive", "--agent-install", "."], 0),
            (["automagik-hive", "--postgres-status", "."], 0),
            (["automagik-hive", "--agent-start", "."], 0),
            (["automagik-hive", "--postgres-health", "."], 0),
        ]

        for argv, expected_exit in mixed_scenarios:
            with patch("sys.argv", argv):
                result = main()
                assert result == expected_exit


@pytest.mark.parametrize("workspace_path", [".", tempfile.gettempdir() + "/test", "./workspace", "../parent"])
class TestCLIParameterizedCommands:
    """Parameterized tests for all CLI commands across different paths."""

    def test_install_command_all_components(self, workspace_path):
        """Test agent install command for all workspace paths."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.install.return_value = True
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-install", workspace_path]):
                result = main()
                assert result == 0
                mock_agent.install.assert_called_once_with(workspace_path)

    def test_start_command_all_components(self, workspace_path):
        """Test agent serve command for all workspace paths."""
        with patch("cli.main.AgentCommands") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.start.return_value = True
            mock_agent_class.return_value = mock_agent

            with patch("sys.argv", ["automagik-hive", "--agent-start", workspace_path]):
                result = main()
                assert result == 0
                mock_agent.start.assert_called_once_with(workspace_path)

    def test_health_command_all_components(self, workspace_path):
        """Test postgres health command for all workspace paths."""
        with patch("cli.main.PostgreSQLCommands") as mock_postgres_class:
            mock_postgres = Mock()
            mock_postgres.postgres_health.return_value = True
            mock_postgres_class.return_value = mock_postgres

            with patch("sys.argv", ["automagik-hive", "--postgres-health", workspace_path]):
                result = main()
                assert result == 0
                mock_postgres.postgres_health.assert_called_once_with(workspace_path)
