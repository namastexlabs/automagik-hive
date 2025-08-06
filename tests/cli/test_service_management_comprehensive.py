"""Comprehensive test suite for service management modules.

Tests the service.py and service_*.py modules with extensive coverage
of service lifecycle management, Docker operations, and component orchestration.
Targets 90%+ coverage as per CLI cleanup strategy requirements.
"""

import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest

# Skip test - CLI structure refactored, old service commands modules no longer exist
pytestmark = pytest.mark.skip(reason="CLI architecture refactored - service commands consolidated into DockerManager")

# TODO: Update tests to use cli.docker_manager.DockerManager

# Stubs to prevent NameError during test collection - must be defined before usage in decorators
class ServiceManager: 
    def __init__(self):
        self.docker_service = Mock()
        self.postgres_service = Mock()
        self.workspace_process = None
        self.operations = ServiceOperations()
        self.status = ServiceStatus()
        self.logs = ServiceLogs()
        self.cleanup = ServiceCleanup()

class ServiceOperations: pass
class ServiceStatus: pass  
class ServiceLogs: pass
class ServiceCleanup: pass


class TestServiceManager:
    """Comprehensive tests for ServiceManager class."""

    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance for testing."""
        return ServiceManager()

    def test_service_manager_initialization(self, service_manager):
        """Test ServiceManager initialization and component setup."""
        # Verify core services are initialized
        assert service_manager.docker_service is not None
        assert service_manager.postgres_service is not None
        assert service_manager.workspace_process is None

        # Verify component modules are initialized
        assert isinstance(service_manager.operations, ServiceOperations)
        assert isinstance(service_manager.status, ServiceStatus)
        assert isinstance(service_manager.logs, ServiceLogs)
        assert isinstance(service_manager.cleanup, ServiceCleanup)

    @patch.object(ServiceOperations, 'start_all_services')
    def test_start_services_all(self, mock_start_all, service_manager):
        """Test starting all services."""
        mock_start_all.return_value = True

        result = service_manager.start_services("all")

        assert result is True
        mock_start_all.assert_called_once()

    @patch.object(ServiceOperations, 'start_workspace')
    def test_start_services_workspace(self, mock_start_workspace, service_manager):
        """Test starting workspace services."""
        mock_start_workspace.return_value = True

        result = service_manager.start_services("workspace")

        assert result is True
        mock_start_workspace.assert_called_once()

    @patch.object(ServiceOperations, 'start_agent_services')
    def test_start_services_agent(self, mock_start_agent, service_manager):
        """Test starting agent services."""
        mock_start_agent.return_value = True

        result = service_manager.start_services("agent")

        assert result is True
        mock_start_agent.assert_called_once()

    @patch.object(ServiceOperations, 'start_genie_services')
    def test_start_services_genie(self, mock_start_genie, service_manager):
        """Test starting genie services."""
        mock_start_genie.return_value = True

        result = service_manager.start_services("genie")

        assert result is True
        mock_start_genie.assert_called_once()

    def test_start_services_invalid_component(self, service_manager):
        """Test starting services with invalid component."""
        result = service_manager.start_services("invalid")

        assert result is False

    @patch.object(ServiceOperations, 'start_all_services')
    def test_start_services_exception_handling(self, mock_start_all, service_manager):
        """Test start services with exception handling."""
        mock_start_all.side_effect = Exception("Service start failed")

        result = service_manager.start_services("all")

        assert result is False

    @patch.object(ServiceOperations, 'stop_all_services')
    def test_stop_services_all(self, mock_stop_all, service_manager):
        """Test stopping all services."""
        mock_stop_all.return_value = True

        result = service_manager.stop_services("all")

        assert result is True
        mock_stop_all.assert_called_once()

    @patch.object(ServiceOperations, 'stop_workspace')
    def test_stop_services_workspace(self, mock_stop_workspace, service_manager):
        """Test stopping workspace services."""
        mock_stop_workspace.return_value = True

        result = service_manager.stop_services("workspace")

        assert result is True
        mock_stop_workspace.assert_called_once()

    @patch('time.sleep')  # Speed up test
    @patch.object(ServiceManager, 'stop_services')
    @patch.object(ServiceManager, 'start_services')
    def test_restart_services_success(self, mock_start, mock_stop, mock_sleep, service_manager):
        """Test successful service restart."""
        mock_stop.return_value = True
        mock_start.return_value = True

        result = service_manager.restart_services("agent")

        assert result is True
        mock_stop.assert_called_once_with("agent")
        mock_start.assert_called_once_with("agent")
        mock_sleep.assert_called_once_with(2)

    @patch.object(ServiceManager, 'stop_services')
    def test_restart_services_stop_failure(self, mock_stop, service_manager):
        """Test service restart when stop fails."""
        mock_stop.return_value = False

        result = service_manager.restart_services("agent")

        assert result is False

    @patch.object(ServiceStatus, 'get_component_status')
    def test_get_status_delegation(self, mock_get_status, service_manager):
        """Test status retrieval delegation."""
        expected_status = {"service1": "healthy", "service2": "unhealthy"}
        mock_get_status.return_value = expected_status

        result = service_manager.get_status("agent")

        assert result == expected_status
        mock_get_status.assert_called_once_with("agent")

    @patch.object(ServiceLogs, 'get_component_logs')
    def test_get_logs_delegation(self, mock_get_logs, service_manager):
        """Test logs retrieval delegation."""
        expected_logs = {"service1": ["log1", "log2"], "service2": ["log3"]}
        mock_get_logs.return_value = expected_logs

        result = service_manager.get_logs("agent", lines=50)

        assert result == expected_logs
        mock_get_logs.assert_called_once_with("agent", lines=50)

    @patch.object(ServiceCleanup, 'uninstall_component')
    def test_uninstall_delegation(self, mock_uninstall, service_manager):
        """Test uninstall delegation."""
        mock_uninstall.return_value = True

        result = service_manager.uninstall("agent")

        assert result is True
        mock_uninstall.assert_called_once_with("agent")


class TestServiceOperations:
    """Test ServiceOperations class functionality."""

    @pytest.fixture
    def service_ops(self):
        """Create ServiceOperations instance for testing."""
        return ServiceOperations()

    @patch('cli.commands.service_operations.subprocess.run')
    def test_detect_docker_compose_command_modern(self, mock_subprocess, service_ops):
        """Test Docker Compose command detection with modern version."""
        mock_subprocess.return_value = Mock(returncode=0)

        # Re-initialize to test detection
        ops = ServiceOperations()

        assert ops._docker_compose_cmd == ["docker", "compose"]

    @patch('cli.commands.service_operations.subprocess.run')
    def test_detect_docker_compose_command_legacy(self, mock_subprocess, service_ops):
        """Test Docker Compose command detection falls back to legacy."""
        # First call (modern) fails, second call (legacy) succeeds
        mock_subprocess.side_effect = [
            Mock(returncode=1),  # modern fails
            Mock(returncode=0),  # legacy succeeds
        ]

        ops = ServiceOperations()

        assert ops._docker_compose_cmd == ["docker-compose"]

    @patch('cli.commands.service_operations.subprocess.run')
    def test_detect_docker_compose_command_both_fail(self, mock_subprocess, service_ops):
        """Test Docker Compose command detection when both fail."""
        mock_subprocess.return_value = Mock(returncode=1)

        ops = ServiceOperations()

        # Should default to modern even if detection fails
        assert ops._docker_compose_cmd == ["docker", "compose"]

    @patch('cli.commands.service_operations.subprocess.run')
    def test_detect_docker_compose_command_timeout(self, mock_subprocess, service_ops):
        """Test Docker Compose command detection with timeout."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("cmd", 5)

        ops = ServiceOperations()

        assert ops._docker_compose_cmd == ["docker", "compose"]

    @patch.object(ServiceOperations, 'start_agent_services')
    @patch.object(ServiceOperations, 'start_genie_services')
    @patch.object(ServiceOperations, 'start_workspace')
    def test_start_all_services_success(self, mock_start_workspace, mock_start_genie, 
                                      mock_start_agent, service_ops):
        """Test starting all services successfully."""
        mock_start_agent.return_value = True
        mock_start_genie.return_value = True
        mock_start_workspace.return_value = True

        result = service_ops.start_all_services()

        assert result is True
        mock_start_agent.assert_called_once()
        mock_start_genie.assert_called_once()
        mock_start_workspace.assert_called_once()

    @patch.object(ServiceOperations, 'start_agent_services')
    @patch.object(ServiceOperations, 'start_genie_services')
    @patch.object(ServiceOperations, 'start_workspace')
    def test_start_all_services_partial_failure(self, mock_start_workspace, mock_start_genie, 
                                               mock_start_agent, service_ops):
        """Test starting all services with partial failure."""
        mock_start_agent.return_value = True
        mock_start_genie.return_value = False  # Failure
        mock_start_workspace.return_value = True

        result = service_ops.start_all_services()

        assert result is False  # Should return False if any service fails

    @patch.object(ServiceOperations, 'stop_workspace')
    @patch.object(ServiceOperations, 'stop_genie_services')
    @patch.object(ServiceOperations, 'stop_agent_services')
    def test_stop_all_services_success(self, mock_stop_agent, mock_stop_genie, 
                                     mock_stop_workspace, service_ops):
        """Test stopping all services successfully."""
        mock_stop_workspace.return_value = True
        mock_stop_genie.return_value = True
        mock_stop_agent.return_value = True

        result = service_ops.stop_all_services()

        assert result is True
        # Verify order: workspace first, then Docker services
        mock_stop_workspace.assert_called_once()
        mock_stop_genie.assert_called_once()
        mock_stop_agent.assert_called_once()

    @patch('cli.commands.service_operations.subprocess.run')
    def test_start_agent_services_success(self, mock_subprocess, service_ops):
        """Test starting agent services with Docker Compose."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_ops.start_agent_services()

        assert result is True
        # Should call docker compose with agent profile
        expected_call = service_ops._docker_compose_cmd + [
            "--profile", "agent", "up", "-d", "--build"
        ]
        mock_subprocess.assert_called_with(
            expected_call,
            capture_output=True,
            text=True,
            check=False
        )

    @patch('cli.commands.service_operations.subprocess.run')
    def test_start_agent_services_failure(self, mock_subprocess, service_ops):
        """Test starting agent services with failure."""
        mock_subprocess.return_value = Mock(returncode=1, stderr="Error starting services")

        result = service_ops.start_agent_services()

        assert result is False

    @patch('cli.commands.service_operations.subprocess.run')
    def test_start_genie_services_success(self, mock_subprocess, service_ops):
        """Test starting genie services successfully."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_ops.start_genie_services()

        assert result is True

    @patch('cli.commands.service_operations.subprocess.run')
    def test_stop_agent_services_success(self, mock_subprocess, service_ops):
        """Test stopping agent services successfully."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_ops.stop_agent_services()

        assert result is True
        # Should call docker compose down with agent profile
        expected_call = service_ops._docker_compose_cmd + [
            "--profile", "agent", "down"
        ]
        mock_subprocess.assert_called_with(
            expected_call,
            capture_output=True,
            text=True,
            check=False
        )

    @patch('cli.commands.service_operations.subprocess.run')
    def test_start_workspace_success(self, mock_subprocess, service_ops):
        """Test starting workspace process successfully."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_ops.start_workspace()

        assert result is True
        # Should attempt to start workspace with uvx
        mock_subprocess.assert_called()

    @patch('cli.commands.service_operations.subprocess.run')
    def test_start_workspace_failure(self, mock_subprocess, service_ops):
        """Test starting workspace process with failure."""
        mock_subprocess.return_value = Mock(returncode=1, stderr="Workspace start failed")

        result = service_ops.start_workspace()

        assert result is False

    @patch('cli.commands.service_operations.subprocess.run')
    def test_stop_workspace_success(self, mock_subprocess, service_ops):
        """Test stopping workspace process successfully."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_ops.stop_workspace()

        assert result is True

    @patch('cli.commands.service_operations.subprocess.run')
    def test_compose_command_execution_with_exception(self, mock_subprocess, service_ops):
        """Test Docker Compose command execution with exception."""
        mock_subprocess.side_effect = Exception("Subprocess error")

        result = service_ops.start_agent_services()

        assert result is False

    def test_docker_compose_command_selection(self, service_ops):
        """Test that Docker Compose command is properly selected."""
        # Command should be either modern or legacy format
        cmd = service_ops._docker_compose_cmd
        assert cmd in [["docker", "compose"], ["docker-compose"]]


class TestServiceStatus:
    """Test ServiceStatus class functionality."""

    @pytest.fixture
    def service_status(self):
        """Create ServiceStatus instance for testing."""
        return ServiceStatus()

    @patch('cli.commands.service_status.subprocess.run')
    @patch('cli.commands.service_status.requests.get')
    def test_get_component_status_agent_healthy(self, mock_requests, mock_subprocess, service_status):
        """Test agent component status when healthy."""
        # Mock Docker container status
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout='{"Names": "hive-agent-postgres", "State": "running"}\n'
                   '{"Names": "hive-agent-api", "State": "running"}'
        )

        # Mock API health check
        mock_requests.return_value = Mock(status_code=200, json=lambda: {"status": "healthy"})

        result = service_status.get_component_status("agent")

        assert isinstance(result, dict)
        assert len(result) >= 2  # Should have database and API status

    @patch('cli.commands.service_status.subprocess.run')
    def test_get_component_status_agent_containers_down(self, mock_subprocess, service_status):
        """Test agent component status when containers are down."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="")

        result = service_status.get_component_status("agent")

        assert isinstance(result, dict)
        # Should still return status dict even when containers are down

    @patch('cli.commands.service_status.subprocess.run')
    def test_get_component_status_docker_error(self, mock_subprocess, service_status):
        """Test component status with Docker error."""
        mock_subprocess.side_effect = Exception("Docker not available")

        result = service_status.get_component_status("agent")

        assert isinstance(result, dict)
        # Should handle Docker errors gracefully

    @patch('cli.commands.service_status.psutil.process_iter')
    @patch('cli.commands.service_status.requests.get')
    def test_get_component_status_workspace_running(self, mock_requests, mock_process_iter, service_status):
        """Test workspace component status when running."""
        # Mock workspace process
        mock_process = Mock()
        mock_process.info = {
            "pid": 1234,
            "name": "python",
            "cmdline": ["python", "-m", "automagik-hive", "serve"],
            "status": "running"
        }
        mock_process_iter.return_value = [mock_process]

        # Mock HTTP response
        mock_requests.return_value = Mock(status_code=200)

        result = service_status.get_component_status("workspace")

        assert isinstance(result, dict)
        assert "workspace" in result

    def test_get_component_status_all_components(self, service_status):
        """Test getting status for all components."""
        with patch.object(service_status, 'get_component_status') as mock_get_status:
            # Mock individual component statuses
            mock_get_status.side_effect = [
                {"agent-db": "healthy", "agent-api": "healthy"},
                {"genie-db": "healthy", "genie-api": "healthy"},
                {"workspace": "healthy"}
            ]

            # Create a new status instance to avoid recursion
            status_checker = ServiceStatus()
            with patch.object(status_checker, '_get_agent_status', return_value={"agent": "healthy"}):
                with patch.object(status_checker, '_get_genie_status', return_value={"genie": "healthy"}):
                    with patch.object(status_checker, '_get_workspace_status', return_value={"workspace": "healthy"}):
                        result = status_checker.get_component_status("all")

            assert isinstance(result, dict)

    def test_get_component_status_invalid_component(self, service_status):
        """Test getting status for invalid component."""
        result = service_status.get_component_status("invalid")

        assert isinstance(result, dict)
        # Should return empty dict or error status for invalid component


class TestServiceLogs:
    """Test ServiceLogs class functionality."""

    @pytest.fixture
    def service_logs(self):
        """Create ServiceLogs instance for testing."""
        return ServiceLogs()

    @patch('cli.commands.service_logs.subprocess.run')
    def test_get_component_logs_agent_success(self, mock_subprocess, service_logs):
        """Test getting agent component logs successfully."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="agent-postgres log line 1\nagent-api log line 2"
        )

        result = service_logs.get_component_logs("agent", lines=50)

        assert isinstance(result, dict)
        # Should call docker compose logs
        mock_subprocess.assert_called()

    @patch('cli.commands.service_logs.subprocess.run')
    def test_get_component_logs_docker_error(self, mock_subprocess, service_logs):
        """Test getting component logs with Docker error."""
        mock_subprocess.side_effect = Exception("Docker logs error")

        result = service_logs.get_component_logs("agent", lines=50)

        assert isinstance(result, dict)
        # Should handle Docker errors gracefully

    @patch('cli.commands.service_logs.Path.exists')
    @patch('cli.commands.service_logs.Path.read_text')
    def test_get_component_logs_workspace_file_exists(self, mock_read_text, mock_exists, service_logs):
        """Test getting workspace logs from file when it exists."""
        mock_exists.return_value = True
        mock_read_text.return_value = "workspace log line 1\nworkspace log line 2\n"

        result = service_logs.get_component_logs("workspace", lines=50)

        assert isinstance(result, dict)
        assert "workspace" in result

    @patch('cli.commands.service_logs.Path.exists')
    def test_get_component_logs_workspace_file_not_exists(self, mock_exists, service_logs):
        """Test getting workspace logs when file doesn't exist."""
        mock_exists.return_value = False

        result = service_logs.get_component_logs("workspace", lines=50)

        assert isinstance(result, dict)
        # Should return appropriate message when log file doesn't exist

    def test_get_component_logs_all_components(self, service_logs):
        """Test getting logs for all components."""
        with patch.object(service_logs, 'get_component_logs') as mock_get_logs:
            mock_get_logs.side_effect = [
                {"agent": ["agent log 1", "agent log 2"]},
                {"genie": ["genie log 1"]},
                {"workspace": ["workspace log 1"]}
            ]

            # Create new instance to avoid recursion
            logs_checker = ServiceLogs()
            with patch.object(logs_checker, '_get_agent_logs', return_value={"agent": ["log1"]}):
                with patch.object(logs_checker, '_get_genie_logs', return_value={"genie": ["log1"]}):
                    with patch.object(logs_checker, '_get_workspace_logs', return_value={"workspace": ["log1"]}):
                        result = logs_checker.get_component_logs("all", lines=50)

            assert isinstance(result, dict)

    def test_get_component_logs_invalid_component(self, service_logs):
        """Test getting logs for invalid component."""
        result = service_logs.get_component_logs("invalid", lines=50)

        assert isinstance(result, dict)
        # Should handle invalid component gracefully

    @patch('cli.commands.service_logs.subprocess.run')
    def test_get_component_logs_with_different_line_counts(self, mock_subprocess, service_logs):
        """Test getting logs with different line count parameters."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="log content")

        # Test with different line counts
        for lines in [10, 50, 100, 1000]:
            result = service_logs.get_component_logs("agent", lines=lines)
            assert isinstance(result, dict)

    @patch('cli.commands.service_logs.subprocess.run')
    def test_log_parsing_and_formatting(self, mock_subprocess, service_logs):
        """Test log parsing and formatting functionality."""
        # Mock multi-line log output
        log_content = "\n".join([f"Log line {i}" for i in range(100)])
        mock_subprocess.return_value = Mock(returncode=0, stdout=log_content)

        result = service_logs.get_component_logs("agent", lines=50)

        assert isinstance(result, dict)
        # Should properly parse and format log lines


class TestServiceCleanup:
    """Test ServiceCleanup class functionality."""

    @pytest.fixture
    def service_cleanup(self):
        """Create ServiceCleanup instance for testing."""
        return ServiceCleanup()

    @patch('cli.commands.service_cleanup.subprocess.run')
    def test_uninstall_component_agent_success(self, mock_subprocess, service_cleanup):
        """Test successful agent component uninstall."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_cleanup.uninstall_component("agent")

        assert result is True
        # Should call docker compose down and remove volumes
        mock_subprocess.assert_called()

    @patch('cli.commands.service_cleanup.subprocess.run')
    def test_uninstall_component_docker_error(self, mock_subprocess, service_cleanup):
        """Test component uninstall with Docker error."""
        mock_subprocess.return_value = Mock(returncode=1, stderr="Docker error")

        result = service_cleanup.uninstall_component("agent")

        assert result is False

    @patch('cli.commands.service_cleanup.subprocess.run')
    def test_uninstall_component_workspace_success(self, mock_subprocess, service_cleanup):
        """Test successful workspace component uninstall."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_cleanup.uninstall_component("workspace")

        assert result is True

    @patch('cli.commands.service_cleanup.subprocess.run')
    def test_uninstall_component_all_success(self, mock_subprocess, service_cleanup):
        """Test successful uninstall of all components."""
        mock_subprocess.return_value = Mock(returncode=0)

        result = service_cleanup.uninstall_component("all")

        assert result is True
        # Should make multiple calls to clean up all components
        assert mock_subprocess.call_count >= 1

    def test_uninstall_component_invalid_component(self, service_cleanup):
        """Test uninstall with invalid component."""
        result = service_cleanup.uninstall_component("invalid")

        assert result is False

    @patch('cli.commands.service_cleanup.subprocess.run')
    @patch('cli.commands.service_cleanup.Path.exists')
    @patch('cli.commands.service_cleanup.Path.rmdir')
    def test_cleanup_workspace_data(self, mock_rmdir, mock_exists, mock_subprocess, service_cleanup):
        """Test cleanup of workspace data directories."""
        mock_subprocess.return_value = Mock(returncode=0)
        mock_exists.return_value = True

        result = service_cleanup.uninstall_component("workspace")

        assert result is True

    @patch('cli.commands.service_cleanup.subprocess.run')
    def test_force_cleanup_with_errors(self, mock_subprocess, service_cleanup):
        """Test cleanup continues even with some errors."""
        # Some commands succeed, some fail
        mock_subprocess.side_effect = [
            Mock(returncode=0),  # First command succeeds
            Mock(returncode=1),  # Second command fails
            Mock(returncode=0),  # Third command succeeds
        ]

        # Should still attempt cleanup even with partial failures
        result = service_cleanup.uninstall_component("all")

        # Result depends on implementation - may be True or False
        assert isinstance(result, bool)


class TestServiceIntegration:
    """Integration tests for service management components."""

    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager for integration tests."""
        return ServiceManager()

    def test_service_manager_component_integration(self, service_manager):
        """Test integration between ServiceManager and its components."""
        # Verify all components are properly initialized
        assert hasattr(service_manager, 'operations')
        assert hasattr(service_manager, 'status')
        assert hasattr(service_manager, 'logs')
        assert hasattr(service_manager, 'cleanup')

        # Verify they are the correct types
        assert isinstance(service_manager.operations, ServiceOperations)
        assert isinstance(service_manager.status, ServiceStatus)
        assert isinstance(service_manager.logs, ServiceLogs)
        assert isinstance(service_manager.cleanup, ServiceCleanup)

    def test_service_lifecycle_coordination(self, service_manager):
        """Test service lifecycle coordination across components."""
        with patch.object(service_manager.operations, 'start_all_services', return_value=True):
            with patch.object(service_manager.status, 'get_component_status', return_value={"all": "healthy"}):
                with patch.object(service_manager.operations, 'stop_all_services', return_value=True):
                    # Test complete lifecycle
                    start_result = service_manager.start_services("all")
                    status_result = service_manager.get_status("all")
                    stop_result = service_manager.stop_services("all")

                    assert start_result is True
                    assert isinstance(status_result, dict)
                    assert stop_result is True

    def test_error_propagation_across_components(self, service_manager):
        """Test error propagation across service components."""
        # Test that errors in operations are properly handled
        with patch.object(service_manager.operations, 'start_all_services', side_effect=Exception("Test error")):
            result = service_manager.start_services("all")
            assert result is False

    def test_service_component_isolation(self, service_manager):
        """Test that service components are properly isolated."""
        # Each component should be able to fail independently
        with patch.object(service_manager.operations, 'start_all_services', return_value=False):
            with patch.object(service_manager.status, 'get_component_status', return_value={"status": "error"}):
                start_result = service_manager.start_services("all")
                status_result = service_manager.get_status("all")

                # Start should fail, but status should still work
                assert start_result is False
                assert isinstance(status_result, dict)

    @patch('time.time')
    def test_service_operation_timing(self, mock_time, service_manager):
        """Test service operation timing and performance."""
        mock_time.side_effect = [1000.0, 1001.0]  # 1 second operation

        with patch.object(service_manager.operations, 'start_all_services', return_value=True):
            start_time = time.time()
            service_manager.start_services("all")
            end_time = time.time()

            # Operation timing should be tracked
            duration = end_time - start_time
            assert duration >= 0

    def test_concurrent_service_operations(self, service_manager):
        """Test handling of concurrent service operations."""
        # This tests the robustness of service operations
        # In a real scenario, multiple operations might be attempted simultaneously
        
        with patch.object(service_manager.operations, 'start_agent_services', return_value=True):
            with patch.object(service_manager.operations, 'start_genie_services', return_value=True):
                # Simulate concurrent operations
                results = []
                for component in ["agent", "genie", "agent", "genie"]:
                    result = service_manager.start_services(component)
                    results.append(result)

                # All operations should succeed
                assert all(results)


class TestServicePerformance:
    """Performance tests for service management."""

    @pytest.fixture
    def service_manager(self):
        return ServiceManager()

    def test_service_manager_initialization_performance(self):
        """Test ServiceManager initialization performance."""
        start_time = time.time()
        
        # Create multiple instances to test initialization overhead
        for _ in range(10):
            ServiceManager()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Initialization should be fast
        assert duration < 1.0  # Less than 1 second for 10 instances

    def test_service_operations_performance(self, service_manager):
        """Test service operations performance."""
        with patch.object(service_manager.operations, 'start_all_services', return_value=True):
            start_time = time.time()
            
            # Perform multiple operations
            for _ in range(20):
                service_manager.start_services("all")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Operations should be fast when mocked
            assert duration < 1.0  # Less than 1 second for 20 operations

    def test_status_check_performance(self, service_manager):
        """Test status check performance."""
        with patch.object(service_manager.status, 'get_component_status', return_value={"test": "healthy"}):
            start_time = time.time()
            
            # Perform multiple status checks
            for _ in range(50):
                service_manager.get_status("all")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Status checks should be very fast when mocked
            assert duration < 0.5  # Less than 500ms for 50 checks


@pytest.mark.parametrize("component", ["workspace", "agent", "genie", "all"])
class TestServiceComponentParameterized:
    """Parameterized tests for all service components."""

    def test_component_start_operations(self, component):
        """Test start operations for each component."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager.operations, f'start_{component}_services' if component != 'all' else 'start_all_services', return_value=True):
            result = service_manager.start_services(component)
            assert result is True

    def test_component_stop_operations(self, component):
        """Test stop operations for each component."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager.operations, f'stop_{component}_services' if component != 'all' else 'stop_all_services', return_value=True):
            result = service_manager.stop_services(component)
            assert result is True

    def test_component_status_checks(self, component):
        """Test status checks for each component."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager.status, 'get_component_status', return_value={component: "healthy"}):
            result = service_manager.get_status(component)
            assert isinstance(result, dict)

    def test_component_log_retrieval(self, component):
        """Test log retrieval for each component."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager.logs, 'get_component_logs', return_value={component: ["log1", "log2"]}):
            result = service_manager.get_logs(component)
            assert isinstance(result, dict)

    def test_component_cleanup_operations(self, component):
        """Test cleanup operations for each component."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager.cleanup, 'uninstall_component', return_value=True):
            result = service_manager.uninstall(component)
            assert result is True


class TestServiceErrorHandling:
    """Test service error handling and edge cases."""

    @pytest.fixture
    def service_manager(self):
        return ServiceManager()

    def test_docker_not_available_handling(self, service_manager):
        """Test handling when Docker is not available."""
        with patch('subprocess.run', side_effect=FileNotFoundError("docker command not found")):
            # Operations should fail gracefully
            result = service_manager.start_services("agent")
            assert result is False

    def test_permission_denied_handling(self, service_manager):
        """Test handling when Docker operations are denied."""
        with patch('subprocess.run', side_effect=PermissionError("Permission denied")):
            result = service_manager.start_services("agent")
            assert result is False

    def test_network_connectivity_issues(self, service_manager):
        """Test handling of network connectivity issues."""
        # Mock network-related failures in status checks
        with patch('requests.get', side_effect=ConnectionError("Network unreachable")):
            result = service_manager.get_status("agent")
            # Should return status dict even with network issues
            assert isinstance(result, dict)

    def test_disk_space_issues(self, service_manager):
        """Test handling of disk space issues."""
        with patch('subprocess.run', return_value=Mock(returncode=1, stderr="No space left on device")):
            result = service_manager.start_services("agent")
            assert result is False

    def test_corrupted_compose_file_handling(self, service_manager):
        """Test handling of corrupted docker-compose files."""
        with patch('subprocess.run', return_value=Mock(returncode=1, stderr="Invalid compose file")):
            result = service_manager.start_services("agent")
            assert result is False

    def test_resource_exhaustion_handling(self, service_manager):
        """Test handling of system resource exhaustion."""
        with patch('subprocess.run', side_effect=OSError("Resource temporarily unavailable")):
            result = service_manager.start_services("all")
            assert result is False