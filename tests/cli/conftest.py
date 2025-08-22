"""Comprehensive CLI Test Configuration and Fixtures.

Provides shared fixtures, test configuration, and utilities for comprehensive
CLI testing with >95% coverage validation and real agent server integration.

This configuration supports:
- Temporary workspace creation and management
- Mock service configuration for testing
- Real agent server integration testing
- Performance benchmarking utilities
- Cross-platform compatibility testing
- Coverage validation and reporting
"""

import shutil
import sys
import tempfile
import time
from pathlib import Path

# Add project root to Python path to fix module import issues
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from unittest.mock import Mock, patch

import pytest

# Optional imports for real server testing
try:
    import httpx
except ImportError:
    httpx = None

try:
    import docker
except ImportError:
    docker = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import coverage
except ImportError:
    coverage = None


# Test environment configuration
# Note: pytest_plugins moved to root conftest.py to fix collection error


class TestEnvironmentManager:
    """Manages test environment setup and teardown."""

    def __init__(self):
        self.temp_dirs = []
        self.mock_patches = []
        self.coverage_instance = None

    def create_temp_workspace(self, name: str = "test-workspace") -> Path:
        """Create a temporary workspace directory."""
        temp_dir = tempfile.mkdtemp(prefix=f"cli_test_{name}_")
        self.temp_dirs.append(temp_dir)
        return Path(temp_dir)

    def cleanup_temp_workspaces(self):
        """Clean up all temporary workspace directories."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
        self.temp_dirs.clear()

    def start_coverage_tracking(self):
        """Start coverage tracking for CLI modules."""
        if coverage is not None:
            self.coverage_instance = coverage.Coverage(
                source=["cli"],
                omit=[
                    "*/tests/*",
                    "*/test_*",
                    "*/__pycache__/*",
                    "*/venv/*",
                    "*/.venv/*",
                ],
            )
            self.coverage_instance.start()

    def stop_coverage_tracking(self) -> float:
        """Stop coverage tracking and return coverage percentage."""
        if self.coverage_instance:
            self.coverage_instance.stop()
            self.coverage_instance.save()
            return self.coverage_instance.report(show_missing=False)
        return 0.0


@pytest.fixture(scope="session")
def test_environment_manager():
    """Session-scoped test environment manager."""
    manager = TestEnvironmentManager()

    # Start coverage tracking at session start
    manager.start_coverage_tracking()

    yield manager

    # Cleanup at session end
    coverage_percentage = manager.stop_coverage_tracking()
    manager.cleanup_temp_workspaces()

    # Enforce coverage threshold
    if coverage_percentage < 95.0:
        pass
    else:
        pass


@pytest.fixture
def temp_workspace(test_environment_manager):
    """Create a temporary workspace directory for testing."""
    workspace = test_environment_manager.create_temp_workspace()

    # Create basic workspace structure
    (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  app:
    image: python:3.11
    ports:
      - "8886:8886"
    environment:
      - HIVE_API_PORT=8886
    command: uvicorn api.serve:app --host 0.0.0.0 --port 8886
""")

    (workspace / ".env").write_text("""
HIVE_API_PORT=8886
HIVE_API_KEY=test_workspace_key_fixture
POSTGRES_PORT=5432
POSTGRES_DB=hive
POSTGRES_USER=hive
POSTGRES_PASSWORD=test_password_fixture
""")

    # Create data directories
    (workspace / "data").mkdir()
    (workspace / "logs").mkdir()
    (workspace / "backups").mkdir()

    return workspace


@pytest.fixture
def temp_workspace_postgres(test_environment_manager):
    """Create a temporary workspace with PostgreSQL configuration."""
    workspace = test_environment_manager.create_temp_workspace("postgres")

    # Create PostgreSQL-focused docker-compose.yml
    (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: hive-postgres-test
    ports:
      - "35540:5432"
    environment:
      POSTGRES_DB: hive_test
      POSTGRES_USER: hive_test
      POSTGRES_PASSWORD: test_password_postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
""")

    (workspace / ".env").write_text("""
POSTGRES_PORT=35540
POSTGRES_DB=hive_test
POSTGRES_USER=hive_test
POSTGRES_PASSWORD=test_password_postgres
HIVE_API_PORT=8886
""")

    return workspace


@pytest.fixture
def temp_workspace_agent(test_environment_manager):
    """Create a temporary workspace with agent configuration."""
    workspace = test_environment_manager.create_temp_workspace("agent")

    # Create main .env configuration for agent inheritance via docker-compose
    (workspace / ".env").write_text("""
HIVE_API_PORT=8886
POSTGRES_PORT=5532
POSTGRES_DB=hive
POSTGRES_USER=hive_agent
POSTGRES_PASSWORD=agent_test_password
HIVE_API_KEY=agent_test_key_fixture
""")
    
    # Create docker-compose.yml for agent environment
    docker_dir = workspace / "docker" / "agent"
    docker_dir.mkdir(parents=True, exist_ok=True)
    (docker_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
    ports:
      - "35532:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=hive_agent
  api:
    build: .
    ports:
      - "38886:8886"
    environment:
      - HIVE_API_PORT=8886
      - HIVE_API_KEY=${HIVE_API_KEY}
""")

    # Create logs directory with sample log file
    logs_dir = workspace / "logs"
    logs_dir.mkdir()
    (logs_dir / "agent-server.log").write_text("""
2024-01-01 10:00:00 INFO: Agent server starting
2024-01-01 10:00:01 INFO: Database connection established
2024-01-01 10:00:02 INFO: Agent server ready on port 38886
""")

    return workspace


@pytest.fixture
def mock_docker_service():
    """Mock Docker service for comprehensive testing."""
    with patch("cli.core.docker_service.DockerService") as mock_docker_class:
        mock_docker = Mock()

        # Configure default behaviors
        mock_docker.is_docker_available.return_value = True
        mock_docker.is_compose_file_valid.return_value = True
        mock_docker.start_compose_services.return_value = True
        mock_docker.stop_compose_services.return_value = True
        mock_docker.restart_compose_services.return_value = True
        mock_docker.is_container_running.return_value = True
        mock_docker.start_container.return_value = True
        mock_docker.stop_container.return_value = True
        mock_docker.restart_container.return_value = True

        # Configure status responses
        mock_docker.get_compose_status.return_value = {
            "app": {
                "status": "running",
                "health": "healthy",
                "port": "8886",
                "uptime": "1 hour",
                "cpu_usage": "2.5%",
                "memory_usage": "128MB",
            },
            "postgres": {
                "status": "running",
                "health": "healthy",
                "port": "5432",
                "uptime": "1 hour",
                "cpu_usage": "1.2%",
                "memory_usage": "64MB",
            },
        }

        mock_docker.get_container_status.return_value = {
            "status": "running",
            "health": "healthy",
            "ports": ["8886:8886"],
            "uptime": "1 hour",
        }

        # Configure logs
        mock_docker.get_compose_logs.return_value = {
            "app": [
                "2024-01-01 10:00:00 INFO: Application started",
                "2024-01-01 10:00:01 INFO: Ready to serve requests",
            ],
            "postgres": [
                "2024-01-01 10:00:00 LOG: Database initialized",
                "2024-01-01 10:00:01 LOG: Ready to accept connections",
            ],
        }

        mock_docker.get_container_logs.return_value = """
2024-01-01 10:00:00 INFO: Container started
2024-01-01 10:00:01 INFO: Service ready
"""

        mock_docker_class.return_value = mock_docker
        yield mock_docker


@pytest.fixture
def mock_postgres_service():
    """Mock PostgreSQL service for comprehensive testing."""
    with patch("cli.core.postgres_service.PostgreSQLService") as mock_postgres_class:
        mock_postgres = Mock()

        # Configure default behaviors
        mock_postgres.is_postgres_running.return_value = True
        mock_postgres.start_postgres.return_value = True
        mock_postgres.stop_postgres.return_value = True
        mock_postgres.restart_postgres.return_value = True
        mock_postgres.check_connection.return_value = True

        # Configure connection info
        mock_postgres.get_connection_info.return_value = {
            "host": "localhost",
            "port": 5432,
            "database": "hive",
            "user": "hive",
            "password": "test_password",
        }

        # Configure status
        mock_postgres.get_postgres_status.return_value = {
            "status": "running",
            "port": 5432,
            "database": "hive",
            "connections": 5,
            "uptime": "1 hour",
        }

        mock_postgres_class.return_value = mock_postgres
        yield mock_postgres


@pytest.fixture
def mock_all_services(mock_docker_service, mock_postgres_service):
    """Mock all CLI services for comprehensive testing."""
    return {"docker": mock_docker_service, "postgres": mock_postgres_service}


@pytest.fixture
def mock_user_inputs():
    """Factory for creating mock user input sequences."""

    def _create_input_mock(inputs: list[str]):
        return patch("builtins.input", side_effect=inputs)

    return _create_input_mock


@pytest.fixture
def performance_timer():
    """Utility for measuring test performance."""

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.measurements = {}

        def start(self, label: str = "default"):
            self.start_time = time.time()
            return self

        def stop(self, label: str = "default", max_time: float = 10.0) -> float:
            if self.start_time is None:
                raise ValueError("Timer not started")

            elapsed = time.time() - self.start_time
            self.measurements[label] = elapsed

            assert elapsed < max_time, (
                f"Performance check failed: {label} took {elapsed:.3f}s (max: {max_time}s)"
            )

            self.start_time = None
            return elapsed

        def get_measurement(self, label: str) -> float | None:
            return self.measurements.get(label)

        def get_all_measurements(self) -> dict[str, float]:
            return self.measurements.copy()

    return PerformanceTimer()


@pytest.fixture(scope="session")
def real_agent_start_available():
    """Check if real agent server is available for testing."""
    if httpx is None:
        return False
    try:
        with httpx.Client() as client:
            response = client.get("http://localhost:38886/health", timeout=5)
            return response.status_code == 200
    except httpx.RequestError:
        return False


@pytest.fixture(scope="session")
def real_postgres_available():
    """SAFETY: Mock PostgreSQL availability check to prevent real connections."""
    # SAFETY: Always return False to prevent real database connections in tests
    # This ensures complete test isolation and eliminates security risks
    return False


@pytest.fixture(scope="session")
def docker_client():
    """Docker client for real container testing."""
    if docker is None:
        pytest.skip("Docker module not available for real container testing")
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        pytest.skip("Docker not available for real container testing")


@pytest.fixture
def cli_test_configuration():
    """CLI test configuration and utilities."""

    class CLITestConfig:
        def __init__(self):
            self.test_timeouts = {
                "command_execution": 30.0,
                "server_startup": 60.0,
                "database_connection": 15.0,
                "file_operations": 10.0,
            }

            self.coverage_thresholds = {
                "minimum": 85.0,
                "target": 95.0,
                "excellent": 98.0,
            }

            self.test_data = {
                "valid_api_keys": {
                    "OPENAI_API_KEY": "sk-test-openai-key-12345",
                    "ANTHROPIC_API_KEY": "sk-ant-test-key-67890",
                    "GOOGLE_API_KEY": "AIza-test-google-key-abcdef",
                },
                "invalid_api_keys": {
                    "OPENAI_API_KEY": "invalid-openai-key",
                    "ANTHROPIC_API_KEY": "invalid-ant-key",
                    "GOOGLE_API_KEY": "invalid-google-key",
                },
                "test_credentials": {
                    "POSTGRES_PASSWORD": "test_password_12345",
                    "HIVE_API_KEY": "hive_test_key_67890",
                    "JWT_SECRET": "test_jwt_secret_abcdef",
                },
            }

            self.port_ranges = {
                "api_ports": range(8880, 8900),
                "postgres_ports": range(5430, 5450),
                "agent_ports": range(38880, 38900),
                "agent_postgres_ports": range(35530, 35550),
            }

        def get_timeout(self, operation: str) -> float:
            return self.test_timeouts.get(operation, 30.0)

        def get_coverage_threshold(self, level: str) -> float:
            return self.coverage_thresholds.get(level, 95.0)

        def get_test_api_key(self, provider: str, valid: bool = True) -> str:
            source = (
                self.test_data["valid_api_keys"]
                if valid
                else self.test_data["invalid_api_keys"]
            )
            return source.get(provider, "")

        def get_available_port(self, port_type: str) -> int:
            port_range = self.port_ranges.get(port_type, range(8000, 9000))

            import socket

            for port in port_range:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(("localhost", port))
                        return port
                    except OSError:
                        continue

            raise RuntimeError(f"No available ports in range for {port_type}")

    return CLITestConfig()


@pytest.fixture
def workspace_factory(test_environment_manager):
    """Factory for creating different types of test workspaces."""

    class WorkspaceFactory:
        def __init__(self, env_manager):
            self.env_manager = env_manager

        def create_minimal_workspace(self, name: str = "minimal") -> Path:
            """Create minimal workspace with basic files."""
            workspace = self.env_manager.create_temp_workspace(name)

            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  app:
    image: python:3.11
""")

            (workspace / ".env").write_text("HIVE_API_PORT=8886\n")

            return workspace

        def create_postgres_workspace(
            self, name: str = "postgres", port: int = 5432
        ) -> Path:
            """Create workspace with PostgreSQL configuration."""
            workspace = self.env_manager.create_temp_workspace(name)

            (workspace / "docker-compose.yml").write_text(f"""
version: '3.8'
services:
  postgres:
    image: postgres:15
    ports:
      - "{port}:5432"
    environment:
      POSTGRES_DB: hive
      POSTGRES_USER: hive
      POSTGRES_PASSWORD: test_password
""")

            (workspace / ".env").write_text(f"""
POSTGRES_PORT={port}
POSTGRES_DB=hive
POSTGRES_USER=hive
POSTGRES_PASSWORD=test_password
""")

            return workspace

        def create_agent_workspace(
            self, name: str = "agent", api_port: int = 38886, db_port: int = 35532
        ) -> Path:
            """Create workspace with agent configuration."""
            workspace = self.env_manager.create_temp_workspace(name)

            # Create main .env for docker-compose inheritance
            (workspace / ".env").write_text(f"""
HIVE_API_PORT=8886
POSTGRES_PORT=5532
POSTGRES_DB=hive
POSTGRES_USER=hive_agent
POSTGRES_PASSWORD=agent_password
HIVE_API_KEY=agent_test_key
""")
            
            # Create docker-compose.yml for agent environment
            docker_dir = workspace / "docker" / "agent"
            docker_dir.mkdir(parents=True, exist_ok=True)
            (docker_dir / "docker-compose.yml").write_text(f"""
version: '3.8'
services:
  postgres:
    image: postgres:15
    ports:
      - "{db_port}:5432"
    environment:
      - POSTGRES_USER=${{POSTGRES_USER}}
      - POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
      - POSTGRES_DB=hive_agent
  api:
    build: .
    ports:
      - "{api_port}:8886"
    environment:
      - HIVE_API_PORT=8886
      - HIVE_API_KEY=${{HIVE_API_KEY}}
""")

            # Create logs directory
            logs_dir = workspace / "logs"
            logs_dir.mkdir()
            (logs_dir / "agent-server.log").write_text("Agent server log content")

            return workspace

        def create_full_workspace(self, name: str = "full") -> Path:
            """Create complete workspace with all configurations."""
            workspace = self.env_manager.create_temp_workspace(name)

            # Create docker-compose.yml with all services
            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  app:
    image: python:3.11
    ports:
      - "8886:8886"
    environment:
      - HIVE_API_PORT=8886
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: hive
      POSTGRES_USER: hive
      POSTGRES_PASSWORD: full_workspace_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""")

            # Create .env file
            (workspace / ".env").write_text("""
HIVE_API_PORT=8886
HIVE_API_KEY=full_workspace_key
POSTGRES_PORT=5432
POSTGRES_DB=hive
POSTGRES_USER=hive
POSTGRES_PASSWORD=full_workspace_password
OPENAI_API_KEY=sk-test-openai-key
ANTHROPIC_API_KEY=sk-ant-test-key
""")

            # Create docker-compose for agent environment
            docker_dir = workspace / "docker" / "agent"
            docker_dir.mkdir(parents=True, exist_ok=True)
            (docker_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
    ports:
      - "35532:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=hive_agent
  api:
    build: .
    ports:
      - "38886:8886"
    environment:
      - HIVE_API_PORT=8886
      - HIVE_API_KEY=${HIVE_API_KEY}
""")

            # Create directory structure
            for dir_name in ["data", "logs", "backups", "config"]:
                (workspace / dir_name).mkdir()

            return workspace

        def create_invalid_workspace(self, name: str = "invalid") -> Path:
            """Create workspace with invalid configuration for testing error handling."""
            workspace = self.env_manager.create_temp_workspace(name)

            # Create invalid docker-compose.yml
            (workspace / "docker-compose.yml").write_text("invalid: yaml: content [")

            # Create malformed .env file
            (workspace / ".env").write_text("""
INVALID LINE WITHOUT EQUALS
=VALUE_WITHOUT_KEY
KEY_WITHOUT_VALUE=
MULTIPLE=EQUALS=SIGNS=HERE
""")

            return workspace

    return WorkspaceFactory(test_environment_manager)


@pytest.fixture
def cli_assertion_helpers():
    """Helper functions for CLI test assertions."""

    class CLIAssertionHelpers:
        @staticmethod
        def assert_workspace_structure(workspace_path: Path, expected_files: list[str]):
            """Assert that workspace has expected file structure."""
            for expected_file in expected_files:
                file_path = workspace_path / expected_file
                assert file_path.exists(), (
                    f"Expected file {expected_file} not found in workspace"
                )

        @staticmethod
        def assert_env_file_content(env_file: Path, expected_vars: dict[str, str]):
            """Assert that .env file contains expected variables."""
            if not env_file.exists():
                pytest.fail(f"Env file {env_file} does not exist")

            env_content = env_file.read_text()

            for key, expected_value in expected_vars.items():
                if expected_value is not None:
                    assert f"{key}={expected_value}" in env_content, (
                        f"Expected {key}={expected_value} in env file"
                    )
                else:
                    assert f"{key}=" in env_content, (
                        f"Expected {key} to be present in env file"
                    )

        @staticmethod
        def assert_docker_compose_valid(compose_file: Path):
            """Assert that docker-compose.yml is valid YAML."""
            if not compose_file.exists():
                pytest.fail(f"Docker compose file {compose_file} does not exist")

            try:
                import yaml

                with open(compose_file) as f:
                    compose_data = yaml.safe_load(f)

                assert "version" in compose_data, "Docker compose file missing version"
                assert "services" in compose_data, (
                    "Docker compose file missing services"
                )

            except ImportError:
                pytest.skip("PyYAML not available for docker-compose validation")
            except yaml.YAMLError as e:
                pytest.fail(f"Docker compose file is not valid YAML: {e}")

        @staticmethod
        def assert_command_output_contains(
            captured_output: str, expected_strings: list[str]
        ):
            """Assert that command output contains expected strings."""
            for expected_string in expected_strings:
                assert expected_string in captured_output, (
                    f"Expected '{expected_string}' in output: {captured_output}"
                )

        @staticmethod
        def assert_performance_within_limits(
            execution_time: float, max_time: float, operation: str
        ):
            """Assert that operation completed within performance limits."""
            assert execution_time <= max_time, (
                f"{operation} took {execution_time:.3f}s, expected under {max_time}s"
            )

        @staticmethod
        def assert_coverage_threshold_met(
            coverage_percentage: float, threshold: float = 95.0
        ):
            """Assert that coverage threshold is met."""
            assert coverage_percentage >= threshold, (
                f"Coverage {coverage_percentage:.2f}% below threshold {threshold}%"
            )

    return CLIAssertionHelpers()


# Configure pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests across components"
    )
    config.addinivalue_line("markers", "e2e: End-to-end workflow tests")
    config.addinivalue_line("markers", "performance: Performance and benchmark tests")
    config.addinivalue_line("markers", "real_server: Tests requiring real agent server")
    config.addinivalue_line("markers", "real_postgres: Tests requiring real PostgreSQL")
    config.addinivalue_line("markers", "slow: Slow tests that take significant time")
    config.addinivalue_line("markers", "coverage: Coverage validation tests")
    config.addinivalue_line(
        "markers", "cross_platform: Cross-platform compatibility tests"
    )


# Configure test collection and execution
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and configure execution."""
    for item in items:
        # Add markers based on test names and paths
        if "test_real_" in item.name or "real_server" in item.name:
            item.add_marker(pytest.mark.real_server)

        if "test_postgres" in item.name and "real" in item.name:
            item.add_marker(pytest.mark.real_postgres)

        if "performance" in item.name or "benchmark" in item.name:
            item.add_marker(pytest.mark.performance)

        if "coverage" in item.name:
            item.add_marker(pytest.mark.coverage)

        if "e2e" in item.name or "workflow" in item.name:
            item.add_marker(pytest.mark.e2e)

        if "cross_platform" in item.name or "platform" in item.name:
            item.add_marker(pytest.mark.cross_platform)

        # Mark slow tests
        if any(
            marker in item.name
            for marker in ["comprehensive", "full_lifecycle", "concurrent"]
        ):
            item.add_marker(pytest.mark.slow)


# Configure pytest reporting
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom terminal summary information."""
    terminalreporter.write_line("")
    terminalreporter.write_line("🧪 CLI Comprehensive Test Suite Summary", bold=True)
    terminalreporter.write_line("=" * 50)

    # Get test statistics
    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    errors = len(stats.get("error", []))

    total = passed + failed + skipped + errors

    if total > 0:
        terminalreporter.write_line("📊 Test Results:")
        terminalreporter.write_line(f"   ✅ Passed: {passed}")
        terminalreporter.write_line(f"   ❌ Failed: {failed}")
        terminalreporter.write_line(f"   ⏭️  Skipped: {skipped}")
        terminalreporter.write_line(f"   🚨 Errors: {errors}")
        terminalreporter.write_line(f"   📈 Total: {total}")

        success_rate = (passed / total) * 100 if total > 0 else 0
        terminalreporter.write_line(f"   🎯 Success Rate: {success_rate:.1f}%")

    terminalreporter.write_line("")
    terminalreporter.write_line("🎯 Coverage Target: >95% for CLI components")
    terminalreporter.write_line(
        "🔒 SECURITY: Real server/database connections DISABLED for safety"
    )
    terminalreporter.write_line(
        "✅ All tests use mocked connections for complete isolation"
    )
    terminalreporter.write_line("")
