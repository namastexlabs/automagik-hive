#!/usr/bin/env python3
"""
Tests for Docker Compose Service (T1.7: Foundational Services Containerization).

Tests PostgreSQL container implementation and credential management
within Docker Compose strategy.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from docker.lib.compose_service import DockerComposeService
from lib.auth.credential_service import CredentialService


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def compose_service(temp_workspace):
    """Create DockerComposeService instance with temp workspace."""
    return DockerComposeService(temp_workspace)


class TestDockerComposeService:
    """Test Docker Compose Service functionality."""

    def test_init_with_workspace_path(self, temp_workspace):
        """Test service initialization with workspace path."""
        service = DockerComposeService(temp_workspace)
        assert service.workspace_path == temp_workspace
        assert isinstance(service.credential_service, CredentialService)

    def test_init_default_workspace(self):
        """Test service initialization with default workspace."""
        service = DockerComposeService()
        assert service.workspace_path == Path.cwd()

    def test_generate_postgresql_service_template_default(self, compose_service):
        """Test PostgreSQL service template generation with defaults."""
        service_config = compose_service.generate_postgresql_service_template()

        # Check basic structure
        assert service_config["image"] == "agnohq/pgvector:16"
        assert service_config["container_name"] == "hive-postgres"
        assert service_config["restart"] == "unless-stopped"

        # Check environment variables
        env_vars = service_config["environment"]
        assert "POSTGRES_USER=${POSTGRES_USER}" in env_vars
        assert "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" in env_vars
        assert "POSTGRES_DB=hive" in env_vars
        assert "PGDATA=/var/lib/postgresql/data/pgdata" in env_vars

        # Check port mapping
        assert "5532:5432" in service_config["ports"]

        # Check volumes
        assert "./data/postgres:/var/lib/postgresql/data" in service_config["volumes"]

        # Check health check
        healthcheck = service_config["healthcheck"]
        assert healthcheck["test"] == ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
        assert healthcheck["interval"] == "10s"
        assert healthcheck["retries"] == 5

        # Check command with PostgreSQL optimizations
        command = service_config["command"]
        assert "postgres" in command
        assert "-c" in command
        assert "max_connections=200" in command
        assert "shared_buffers=256MB" in command

    def test_generate_postgresql_service_template_custom(self, compose_service):
        """Test PostgreSQL service template with custom parameters."""
        service_config = compose_service.generate_postgresql_service_template(
            external_port=5433, database="custom_db", volume_path="./custom/data"
        )

        # Check custom parameters
        assert "5433:5432" in service_config["ports"]
        assert "POSTGRES_DB=custom_db" in service_config["environment"]
        assert "./custom/data:/var/lib/postgresql/data" in service_config["volumes"]

    def test_generate_complete_docker_compose_template_postgres_only(
        self, compose_service
    ):
        """Test complete Docker Compose template with PostgreSQL only."""
        compose_config = compose_service.generate_complete_docker_compose_template(
            postgres_port=5532, postgres_database="hive", include_app_service=False
        )

        # Check structure
        assert "services" in compose_config
        assert "networks" in compose_config
        assert "volumes" in compose_config

        # Check PostgreSQL service present
        assert "postgres" in compose_config["services"]
        postgres_service = compose_config["services"]["postgres"]
        assert postgres_service["image"] == "agnohq/pgvector:16"

        # Check app service not present
        assert "app" not in compose_config["services"]

        # Check networks configuration
        networks = compose_config["networks"]
        assert "app_network" in networks
        assert networks["app_network"]["driver"] == "bridge"

        # Check volumes configuration
        volumes = compose_config["volumes"]
        assert "app_logs" in volumes
        assert "app_data" in volumes

    def test_generate_complete_docker_compose_template_with_app(self, compose_service):
        """Test complete Docker Compose template with application service."""
        compose_config = compose_service.generate_complete_docker_compose_template(
            postgres_port=5532, postgres_database="hive", include_app_service=True
        )

        # Check both services present
        assert "postgres" in compose_config["services"]
        assert "app" in compose_config["services"]

        # Check app service configuration
        app_service = compose_config["services"]["app"]
        assert app_service["container_name"] == "hive-agents"
        assert "build" in app_service
        assert "depends_on" in app_service
        assert app_service["depends_on"]["postgres"]["condition"] == "service_healthy"

    @patch.object(CredentialService, "setup_complete_credentials")
    def test_generate_workspace_environment_file_with_credentials(
        self, mock_credentials, compose_service
    ):
        """Test environment file generation with provided credentials."""
        # Mock credentials
        mock_creds = {
            "postgres_user": "test_user",
            "postgres_password": "test_pass",
            "postgres_url": "postgresql+psycopg://test_user:test_pass@localhost:5532/hive",
            "api_key": "hive_test_api_key_12345",
        }

        env_content = compose_service.generate_workspace_environment_file(
            credentials=mock_creds,
            postgres_port=5532,
            postgres_database="hive",
            api_port=8886,
        )

        # Verify credentials are in environment file
        assert "POSTGRES_USER=test_user" in env_content
        assert "POSTGRES_PASSWORD=test_pass" in env_content
        assert "POSTGRES_DB=hive" in env_content
        assert (
            "HIVE_DATABASE_URL=postgresql+psycopg://test_user:test_pass@localhost:5532/hive"
            in env_content
        )
        assert "HIVE_API_KEY=hive_test_api_key_12345" in env_content

        # Check API configuration
        assert "HIVE_API_PORT=8886" in env_content
        assert "HIVE_API_HOST=0.0.0.0" in env_content

        # Check placeholder API keys are present
        assert "OPENAI_API_KEY=your-openai-api-key-here" in env_content
        assert "ANTHROPIC_API_KEY=your-anthropic-api-key-here" in env_content

        # Check UID/GID handling
        if hasattr(os, "getuid"):
            assert f"POSTGRES_UID={os.getuid()}" in env_content
            assert f"POSTGRES_GID={os.getgid()}" in env_content
        else:
            assert "POSTGRES_UID=1000" in env_content
            assert "POSTGRES_GID=1000" in env_content

    @patch.object(CredentialService, "setup_complete_credentials")
    def test_generate_workspace_environment_file_generate_credentials(
        self, mock_credentials, compose_service
    ):
        """Test environment file generation with credential generation."""
        # Mock credential generation
        mock_creds = {
            "postgres_user": "generated_user",
            "postgres_password": "generated_pass",
            "postgres_url": "postgresql+psycopg://generated_user:generated_pass@localhost:5532/hive",
            "api_key": "hive_generated_api_key",
        }
        mock_credentials.return_value = mock_creds

        env_content = compose_service.generate_workspace_environment_file(
            credentials=None,  # Should trigger generation
            postgres_port=5532,
            postgres_database="hive",
            api_port=8886,
        )

        # Verify credential service was called
        mock_credentials.assert_called_once_with(
            postgres_host="localhost", postgres_port=5532, postgres_database="hive"
        )

        # Verify generated credentials in output
        assert "POSTGRES_USER=generated_user" in env_content
        assert "HIVE_API_KEY=hive_generated_api_key" in env_content

    def test_save_docker_compose_template(self, compose_service, temp_workspace):
        """Test saving Docker Compose template to file."""
        # Generate test config
        compose_config = {
            "services": {
                "postgres": {"image": "agnohq/pgvector:16", "ports": ["5532:5432"]}
            },
            "networks": {"app_network": {"driver": "bridge"}},
        }

        # Save template
        output_path = temp_workspace / "test-compose.yml"
        saved_path = compose_service.save_docker_compose_template(
            compose_config, output_path
        )

        # Verify file was saved
        assert saved_path == output_path
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["services"]["postgres"]["image"] == "agnohq/pgvector:16"
        assert saved_config["networks"]["app_network"]["driver"] == "bridge"

    def test_save_docker_compose_template_default_path(
        self, compose_service, temp_workspace
    ):
        """Test saving Docker Compose template with default path."""
        compose_config = {"services": {"test": {"image": "test"}}}

        saved_path = compose_service.save_docker_compose_template(compose_config)

        expected_path = temp_workspace / "docker-compose.yml"
        assert saved_path == expected_path
        assert expected_path.exists()

    def test_save_environment_file(self, compose_service, temp_workspace):
        """Test saving environment file with secure permissions."""
        env_content = """POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
HIVE_API_KEY=hive_test_key"""

        # Save environment file
        output_path = temp_workspace / "test.env"
        saved_path = compose_service.save_environment_file(env_content, output_path)

        # Verify file was saved
        assert saved_path == output_path
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            saved_content = f.read()
        assert saved_content == env_content

        # Verify secure permissions (600)
        file_permissions = output_path.stat().st_mode & 0o777
        assert file_permissions == 0o600

    def test_save_environment_file_default_path(self, compose_service, temp_workspace):
        """Test saving environment file with default path."""
        env_content = "TEST=value"

        saved_path = compose_service.save_environment_file(env_content)

        expected_path = temp_workspace / ".env"
        assert saved_path == expected_path
        assert expected_path.exists()

    def test_create_data_directories(self, compose_service, temp_workspace):
        """Test creating PostgreSQL data directories."""
        data_path = "./data/postgres"

        created_dir = compose_service.create_data_directories(data_path)

        expected_dir = temp_workspace / "data/postgres"
        assert created_dir == expected_dir
        assert expected_dir.exists()
        assert expected_dir.is_dir()

        # Check permissions (755)
        dir_permissions = expected_dir.stat().st_mode & 0o777
        assert dir_permissions == 0o755

    def test_create_data_directories_already_exists(
        self, compose_service, temp_workspace
    ):
        """Test creating data directories when they already exist."""
        data_path = "./data/postgres"
        expected_dir = temp_workspace / "data/postgres"

        # Create directory first
        expected_dir.mkdir(parents=True, exist_ok=True)

        # Should not raise error
        created_dir = compose_service.create_data_directories(data_path)
        assert created_dir == expected_dir
        assert expected_dir.exists()

    def test_update_gitignore_for_security_new_file(
        self, compose_service, temp_workspace
    ):
        """Test updating .gitignore for security with new file."""
        gitignore_path = temp_workspace / ".gitignore"

        compose_service.update_gitignore_for_security(gitignore_path)

        # Verify file was created
        assert gitignore_path.exists()

        # Verify security exclusions were added
        with open(gitignore_path) as f:
            content = f.read()

        assert "UVX Automagik Hive - Security Exclusions" in content
        assert ".env" in content
        assert "data/postgres/" in content
        assert "__pycache__/" in content

    def test_update_gitignore_for_security_existing_file(
        self, compose_service, temp_workspace
    ):
        """Test updating .gitignore for security with existing file."""
        gitignore_path = temp_workspace / ".gitignore"

        # Create existing .gitignore
        existing_content = "*.pyc\n__pycache__/\n"
        with open(gitignore_path, "w") as f:
            f.write(existing_content)

        compose_service.update_gitignore_for_security(gitignore_path)

        # Verify original content preserved and new content added
        with open(gitignore_path) as f:
            content = f.read()

        assert existing_content.strip() in content
        assert "UVX Automagik Hive - Security Exclusions" in content
        assert ".env" in content

    def test_update_gitignore_for_security_already_updated(
        self, compose_service, temp_workspace
    ):
        """Test updating .gitignore when already contains UVX exclusions."""
        gitignore_path = temp_workspace / ".gitignore"

        # Create .gitignore with UVX exclusions
        existing_content = """*.pyc
# UVX Automagik Hive - Security Exclusions
.env
"""
        with open(gitignore_path, "w") as f:
            f.write(existing_content)

        original_size = gitignore_path.stat().st_size

        compose_service.update_gitignore_for_security(gitignore_path)

        # Verify file size didn't change (no duplicates added)
        assert gitignore_path.stat().st_size == original_size

    @patch.object(CredentialService, "setup_complete_credentials")
    def test_setup_foundational_services_complete(
        self, mock_credentials, compose_service, temp_workspace
    ):
        """Test complete foundational services setup."""
        # Mock credentials
        mock_creds = {
            "postgres_user": "setup_user",
            "postgres_password": "setup_pass",
            "postgres_url": "postgresql+psycopg://setup_user:setup_pass@localhost:5532/hive",
            "api_key": "hive_setup_key",
        }
        mock_credentials.return_value = mock_creds

        # Run setup
        compose_path, env_path, data_dir = compose_service.setup_foundational_services(
            postgres_port=5532,
            postgres_database="hive",
            api_port=8886,
            include_app_service=False,
        )

        # Verify credential service was called
        mock_credentials.assert_called_once_with(
            postgres_host="localhost", postgres_port=5532, postgres_database="hive"
        )

        # Verify files were created
        assert compose_path.exists()
        assert env_path.exists()
        assert data_dir.exists()

        # Verify docker-compose.yml content
        with open(compose_path) as f:
            compose_config = yaml.safe_load(f)

        assert "postgres" in compose_config["services"]
        postgres_service = compose_config["services"]["postgres"]
        assert postgres_service["image"] == "agnohq/pgvector:16"
        assert "5532:5432" in postgres_service["ports"]

        # Verify .env content
        with open(env_path) as f:
            env_content = f.read()

        assert "POSTGRES_USER=setup_user" in env_content
        assert "HIVE_API_KEY=hive_setup_key" in env_content

        # Verify .env permissions
        env_permissions = env_path.stat().st_mode & 0o777
        assert env_permissions == 0o600

        # Verify data directory
        assert data_dir.is_dir()
        data_permissions = data_dir.stat().st_mode & 0o777
        assert data_permissions == 0o755

        # Verify .gitignore was updated
        gitignore_path = temp_workspace / ".gitignore"
        assert gitignore_path.exists()
        with open(gitignore_path) as f:
            gitignore_content = f.read()
        assert "UVX Automagik Hive - Security Exclusions" in gitignore_content

    def test_setup_foundational_services_custom_parameters(
        self, compose_service, temp_workspace
    ):
        """Test foundational services setup with custom parameters."""
        with patch.object(
            CredentialService, "setup_complete_credentials"
        ) as mock_creds:
            mock_creds.return_value = {
                "postgres_user": "custom_user",
                "postgres_password": "custom_pass",
                "postgres_url": "postgresql+psycopg://custom_user:custom_pass@localhost:5433/custom_db",
                "api_key": "hive_custom_key",
            }

            compose_path, env_path, data_dir = (
                compose_service.setup_foundational_services(
                    postgres_port=5433,
                    postgres_database="custom_db",
                    api_port=8887,
                    include_app_service=True,
                )
            )

            # Verify custom parameters were used
            mock_creds.assert_called_once_with(
                postgres_host="localhost",
                postgres_port=5433,
                postgres_database="custom_db",
            )

            # Verify docker-compose.yml has custom port
            with open(compose_path) as f:
                compose_config = yaml.safe_load(f)

            postgres_service = compose_config["services"]["postgres"]
            assert "5433:5432" in postgres_service["ports"]

            # Verify app service included
            assert "app" in compose_config["services"]

            # Verify .env has custom values
            with open(env_path) as f:
                env_content = f.read()

            assert "POSTGRES_DB=custom_db" in env_content
            assert "HIVE_API_PORT=8887" in env_content


if __name__ == "__main__":
    pytest.main([__file__])
