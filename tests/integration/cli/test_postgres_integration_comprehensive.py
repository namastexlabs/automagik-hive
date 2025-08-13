"""Comprehensive PostgreSQL Container Integration Tests.

Tests real PostgreSQL container integration with database validation,
connection testing, and schema verification against actual running containers.

CRITICAL: These tests validate against real PostgreSQL containers for complete
integration coverage with container management and database operations.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import psycopg2
import pytest

import docker
# Skip test - CLI structure refactored, old postgres commands/core modules no longer exist
pytestmark = pytest.mark.skip(reason="CLI architecture refactored - postgres commands consolidated")

# TODO: Update tests to use cli.docker_manager.DockerManager


class TestPostgreSQLContainerManagement:
    """Test PostgreSQL container lifecycle management."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with PostgreSQL configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create docker-compose.yml for PostgreSQL
            compose_content = """
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: hive-postgres-test
    ports:
      - "35534:5432"
    environment:
      POSTGRES_DB: hive_test
      POSTGRES_USER: hive_test
      POSTGRES_PASSWORD: test_password_123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
"""
            (workspace / "docker-compose.yml").write_text(compose_content)

            # Create .env file
            (workspace / ".env").write_text("""
POSTGRES_PORT=35534
POSTGRES_DB=hive_test
POSTGRES_USER=hive_test
POSTGRES_PASSWORD=test_password_123
HIVE_API_PORT=8886
""")

            yield workspace

    @pytest.fixture
    def mock_docker_service(self):
        """Mock Docker service for testing without real containers."""
        with patch("cli.core.postgres_service.DockerService") as mock_docker_class:
            mock_docker = Mock()
            mock_docker.is_docker_available.return_value = True
            mock_docker.is_container_running.return_value = False
            mock_docker.start_container.return_value = True
            mock_docker.stop_container.return_value = True
            mock_docker.restart_container.return_value = True
            mock_docker.get_container_logs.return_value = "PostgreSQL init completed"
            mock_docker.get_container_status.return_value = {
                "status": "running",
                "health": "healthy",
                "ports": ["35534:5432"],
            }
            mock_docker_class.return_value = mock_docker
            yield mock_docker

    def test_postgres_commands_initialization(self):
        """Test PostgreSQLCommands initializes correctly."""
        commands = PostgreSQLCommands()

        # Should fail initially - initialization not implemented
        assert hasattr(commands, "postgres_service")
        assert commands.postgres_service is not None

    def test_postgres_start_command_success(self, temp_workspace, mock_docker_service):
        """Test successful PostgreSQL container start."""
        mock_docker_service.is_container_running.return_value = False
        mock_docker_service.start_container.return_value = True

        commands = PostgreSQLCommands()
        result = commands.postgres_start(str(temp_workspace))

        # Should fail initially - postgres start not implemented
        assert result is True
        mock_docker_service.start_container.assert_called_once()

    def test_postgres_start_command_already_running(
        self, temp_workspace, mock_docker_service
    ):
        """Test PostgreSQL start when container already running."""
        mock_docker_service.is_container_running.return_value = True

        commands = PostgreSQLCommands()
        result = commands.postgres_start(str(temp_workspace))

        # Should fail initially - already running check not implemented
        assert result is True
        mock_docker_service.start_container.assert_not_called()

    def test_postgres_stop_command_success(self, temp_workspace, mock_docker_service):
        """Test successful PostgreSQL container stop."""
        mock_docker_service.is_container_running.return_value = True
        mock_docker_service.stop_container.return_value = True

        commands = PostgreSQLCommands()
        result = commands.postgres_stop(str(temp_workspace))

        # Should fail initially - postgres stop not implemented
        assert result is True
        mock_docker_service.stop_container.assert_called_once()

    def test_postgres_stop_command_not_running(
        self, temp_workspace, mock_docker_service
    ):
        """Test PostgreSQL stop when container not running."""
        mock_docker_service.is_container_running.return_value = False

        commands = PostgreSQLCommands()
        result = commands.postgres_stop(str(temp_workspace))

        # Should fail initially - not running check not implemented
        assert result is True
        mock_docker_service.stop_container.assert_not_called()

    def test_postgres_restart_command_success(
        self, temp_workspace, mock_docker_service
    ):
        """Test successful PostgreSQL container restart."""
        mock_docker_service.restart_container.return_value = True

        commands = PostgreSQLCommands()
        result = commands.postgres_restart(str(temp_workspace))

        # Should fail initially - postgres restart not implemented
        assert result is True
        mock_docker_service.restart_container.assert_called_once()

    def test_postgres_status_command_running(self, temp_workspace, mock_docker_service):
        """Test PostgreSQL status when container is running."""
        mock_docker_service.get_container_status.return_value = {
            "status": "running",
            "health": "healthy",
            "ports": ["35534:5432"],
            "uptime": "2 hours",
        }

        commands = PostgreSQLCommands()
        result = commands.postgres_status(str(temp_workspace))

        # Should fail initially - status display not implemented
        assert result is True
        mock_docker_service.get_container_status.assert_called_once()

    def test_postgres_status_command_stopped(self, temp_workspace, mock_docker_service):
        """Test PostgreSQL status when container is stopped."""
        mock_docker_service.get_container_status.return_value = {
            "status": "stopped",
            "health": "unknown",
            "ports": [],
            "uptime": "0",
        }

        commands = PostgreSQLCommands()
        result = commands.postgres_status(str(temp_workspace))

        # Should fail initially - stopped status handling not implemented
        assert result is True

    def test_postgres_logs_command_success(self, temp_workspace, mock_docker_service):
        """Test PostgreSQL logs command."""
        mock_logs = """
2024-01-01 10:00:00.000 UTC [1] LOG:  starting PostgreSQL 15.5
2024-01-01 10:00:01.000 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2024-01-01 10:00:02.000 UTC [1] LOG:  database system is ready to accept connections
"""
        mock_docker_service.get_container_logs.return_value = mock_logs

        commands = PostgreSQLCommands()
        result = commands.postgres_logs(str(temp_workspace), tail=50)

        # Should fail initially - logs display not implemented
        assert result is True
        mock_docker_service.get_container_logs.assert_called_once_with(
            container_name="hive-postgres-test", tail=50
        )

    def test_postgres_logs_command_custom_tail(
        self, temp_workspace, mock_docker_service
    ):
        """Test PostgreSQL logs command with custom tail count."""
        mock_docker_service.get_container_logs.return_value = "Mock logs"

        commands = PostgreSQLCommands()
        result = commands.postgres_logs(str(temp_workspace), tail=100)

        # Should fail initially - custom tail not implemented
        assert result is True
        mock_docker_service.get_container_logs.assert_called_once_with(
            container_name="hive-postgres-test", tail=100
        )

    def test_postgres_health_command_healthy(self, temp_workspace, mock_docker_service):
        """Test PostgreSQL health check when healthy."""
        mock_docker_service.get_container_status.return_value = {
            "status": "running",
            "health": "healthy",
        }

        with patch("cli.commands.postgres.psycopg2.connect") as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = ("PostgreSQL 15.5",)
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            commands = PostgreSQLCommands()
            result = commands.postgres_health(str(temp_workspace))

        # Should fail initially - health check not implemented
        assert result is True
        mock_connect.assert_called_once()

    def test_postgres_health_command_connection_failed(
        self, temp_workspace, mock_docker_service
    ):
        """Test PostgreSQL health check when connection fails."""
        mock_docker_service.get_container_status.return_value = {
            "status": "running",
            "health": "unhealthy",
        }

        with patch("cli.commands.postgres.psycopg2.connect") as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("Connection failed")

            commands = PostgreSQLCommands()
            result = commands.postgres_health(str(temp_workspace))

        # Should fail initially - connection failure handling not implemented
        assert result is False


class TestPostgreSQLServiceCore:
    """Test core PostgreSQL service functionality."""

    @pytest.fixture
    def mock_docker_service(self):
        """Mock Docker service for PostgreSQL service testing."""
        with patch("cli.core.postgres_service.DockerService") as mock_docker_class:
            mock_docker = Mock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_class.return_value = mock_docker
            yield mock_docker

    def test_postgres_service_initialization(self, mock_docker_service):
        """Test PostgreSQLService initializes correctly."""
        service = PostgreSQLService()

        # Should fail initially - service initialization not implemented
        assert hasattr(service, "docker_service")
        assert service.docker_service is not None

    def test_postgres_service_start_container(self, mock_docker_service):
        """Test PostgreSQL service starts container correctly."""
        mock_docker_service.start_container.return_value = True
        mock_docker_service.is_container_running.return_value = False

        service = PostgreSQLService()
        result = service.start_postgres("test-workspace", "hive-postgres-test")

        # Should fail initially - start postgres not implemented
        assert result is True
        mock_docker_service.start_container.assert_called_once()

    def test_postgres_service_stop_container(self, mock_docker_service):
        """Test PostgreSQL service stops container correctly."""
        mock_docker_service.stop_container.return_value = True
        mock_docker_service.is_container_running.return_value = True

        service = PostgreSQLService()
        result = service.stop_postgres("test-workspace", "hive-postgres-test")

        # Should fail initially - stop postgres not implemented
        assert result is True
        mock_docker_service.stop_container.assert_called_once()

    def test_postgres_service_get_connection_info(self, mock_docker_service):
        """Test PostgreSQL service gets connection information."""
        mock_docker_service.get_container_status.return_value = {
            "status": "running",
            "ports": ["35534:5432"],
        }

        service = PostgreSQLService()
        connection_info = service.get_connection_info("test-workspace")

        # Should fail initially - connection info not implemented
        assert connection_info is not None
        assert "host" in connection_info
        assert "port" in connection_info
        assert "database" in connection_info

    def test_postgres_service_check_connection(self, mock_docker_service):
        """Test PostgreSQL service connection check."""
        with patch("cli.core.postgres_service.psycopg2.connect") as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            service = PostgreSQLService()
            result = service.check_connection(
                host="localhost",
                port=35534,
                database="hive_test",
                user="hive_test",
                password="test_password_123",
            )

        # Should fail initially - connection check not implemented
        assert result is True
        mock_connect.assert_called_once()

    def test_postgres_service_check_connection_failed(self, mock_docker_service):
        """Test PostgreSQL service connection check failure."""
        with patch("cli.core.postgres_service.psycopg2.connect") as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("Connection refused")

            service = PostgreSQLService()
            result = service.check_connection(
                host="localhost",
                port=35534,
                database="hive_test",
                user="hive_test",
                password="wrong_password",
            )

        # Should fail initially - connection failure handling not implemented
        assert result is False


class TestRealPostgreSQLContainerIntegration:
    """Tests against real PostgreSQL containers when available."""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client for real container testing."""
        try:
            client = docker.from_env()
            # Test Docker connectivity
            client.ping()
            return client
        except Exception:
            pytest.skip("Docker not available for real container testing")

    @pytest.fixture
    def temp_workspace_real(self):
        """Create temporary workspace for real container testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create docker-compose.yml for real testing
            compose_content = """
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: hive-postgres-real-test
    ports:
      - "35535:5432"
    environment:
      POSTGRES_DB: hive_real_test
      POSTGRES_USER: hive_real_test
      POSTGRES_PASSWORD: real_test_password_456
    volumes:
      - postgres_real_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_real_data:
"""
            (workspace / "docker-compose.yml").write_text(compose_content)

            (workspace / ".env").write_text("""
POSTGRES_PORT=35535
POSTGRES_DB=hive_real_test
POSTGRES_USER=hive_real_test
POSTGRES_PASSWORD=real_test_password_456
""")

            yield workspace

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_POSTGRES_CONTAINERS", "").lower() != "true",
        reason="Real PostgreSQL container testing disabled. Set TEST_REAL_POSTGRES_CONTAINERS=true to enable.",
    )
    def test_real_postgres_container_lifecycle(
        self, docker_client, temp_workspace_real
    ):
        """Test complete PostgreSQL container lifecycle with real containers."""
        commands = PostgreSQLCommands()
        workspace_path = str(temp_workspace_real)

        try:
            # Clean up any existing test container
            try:
                existing_container = docker_client.containers.get(
                    "hive-postgres-real-test"
                )
                existing_container.stop()
                existing_container.remove()
            except docker.errors.NotFound:
                pass

            # Test start
            result = commands.postgres_start(workspace_path)
            # Should fail initially - real container start not implemented
            assert result is True

            # Wait for container to be ready
            time.sleep(5)

            # Test status
            result = commands.postgres_status(workspace_path)
            # Should fail initially - real container status not implemented
            assert result is True

            # Test health
            result = commands.postgres_health(workspace_path)
            # Should fail initially - real container health not implemented
            assert result is True

            # Test logs
            result = commands.postgres_logs(workspace_path, tail=10)
            # Should fail initially - real container logs not implemented
            assert result is True

            # Test restart
            result = commands.postgres_restart(workspace_path)
            # Should fail initially - real container restart not implemented
            assert result is True

            # Wait for restart to complete
            time.sleep(5)

            # Test stop
            result = commands.postgres_stop(workspace_path)
            # Should fail initially - real container stop not implemented
            assert result is True

        finally:
            # Cleanup
            try:
                container = docker_client.containers.get("hive-postgres-real-test")
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_POSTGRES_CONTAINERS", "").lower() != "true",
        reason="Real PostgreSQL container testing disabled. Set TEST_REAL_POSTGRES_CONTAINERS=true to enable.",
    )
    def test_real_postgres_database_connection(
        self, docker_client, temp_workspace_real
    ):
        """Test real database connection and operations."""
        commands = PostgreSQLCommands()
        workspace_path = str(temp_workspace_real)

        try:
            # Start container
            result = commands.postgres_start(workspace_path)
            assert result is True

            # Wait for PostgreSQL to be ready
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    conn = psycopg2.connect(
                        host="localhost",
                        port=35535,
                        database="hive_real_test",
                        user="hive_real_test",
                        password="real_test_password_456",
                        connect_timeout=5,
                    )
                    conn.close()
                    break
                except psycopg2.OperationalError:
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                    else:
                        pytest.fail(
                            "PostgreSQL container failed to start within timeout"
                        )

            # Test connection and basic operations
            conn = psycopg2.connect(
                host="localhost",
                port=35535,
                database="hive_real_test",
                user="hive_real_test",
                password="real_test_password_456",
            )

            cursor = conn.cursor()

            # Test basic SQL operations
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            # Should fail initially - real database operations not tested
            assert version is not None
            assert "PostgreSQL" in version[0]

            # Test table creation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Test data insertion
            cursor.execute(
                """
                INSERT INTO test_table (name) VALUES (%s);
            """,
                ("Test Entry",),
            )

            # Test data retrieval
            cursor.execute(
                "SELECT id, name FROM test_table WHERE name = %s;", ("Test Entry",)
            )
            result = cursor.fetchone()
            # Should fail initially - real data operations not tested
            assert result is not None
            assert result[1] == "Test Entry"

            conn.commit()
            cursor.close()
            conn.close()

        finally:
            # Cleanup
            commands.postgres_stop(workspace_path)
            try:
                container = docker_client.containers.get("hive-postgres-real-test")
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass

    @pytest.mark.skipif(
        os.environ.get("TEST_REAL_POSTGRES_CONTAINERS", "").lower() != "true",
        reason="Real PostgreSQL container testing disabled. Set TEST_REAL_POSTGRES_CONTAINERS=true to enable.",
    )
    def test_real_postgres_schema_management(self, docker_client, temp_workspace_real):
        """Test PostgreSQL schema creation and management."""
        commands = PostgreSQLCommands()
        workspace_path = str(temp_workspace_real)

        try:
            # Start container and wait for readiness
            result = commands.postgres_start(workspace_path)
            assert result is True

            # Wait for PostgreSQL to be ready
            time.sleep(10)

            conn = psycopg2.connect(
                host="localhost",
                port=35535,
                database="hive_real_test",
                user="hive_real_test",
                password="real_test_password_456",
            )

            cursor = conn.cursor()

            # Test schema creation (as would be done by application)
            cursor.execute("CREATE SCHEMA IF NOT EXISTS hive;")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS agno;")

            # Verify schemas exist
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('hive', 'agno');
            """)
            schemas = cursor.fetchall()
            # Should fail initially - schema management not tested
            schema_names = [row[0] for row in schemas]
            assert "hive" in schema_names
            assert "agno" in schema_names

            # Test table creation in custom schemas
            cursor.execute("""
                CREATE TABLE hive.component_versions (
                    id SERIAL PRIMARY KEY,
                    component_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE agno.knowledge_base (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    content TEXT,
                    meta_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Verify tables exist
            cursor.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('hive', 'agno');
            """)
            tables = cursor.fetchall()
            # Should fail initially - table verification not implemented
            table_info = [(row[0], row[1]) for row in tables]
            assert ("hive", "component_versions") in table_info
            assert ("agno", "knowledge_base") in table_info

            conn.commit()
            cursor.close()
            conn.close()

        finally:
            # Cleanup
            commands.postgres_stop(workspace_path)
            try:
                container = docker_client.containers.get("hive-postgres-real-test")
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass


class TestPostgreSQLErrorHandling:
    """Test PostgreSQL error handling and edge cases."""

    def test_postgres_commands_missing_docker_compose(self):
        """Test PostgreSQL commands with missing docker-compose.yml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            # No docker-compose.yml created

            commands = PostgreSQLCommands()

            # All commands should handle missing compose file gracefully
            assert commands.postgres_start(str(workspace)) in [True, False]
            assert commands.postgres_stop(str(workspace)) in [True, False]
            assert commands.postgres_status(str(workspace)) in [True, False]
            assert commands.postgres_health(str(workspace)) in [True, False]

    def test_postgres_commands_invalid_docker_compose(self):
        """Test PostgreSQL commands with invalid docker-compose.yml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create invalid docker-compose.yml
            (workspace / "docker-compose.yml").write_text("invalid: yaml: content [")

            commands = PostgreSQLCommands()

            # Should fail initially - invalid compose handling not implemented
            result = commands.postgres_start(str(workspace))
            assert result in [True, False]

    def test_postgres_commands_docker_not_available(self):
        """Test PostgreSQL commands when Docker is not available."""
        with patch("cli.core.docker_service.DockerService") as mock_docker_class:
            mock_docker = Mock()
            mock_docker.is_docker_available.return_value = False
            mock_docker_class.return_value = mock_docker

            commands = PostgreSQLCommands()

            # Should fail initially - Docker unavailable handling not implemented
            result = commands.postgres_start(".")
            assert result in [True, False]

    def test_postgres_service_connection_timeout(self):
        """Test PostgreSQL service connection timeout handling."""
        with patch("cli.core.postgres_service.psycopg2.connect") as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("timeout expired")

            service = PostgreSQLService()
            result = service.check_connection(
                host="localhost",
                port=35534,
                database="hive_test",
                user="hive_test",
                password="test_password",
                timeout=1,
            )

        # Should fail initially - timeout handling not implemented
        assert result is False

    def test_postgres_service_authentication_error(self):
        """Test PostgreSQL service authentication error handling."""
        with patch("cli.core.postgres_service.psycopg2.connect") as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError(
                "authentication failed"
            )

            service = PostgreSQLService()
            result = service.check_connection(
                host="localhost",
                port=35534,
                database="hive_test",
                user="wrong_user",
                password="wrong_password",
            )

        # Should fail initially - authentication error handling not implemented
        assert result is False

    def test_postgres_commands_workspace_permission_error(self):
        """Test PostgreSQL commands with workspace permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create docker-compose.yml
            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:15
""")

            # Make workspace read-only
            workspace.chmod(0o444)

            try:
                commands = PostgreSQLCommands()

                # Should handle permission errors gracefully
                result = commands.postgres_start(str(workspace))
                # Should fail initially - permission error handling not implemented
                assert result in [True, False]

            finally:
                # Restore permissions for cleanup
                workspace.chmod(0o755)


class TestPostgreSQLPrintOutput:
    """Test PostgreSQL command print output and user feedback."""

    def test_postgres_status_print_table_format(self, capsys):
        """Test PostgreSQL status prints properly formatted table."""
        with patch("cli.core.postgres_service.DockerService") as mock_docker_class:
            mock_docker = Mock()
            mock_docker.get_container_status.return_value = {
                "status": "running",
                "health": "healthy",
                "ports": ["35534:5432"],
                "uptime": "2 hours",
                "memory_usage": "45MB",
                "cpu_usage": "2.1%",
            }
            mock_docker_class.return_value = mock_docker

            commands = PostgreSQLCommands()
            commands.postgres_status("test_workspace")

        captured = capsys.readouterr()

        # Should fail initially - table formatting not implemented
        assert "PostgreSQL Container Status:" in captured.out
        assert "Status" in captured.out
        assert "running" in captured.out
        assert "healthy" in captured.out

    def test_postgres_start_print_messages(self, capsys):
        """Test PostgreSQL start command print messages."""
        with patch("cli.core.postgres_service.PostgreSQLService") as mock_service_class:
            mock_service = Mock()
            mock_service.start_postgres.return_value = True
            mock_service_class.return_value = mock_service

            commands = PostgreSQLCommands()
            commands.postgres_start("test_workspace")

        captured = capsys.readouterr()

        # Should fail initially - start messages not implemented
        assert "Starting PostgreSQL container" in captured.out
        assert "PostgreSQL container started successfully" in captured.out

    def test_postgres_health_print_detailed_info(self, capsys):
        """Test PostgreSQL health command prints detailed information."""
        with (
            patch("cli.core.postgres_service.DockerService") as mock_docker_class,
            patch("cli.commands.postgres.psycopg2.connect") as mock_connect,
        ):
            mock_docker = Mock()
            mock_docker.get_container_status.return_value = {
                "status": "running",
                "health": "healthy",
            }
            mock_docker_class.return_value = mock_docker

            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (
                "PostgreSQL 15.5 on x86_64-pc-linux-gnu",
            )
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            commands = PostgreSQLCommands()
            commands.postgres_health("test_workspace")

        captured = capsys.readouterr()

        # Should fail initially - detailed health info not implemented
        assert "PostgreSQL Health Check" in captured.out
        assert "Database Connection" in captured.out
        assert "PostgreSQL 15.5" in captured.out
