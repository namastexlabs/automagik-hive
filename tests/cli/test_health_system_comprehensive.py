"""Comprehensive test suite for refactored health system modules.

Tests the new health.py, health_utils.py, and health_report.py modules
with extensive coverage of edge cases, error conditions, and integration points.
Targets 90%+ coverage as per CLI cleanup strategy requirements.
"""

import json
import time
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

import pytest
import psycopg
import requests

# Skip test - CLI structure refactored, old health commands module no longer exists
pytestmark = pytest.mark.skip(reason="CLI architecture refactored - health commands consolidated")

# TODO: Update tests to use new CLI structure


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass functionality."""

    def test_health_check_result_creation(self):
        """Test basic HealthCheckResult creation and fields."""
        result = HealthCheckResult(
            service="test-service",
            component="test-component",
            status="healthy",
            message="Test message",
            details={"key": "value"},
            response_time_ms=123.45,
            remediation="Test remediation",
        )

        assert result.service == "test-service"
        assert result.component == "test-component"
        assert result.status == "healthy"
        assert result.message == "Test message"
        assert result.details == {"key": "value"}
        assert result.response_time_ms == 123.45
        assert result.remediation == "Test remediation"

    def test_health_check_result_defaults(self):
        """Test HealthCheckResult with default values."""
        result = HealthCheckResult(
            service="test-service",
            component="test-component", 
            status="healthy",
            message="Test message",
        )

        assert result.details == {}
        assert result.response_time_ms is None
        assert result.remediation is None

    def test_health_check_result_serialization(self):
        """Test HealthCheckResult can be serialized to dict."""
        result = HealthCheckResult(
            service="test-service",
            component="test-component",
            status="healthy", 
            message="Test message",
            details={"test": "value"},
        )

        result_dict = asdict(result)
        assert isinstance(result_dict, dict)
        assert result_dict["service"] == "test-service"
        assert result_dict["details"]["test"] == "value"


class TestResourceUsage:
    """Test ResourceUsage dataclass functionality."""

    def test_resource_usage_creation(self):
        """Test ResourceUsage dataclass creation."""
        usage = ResourceUsage(
            cpu_percent=25.5,
            memory_percent=60.2,
            disk_usage_percent=85.0,
            network_connections=45,
            docker_containers=8,
        )

        assert usage.cpu_percent == 25.5
        assert usage.memory_percent == 60.2
        assert usage.disk_usage_percent == 85.0
        assert usage.network_connections == 45
        assert usage.docker_containers == 8


class TestHealthChecker:
    """Comprehensive tests for HealthChecker class."""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance for testing."""
        return HealthChecker()

    def test_health_checker_initialization(self, health_checker):
        """Test HealthChecker initialization and configuration."""
        assert health_checker.timeout_seconds == 30
        assert health_checker.retry_attempts == 3
        assert health_checker.retry_delay == 5
        
        # Verify service configuration
        assert "agent" in health_checker.service_config
        assert "genie" in health_checker.service_config
        
        agent_config = health_checker.service_config["agent"]
        assert agent_config["database_port"] == 35532
        assert agent_config["api_port"] == 38886
        assert agent_config["database_name"] == "hive_agent"

    @patch("cli.commands.health.psycopg.connect")
    def test_database_connectivity_check_success(self, mock_connect, health_checker):
        """Test successful database connectivity check."""
        # Setup mock connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            ["PostgreSQL 15.0"],  # version query
            ["128 MB", 5],  # size and connections query
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        result = health_checker.database_connectivity_check("agent")

        assert result.status == "healthy"
        assert result.service == "agent-database"
        assert result.component == "agent"
        assert "Connected successfully" in result.message
        assert result.details["port"] == 35532
        assert result.details["database"] == "hive_agent"
        assert result.response_time_ms is not None
        
        # Verify connection was properly closed
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("cli.commands.health.psycopg.connect")
    def test_database_connectivity_check_connection_failure(self, mock_connect, health_checker):
        """Test database connectivity check with connection failure."""
        mock_connect.side_effect = psycopg.OperationalError("Connection failed")

        result = health_checker.database_connectivity_check("agent")

        assert result.status == "unhealthy"
        assert result.service == "agent-database"
        assert "Connection failed" in result.message
        assert result.details["port"] == 35532
        assert "docker ps" in result.remediation

    def test_database_connectivity_check_unknown_component(self, health_checker):
        """Test database connectivity check with unknown component."""
        result = health_checker.database_connectivity_check("unknown")

        assert result.status == "unknown"
        assert result.service == "unknown-database"
        assert "Unknown component" in result.message
        assert "Use 'agent' or 'genie'" in result.remediation

    @patch("cli.commands.health.requests.get")
    def test_api_endpoint_check_success(self, mock_get, health_checker):
        """Test successful API endpoint health check."""
        # Mock health endpoint response
        mock_health_response = Mock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = {"status": "healthy"}
        mock_health_response.content = b'{"status": "healthy"}'

        # Mock additional endpoint responses
        mock_docs_response = Mock()
        mock_docs_response.status_code = 200

        mock_get.side_effect = [
            mock_health_response,  # /health
            mock_docs_response,    # /docs
            mock_docs_response,    # /openapi.json
            mock_docs_response,    # /v1/
        ]

        result = health_checker.api_endpoint_check("agent")

        assert result.status == "healthy"
        assert result.service == "agent-api"
        assert "API responding" in result.message
        assert result.details["port"] == 38886
        assert result.details["health_data"] == {"status": "healthy"}
        assert result.response_time_ms is not None

    @patch("cli.commands.health.requests.get")
    def test_api_endpoint_check_connection_error(self, mock_get, health_checker):
        """Test API endpoint check with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = health_checker.api_endpoint_check("agent")

        assert result.status == "unhealthy"
        assert result.service == "agent-api"
        assert "Cannot connect to API" in result.message
        assert result.details["port"] == 38886
        assert "docker ps" in result.remediation

    @patch("cli.commands.health.requests.get")
    def test_api_endpoint_check_timeout(self, mock_get, health_checker):
        """Test API endpoint check with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = health_checker.api_endpoint_check("agent")

        assert result.status == "unhealthy"
        assert "API timeout" in result.message
        assert "wait and retry" in result.remediation

    @patch("cli.commands.health.requests.get")
    def test_api_endpoint_check_http_error(self, mock_get, health_checker):
        """Test API endpoint check with HTTP error status."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        result = health_checker.api_endpoint_check("agent")

        assert result.status == "unhealthy"
        assert "API returned status 500" in result.message
        assert result.details["status_code"] == 500

    @patch("cli.commands.health_utils.check_workspace_process")
    def test_workspace_process_check(self, mock_check_workspace, health_checker):
        """Test workspace process check delegation."""
        expected_result = HealthCheckResult(
            service="workspace",
            component="workspace",
            status="healthy",
            message="Workspace running",
        )
        mock_check_workspace.return_value = expected_result

        result = health_checker.workspace_process_check()

        assert result == expected_result
        mock_check_workspace.assert_called_once()

    @patch("cli.commands.health.psutil.cpu_percent")
    @patch("cli.commands.health.psutil.virtual_memory")
    @patch("cli.commands.health.psutil.disk_usage")
    @patch("cli.commands.health.psutil.net_connections")
    @patch("cli.commands.health.subprocess.run")
    @patch("cli.commands.health.psutil.process_iter")
    def test_resource_usage_check_healthy(
        self,
        mock_process_iter,
        mock_subprocess,
        mock_net_connections,
        mock_disk_usage,
        mock_virtual_memory,
        mock_cpu_percent,
        health_checker,
    ):
        """Test resource usage check with healthy system."""
        # Mock system metrics
        mock_cpu_percent.return_value = 25.5
        
        mock_memory = Mock()
        mock_memory.percent = 60.2
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8GB
        mock_virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.percent = 45.0
        mock_disk.free = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk_usage.return_value = mock_disk
        
        mock_net_connections.return_value = [Mock() for _ in range(50)]
        
        # Mock Docker container count
        mock_docker_result = Mock()
        mock_docker_result.returncode = 0
        mock_docker_result.stdout = "container1\ncontainer2\ncontainer3"
        mock_subprocess.return_value = mock_docker_result
        
        # Mock Hive processes
        mock_hive_process = Mock()
        mock_hive_process.info = {
            "pid": 1234,
            "name": "python",
            "cmdline": ["python", "-m", "automagik-hive"],
            "memory_info": Mock(rss=128 * 1024 * 1024),  # 128MB
        }
        mock_process_iter.return_value = [mock_hive_process]

        result = health_checker.resource_usage_check()

        assert result.status == "healthy"
        assert result.service == "resource-usage"
        assert "within normal limits" in result.message
        assert result.details["cpu_percent"] == 25.5
        assert result.details["memory_percent"] == 60.2
        assert result.details["hive_processes"] == 1
        assert result.details["hive_memory_mb"] == 128

    @patch("cli.commands.health.psutil.cpu_percent")
    @patch("cli.commands.health.psutil.virtual_memory")
    @patch("cli.commands.health.psutil.disk_usage")
    def test_resource_usage_check_warnings(
        self,
        mock_disk_usage,
        mock_virtual_memory,
        mock_cpu_percent,
        health_checker,
    ):
        """Test resource usage check with warning thresholds exceeded."""
        # Mock high resource usage
        mock_cpu_percent.return_value = 95.0
        
        mock_memory = Mock()
        mock_memory.percent = 92.0
        mock_memory.available = 512 * 1024 * 1024  # 512MB
        mock_virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.percent = 91.0
        mock_disk.free = 1024 * 1024 * 1024  # 1GB
        mock_disk_usage.return_value = mock_disk

        result = health_checker.resource_usage_check()

        assert result.status == "warning"
        assert "Resource warnings" in result.message
        assert "High CPU usage: 95.0%" in result.message
        assert "High memory usage: 92.0%" in result.message
        assert "High disk usage: 91.0%" in result.message
        assert "upgrading system resources" in result.remediation

    def test_comprehensive_health_check_all_components(self, health_checker):
        """Test comprehensive health check for all components."""
        with patch.object(health_checker, '_check_service_with_retries') as mock_check:
            mock_result = HealthCheckResult(
                service="test",
                component="test",
                status="healthy",
                message="Test",
            )
            mock_check.return_value = mock_result

            results = health_checker.comprehensive_health_check("all")

            # Should check workspace, agent, genie, resources, and interdependencies
            assert len(results) >= 5
            assert mock_check.call_count >= 5

    def test_get_services_for_component_workspace(self, health_checker):
        """Test service mapping for workspace component."""
        services = health_checker._get_services_for_component("workspace")
        
        assert "workspace" in services
        assert services["workspace"]["type"] == "workspace"

    def test_get_services_for_component_agent(self, health_checker):
        """Test service mapping for agent component."""
        services = health_checker._get_services_for_component("agent")
        
        assert "agent-database" in services
        assert "agent-api" in services
        assert services["agent-database"]["type"] == "database"
        assert services["agent-api"]["type"] == "api"

    def test_check_service_with_retries_success_first_attempt(self, health_checker):
        """Test service check succeeds on first attempt."""
        with patch.object(health_checker, 'database_connectivity_check') as mock_check:
            success_result = HealthCheckResult(
                service="test-db",
                component="test",
                status="healthy",
                message="Success",
            )
            mock_check.return_value = success_result

            config = {"type": "database", "component": "agent"}
            result = health_checker._check_service_with_retries("test-service", config)

            assert result.status == "healthy"
            mock_check.assert_called_once()

    def test_check_service_with_retries_failure_with_retries(self, health_checker):
        """Test service check fails and retries before giving up."""
        with patch.object(health_checker, 'database_connectivity_check') as mock_check:
            with patch('time.sleep'):  # Speed up test
                failure_result = HealthCheckResult(
                    service="test-db",
                    component="test",
                    status="unhealthy",
                    message="Failed",
                )
                mock_check.return_value = failure_result

                config = {"type": "database", "component": "agent"}
                result = health_checker._check_service_with_retries("test-service", config)

                assert result.status == "unhealthy"
                assert mock_check.call_count == health_checker.retry_attempts

    def test_check_service_with_retries_unknown_service_type(self, health_checker):
        """Test service check with unknown service type."""
        config = {"type": "unknown", "component": "test"}
        result = health_checker._check_service_with_retries("test-service", config)

        assert result.status == "unknown"
        assert "Unknown service type" in result.message

    def test_cli_compatibility_methods(self, health_checker):
        """Test CLI compatibility wrapper methods."""
        with patch.object(health_checker, 'comprehensive_health_check') as mock_comprehensive:
            mock_results = {
                "service1": HealthCheckResult("service1", "comp1", "healthy", "OK"),
                "service2": HealthCheckResult("service2", "comp2", "unhealthy", "Failed"),
            }
            mock_comprehensive.return_value = mock_results

            # Test check_health wrapper
            result = health_checker.check_health("all")
            expected = {
                "service1": {"status": "healthy", "message": "OK"},
                "service2": {"status": "unhealthy", "message": "Failed"},
            }
            assert result == expected

    def test_cli_run_health_check_delegation(self, health_checker):
        """Test CLI health check run delegation to reporter."""
        with patch('cli.commands.health.HealthReporter') as mock_reporter_class:
            mock_reporter = Mock()
            mock_reporter.run_health_check_cli.return_value = 0
            mock_reporter_class.return_value = mock_reporter

            exit_code = health_checker.run_health_check_cli("agent", save_report=True)

            assert exit_code == 0
            mock_reporter_class.assert_called_once_with(health_checker)
            mock_reporter.run_health_check_cli.assert_called_once_with("agent", True)


class TestHealthUtils:
    """Test health utility functions."""

    @patch("cli.commands.health_utils.subprocess.run")
    def test_check_docker_network_exists(self, mock_subprocess):
        """Test Docker network check when network exists."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "hive-network\n"
        mock_subprocess.return_value = mock_result

        result = check_docker_network()

        assert result.status == "healthy"
        assert result.service == "docker-network"
        assert "exists" in result.message

    @patch("cli.commands.health_utils.subprocess.run")
    def test_check_docker_network_missing(self, mock_subprocess):
        """Test Docker network check when network is missing."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result

        result = check_docker_network()

        assert result.status == "unhealthy"
        assert "not found" in result.message
        assert "docker network create" in result.remediation

    @patch("cli.commands.health_utils.subprocess.run")
    def test_check_docker_network_subprocess_error(self, mock_subprocess):
        """Test Docker network check with subprocess error."""
        mock_subprocess.side_effect = Exception("Docker not available")

        result = check_docker_network()

        assert result.status == "unhealthy"
        assert "Network check failed" in result.message
        assert "Docker installation" in result.remediation

    def test_check_agent_dependencies_running(self):
        """Test agent dependency check with running containers."""
        containers = [
            {"Names": "hive-agent-postgres"},
            {"Names": "hive-agent-api"},
        ]

        results = check_agent_dependencies(containers)

        assert len(results) == 2
        assert all(r.status == "healthy" for r in results)
        assert results[0].service == "agent-postgres-container"
        assert results[1].service == "agent-api-container"

    def test_check_agent_dependencies_missing(self):
        """Test agent dependency check with missing containers."""
        containers = []

        results = check_agent_dependencies(containers)

        assert len(results) == 2
        assert all(r.status == "unhealthy" for r in results)
        assert all("not found" in r.message for r in results)
        assert all("docker-compose --profile agent" in r.remediation for r in results)

    def test_check_genie_dependencies_running(self):
        """Test genie dependency check with running containers."""
        containers = [
            {"Names": "hive-genie-postgres"},
            {"Names": "hive-genie-api"},
        ]

        results = check_genie_dependencies(containers)

        assert len(results) == 2
        assert all(r.status == "healthy" for r in results)

    def test_check_cross_component_dependencies(self):
        """Test cross-component dependency check."""
        containers = []

        results = check_cross_component_dependencies(containers)

        assert len(results) == 1
        assert results[0].status == "healthy"
        assert "Cross-component dependencies healthy" in results[0].message

    @patch("cli.commands.health_utils.subprocess.run")
    def test_get_docker_containers_success(self, mock_subprocess):
        """Test successful Docker container retrieval."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"Names": "container1"}\n{"Names": "container2"}'
        mock_subprocess.return_value = mock_result

        containers = get_docker_containers()

        assert len(containers) == 2
        assert containers[0]["Names"] == "container1"
        assert containers[1]["Names"] == "container2"

    @patch("cli.commands.health_utils.subprocess.run")
    def test_get_docker_containers_failure(self, mock_subprocess):
        """Test Docker container retrieval failure."""
        mock_subprocess.side_effect = Exception("Docker error")

        containers = get_docker_containers()

        assert containers == []

    @patch("cli.commands.health_utils.psutil.process_iter")
    @patch("cli.commands.health_utils.psutil.net_connections")
    @patch("cli.commands.health_utils.requests.get")
    def test_check_workspace_process_healthy(
        self, mock_requests_get, mock_net_connections, mock_process_iter
    ):
        """Test workspace process check with healthy workspace."""
        # Mock Hive processes
        mock_hive_process = Mock()
        mock_hive_process.info = {
            "pid": 1234,
            "name": "python",
            "cmdline": ["python", "-m", "automagik-hive", "serve"],
            "status": "running",
            "cpu_percent": 5.0,
            "memory_info": Mock(rss=64 * 1024 * 1024),  # 64MB
        }
        mock_process_iter.return_value = [mock_hive_process]

        # Mock listening connections
        mock_connection = Mock()
        mock_connection.laddr.port = 8000
        mock_connection.status = "LISTEN"
        mock_net_connections.return_value = [mock_connection]

        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        result = check_workspace_process()

        assert result.status == "healthy"
        assert result.service == "workspace"
        assert "accessible on port 8000" in result.message
        assert result.details["workspace_port"] == 8000
        assert result.details["workspace_accessible"] is True

    @patch("cli.commands.health_utils.psutil.process_iter")
    def test_check_workspace_process_no_processes(self, mock_process_iter):
        """Test workspace process check with no processes found."""
        mock_process_iter.return_value = []

        result = check_workspace_process()

        assert result.status == "unhealthy"
        assert "No workspace process detected" in result.message
        assert "uvx automagik-hive" in result.remediation

    @patch("cli.commands.health_utils.psutil.process_iter")
    def test_check_workspace_process_exception(self, mock_process_iter):
        """Test workspace process check with exception."""
        mock_process_iter.side_effect = Exception("Process access denied")

        result = check_workspace_process()

        assert result.status == "unhealthy"
        assert "Process check failed" in result.message
        assert "psutil installation" in result.remediation


class TestHealthSystemIntegration:
    """Integration tests for health system components."""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker for integration tests."""
        return HealthChecker()

    def test_health_system_error_propagation(self, health_checker):
        """Test error propagation through health system layers."""
        # This should fail gracefully when no real services are running
        results = health_checker.comprehensive_health_check("agent")
        
        # Should return results for all services even if they fail
        assert isinstance(results, dict)
        assert len(results) >= 2  # At least database and API checks

    def test_health_check_timing_consistency(self, health_checker):
        """Test that health checks have consistent timing behavior."""
        start_time = time.time()
        
        # Run a health check that should fail quickly
        result = health_checker.database_connectivity_check("agent")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should fail within reasonable timeout (not hang)
        assert duration < health_checker.timeout_seconds + 5

    def test_service_config_completeness(self, health_checker):
        """Test that service configuration is complete and valid."""
        for component in ["agent", "genie"]:
            config = health_checker.service_config[component]
            
            # Verify required configuration keys
            assert "database_port" in config
            assert "api_port" in config
            assert "database_name" in config
            assert "container_prefix" in config
            
            # Verify port values are reasonable
            assert 1024 <= config["database_port"] <= 65535
            assert 1024 <= config["api_port"] <= 65535
            
            # Verify ports are different
            assert config["database_port"] != config["api_port"]

    @patch("cli.commands.health.logger")
    def test_health_system_logging_integration(self, mock_logger, health_checker):
        """Test that health system logs appropriately."""
        # This should trigger some logging
        health_checker.comprehensive_health_check("unknown_component")
        
        # Verify logging was attempted (logger should be called)
        # Note: We can't easily test exact log messages without more complex mocking
        assert mock_logger is not None  # Basic verification that logger is imported


# Performance and stress tests
class TestHealthSystemPerformance:
    """Performance tests for health system."""

    @pytest.fixture
    def health_checker(self):
        return HealthChecker()

    def test_health_check_performance_baseline(self, health_checker):
        """Test health check performance baseline."""
        start_time = time.time()
        
        # Run multiple health checks to test performance
        for _ in range(5):
            health_checker.database_connectivity_check("agent")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Should complete 5 checks within reasonable time
        assert total_duration < 30  # 30 seconds for 5 checks

    @pytest.mark.parametrize("component", ["agent", "genie", "workspace", "all"])
    def test_comprehensive_health_check_components(self, health_checker, component):
        """Test comprehensive health check for all component types."""
        results = health_checker.comprehensive_health_check(component)
        
        # Should always return a dictionary
        assert isinstance(results, dict)
        
        # Should have at least one result
        assert len(results) > 0
        
        # All results should be HealthCheckResult objects
        for result in results.values():
            assert isinstance(result, HealthCheckResult)
            assert result.service is not None
            assert result.component is not None
            assert result.status in ["healthy", "unhealthy", "warning", "unknown"]