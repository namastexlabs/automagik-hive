#!/usr/bin/env python3
"""Docker Compose Service for UVX Automagik Hive.

Implements T1.7: Foundational Services Containerization with PostgreSQL container
and credential management within Docker Compose strategy.

Key Features:
- PostgreSQL service definition with agnohq/pgvector:16
- Secure credential generation and integration
- Template generation for docker-compose.yml and .env files
- Health checks and volume persistence
- Cross-platform UID/GID handling
"""

import os
from pathlib import Path

import yaml

from lib.auth.credential_service import CredentialService
from lib.logging import logger


class DockerComposeService:
    """Service for Docker Compose template generation and management."""

    def __init__(self, workspace_path: Path | None = None) -> None:
        """Initialize Docker Compose service.

        Args:
            workspace_path: Path to workspace directory
        """
        self.workspace_path = workspace_path or Path.cwd()
        self.credential_service = CredentialService()

    def generate_postgresql_service_template(
        self,
        external_port: int = 5532,
        database: str = "hive",
        volume_path: str = "./data/postgres",
    ) -> dict:
        """Generate PostgreSQL service definition for Docker Compose template.

        Based on existing docker-compose.yml PostgreSQL service with:
        - agnohq/pgvector:16 image (same as production)
        - Port 5532 (external) → 5432 (container)
        - pgvector extensions for AI embeddings
        - Health checks with pg_isready
        - Volume persistence

        Args:
            external_port: External port mapping (default: 5532)
            database: Database name (default: hive)
            volume_path: Volume mount path (default: ./data/postgres)

        Returns:
            PostgreSQL service definition dictionary
        """
        logger.info(
            "Generating PostgreSQL service template",
            external_port=external_port,
            database=database,
        )

        service_config = {
            "image": "agnohq/pgvector:16",
            "container_name": "hive-postgres",
            "restart": "unless-stopped",
            "user": "${POSTGRES_UID:-1000}:${POSTGRES_GID:-1000}",
            "environment": [
                "POSTGRES_USER=${POSTGRES_USER}",
                "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}",
                f"POSTGRES_DB={database}",
                "PGDATA=/var/lib/postgresql/data/pgdata",
            ],
            "volumes": [f"{volume_path}:/var/lib/postgresql/data"],
            "command": [
                "postgres",
                "-c",
                "max_connections=200",
                "-c",
                "shared_buffers=256MB",
                "-c",
                "effective_cache_size=1GB",
            ],
            "ports": [f"{external_port}:5432"],
            "networks": ["app_network"],
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
            },
        }

        logger.info("PostgreSQL service template generated successfully")
        return service_config

    def generate_complete_docker_compose_template(
        self,
        postgres_port: int = 5532,
        postgres_database: str = "hive",
        include_app_service: bool = False,
    ) -> dict:
        """Generate complete Docker Compose template with PostgreSQL service.

        Based on existing docker-compose.yml patterns with foundational services:
        - PostgreSQL with pgvector extension
        - Networks and volumes configuration
        - Health checks and dependencies
        - Optional application service

        Args:
            postgres_port: PostgreSQL external port
            postgres_database: PostgreSQL database name
            include_app_service: Whether to include application service

        Returns:
            Complete Docker Compose configuration dictionary
        """
        logger.info(
            "Generating complete Docker Compose template",
            postgres_port=postgres_port,
            include_app=include_app_service,
        )

        # Base compose structure
        compose_config = {
            "services": {},
            "networks": {"app_network": {"driver": "bridge"}},
            "volumes": {
                "app_logs": {"driver": "local"},
                "app_data": {"driver": "local"},
            },
        }

        # Add PostgreSQL service (foundational)
        compose_config["services"]["postgres"] = (
            self.generate_postgresql_service_template(
                external_port=postgres_port, database=postgres_database
            )
        )

        # Optionally add application service (for complete setup)
        if include_app_service:
            compose_config["services"]["app"] = self._generate_app_service_template(
                postgres_port=postgres_port
            )

        logger.info("Complete Docker Compose template generated")
        return compose_config

    def _generate_app_service_template(self, postgres_port: int = 5532) -> dict:
        """Generate application service template (optional)."""
        return {
            "build": {
                "context": ".",
                "dockerfile": "Dockerfile",
                "args": {
                    "BUILD_VERSION": "${BUILD_VERSION:-latest}",
                    "API_PORT": "${HIVE_API_PORT:-8886}",
                },
                "target": "production",
            },
            "container_name": "hive-agents",
            "restart": "unless-stopped",
            "ports": ["${HIVE_API_PORT:-8886}:${HIVE_API_PORT:-8886}"],
            "environment": [
                "HIVE_DATABASE_URL=postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-hive}",
                "RUNTIME_ENV=prd",
                "HIVE_LOG_LEVEL=info",
                "HIVE_API_HOST=0.0.0.0",
                "HIVE_API_PORT=${HIVE_API_PORT:-8886}",
                "HIVE_API_WORKERS=${API_WORKERS:-4}",
                "PYTHONUNBUFFERED=1",
                "PYTHONDONTWRITEBYTECODE=1",
            ],
            "volumes": ["app_logs:/app/logs", "app_data:/app/data"],
            "depends_on": {"postgres": {"condition": "service_healthy"}},
            "networks": ["app_network"],
            "healthcheck": {
                "test": [
                    "CMD",
                    "curl",
                    "-f",
                    "http://localhost:${HIVE_API_PORT:-8886}/api/v1/health",
                ],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "60s",
            },
        }

    def generate_workspace_environment_file(
        self,
        credentials: dict[str, str] | None = None,
        postgres_port: int = 5532,
        postgres_database: str = "hive",
        api_port: int = 8886,
    ) -> str:
        """Generate .env file content for workspace with secure credentials.

        Integrates with existing credential management system to create
        complete environment configuration for Docker Compose.

        Args:
            credentials: Pre-generated credentials (optional)
            postgres_port: PostgreSQL port
            postgres_database: PostgreSQL database name
            api_port: API server port

        Returns:
            Complete .env file content as string
        """
        logger.info(
            "Generating workspace environment file",
            postgres_port=postgres_port,
            api_port=api_port,
        )

        # Generate credentials if not provided
        if not credentials:
            credentials = self.credential_service.setup_complete_credentials(
                postgres_host="localhost",
                postgres_port=postgres_port,
                postgres_database=postgres_database,
            )

        # Cross-platform UID/GID handling (like existing Makefile)
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        gid = os.getgid() if hasattr(os, "getgid") else 1000

        env_content = f"""# =============================================================================
# Automagik Hive Workspace Environment Configuration
# Generated by UVX CLI - DO NOT EDIT MANUALLY
# =============================================================================

# PostgreSQL Database Configuration
POSTGRES_USER={credentials["postgres_user"]}
POSTGRES_PASSWORD={credentials["postgres_password"]}
POSTGRES_DB={postgres_database}
POSTGRES_UID={uid}
POSTGRES_GID={gid}

# Database Connection
HIVE_DATABASE_URL={credentials["postgres_url"]}

# API Server Configuration
HIVE_API_PORT={api_port}
HIVE_API_HOST=0.0.0.0
HIVE_API_WORKERS=4
HIVE_API_KEY={credentials["api_key"]}

# Runtime Configuration
RUNTIME_ENV=dev
HIVE_LOG_LEVEL=info
HIVE_AUTH_DISABLED=false

# Build Configuration
BUILD_VERSION=latest
API_WORKERS=4

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# =============================================================================
# Add your AI provider API keys below:
# =============================================================================

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key-here

# XAI Configuration
XAI_API_KEY=your-xai-api-key-here

# =============================================================================
# Optional: External Services
# =============================================================================

# Twilio (SMS/WhatsApp)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# Evolution API (WhatsApp)
EVOLUTION_API_BASE_URL=your-evolution-api-url
EVOLUTION_API_KEY=your-evolution-api-key
EVOLUTION_API_INSTANCE=your-instance-name
"""

        logger.info("Workspace environment file content generated")
        return env_content

    def save_docker_compose_template(
        self, compose_config: dict, output_path: Path | None = None
    ) -> Path:
        """Save Docker Compose configuration to file.

        Args:
            compose_config: Docker Compose configuration dictionary
            output_path: Output file path (default: docker-compose.yml in workspace)

        Returns:
            Path to saved file
        """
        if not output_path:
            output_path = self.workspace_path / "docker-compose.yml"

        logger.info("Saving Docker Compose template", output_path=str(output_path))

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save YAML with proper formatting
        with open(output_path, "w") as f:
            yaml.dump(
                compose_config, f, default_flow_style=False, indent=2, sort_keys=False
            )

        logger.info("Docker Compose template saved successfully")
        return output_path

    def save_environment_file(
        self, env_content: str, output_path: Path | None = None
    ) -> Path:
        """Save environment file content to .env file.

        Args:
            env_content: Environment file content
            output_path: Output file path (default: .env in workspace)

        Returns:
            Path to saved file
        """
        if not output_path:
            output_path = self.workspace_path / ".env"

        logger.info("Saving environment file", output_path=str(output_path))

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save with proper permissions (600 for security)
        with open(output_path, "w") as f:
            f.write(env_content)

        # Set secure permissions (user read/write only)
        output_path.chmod(0o600)

        logger.info("Environment file saved with secure permissions")
        return output_path

    def create_data_directories(
        self, postgres_data_path: str = "./data/postgres"
    ) -> Path:
        """Create required data directories for PostgreSQL persistence.

        Args:
            postgres_data_path: Path for PostgreSQL data directory

        Returns:
            Path to created postgres data directory
        """
        data_dir = self.workspace_path / postgres_data_path.lstrip("./")
        logger.info("Creating PostgreSQL data directory", path=str(data_dir))

        # Create directory with proper permissions
        data_dir.mkdir(parents=True, exist_ok=True)

        # Set appropriate permissions for PostgreSQL
        try:
            data_dir.chmod(0o755)
            logger.info("PostgreSQL data directory created with proper permissions")
        except OSError as e:
            logger.warning("Could not set directory permissions", error=str(e))

        return data_dir

    def update_gitignore_for_security(self, gitignore_path: Path | None = None) -> None:
        """Update .gitignore to exclude sensitive files.

        Args:
            gitignore_path: Path to .gitignore file (default: .gitignore in workspace)
        """
        if not gitignore_path:
            gitignore_path = self.workspace_path / ".gitignore"

        logger.info("Updating .gitignore for security", path=str(gitignore_path))

        # Security exclusions to add
        security_exclusions = [
            "\n# =============================================================================",
            "# UVX Automagik Hive - Security Exclusions",
            "# =============================================================================",
            "",
            "# Environment files with credentials",
            ".env",
            ".env.local",
            ".env.*.local",
            "",
            "# PostgreSQL data directories",
            "data/postgres/",
            "data/postgres-*/",
            "",
            "# Docker volumes and logs",
            "logs/",
            "*.log",
            "",
            "# Temporary and cache files",
            ".DS_Store",
            "Thumbs.db",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "wheels/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            "",
        ]

        # Read existing .gitignore content
        existing_content = ""
        if gitignore_path.exists():
            with open(gitignore_path) as f:
                existing_content = f.read()

        # Check if UVX security section already exists
        if "UVX Automagik Hive - Security Exclusions" in existing_content:
            logger.info(".gitignore already contains UVX security exclusions")
            return

        # Append security exclusions
        with open(gitignore_path, "a") as f:
            f.write("\n".join(security_exclusions))

        logger.info(".gitignore updated with security exclusions")

    def setup_foundational_services(
        self,
        postgres_port: int = 5532,
        postgres_database: str = "hive",
        api_port: int = 8886,
        include_app_service: bool = False,
    ) -> tuple[Path, Path, Path]:
        """Complete setup of foundational services containerization.

        This is the main method for T1.7 implementation, providing:
        - PostgreSQL container service definition
        - Secure credential generation and management
        - Docker Compose template generation
        - Environment file creation
        - Data directory setup
        - Security configurations

        Args:
            postgres_port: PostgreSQL external port (default: 5532)
            postgres_database: PostgreSQL database name (default: hive)
            api_port: API server port (default: 8886)
            include_app_service: Include application service in compose

        Returns:
            Tuple of (docker-compose.yml path, .env path, data directory path)
        """
        logger.info("Setting up foundational services containerization")

        # 1. Generate secure credentials
        logger.info("Generating secure credentials for workspace")
        credentials = self.credential_service.setup_complete_credentials(
            postgres_host="localhost",
            postgres_port=postgres_port,
            postgres_database=postgres_database,
        )

        # 2. Generate Docker Compose template
        logger.info("Generating Docker Compose template")
        compose_config = self.generate_complete_docker_compose_template(
            postgres_port=postgres_port,
            postgres_database=postgres_database,
            include_app_service=include_app_service,
        )

        # 3. Generate environment file
        logger.info("Generating workspace environment file")
        env_content = self.generate_workspace_environment_file(
            credentials=credentials,
            postgres_port=postgres_port,
            postgres_database=postgres_database,
            api_port=api_port,
        )

        # 4. Create data directories
        logger.info("Creating PostgreSQL data directories")
        data_dir = self.create_data_directories()

        # 5. Save configuration files
        compose_path = self.save_docker_compose_template(compose_config)
        env_path = self.save_environment_file(env_content)

        # 6. Update .gitignore for security
        self.update_gitignore_for_security()

        logger.info(
            "Foundational services containerization setup complete",
            compose_path=str(compose_path),
            env_path=str(env_path),
            data_path=str(data_dir),
        )

        return compose_path, env_path, data_dir
