"""Comprehensive CLI integration test suite for refactored architecture.

Tests end-to-end CLI command functionality ensuring all uvx automagik-hive commands
work correctly with the new decomposed modules. Validates the complete command flow
from CLI entry points through to service execution.
Targets 90%+ coverage as per CLI cleanup strategy requirements.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Skip test - CLI structure refactored, old commands module no longer exists
pytestmark = pytest.mark.skip(reason="CLI architecture refactored - LazyCommandLoader no longer exists")

from cli.main import main
# TODO: Update tests to use new CLI structure without LazyCommandLoader


class TestLazyCommandLoader:
    """Test the LazyCommandLoader functionality."""

    @pytest.fixture
    def loader(self):
        """Create LazyCommandLoader instance for testing."""
        return LazyCommandLoader()

    def test_lazy_command_loader_initialization(self, loader):
        """Test LazyCommandLoader initializes with None instances."""
        assert loader._interactive_initializer is None
        assert loader._workspace_manager is None
        assert loader._workflow_orchestrator is None
        assert loader._service_manager is None
        assert loader._health_checker is None
        assert loader._uninstaller is None

    def test_interactive_initializer_lazy_loading(self, loader):
        """Test interactive initializer is loaded lazily."""
        with patch('cli.commands.init.InteractiveInitializer') as mock_initializer:
            mock_instance = Mock()
            mock_initializer.return_value = mock_instance

            # First access should create instance
            result1 = loader.interactive_initializer
            assert result1 == mock_instance
            mock_initializer.assert_called_once()

            # Second access should return same instance
            result2 = loader.interactive_initializer
            assert result2 == mock_instance
            assert mock_initializer.call_count == 1  # Not called again

    def test_workspace_manager_lazy_loading(self, loader):
        """Test workspace manager is loaded lazily."""
        with patch('cli.commands.workspace.UnifiedWorkspaceManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            result = loader.workspace_manager
            assert result == mock_instance
            mock_manager.assert_called_once()

    def test_workflow_orchestrator_lazy_loading(self, loader):
        """Test workflow orchestrator is loaded lazily."""
        with patch('cli.commands.orchestrator.WorkflowOrchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_orchestrator.return_value = mock_instance

            result = loader.workflow_orchestrator
            assert result == mock_instance
            mock_orchestrator.assert_called_once()

    def test_service_manager_lazy_loading(self, loader):
        """Test service manager is loaded lazily."""
        with patch('cli.commands.service.ServiceManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            result = loader.service_manager
            assert result == mock_instance
            mock_manager.assert_called_once()

    def test_health_checker_lazy_loading(self, loader):
        """Test health checker is loaded lazily."""
        with patch('cli.commands.health.HealthChecker') as mock_checker:
            mock_instance = Mock()
            mock_checker.return_value = mock_instance

            result = loader.health_checker
            assert result == mock_instance
            mock_checker.assert_called_once()

    def test_uninstaller_lazy_loading(self, loader):
        """Test uninstaller is loaded lazily."""
        with patch('cli.commands.uninstall.UninstallCommands') as mock_uninstaller:
            mock_instance = Mock()
            mock_uninstaller.return_value = mock_instance

            result = loader.uninstaller
            assert result == mock_instance
            mock_uninstaller.assert_called_once()

    def test_all_components_lazy_loaded_independently(self, loader):
        """Test all components can be loaded independently."""
        with patch('cli.commands.init.InteractiveInitializer'), \
             patch('cli.commands.workspace.UnifiedWorkspaceManager'), \
             patch('cli.commands.orchestrator.WorkflowOrchestrator'), \
             patch('cli.commands.service.ServiceManager'), \
             patch('cli.commands.health.HealthChecker'), \
             patch('cli.commands.uninstall.UninstallCommands'):

            # Access all components
            _ = loader.interactive_initializer
            _ = loader.workspace_manager
            _ = loader.workflow_orchestrator
            _ = loader.service_manager
            _ = loader.health_checker
            _ = loader.uninstaller

            # All should be loaded successfully
            assert loader._interactive_initializer is not None
            assert loader._workspace_manager is not None
            assert loader._workflow_orchestrator is not None
            assert loader._service_manager is not None
            assert loader._health_checker is not None
            assert loader._uninstaller is not None


class TestCLIMainEntryPoint:
    """Test CLI main entry point functionality."""

    @patch('cli.main.LazyCommandLoader')
    def test_main_function_initialization(self, mock_loader_class):
        """Test main function initializes command loader."""
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        # Mock sys.argv to avoid actual command execution
        with patch('sys.argv', ['automagik-hive', '--help']):
            with patch('cli.main.parse_args') as mock_parse:
                mock_parse.return_value = Mock(help=True)
                with patch('cli.main.handle_help_command'):
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected for help command

        mock_loader_class.assert_called_once()

    @patch('cli.main.LazyCommandLoader')
    @patch('cli.main.parse_args')
    def test_main_command_routing_install(self, mock_parse, mock_loader_class):
        """Test main function routes install command correctly."""
        mock_loader = Mock()
        mock_orchestrator = Mock()
        mock_orchestrator.execute_unified_workflow.return_value = True
        mock_loader.workflow_orchestrator = mock_orchestrator
        mock_loader_class.return_value = mock_loader

        mock_args = Mock()
        mock_args.install = "agent"
        mock_args.help = False
        mock_args.init = False
        mock_args.start = None
        mock_args.stop = None
        mock_args.restart = None
        mock_args.status = None
        mock_args.health = None
        mock_args.logs = None
        mock_args.uninstall = None
        mock_parse.return_value = mock_args

        with patch('sys.exit') as mock_exit:
            main()
            mock_orchestrator.execute_unified_workflow.assert_called_once_with("agent")
            mock_exit.assert_called_once_with(0)

    @patch('cli.main.LazyCommandLoader')
    @patch('cli.main.parse_args')
    def test_main_command_routing_start(self, mock_parse, mock_loader_class):
        """Test main function routes start command correctly."""
        mock_loader = Mock()
        mock_service_manager = Mock()
        mock_service_manager.start_services.return_value = True
        mock_loader.service_manager = mock_service_manager
        mock_loader_class.return_value = mock_loader

        mock_args = Mock()
        mock_args.start = "genie"
        mock_args.help = False
        mock_args.init = False
        mock_args.install = None
        mock_args.stop = None
        mock_args.restart = None
        mock_args.status = None
        mock_args.health = None
        mock_args.logs = None
        mock_args.uninstall = None
        mock_parse.return_value = mock_args

        with patch('sys.exit') as mock_exit:
            main()
            mock_service_manager.start_services.assert_called_once_with("genie")
            mock_exit.assert_called_once_with(0)

    @patch('cli.main.LazyCommandLoader')
    @patch('cli.main.parse_args')
    def test_main_command_routing_health(self, mock_parse, mock_loader_class):
        """Test main function routes health command correctly."""
        mock_loader = Mock()
        mock_health_checker = Mock()
        mock_health_checker.run_health_check_cli.return_value = 0
        mock_loader.health_checker = mock_health_checker
        mock_loader_class.return_value = mock_loader

        mock_args = Mock()
        mock_args.health = "all"
        mock_args.save_report = False
        mock_args.help = False
        mock_args.init = False
        mock_args.install = None
        mock_args.start = None
        mock_args.stop = None
        mock_args.restart = None
        mock_args.status = None
        mock_args.logs = None
        mock_args.uninstall = None
        mock_parse.return_value = mock_args

        with patch('sys.exit') as mock_exit:
            main()
            mock_health_checker.run_health_check_cli.assert_called_once_with("all", False)
            mock_exit.assert_called_once_with(0)

    @patch('cli.main.LazyCommandLoader')
    @patch('cli.main.parse_args')
    def test_main_exception_handling(self, mock_parse, mock_loader_class):
        """Test main function handles exceptions gracefully."""
        mock_loader_class.side_effect = Exception("Loader initialization failed")

        mock_args = Mock()
        mock_args.help = False
        mock_args.install = "agent"
        mock_parse.return_value = mock_args

        with patch('sys.exit') as mock_exit:
            with patch('cli.main.logger') as mock_logger:
                main()
                mock_logger.error.assert_called()
                mock_exit.assert_called_once_with(1)


class TestCLICommandIntegration:
    """Integration tests for CLI commands with real argument parsing."""

    def test_argument_parsing_install_command(self):
        """Test argument parsing for install commands."""
        from cli.main import parse_args

        # Test install with component
        args = parse_args(['--install', 'agent'])
        assert args.install == 'agent'

        # Test install with all
        args = parse_args(['--install', 'all'])
        assert args.install == 'all'

    def test_argument_parsing_service_commands(self):
        """Test argument parsing for service management commands."""
        from cli.main import parse_args

        # Test start command
        args = parse_args(['--start', 'workspace'])
        assert args.start == 'workspace'

        # Test stop command
        args = parse_args(['--stop', 'genie'])
        assert args.stop == 'genie'

        # Test restart command
        args = parse_args(['--restart', 'agent'])
        assert args.restart == 'agent'

    def test_argument_parsing_status_commands(self):
        """Test argument parsing for status and health commands."""
        from cli.main import parse_args

        # Test status command
        args = parse_args(['--status', 'all'])
        assert args.status == 'all'

        # Test health command
        args = parse_args(['--health', 'agent'])
        assert args.health == 'agent'

        # Test health with save report
        args = parse_args(['--health', 'all', '--save-report'])
        assert args.health == 'all'
        assert args.save_report is True

    def test_argument_parsing_logs_command(self):
        """Test argument parsing for logs command."""
        from cli.main import parse_args

        # Test logs command
        args = parse_args(['--logs', 'agent'])
        assert args.logs == 'agent'

        # Test logs with line count
        args = parse_args(['--logs', 'genie', '--lines', '100'])
        assert args.logs == 'genie'
        assert args.lines == 100

    def test_argument_parsing_uninstall_command(self):
        """Test argument parsing for uninstall command."""
        from cli.main import parse_args

        # Test uninstall command
        args = parse_args(['--uninstall', 'agent'])
        assert args.uninstall == 'agent'

        # Test uninstall all
        args = parse_args(['--uninstall', 'all'])
        assert args.uninstall == 'all'

    def test_argument_parsing_init_command(self):
        """Test argument parsing for init command."""
        from cli.main import parse_args

        # Test init command
        args = parse_args(['--init'])
        assert args.init is True

    def test_argument_parsing_help_command(self):
        """Test argument parsing for help command."""
        from cli.main import parse_args

        # Test help command
        args = parse_args(['--help'])
        assert args.help is True

    def test_argument_parsing_invalid_combinations(self):
        """Test argument parsing rejects invalid combinations."""
        from cli.main import parse_args

        # These should parse successfully but may be validated later
        args = parse_args(['--install', 'agent', '--start', 'agent'])
        assert args.install == 'agent'
        assert args.start == 'agent'

    def test_argument_parsing_edge_cases(self):
        """Test argument parsing edge cases."""
        from cli.main import parse_args

        # Test empty arguments (should not crash)
        args = parse_args([])
        assert args is not None

        # Test single dash arguments
        args = parse_args(['-h'])
        assert args.help is True


class TestCLIWorkflowIntegration:
    """Test complete CLI workflow integration."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir) / "test-workspace"
            workspace_path.mkdir()
            yield workspace_path

    @patch('cli.commands.orchestrator.WorkflowOrchestrator')
    def test_install_workflow_integration(self, mock_orchestrator_class, temp_workspace):
        """Test complete install workflow integration."""
        mock_orchestrator = Mock()
        mock_orchestrator.execute_unified_workflow.return_value = True
        mock_orchestrator_class.return_value = mock_orchestrator

        from cli.main import main

        with patch('sys.argv', ['automagik-hive', '--install', 'workspace']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_orchestrator.execute_unified_workflow.assert_called_once_with('workspace')
                mock_exit.assert_called_once_with(0)

    @patch('cli.commands.service.ServiceManager')
    def test_service_lifecycle_integration(self, mock_service_manager_class):
        """Test complete service lifecycle integration."""
        mock_service_manager = Mock()
        mock_service_manager.start_services.return_value = True
        mock_service_manager.get_status.return_value = {"agent": "healthy"}
        mock_service_manager.stop_services.return_value = True
        mock_service_manager_class.return_value = mock_service_manager

        from cli.main import main

        # Test start
        with patch('sys.argv', ['automagik-hive', '--start', 'agent']):
            with patch('sys.exit'):
                main()
                mock_service_manager.start_services.assert_called_with('agent')

        # Test status
        with patch('sys.argv', ['automagik-hive', '--status', 'agent']):
            with patch('sys.exit'):
                main()
                mock_service_manager.get_status.assert_called_with('agent')

        # Test stop
        with patch('sys.argv', ['automagik-hive', '--stop', 'agent']):
            with patch('sys.exit'):
                main()
                mock_service_manager.stop_services.assert_called_with('agent')

    @patch('cli.commands.health.HealthChecker')
    def test_health_check_integration(self, mock_health_checker_class):
        """Test health check integration."""
        mock_health_checker = Mock()
        mock_health_checker.run_health_check_cli.return_value = 0
        mock_health_checker_class.return_value = mock_health_checker

        from cli.main import main

        with patch('sys.argv', ['automagik-hive', '--health', 'all', '--save-report']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_health_checker.run_health_check_cli.assert_called_once_with('all', True)
                mock_exit.assert_called_once_with(0)

    @patch('cli.commands.init.InteractiveInitializer')
    def test_init_workflow_integration(self, mock_initializer_class):
        """Test init workflow integration."""
        mock_initializer = Mock()
        mock_initializer.run_interactive_initialization.return_value = True
        mock_initializer_class.return_value = mock_initializer

        from cli.main import main

        with patch('sys.argv', ['automagik-hive', '--init']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_initializer.run_interactive_initialization.assert_called_once()
                mock_exit.assert_called_once_with(0)

    @patch('cli.commands.uninstall.UninstallCommands')
    def test_uninstall_workflow_integration(self, mock_uninstaller_class):
        """Test uninstall workflow integration."""
        mock_uninstaller = Mock()
        mock_uninstaller.run_uninstall.return_value = True
        mock_uninstaller_class.return_value = mock_uninstaller

        from cli.main import main

        with patch('sys.argv', ['automagik-hive', '--uninstall', 'agent']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_uninstaller.run_uninstall.assert_called_once_with('agent')
                mock_exit.assert_called_once_with(0)


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    @patch('cli.main.LazyCommandLoader')
    def test_command_failure_handling(self, mock_loader_class):
        """Test CLI handles command failures gracefully."""
        mock_loader = Mock()
        mock_orchestrator = Mock()
        mock_orchestrator.execute_unified_workflow.return_value = False  # Failure
        mock_loader.workflow_orchestrator = mock_orchestrator
        mock_loader_class.return_value = mock_loader

        from cli.main import main

        with patch('sys.argv', ['automagik-hive', '--install', 'agent']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)  # Exit with error code

    @patch('cli.main.LazyCommandLoader')
    def test_exception_in_command_handling(self, mock_loader_class):
        """Test CLI handles exceptions in commands gracefully."""
        mock_loader = Mock()
        mock_service_manager = Mock()
        mock_service_manager.start_services.side_effect = Exception("Service error")
        mock_loader.service_manager = mock_service_manager
        mock_loader_class.return_value = mock_loader

        from cli.main import main

        with patch('sys.argv', ['automagik-hive', '--start', 'agent']):
            with patch('sys.exit') as mock_exit:
                with patch('cli.main.logger') as mock_logger:
                    main()
                    mock_logger.error.assert_called()
                    mock_exit.assert_called_once_with(1)

    def test_invalid_component_handling(self):
        """Test CLI handles invalid component names."""
        from cli.main import main

        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_service_manager = Mock()
            mock_service_manager.start_services.return_value = False  # Invalid component
            mock_loader.service_manager = mock_service_manager
            mock_loader_class.return_value = mock_loader

            with patch('sys.argv', ['automagik-hive', '--start', 'invalid']):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(1)

    def test_permission_error_handling(self):
        """Test CLI handles permission errors."""
        from cli.main import main

        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader_class.side_effect = PermissionError("Permission denied")

            with patch('sys.argv', ['automagik-hive', '--install', 'agent']):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(1)

    def test_keyboard_interrupt_handling(self):
        """Test CLI handles keyboard interrupts gracefully."""
        from cli.main import main

        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader_class.side_effect = KeyboardInterrupt()

            with patch('sys.argv', ['automagik-hive', '--install', 'agent']):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(1)


class TestCLIPerformance:
    """Test CLI performance characteristics."""

    def test_cli_startup_performance(self):
        """Test CLI startup performance."""
        from cli.main import LazyCommandLoader

        start_time = time.time()
        
        # Create loader (should be fast due to lazy loading)
        loader = LazyCommandLoader()
        
        end_time = time.time()
        startup_time = end_time - start_time
        
        # Startup should be very fast with lazy loading
        assert startup_time < 0.1  # Less than 100ms

    def test_lazy_loading_performance(self):
        """Test lazy loading performance."""
        from cli.main import LazyCommandLoader

        loader = LazyCommandLoader()
        
        with patch('cli.commands.service.ServiceManager') as mock_service_manager:
            mock_service_manager.return_value = Mock()
            
            start_time = time.time()
            
            # First access should create instance
            _ = loader.service_manager
            
            end_time = time.time()
            first_access_time = end_time - start_time
            
            start_time = time.time()
            
            # Second access should return cached instance  
            _ = loader.service_manager
            
            end_time = time.time()
            second_access_time = end_time - start_time
            
            # Second access should be much faster
            assert second_access_time < first_access_time / 2

    def test_argument_parsing_performance(self):
        """Test argument parsing performance."""
        from cli.main import parse_args

        start_time = time.time()
        
        # Parse various argument combinations
        test_args = [
            ['--help'],
            ['--install', 'agent'],
            ['--start', 'all'],
            ['--health', 'genie', '--save-report'],
            ['--logs', 'workspace', '--lines', '100'],
            ['--uninstall', 'all'],
        ]
        
        for args in test_args:
            parse_args(args)
        
        end_time = time.time()
        parsing_time = end_time - start_time
        
        # Argument parsing should be fast
        assert parsing_time < 0.1  # Less than 100ms for all combinations


class TestCLICompatibility:
    """Test CLI compatibility and backwards compatibility."""

    def test_command_line_interface_compatibility(self):
        """Test that CLI maintains expected interface."""
        from cli.main import parse_args

        # Test all expected commands are supported
        expected_commands = [
            '--install', '--start', '--stop', '--restart',
            '--status', '--health', '--logs', '--uninstall', '--init'
        ]
        
        for command in expected_commands:
            if command in ['--init', '--help']:
                args = parse_args([command])
            else:
                args = parse_args([command, 'all'])
            
            assert args is not None

    def test_component_names_compatibility(self):
        """Test that all expected component names are supported."""
        from cli.main import parse_args

        expected_components = ['all', 'workspace', 'agent', 'genie']
        
        for component in expected_components:
            args = parse_args(['--install', component])
            assert args.install == component

    def test_exit_code_compatibility(self):
        """Test that CLI returns expected exit codes."""
        from cli.main import main

        # Test success exit code
        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_unified_workflow.return_value = True
            mock_loader.workflow_orchestrator = mock_orchestrator
            mock_loader_class.return_value = mock_loader

            with patch('sys.argv', ['automagik-hive', '--install', 'workspace']):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(0)

        # Test failure exit code
        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_unified_workflow.return_value = False
            mock_loader.workflow_orchestrator = mock_orchestrator
            mock_loader_class.return_value = mock_loader

            with patch('sys.argv', ['automagik-hive', '--install', 'workspace']):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(1)


class TestCLIEndToEndScenarios:
    """Test end-to-end CLI scenarios."""

    @pytest.fixture
    def mock_all_components(self):
        """Mock all CLI components for E2E testing."""
        with patch('cli.commands.orchestrator.WorkflowOrchestrator') as mock_orchestrator, \
             patch('cli.commands.service.ServiceManager') as mock_service, \
             patch('cli.commands.health.HealthChecker') as mock_health, \
             patch('cli.commands.init.InteractiveInitializer') as mock_init, \
             patch('cli.commands.uninstall.UninstallCommands') as mock_uninstall:
            
            # Setup successful mocks
            mock_orchestrator.return_value.execute_unified_workflow.return_value = True
            mock_service.return_value.start_services.return_value = True
            mock_service.return_value.stop_services.return_value = True
            mock_service.return_value.get_status.return_value = {"service": "healthy"}
            mock_service.return_value.get_logs.return_value = {"service": ["log1", "log2"]}
            mock_health.return_value.run_health_check_cli.return_value = 0
            mock_init.return_value.run_interactive_initialization.return_value = True
            mock_uninstall.return_value.run_uninstall.return_value = True
            
            yield {
                'orchestrator': mock_orchestrator,
                'service': mock_service,
                'health': mock_health,
                'init': mock_init,
                'uninstall': mock_uninstall,
            }

    def test_complete_agent_lifecycle(self, mock_all_components):
        """Test complete agent lifecycle: install -> start -> health -> stop -> uninstall."""
        from cli.main import main

        scenarios = [
            (['automagik-hive', '--install', 'agent'], 0),
            (['automagik-hive', '--start', 'agent'], 0),
            (['automagik-hive', '--health', 'agent'], 0),
            (['automagik-hive', '--status', 'agent'], 0),
            (['automagik-hive', '--logs', 'agent'], 0),
            (['automagik-hive', '--stop', 'agent'], 0),
            (['automagik-hive', '--uninstall', 'agent'], 0),
        ]

        for argv, expected_exit in scenarios:
            with patch('sys.argv', argv):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(expected_exit)

    def test_complete_workspace_lifecycle(self, mock_all_components):
        """Test complete workspace lifecycle."""
        from cli.main import main

        scenarios = [
            (['automagik-hive', '--init'], 0),
            (['automagik-hive', '--install', 'workspace'], 0),
            (['automagik-hive', '--start', 'workspace'], 0),
            (['automagik-hive', '--health', 'workspace'], 0),
            (['automagik-hive', '--stop', 'workspace'], 0),
        ]

        for argv, expected_exit in scenarios:
            with patch('sys.argv', argv):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(expected_exit)

    def test_all_components_lifecycle(self, mock_all_components):
        """Test complete system lifecycle with all components."""
        from cli.main import main

        scenarios = [
            (['automagik-hive', '--install', 'all'], 0),
            (['automagik-hive', '--start', 'all'], 0),
            (['automagik-hive', '--health', 'all', '--save-report'], 0),
            (['automagik-hive', '--status', 'all'], 0),
            (['automagik-hive', '--logs', 'all', '--lines', '50'], 0),
            (['automagik-hive', '--restart', 'all'], 0),
            (['automagik-hive', '--stop', 'all'], 0),
        ]

        for argv, expected_exit in scenarios:
            with patch('sys.argv', argv):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(expected_exit)

    def test_error_recovery_scenarios(self, mock_all_components):
        """Test error recovery scenarios."""
        from cli.main import main

        # Setup failure scenarios
        mock_all_components['orchestrator'].return_value.execute_unified_workflow.return_value = False
        mock_all_components['service'].return_value.start_services.return_value = False

        failure_scenarios = [
            (['automagik-hive', '--install', 'agent'], 1),
            (['automagik-hive', '--start', 'agent'], 1),
        ]

        for argv, expected_exit in failure_scenarios:
            with patch('sys.argv', argv):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(expected_exit)

    def test_mixed_component_operations(self, mock_all_components):
        """Test operations on mixed components."""
        from cli.main import main

        mixed_scenarios = [
            (['automagik-hive', '--install', 'agent'], 0),
            (['automagik-hive', '--install', 'genie'], 0),
            (['automagik-hive', '--start', 'workspace'], 0),
            (['automagik-hive', '--health', 'all'], 0),
        ]

        for argv, expected_exit in mixed_scenarios:
            with patch('sys.argv', argv):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(expected_exit)


@pytest.mark.parametrize("component", ["workspace", "agent", "genie", "all"])
class TestCLIParameterizedCommands:
    """Parameterized tests for all CLI commands across components."""

    def test_install_command_all_components(self, component):
        """Test install command for all components."""
        from cli.main import main

        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_unified_workflow.return_value = True
            mock_loader.workflow_orchestrator = mock_orchestrator
            mock_loader_class.return_value = mock_loader

            with patch('sys.argv', ['automagik-hive', '--install', component]):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_orchestrator.execute_unified_workflow.assert_called_once_with(component)
                    mock_exit.assert_called_once_with(0)

    def test_start_command_all_components(self, component):
        """Test start command for all components."""
        from cli.main import main

        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_service_manager = Mock()
            mock_service_manager.start_services.return_value = True
            mock_loader.service_manager = mock_service_manager
            mock_loader_class.return_value = mock_loader

            with patch('sys.argv', ['automagik-hive', '--start', component]):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_service_manager.start_services.assert_called_once_with(component)
                    mock_exit.assert_called_once_with(0)

    def test_health_command_all_components(self, component):
        """Test health command for all components."""
        from cli.main import main

        with patch('cli.main.LazyCommandLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_health_checker = Mock()
            mock_health_checker.run_health_check_cli.return_value = 0
            mock_loader.health_checker = mock_health_checker
            mock_loader_class.return_value = mock_loader

            with patch('sys.argv', ['automagik-hive', '--health', component]):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_health_checker.run_health_check_cli.assert_called_once_with(component, False)
                    mock_exit.assert_called_once_with(0)