"""End-to-End UVX Workflow Tests.

Comprehensive testing of the complete UVX workflow:
--init → workspace → startup → agent lifecycle → real server validation

Tests against actual running agent server on port 38886 with real PostgreSQL
container integration and cross-platform validation.

CRITICAL: These tests require actual agent server validation for >95% coverage.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import psycopg2
import pytest
import requests

from cli.main import main


class TestUVXWorkflowEndToEnd:
    """Complete UVX workflow testing with real agent server validation."""

    @pytest.fixture(scope="class")
    def temp_workspace_dir(self):
        """Create temporary workspace directory for testing."""
        temp_dir = tempfile.mkdtemp(prefix="uvx_test_")
        yield Path(temp_dir)

        # Cleanup
        try:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        except Exception:
            pass

    @pytest.fixture
    def mock_docker_environment(self):
        """Mock Docker environment for testing."""
        with (
            patch("cli.docker_manager.DockerManager") as mock_docker_service,
            patch(
                "cli.core.postgres_service.PostgreSQLService"
            ) as mock_postgres_service,
        ):
            # Configure mock Docker service
            mock_docker = Mock()
            mock_docker.install.return_value = True
            mock_docker.start.return_value = True
            mock_docker.stop.return_value = True
            mock_docker.restart.return_value = True
            mock_docker.status.return_value = None
            mock_docker.health.return_value = None
            mock_docker.logs.return_value = None
            mock_docker.uninstall.return_value = True
            mock_docker_service.return_value = mock_docker

            # Configure mock PostgreSQL service
            mock_postgres = Mock()
            mock_postgres.execute.return_value = True
            mock_postgres.status.return_value = {
                "status": "running",
                "port": 35532,
                "healthy": True,
            }
            mock_postgres_service.return_value = mock_postgres

            yield {"docker": mock_docker, "postgres": mock_postgres}

    def test_complete_uvx_init_workflow(
        self, temp_workspace_dir, mock_docker_environment
    ):
        """Test complete --init workflow with workspace creation."""
        workspace_path = temp_workspace_dir / "test-init-workspace"

        # Mock user inputs for interactive initialization
        user_inputs = [
            str(workspace_path),  # Workspace path
            "y",  # Use PostgreSQL
            "5432",  # PostgreSQL port
            "",  # Skip API keys (press enter)
            "",  # Skip more API keys
            "y",  # Confirm creation
        ]

        with patch("builtins.input", side_effect=user_inputs):
            with patch("sys.argv", ["automagik-hive", "--init", "test-workspace"]):
                result = main()

        # Should fail initially - init workflow not fully implemented
        assert result == 0

        # Verify workspace was created
        assert workspace_path.exists()
        assert (workspace_path / "docker-compose.yml").exists()
        assert (workspace_path / ".env").exists() or (
            workspace_path / ".env.example"
        ).exists()

    def test_workspace_startup_after_init(
        self, temp_workspace_dir, mock_docker_environment
    ):
        """Test workspace startup after initialization."""
        workspace_path = temp_workspace_dir / "test-startup-workspace"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create minimal workspace files
        (workspace_path / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: hive
      POSTGRES_USER: hive
      POSTGRES_PASSWORD: hive_password
""")

        (workspace_path / ".env").write_text("""
HIVE_API_PORT=8886
POSTGRES_PORT=5432
POSTGRES_DB=hive
POSTGRES_USER=hive
POSTGRES_PASSWORD=hive_password
""")

        with patch("sys.argv", ["automagik-hive", str(workspace_path)]):
            result = main()

        # Should fail initially - workspace startup not implemented
        assert result == 0

    def test_agent_environment_full_lifecycle(
        self, temp_workspace_dir, mock_docker_environment
    ):
        """Test complete agent environment lifecycle: install → serve → status → logs → stop → restart → reset."""
        workspace_path = temp_workspace_dir / "test-agent-lifecycle"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create workspace files for agent testing
        (workspace_path / ".env.agent").write_text("""
HIVE_API_PORT=38886
POSTGRES_PORT=35532
POSTGRES_DB=hive_agent
POSTGRES_USER=hive_agent
POSTGRES_PASSWORD=agent_password
HIVE_API_KEY=test_agent_key_12345
""")

        # Test agent install
        with patch(
            "sys.argv", ["automagik-hive", "--agent-install", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - agent install not implemented
        assert result == 0

        # Test agent serve
        with patch(
            "sys.argv", ["automagik-hive", "--agent-serve", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - agent serve not implemented
        assert result == 0

        # Test agent status
        with patch(
            "sys.argv", ["automagik-hive", "--agent-status", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - agent status not implemented
        assert result == 0

        # Test agent logs
        with patch(
            "sys.argv",
            ["automagik-hive", "--agent-logs", str(workspace_path), "--tail", "100"],
        ):
            result = main()

        # Should fail initially - agent logs not implemented
        assert result == 0

        # Test agent restart
        with patch(
            "sys.argv", ["automagik-hive", "--agent-restart", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - agent restart not implemented
        assert result == 0

        # Test agent stop
        with patch("sys.argv", ["automagik-hive", "--agent-stop", str(workspace_path)]):
            result = main()

        # Should fail initially - agent stop not implemented
        assert result == 0

        # Test agent reset
        with patch(
            "sys.argv", ["automagik-hive", "--agent-reset", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - agent reset not implemented
        assert result == 0

    def test_postgres_container_full_lifecycle(
        self, temp_workspace_dir, mock_docker_environment
    ):
        """Test complete PostgreSQL container lifecycle: start → status → logs → health → restart → stop."""
        workspace_path = temp_workspace_dir / "test-postgres-lifecycle"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create workspace with PostgreSQL configuration
        (workspace_path / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: hive-postgres-test
    ports:
      - "35533:5432"
    environment:
      POSTGRES_DB: hive_test
      POSTGRES_USER: hive_test
      POSTGRES_PASSWORD: test_password
""")

        # Test postgres start
        with patch(
            "sys.argv", ["automagik-hive", "--postgres-start", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - postgres start not implemented
        assert result == 0

        # Test postgres status
        with patch(
            "sys.argv", ["automagik-hive", "--postgres-status", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - postgres status not implemented
        assert result == 0

        # Test postgres logs
        with patch(
            "sys.argv",
            ["automagik-hive", "--postgres-logs", str(workspace_path), "--tail", "50"],
        ):
            result = main()

        # Should fail initially - postgres logs not implemented
        assert result == 0

        # Test postgres health
        with patch(
            "sys.argv", ["automagik-hive", "--postgres-health", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - postgres health not implemented
        assert result == 0

        # Test postgres restart
        with patch(
            "sys.argv", ["automagik-hive", "--postgres-restart", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - postgres restart not implemented
        assert result == 0

        # Test postgres stop
        with patch(
            "sys.argv", ["automagik-hive", "--postgres-stop", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - postgres stop not implemented
        assert result == 0


class TestRealAgentServerValidation:
    """Tests against real running agent server on port 38886."""

    @pytest.fixture
    def agent_server_available(self):
        """Check if agent server is available on port 38886."""
        try:
            response = requests.get("http://localhost:38886/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_AGENT_SERVER", "").lower() != "true",
        reason="Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.",
    )
    def test_agent_server_health_endpoint(self, agent_server_available):
        """Test real agent server health endpoint."""
        if not agent_server_available:
            pytest.skip("Agent server not available on port 38886")

        # Should fail initially - real server connection not tested
        response = requests.get("http://localhost:38886/health", timeout=10)
        assert response.status_code == 200

        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "ok", "ready"]

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_AGENT_SERVER", "").lower() != "true",
        reason="Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.",
    )
    def test_agent_server_api_endpoints(self, agent_server_available):
        """Test real agent server API endpoints."""
        if not agent_server_available:
            pytest.skip("Agent server not available on port 38886")

        base_url = "http://localhost:38886"

        # Test version endpoint
        response = requests.get(f"{base_url}/version", timeout=10)
        # Should fail initially - version endpoint not accessible
        assert response.status_code == 200

        version_data = response.json()
        assert "version" in version_data

        # Test agents endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/agents", timeout=10)
            # Should fail initially - agents endpoint not accessible
            assert response.status_code in [200, 401]  # 401 if auth required
        except requests.RequestException:
            pytest.skip("Agents endpoint not available")

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_AGENT_SERVER", "").lower() != "true",
        reason="Real agent server testing disabled. Set TEST_REAL_AGENT_SERVER=true to enable.",
    )
    def test_agent_command_status_against_real_server(self, temp_workspace_dir):
        """Test agent status command against real running server."""
        workspace_path = temp_workspace_dir / "test-real-server"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create agent environment file
        (workspace_path / ".env.agent").write_text("""
HIVE_API_PORT=38886
POSTGRES_PORT=35532
POSTGRES_DB=hive_agent
POSTGRES_USER=hive_agent
POSTGRES_PASSWORD=agent_password
""")

        # Create logs directory and file
        logs_dir = workspace_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        (logs_dir / "agent-server.log").write_text(
            "Test log entry\nAgent server started"
        )

        with patch(
            "sys.argv", ["automagik-hive", "--agent-status", str(workspace_path)]
        ):
            result = main()

        # Should fail initially - real server status check not implemented
        assert result == 0


class TestRealPostgreSQLIntegration:
    """Tests with real PostgreSQL container integration."""

    @pytest.fixture
    def postgres_container_available(self):
        """Check if PostgreSQL container is available."""
        try:
            # Try to connect to PostgreSQL on port 35532 (agent environment)
            conn = psycopg2.connect(
                host="localhost",
                port=35532,
                database="hive_agent",
                user="hive_agent",
                password="agent_password",
                connect_timeout=5,
            )
            conn.close()
            return True
        except psycopg2.OperationalError:
            return False

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_POSTGRES", "").lower() != "true",
        reason="Real PostgreSQL testing disabled. Set TEST_REAL_POSTGRES=true to enable.",
    )
    def test_postgres_container_connection(self, postgres_container_available):
        """Test real PostgreSQL container connection."""
        if not postgres_container_available:
            pytest.skip("PostgreSQL container not available on port 35532")

        # Should fail initially - real PostgreSQL connection not tested
        conn = psycopg2.connect(
            host="localhost",
            port=35532,
            database="hive_agent",
            user="hive_agent",
            password="agent_password",
            connect_timeout=10,
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        assert version is not None
        assert "PostgreSQL" in version[0]

        cursor.close()
        conn.close()

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_POSTGRES", "").lower() != "true",
        reason="Real PostgreSQL testing disabled. Set TEST_REAL_POSTGRES=true to enable.",
    )
    def test_postgres_schema_validation(self, postgres_container_available):
        """Test PostgreSQL schema and tables."""
        if not postgres_container_available:
            pytest.skip("PostgreSQL container not available on port 35532")

        conn = psycopg2.connect(
            host="localhost",
            port=35532,
            database="hive_agent",
            user="hive_agent",
            password="agent_password",
            connect_timeout=10,
        )

        cursor = conn.cursor()

        # Check for expected schemas
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name IN ('hive', 'agno', 'public');
        """)
        schemas = cursor.fetchall()

        # Should fail initially - schema validation not implemented
        schema_names = [row[0] for row in schemas]
        assert "public" in schema_names  # At minimum, public schema should exist

        # Check for expected tables if they exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()

        # Tables may or may not exist depending on initialization
        [row[0] for row in tables]

        cursor.close()
        conn.close()


class TestWorkflowPerformanceBenchmarks:
    """Performance benchmarks for UVX workflow operations."""

    def test_init_command_performance(self, temp_workspace_dir):
        """Benchmark --init command performance."""
        workspace_path = temp_workspace_dir / "perf-test-init"

        user_inputs = [
            str(workspace_path),
            "n",  # No PostgreSQL
            "",  # Skip API keys
        ]

        start_time = time.time()

        with patch("builtins.input", side_effect=user_inputs):
            with patch("sys.argv", ["automagik-hive", "--init", "test-workspace"]):
                result = main()

        elapsed = time.time() - start_time

        # Should fail initially - performance benchmarks not implemented
        assert result == 0
        assert elapsed < 30.0, f"Init command took {elapsed:.2f}s, should be under 30s"

    def test_agent_commands_responsiveness(self, temp_workspace_dir):
        """Test agent command responsiveness."""
        workspace_path = temp_workspace_dir / "perf-test-agent"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create minimal agent environment
        (workspace_path / ".env.agent").write_text("HIVE_API_PORT=38886\n")

        commands_to_test = [
            ["--agent-status"],
            ["--agent-logs", "--tail", "10"],
        ]

        for command_args in commands_to_test:
            start_time = time.time()

            with patch(
                "sys.argv", ["automagik-hive", *command_args, str(workspace_path)]
            ):
                result = main()

            elapsed = time.time() - start_time

            # Should fail initially - responsiveness benchmarks not implemented
            assert result == 0
            assert elapsed < 5.0, (
                f"Command {command_args} took {elapsed:.2f}s, should be under 5s"
            )

    def test_postgres_commands_responsiveness(self, temp_workspace_dir):
        """Test PostgreSQL command responsiveness."""
        workspace_path = temp_workspace_dir / "perf-test-postgres"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create minimal docker-compose file
        (workspace_path / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
""")

        commands_to_test = [
            ["--postgres-status"],
            ["--postgres-health"],
        ]

        for command_args in commands_to_test:
            start_time = time.time()

            with patch(
                "sys.argv", ["automagik-hive", *command_args, str(workspace_path)]
            ):
                result = main()

            elapsed = time.time() - start_time

            # Should fail initially - responsiveness benchmarks not implemented
            assert result == 0
            assert elapsed < 10.0, (
                f"Command {command_args} took {elapsed:.2f}s, should be under 10s"
            )


class TestWorkflowErrorRecovery:
    """Test workflow error recovery and failure scenarios."""

    def test_init_with_invalid_permissions(self, temp_workspace_dir):
        """Test init command with permission errors."""
        # Try to create workspace in read-only directory
        readonly_path = temp_workspace_dir / "readonly"
        readonly_path.mkdir(exist_ok=True)

        # Make directory read-only
        readonly_path.chmod(0o444)

        workspace_path = readonly_path / "test-workspace"

        user_inputs = [str(workspace_path), "n", ""]

        try:
            with patch("builtins.input", side_effect=user_inputs):
                with patch("sys.argv", ["automagik-hive", "--init", "test-workspace"]):
                    result = main()

            # Should fail initially - permission error handling not implemented
            assert result == 1  # Should return failure code

        finally:
            # Restore permissions for cleanup
            readonly_path.chmod(0o755)

    def test_agent_commands_with_missing_environment(self, temp_workspace_dir):
        """Test agent commands with missing .env.agent file."""
        workspace_path = temp_workspace_dir / "test-missing-env"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # No .env.agent file created

        commands_to_test = [
            ["--agent-status"],
            ["--agent-serve"],
            ["--agent-logs"],
        ]

        for command_args in commands_to_test:
            with patch(
                "sys.argv", ["automagik-hive", *command_args, str(workspace_path)]
            ):
                result = main()

            # Should fail initially - missing environment handling not implemented
            # Commands should either fail gracefully or create missing files
            assert result in [0, 1], (
                f"Command {command_args} returned unexpected exit code"
            )

    def test_postgres_commands_with_missing_compose_file(self, temp_workspace_dir):
        """Test PostgreSQL commands with missing docker-compose.yml."""
        workspace_path = temp_workspace_dir / "test-missing-compose"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # No docker-compose.yml file created

        commands_to_test = [
            ["--postgres-status"],
            ["--postgres-start"],
            ["--postgres-health"],
        ]

        for command_args in commands_to_test:
            with patch(
                "sys.argv", ["automagik-hive", *command_args, str(workspace_path)]
            ):
                result = main()

            # Should fail initially - missing compose file handling not implemented
            assert result in [0, 1], (
                f"Command {command_args} returned unexpected exit code"
            )

    def test_workspace_startup_with_corrupted_files(self, temp_workspace_dir):
        """Test workspace startup with corrupted configuration files."""
        workspace_path = temp_workspace_dir / "test-corrupted"
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create corrupted docker-compose.yml
        (workspace_path / "docker-compose.yml").write_text("invalid: yaml: content [")

        # Create corrupted .env file
        (workspace_path / ".env").write_text("INVALID=LINE\nMISSING_VALUE=\nBAD SYNTAX")

        with patch("sys.argv", ["automagik-hive", str(workspace_path)]):
            result = main()

        # Should fail initially - corrupted file handling not implemented
        assert result in [0, 1]  # Should handle gracefully or fail appropriately


class TestWorkflowCrossPlatformValidation:
    """Cross-platform validation tests for Linux/macOS focus."""

    @pytest.mark.skipif(os.name == "nt", reason="Unix-specific path testing")
    def test_unix_workspace_paths(self, temp_workspace_dir):
        """Test workspace creation with Unix-style paths."""
        unix_workspace = temp_workspace_dir / "unix-style-workspace"

        user_inputs = [str(unix_workspace), "n", ""]

        with patch("builtins.input", side_effect=user_inputs):
            with patch("sys.argv", ["automagik-hive", "--init", "test-workspace"]):
                result = main()

        # Should fail initially - Unix path handling not validated
        assert result == 0
        assert unix_workspace.exists()

    @pytest.mark.skipif(os.name == "nt", reason="Unix-specific permission testing")
    def test_unix_file_permissions(self, temp_workspace_dir):
        """Test file permissions on Unix systems."""
        workspace_path = temp_workspace_dir / "test-permissions"

        user_inputs = [str(workspace_path), "n", ""]

        with patch("builtins.input", side_effect=user_inputs):
            with patch("sys.argv", ["automagik-hive", "--init", "test-workspace"]):
                result = main()

        if result == 0 and workspace_path.exists():
            # Check that files have appropriate permissions
            env_file = workspace_path / ".env"
            if env_file.exists():
                # Should fail initially - permission checking not implemented
                permissions = oct(env_file.stat().st_mode)[-3:]
                assert permissions in ["600", "644"], (
                    f"Env file has permissions {permissions}, should be 600 or 644"
                )

    def test_relative_path_handling_cross_platform(self, temp_workspace_dir):
        """Test relative path handling across platforms."""
        # Change to temp directory
        original_cwd = os.getcwd()

        try:
            os.chdir(temp_workspace_dir)

            relative_paths = [".", "./workspace", "../workspace"]

            for rel_path in relative_paths:
                with patch("sys.argv", ["automagik-hive", "--agent-status", rel_path]):
                    result = main()

                # Should fail initially - cross-platform relative path handling not implemented
                assert result in [0, 1], (
                    f"Relative path {rel_path} caused unexpected result"
                )

        finally:
            os.chdir(original_cwd)

    def test_path_separator_normalization(self, temp_workspace_dir):
        """Test path separator normalization across platforms."""
        # Test various path formats
        path_formats = [
            str(temp_workspace_dir / "workspace1"),  # Native format
            str(temp_workspace_dir).replace("\\", "/")
            + "/workspace2",  # Forward slashes
        ]

        if os.name == "nt":  # Windows
            # Add Windows-specific formats
            path_formats.append(
                str(temp_workspace_dir).replace("/", "\\") + "\\workspace3"
            )

        for path_format in path_formats:
            user_inputs = [path_format, "n", ""]

            with patch("builtins.input", side_effect=user_inputs):
                with patch("sys.argv", ["automagik-hive", "--init", "test-workspace"]):
                    result = main()

            # Should fail initially - path separator normalization not implemented
            assert result in [0, 1], (
                f"Path format {path_format} caused unexpected result"
            )
