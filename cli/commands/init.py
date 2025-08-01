"""Workspace Initialization CLI Commands for Automagik Hive.

This module provides the --init command implementation for interactive
workspace creation with API key collection and Docker Compose setup.
"""

import base64
import contextlib
import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path

from cli.core.docker_service import DockerService
from cli.core.mcp_config_manager import MCPConfigManager
from cli.core.postgres_service import PostgreSQLService
from cli.core.security_utils import (
    SecurityError,
    secure_resolve_workspace,
    secure_subprocess_call,
)


class InitCommands:
    """Workspace initialization CLI command implementations.

    Provides interactive workspace creation with secure credential
    generation, API key collection, and Docker Compose setup.
    """

    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()
        self.mcp_config_manager = MCPConfigManager()

    def init_workspace(self, workspace_name: str | None = None) -> bool:
        """Initialize a new workspace with enhanced interactive setup and error handling.

        Args:
            workspace_name: Optional workspace name/path

        Returns:
            True if initialization successful, False otherwise
        """
        # Display welcome message

        current_step = 0

        try:
            # Step 1: Determine workspace path
            current_step += 1
            workspace_path = self._get_workspace_path(workspace_name)
            if not workspace_path:
                return self._handle_initialization_failure(
                    "Workspace path validation failed", current_step
                )

            # Step 2: Create workspace directory
            current_step += 1
            if not self._create_workspace_directory(workspace_path):
                return self._handle_initialization_failure(
                    "Failed to create workspace directory", current_step
                )

            # Step 3: Interactive PostgreSQL setup choice
            current_step += 1
            postgres_config = self._setup_postgres_interactively()
            if not postgres_config:
                return self._handle_initialization_failure(
                    "PostgreSQL setup cancelled or failed", current_step
                )

            # Step 4: Container services selection
            current_step += 1
            container_services = self._select_container_services()

            # Step 5: Generate secure credentials
            current_step += 1
            credentials = self._generate_credentials(postgres_config)

            # Step 6: Collect API keys interactively
            current_step += 1
            api_keys = self._collect_api_keys()

            # Step 7: Create workspace files and containers
            current_step += 1
            if not self._create_workspace_files(
                workspace_path,
                credentials,
                api_keys,
                postgres_config,
                container_services,
            ):
                return self._handle_initialization_failure(
                    "Failed to create workspace files", current_step
                )

            # Step 8: Create data directories
            current_step += 1
            self._create_data_directories(workspace_path, container_services)

            # Step 8.5: Start all selected services
            current_step += 1
            self._start_docker_containers(
                workspace_path, container_services, postgres_config
            )

            # Show service startup instructions
            for service in container_services:
                if (
                    service == "postgres" and postgres_config["type"] == "docker"
                ) or service in {"agent", "genie"}:
                    pass

            # Step 9: Comprehensive workspace validation
            current_step += 1
            is_valid, success_messages, error_messages = (
                self.docker_service.validate_workspace_after_creation(workspace_path)
            )

            # Display validation results
            for _message in success_messages:
                pass

            for _message in error_messages:
                pass

            if not is_valid:
                pass

            # Step 10: Enhanced success message with next steps
            current_step += 1
            self._show_enhanced_success_message(
                workspace_path, container_services, is_valid
            )

            return True

        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def _create_workspace_directory(self, workspace_path: Path) -> bool:
        """Create workspace directory with enhanced error handling."""
        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            return False
        except OSError:
            return False
        except Exception:
            return False

    def _handle_initialization_failure(self, reason: str, step: int) -> bool:
        """Handle initialization failure with helpful recovery suggestions."""
        if (
            "path" in reason.lower()
            or "docker" in reason.lower()
            or "postgres" in reason.lower()
            or "permission" in reason.lower()
        ):
            pass
        else:
            pass

        return False

    def _get_workspace_path(self, workspace_name: str | None) -> Path | None:
        """Get and validate workspace path with enhanced cross-platform support."""
        try:
            if workspace_name:
                # Secure workspace path validation
                workspace_path = secure_resolve_workspace(workspace_name)
            else:
                # Interactive workspace name input with platform-specific examples
                self._get_platform_specific_example()

                while True:
                    name = input("Workspace path: ").strip()
                    if not name:
                        continue
                    try:
                        # Secure validation of user input
                        workspace_path = secure_resolve_workspace(name)
                        break
                    except SecurityError:
                        continue

            # Enhanced directory existence check
            if workspace_path.exists():
                if any(workspace_path.iterdir()):
                    # Check for permission issues with existing files
                    self._check_and_fix_permissions(workspace_path)
                else:
                    pass

            return workspace_path
        except SecurityError:
            return None

    def _get_platform_specific_example(self) -> str:
        """Get platform-specific path example for user guidance."""
        import platform

        system = platform.system().lower()

        if system == "windows":
            return "C:\\Projects\\my-hive-workspace or .\\my-workspace"
        if system == "darwin":
            return "~/Documents/my-hive-workspace or ./my-workspace"
        # Linux and others
        return "~/workspace/my-hive-workspace or ./my-workspace"

    def _select_container_services(self) -> list[str]:
        """Interactive container services selection."""
        while True:
            try:
                choice = input("Enter your choice (1-3): ").strip()

                if choice == "1":
                    return ["postgres"]
                if choice == "2":
                    return ["postgres", "agent", "genie"]
                if choice == "3":
                    return self._custom_service_selection()

            except (EOFError, KeyboardInterrupt):
                return ["postgres"]  # Default to basic PostgreSQL

    def _custom_service_selection(self) -> list[str]:
        """Custom service selection with individual choices."""
        services = []

        # PostgreSQL is always included
        services.append("postgres")

        # Agent development environment
        try:
            agent_choice = (
                input("🤖 Agent Development Environment? (y/N): ").strip().lower()
            )
            if agent_choice == "y":
                services.append("agent")
        except (EOFError, KeyboardInterrupt):
            pass

        # Genie development assistant service
        try:
            genie_choice = (
                input("🧞 Genie Development Assistant? (y/N): ").strip().lower()
            )
            if genie_choice == "y":
                services.append("genie")
        except (EOFError, KeyboardInterrupt):
            pass

        return services

    def _check_and_fix_permissions(self, workspace_path: Path):
        """Check and fix permission issues with existing workspace files."""
        try:
            # Check if data directory exists and has permission issues
            data_path = workspace_path / "data"
            if data_path.exists():
                # Try to write a test file to check permissions
                test_file = data_path / ".permission_test"
                try:
                    test_file.touch()
                    test_file.unlink()  # Remove test file
                except PermissionError:
                    # Automatically attempt to fix permissions
                    try:
                        # SECURITY: Use secure subprocess call with validation
                        uid = os.getuid() if hasattr(os, "getuid") else 1000
                        gid = os.getgid() if hasattr(os, "getgid") else 1000

                        # Validate the data path before using it in subprocess
                        validated_data_path = secure_resolve_workspace(str(data_path))

                        result = secure_subprocess_call(
                            [
                                "sudo",
                                "chown",
                                "-R",
                                f"{uid}:{gid}",
                                str(validated_data_path),
                            ]
                        )

                        if result.returncode == 0:
                            pass
                        else:
                            pass
                    except (SecurityError, subprocess.SubprocessError):
                        pass
                    except Exception:
                        pass

        except Exception:
            pass

    def _setup_postgres_interactively(self) -> dict[str, str] | None:
        """Interactive PostgreSQL setup with user choice."""
        while True:
            try:
                choice = input("Enter your choice (1-3): ").strip()

                if choice == "1":
                    return self._setup_docker_postgres()
                if choice == "2":
                    return self._setup_external_postgres()
                if choice == "3":
                    return {
                        "type": "manual",
                        "database_url": "postgresql+psycopg://user:pass@localhost:5432/hive",
                    }

            except (EOFError, KeyboardInterrupt):
                return None

    def _setup_docker_postgres(self) -> dict[str, str] | None:
        """Set up Docker PostgreSQL with automatic configuration."""
        # Check Docker availability
        if not self._check_docker_setup():
            return None

        return {
            "type": "docker",
            "image": "agnohq/pgvector:16",
            "port": "5532",
            "database": "hive",
        }

    def _setup_external_postgres(self) -> dict[str, str] | None:
        """Set up external PostgreSQL with user-provided connection details."""
        try:
            # Collect connection details
            host = (
                input("PostgreSQL Host (default: localhost): ").strip() or "localhost"
            )
            port = input("PostgreSQL Port (default: 5432): ").strip() or "5432"

            # Validate port
            try:
                port_int = int(port)
                if not (1 <= port_int <= 65535):
                    raise ValueError("Port must be between 1-65535")
            except ValueError:
                return None

            database = input("Database Name (default: hive): ").strip() or "hive"
            username = input("Username: ").strip()

            if not username:
                return None

            import getpass

            password = getpass.getpass("Password: ")

            # Build connection URL
            database_url = (
                f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
            )

            # Test connection
            if self._test_postgres_connection(database_url):
                return {
                    "type": "external",
                    "database_url": database_url,
                    "host": host,
                    "port": port,
                    "database": database,
                    "username": username,
                }
            return None

        except (EOFError, KeyboardInterrupt):
            return None

    def _test_postgres_connection(self, database_url: str) -> bool:
        """Test PostgreSQL connection."""
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def _check_docker_setup(self) -> bool:
        """Check Docker availability and setup with enhanced cross-platform detection."""
        # Get comprehensive Docker status
        docker_check = self.docker_service.comprehensive_docker_check()

        # Display platform information
        docker_check["platform"]

        # Check WSL if on Linux
        if docker_check["wsl"]["detected"]:
            pass

        # Check Docker installation
        docker_status = docker_check["docker"]
        if docker_status["available"]:
            if docker_status["version"]:
                pass
        else:
            self._show_enhanced_docker_install_instructions(
                docker_check["installation_guide"]
            )
            return False

        # Check Docker daemon
        daemon_status = docker_check["daemon"]
        if daemon_status["running"]:
            # Show daemon info if available
            daemon_info = daemon_status.get("info", {})
            if daemon_info:
                if "Server Version" in daemon_info:
                    pass
                if "Containers" in daemon_info:
                    pass
                if "Images" in daemon_info:
                    pass
        else:
            self._show_daemon_troubleshooting(docker_check)
            return False

        # Check Docker Compose
        compose_status = docker_check["compose"]
        if compose_status["available"]:
            if compose_status["version"]:
                pass
        else:
            return False

        return True

    def _show_enhanced_docker_install_instructions(self, installation_guide: dict):
        """Show enhanced platform-specific Docker installation instructions."""
        for _i, _step in enumerate(installation_guide["post_install"], 1):
            pass

    def _show_daemon_troubleshooting(self, docker_check: dict):
        """Show Docker daemon troubleshooting guidance."""
        platform_system = docker_check["platform"]["system"].lower()

        if platform_system in {"windows", "darwin"}:
            pass

        elif platform_system == "linux":
            if docker_check["wsl"]["detected"]:
                pass
            else:
                pass

    def _generate_credentials(self, postgres_config: dict[str, str]) -> dict[str, str]:
        """Generate secure credentials for the workspace."""
        # Generate Hive API key (hive_ + 32 char secure token)
        api_key_token = self._generate_secure_string(32)
        hive_api_key = f"hive_{api_key_token}"

        if postgres_config["type"] == "docker":
            # Generate PostgreSQL credentials for Docker setup
            postgres_user = self._generate_secure_string(16)
            postgres_password = self._generate_secure_string(16)
            database_url = f"postgresql+psycopg://{postgres_user}:{postgres_password}@localhost:{postgres_config['port']}/{postgres_config['database']}"

            return {
                "postgres_user": postgres_user,
                "postgres_password": postgres_password,
                "database_url": database_url,
                "hive_api_key": hive_api_key,
            }
        if postgres_config["type"] == "external":
            # Use provided external PostgreSQL connection
            return {
                "database_url": postgres_config["database_url"],
                "hive_api_key": hive_api_key,
            }
        # manual setup
        # Placeholder credentials for manual configuration
        return {
            "database_url": postgres_config["database_url"],
            "hive_api_key": hive_api_key,
        }

    # NOTE: _convert_to_container_credentials removed - focusing on MCP configuration

    # NOTE: _convert_to_container_credentials method removed for MCP configuration focus

    def _generate_secure_string(self, length: int) -> str:
        """Generate cryptographically secure random string."""
        # Use URL-safe base64 encoding for secure random strings
        random_bytes = secrets.token_bytes(
            length * 3 // 4
        )  # Adjust for base64 encoding
        return base64.urlsafe_b64encode(random_bytes).decode("ascii")[:length]

    def _collect_api_keys(self) -> dict[str, str]:
        """Collect API keys from user interactively."""
        api_keys = {}

        try:
            # OpenAI API Key
            openai_key = input("OpenAI API Key (for GPT models): ").strip()
            if openai_key:
                api_keys["openai_api_key"] = openai_key

            # Anthropic API Key
            anthropic_key = input("Anthropic API Key (for Claude models): ").strip()
            if anthropic_key:
                api_keys["anthropic_api_key"] = anthropic_key

            # Google API Key
            google_key = input("Google API Key (for Gemini models): ").strip()
            if google_key:
                api_keys["google_api_key"] = google_key

            # XAI API Key
            xai_key = input("X.AI API Key (for Grok models): ").strip()
            if xai_key:
                api_keys["xai_api_key"] = xai_key

            # LangWatch integration
            langwatch_choice = (
                input("\nEnable LangWatch monitoring? (y/N): ").strip().lower()
            )
            if langwatch_choice == "y":
                langwatch_key = input("LangWatch API Key: ").strip()
                if langwatch_key:
                    api_keys["langwatch_api_key"] = langwatch_key
                    api_keys["langwatch_enabled"] = "true"
                else:
                    pass
            else:
                api_keys["langwatch_enabled"] = "false"

        except (EOFError, KeyboardInterrupt):
            return {}

        if api_keys:
            pass
        else:
            pass

        return api_keys

    def _create_workspace_files(
        self,
        workspace_path: Path,
        credentials: dict[str, str],
        api_keys: dict[str, str],
        postgres_config: dict[str, str],
        container_services: list[str],
    ) -> bool:
        """Create workspace configuration files."""
        try:
            # Create .env file
            self._create_env_file(workspace_path, credentials, api_keys)

            # Create docker-compose files for selected services
            if postgres_config["type"] == "docker":
                self._create_docker_compose_files(
                    workspace_path, credentials, container_services, postgres_config
                )

            # Copy .claude/ directory if available
            self._copy_claude_directory(workspace_path)

            # Create .mcp.json for Claude Code integration with multi-server support
            self._create_advanced_mcp_config(
                workspace_path, credentials, postgres_config
            )

            # Create ai/ directory structure
            self._create_ai_structure(workspace_path)

            # Create .gitignore
            self._create_gitignore(workspace_path)

            # Create startup script for convenience
            self._create_startup_script(workspace_path, postgres_config)

            return True

        except Exception:
            return False

    def _create_env_file(
        self,
        workspace_path: Path,
        credentials: dict[str, str],
        api_keys: dict[str, str],
    ):
        """Create .env file with credentials and API keys."""
        env_content = f"""# Automagik Hive Workspace Configuration
# Generated by uvx automagik-hive --init

# === Database Configuration ===
DATABASE_URL={credentials["database_url"]}
HIVE_DATABASE_URL={credentials["database_url"]}
"""

        # Add PostgreSQL-specific environment variables only for Docker setup
        if "postgres_user" in credentials:
            env_content += f"""POSTGRES_USER={credentials["postgres_user"]}
POSTGRES_PASSWORD={credentials["postgres_password"]}
POSTGRES_DB=hive
"""

        env_content += f"""
# === API Configuration ===
HIVE_API_KEY={credentials["hive_api_key"]}
HIVE_HOST=0.0.0.0
HIVE_PORT=8886

# === AI Provider API Keys ===
"""

        # Add collected API keys
        for key, value in api_keys.items():
            env_content += f"{key.upper()}={value}\n"

        # Add placeholder for missing keys
        if "openai_api_key" not in api_keys:
            env_content += "# OPENAI_API_KEY=your-openai-key-here\n"
        if "anthropic_api_key" not in api_keys:
            env_content += "# ANTHROPIC_API_KEY=your-anthropic-key-here\n"
        if "google_api_key" not in api_keys:
            env_content += "# GOOGLE_API_KEY=your-google-key-here\n"
        if "xai_api_key" not in api_keys:
            env_content += "# XAI_API_KEY=your-xai-key-here\n"

        env_content += """
# === MCP Server Configuration ===
MCP_SERVER_PORT=8887

# === Development Settings ===
ENVIRONMENT=development
LOG_LEVEL=INFO
HIVE_DEV_MODE=true
"""

        env_file = workspace_path / ".env"
        env_file.write_text(env_content)

        # Set secure permissions
        env_file.chmod(0o600)

    def _create_container_templates(
        self,
        workspace_path: Path,
        credentials: dict[str, str],
        postgres_config: dict[str, str],
        container_services: list[str],
    ):
        """Create container templates using the template system."""
        # Convert to ContainerCredentials
        container_credentials = self._convert_to_container_credentials(
            credentials, postgres_config
        )

        # Create required directories first
        self.template_manager.create_required_directories(workspace_path)

        generated_files = {}

        # Generate templates based on selected services
        if "postgres" in container_services or len(container_services) == 1:
            # Main workspace compose file
            generated_files["workspace"] = (
                self.template_manager.generate_workspace_compose(
                    workspace_path, container_credentials
                )
            )

        if "agent" in container_services:
            # Agent development environment
            generated_files["agent"] = self.template_manager.generate_agent_compose(
                workspace_path, container_credentials
            )

        if "genie" in container_services:
            # Genie consultation service
            generated_files["genie"] = self.template_manager.generate_genie_compose(
                workspace_path, container_credentials
            )

        # Show generated files
        for _service_type, _file_path in generated_files.items():
            pass

    def _create_docker_compose_files(
        self,
        workspace_path: Path,
        credentials: dict[str, str],
        container_services: list[str],
        postgres_config: dict[str, str],
    ):
        """Create docker-compose files for selected services using templates."""
        template_dir = Path(__file__).parent.parent.parent / "docker" / "templates"

        if not template_dir.exists():
            # Fallback to basic compose file
            self._create_basic_docker_compose_file(workspace_path, credentials)
            return

        # Always create workspace compose for PostgreSQL
        if "postgres" in container_services:
            self._copy_and_customize_template(
                template_dir / "workspace.yml",
                workspace_path / "docker-compose.yml",
                credentials,
            )

        # Create agent directory structure and unified compose file if selected
        if "agent" in container_services:
            # Create docker/agent directory in workspace
            agent_docker_dir = workspace_path / "docker" / "agent"
            agent_docker_dir.mkdir(parents=True, exist_ok=True)

            # Use the unified docker-compose file from the source
            source_agent_dir = Path(__file__).parent.parent.parent / "docker" / "agent"
            unified_agent_template = source_agent_dir / "docker-compose.unified.yml"

            if unified_agent_template.exists():
                # Copy the unified compose file directly
                shutil.copy2(
                    unified_agent_template,
                    agent_docker_dir / "docker-compose.unified.yml",
                )
            else:
                pass

            # Copy unified container build files for agent
            self._copy_unified_container_files("agent", workspace_path, credentials)

        # Create genie directory structure and unified compose file if selected
        if "genie" in container_services:
            # Create docker/genie directory in workspace
            genie_docker_dir = workspace_path / "docker" / "genie"
            genie_docker_dir.mkdir(parents=True, exist_ok=True)

            # Use the unified docker-compose file from the source
            source_genie_dir = Path(__file__).parent.parent.parent / "docker" / "genie"
            unified_genie_template = source_genie_dir / "docker-compose.unified.yml"

            if unified_genie_template.exists():
                # Copy the unified compose file directly
                shutil.copy2(
                    unified_genie_template,
                    genie_docker_dir / "docker-compose.unified.yml",
                )
            else:
                pass

            # Copy unified container build files for genie
            self._copy_unified_container_files("genie", workspace_path, credentials)

    def _copy_and_customize_template(
        self, template_path: Path, dest_path: Path, credentials: dict[str, str]
    ):
        """Copy template and customize with credentials."""
        try:
            if template_path.exists():
                template_content = template_path.read_text()

                # Keep build sections for unified containers - they need to be built locally
                # The unified containers have proper Dockerfiles and should be built, not replaced with placeholders

                # Replace template variables with actual credentials
                if "postgres_user" in credentials:
                    template_content = template_content.replace(
                        "${POSTGRES_USER:-workspace}", credentials["postgres_user"]
                    )
                    template_content = template_content.replace(
                        "${POSTGRES_PASSWORD:-workspace}",
                        credentials["postgres_password"],
                    )
                    template_content = template_content.replace(
                        "${POSTGRES_USER:-agent}", credentials["postgres_user"]
                    )
                    template_content = template_content.replace(
                        "${POSTGRES_PASSWORD:-agent}", credentials["postgres_password"]
                    )
                    template_content = template_content.replace(
                        "${POSTGRES_USER:-genie}", credentials["postgres_user"]
                    )
                    template_content = template_content.replace(
                        "${POSTGRES_PASSWORD:-genie}", credentials["postgres_password"]
                    )

                # Add user/group settings for proper permissions
                import os

                uid = os.getuid() if hasattr(os, "getuid") else 1000
                gid = os.getgid() if hasattr(os, "getgid") else 1000
                template_content = template_content.replace(
                    "${POSTGRES_UID:-1000}:${POSTGRES_GID:-1000}", f"{uid}:{gid}"
                )

                dest_path.write_text(template_content)
            else:
                # Fallback for missing template
                self._create_basic_docker_compose_file(dest_path.parent, credentials)
        except Exception:
            # Fallback on any template processing error
            self._create_basic_docker_compose_file(dest_path.parent, credentials)

    def _copy_unified_container_files(
        self, service_type: str, workspace_path: Path, credentials: dict[str, str]
    ):
        """Copy all unified container build files to workspace."""
        try:
            # Source directory in the package
            source_dir = Path(__file__).parent.parent.parent / "docker" / service_type

            # Destination directory in workspace
            dest_dir = workspace_path / "docker" / service_type
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Files to copy for unified containers
            files_to_copy = [
                "Dockerfile.unified",
                "supervisord.conf",
                "entrypoint.sh",
                "health-monitor.sh",
                "pg_hba.conf",
                "postgresql.conf",
            ]

            for filename in files_to_copy:
                source_file = source_dir / filename
                dest_file = dest_dir / filename

                if source_file.exists():
                    # Copy file content and customize if needed
                    content = source_file.read_text()

                    # Make executable files executable
                    if filename.endswith(".sh"):
                        dest_file.write_text(content)
                        dest_file.chmod(0o755)
                    else:
                        dest_file.write_text(content)

        except Exception:
            # Don't fail initialization if file copying fails
            # The containers might still work with pre-built images
            pass

    def _create_basic_docker_compose_file(
        self, workspace_path: Path, credentials: dict[str, str]
    ):
        """Create basic docker-compose.yml file as fallback."""
        import os

        # Get current user ID and group ID to avoid root ownership issues
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        gid = os.getgid() if hasattr(os, "getgid") else 1000

        compose_content = f"""# Automagik Hive Docker Compose Configuration
# Generated by uvx automagik-hive --init

version: '3.8'

services:
  postgres:
    image: agnohq/pgvector:16
    container_name: hive-postgres
    user: "{uid}:{gid}"
    environment:
      POSTGRES_USER: {credentials["postgres_user"]}
      POSTGRES_PASSWORD: {credentials["postgres_password"]}
      POSTGRES_DB: hive
      PGUSER: {credentials["postgres_user"]}
    ports:
      - "5532:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {credentials["postgres_user"]} -d hive"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    networks:
      - hive-network

networks:
  hive-network:
    driver: bridge

volumes:
  postgres-data:
    driver: local
"""

        compose_file = workspace_path / "docker-compose.yml"
        compose_file.write_text(compose_content)

    def _copy_claude_directory(self, workspace_path: Path):
        """Copy .claude/ directory from package if available."""
        # Try to find .claude/ directory in the package
        possible_paths = [
            Path(__file__).parent.parent.parent / ".claude",  # From package
            Path.cwd() / ".claude",  # From current directory
        ]

        source_claude = None
        for path in possible_paths:
            if path.exists() and path.is_dir():
                source_claude = path
                break

        if source_claude:
            dest_claude = workspace_path / ".claude"
            with contextlib.suppress(Exception):
                shutil.copytree(source_claude, dest_claude, dirs_exist_ok=True)
        else:
            pass

    def _create_advanced_mcp_config(
        self,
        workspace_path: Path,
        credentials: dict[str, str],
        postgres_config: dict[str, str] | None = None,
    ):
        """Create advanced multi-server MCP configuration with dynamic template processing."""
        try:
            # Create comprehensive template context
            template_context = self.template_processor.create_workspace_context(
                workspace_path, postgres_config
            )

            # Add credentials to context
            template_context.update(
                {
                    "hive_api_key": credentials.get("hive_api_key", ""),
                    "database_user": credentials.get("postgres_user", "hive_user"),
                    "database_password": credentials.get("postgres_password", ""),
                }
            )

            # Generate dynamic MCP configuration
            mcp_config = self.mcp_generator.generate_mcp_config(template_context)

            # Write configuration with validation
            mcp_file = workspace_path / ".mcp.json"
            if self.mcp_generator.write_mcp_config(mcp_config, mcp_file):
                pass
            else:
                raise Exception("MCP configuration validation failed")

        except Exception:
            self._create_basic_mcp_fallback(workspace_path, credentials)

    def _create_basic_mcp_fallback(
        self, workspace_path: Path, credentials: dict[str, str]
    ):
        """Create basic MCP configuration as fallback."""
        # Ensure workspace directory exists
        workspace_path.mkdir(parents=True, exist_ok=True)

        basic_config = {
            "mcpServers": {
                "postgres": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres"],
                },
                "automagik-hive": {
                    "command": "echo",
                    "args": ["Automagik Hive server not configured - set up manually"],
                },
            }
        }

        # Add database URL to postgres if available
        if "database_url" in credentials:
            basic_config["mcpServers"]["postgres"]["args"].append(
                credentials["database_url"]
            )

        mcp_file = workspace_path / ".mcp.json"
        mcp_file.write_text(json.dumps(basic_config, indent=2))

    def _create_ai_structure(self, workspace_path: Path):
        """Create ai/ directory structure with template components."""
        ai_path = workspace_path / "ai"
        ai_path.mkdir(parents=True, exist_ok=True)

        # Create README files
        (ai_path / "README.md").write_text(
            "# AI Components\n\nCustom agents, teams, workflows, and tools for your workspace.\n"
        )

        # Copy template components from package
        package_ai_path = Path(__file__).parent.parent.parent / "ai"
        if package_ai_path.exists():
            # Create subdirectories and copy templates
            for subdir in ["agents", "teams", "workflows", "tools"]:
                # Create the subdirectory
                (ai_path / subdir).mkdir(parents=True, exist_ok=True)

                # Copy template component if it exists
                template_name = f"template-{subdir[:-1]}"  # Remove 's' from plural
                source_template = package_ai_path / subdir / template_name

                if source_template.exists():
                    dest_template = ai_path / subdir / template_name
                    try:
                        shutil.copytree(
                            source_template, dest_template, dirs_exist_ok=True
                        )
                    except Exception:
                        # Create empty directory as fallback
                        dest_template.mkdir(parents=True, exist_ok=True)
        else:
            # Fallback: create empty directories
            for subdir in ["agents", "teams", "workflows", "tools"]:
                (ai_path / subdir).mkdir(parents=True, exist_ok=True)

    def _create_gitignore(self, workspace_path: Path):
        """Create .gitignore file."""
        gitignore_content = """# Automagik Hive Workspace
.env
.env.local
data/
logs/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

        gitignore_file = workspace_path / ".gitignore"
        gitignore_file.write_text(gitignore_content)

    def _create_data_directories(
        self, workspace_path: Path, container_services: list[str]
    ):
        """Create data directories for persistence with proper permissions."""
        data_path = workspace_path / "data"

        try:
            # Base directories
            base_dirs = ["logs"]

            # Add service-specific directories
            if "postgres" in container_services or len(container_services) == 1:
                base_dirs.append("postgres")
            if "agent" in container_services:
                base_dirs.append("postgres-agent")
            if "genie" in container_services:
                base_dirs.append("postgres-genie")

            # Create directories with explicit permissions
            for subdir in base_dirs:
                dir_path = data_path / subdir

                # Remove existing directory if it has permission issues
                if dir_path.exists():
                    try:
                        # Try to write a test file to check permissions
                        test_file = dir_path / ".permission_test"
                        test_file.touch()
                        test_file.unlink()
                    except (PermissionError, OSError):
                        # Remove problematic directory
                        try:
                            import shutil

                            shutil.rmtree(dir_path)
                        except Exception:
                            pass

                # Create directory with proper permissions
                dir_path.mkdir(parents=True, exist_ok=True)
                # Set permissions to allow current user read/write/execute
                dir_path.chmod(0o755)

                # For PostgreSQL directories, ensure proper ownership
                if "postgres" in subdir:
                    try:
                        import os

                        uid = os.getuid() if hasattr(os, "getuid") else 1000
                        gid = os.getgid() if hasattr(os, "getgid") else 1000
                        os.chown(dir_path, uid, gid)
                    except Exception:
                        # Don't fail if chown doesn't work
                        pass

        except PermissionError:
            # Don't fail the entire initialization for this
            pass

    def _create_startup_script(
        self,
        workspace_path: Path,
        postgres_config: dict[str, str],
        container_services: list[str] | None = None,
    ):
        """Create convenience startup script."""
        if postgres_config["type"] == "docker":
            startup_script = """#!/bin/bash
# Automagik Hive Workspace Startup Script
# Generated by uvx automagik-hive --init

set -e

echo "🧞 Starting Automagik Hive Workspace..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start PostgreSQL first
echo "🗄️ Starting PostgreSQL..."
docker compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U $(grep POSTGRES_USER .env | cut -d '=' -f2) >/dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Start the workspace
echo "🚀 Starting workspace server..."
uvx automagik-hive ./

echo "🎉 Workspace started successfully!"
"""
        else:
            startup_script = """#!/bin/bash
# Automagik Hive Workspace Startup Script
# Generated by uvx automagik-hive --init

set -e

echo "🧞 Starting Automagik Hive Workspace..."

# Note: Using external PostgreSQL - ensure it's running and accessible
echo "🗄️ Using external PostgreSQL..."
echo "💡 Make sure your PostgreSQL server is running and accessible"

# Start the workspace
echo "🚀 Starting workspace server..."
uvx automagik-hive ./

echo "🎉 Workspace started successfully!"
"""

        script_file = workspace_path / "start.sh"
        script_file.write_text(startup_script)
        script_file.chmod(0o755)  # Make executable

        # Also create a Windows batch file
        if postgres_config["type"] == "docker":
            windows_script = """@echo off
REM Automagik Hive Workspace Startup Script
REM Generated by uvx automagik-hive --init

echo 🧞 Starting Automagik Hive Workspace...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Start PostgreSQL first
echo 🗄️ Starting PostgreSQL...
docker compose up -d postgres

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
:wait_postgres
timeout /t 2 /nobreak >nul
docker compose exec postgres pg_isready >nul 2>&1
if errorlevel 1 goto wait_postgres

echo ✅ PostgreSQL is ready!

REM Start the workspace
echo 🚀 Starting workspace server...
uvx automagik-hive ./

echo 🎉 Workspace started successfully!
"""
        else:
            windows_script = """@echo off
REM Automagik Hive Workspace Startup Script
REM Generated by uvx automagik-hive --init

echo 🧞 Starting Automagik Hive Workspace...

REM Note: Using external PostgreSQL - ensure it's running and accessible
echo 🗄️ Using external PostgreSQL...
echo 💡 Make sure your PostgreSQL server is running and accessible

REM Start the workspace
echo 🚀 Starting workspace server...
uvx automagik-hive ./

echo 🎉 Workspace started successfully!
"""

        batch_file = workspace_path / "start.bat"
        batch_file.write_text(windows_script)

    def _show_enhanced_success_message(
        self,
        workspace_path: Path,
        container_services: list[str] | None = None,
        is_valid: bool = True,
    ):
        """Show enhanced success message with validation status and comprehensive next steps."""
        if container_services is None:
            container_services = ["postgres"]

        # Header with validation status
        if is_valid:
            pass
        else:
            pass

        # Quick Start Guide

        # Cross-platform startup options
        import platform

        current_os = platform.system().lower()

        if current_os in {"windows", "darwin"}:
            pass
        else:
            pass

        # Configuration guidance

        # Check what API keys are missing
        env_file = workspace_path / ".env"
        missing_keys = []
        if env_file.exists():
            env_content = env_file.read_text()
            api_keys_to_check = [
                ("OPENAI_API_KEY", "OpenAI GPT models"),
                ("ANTHROPIC_API_KEY", "Anthropic Claude models"),
                ("GOOGLE_API_KEY", "Google Gemini models"),
                ("XAI_API_KEY", "X.AI Grok models"),
            ]

            for key, description in api_keys_to_check:
                if f"# {key}" in env_content:  # Commented out = missing
                    missing_keys.append((key, description))

        if missing_keys:
            for key, description in missing_keys:
                pass
        else:
            pass

        # Workspace structure with descriptions

        # First run suggestions

        # Troubleshooting hints
        if not is_valid:
            pass

    def _start_docker_containers(
        self,
        workspace_path: Path,
        container_services: list[str],
        postgres_config: dict[str, str],
    ) -> bool:
        """Start Docker containers and configure other services."""
        try:
            success = True

            # Change to workspace directory for docker-compose
            original_cwd = os.getcwd()
            os.chdir(workspace_path)

            # Clean up any conflicting containers and networks first
            self._cleanup_existing_containers()

            try:
                for service in container_services:
                    if service == "postgres" and postgres_config["type"] == "docker":
                        result = secure_subprocess_call(
                            [
                                "docker",
                                "compose",
                                "up",
                                "-d",
                                "postgres",
                                "--remove-orphans",
                            ],
                            capture_output=True,
                            timeout=120,
                        )
                        if result.returncode == 0:
                            pass
                        else:
                            success = False

                    elif service == "agent":
                        # Check if the compose file exists
                        agent_compose_file = (
                            workspace_path
                            / "docker"
                            / "agent"
                            / "docker-compose.unified.yml"
                        )
                        if not agent_compose_file.exists():
                            success = False
                            continue

                        result = secure_subprocess_call(
                            [
                                "docker",
                                "compose",
                                "-f",
                                "docker/agent/docker-compose.unified.yml",
                                "up",
                                "-d",
                                "agent-all-in-one",
                                "--remove-orphans",
                            ],
                            capture_output=True,
                            timeout=120,
                        )
                        if result.returncode == 0:
                            pass
                        else:
                            success = False

                    elif service == "genie":
                        # Check if the compose file exists
                        genie_compose_file = (
                            workspace_path
                            / "docker"
                            / "genie"
                            / "docker-compose.unified.yml"
                        )
                        if not genie_compose_file.exists():
                            success = False
                            continue

                        result = secure_subprocess_call(
                            [
                                "docker",
                                "compose",
                                "-f",
                                "docker/genie/docker-compose.unified.yml",
                                "up",
                                "-d",
                                "genie-all-in-one",
                                "--remove-orphans",
                            ],
                            capture_output=True,
                            timeout=120,
                        )
                        if result.returncode == 0:
                            pass
                        else:
                            success = False

            finally:
                os.chdir(original_cwd)

            if success:
                pass
            else:
                pass

            return success

        except Exception:
            return False

    def _cleanup_existing_containers(self):
        """Clean up existing containers and networks to prevent conflicts."""
        try:
            # Stop and remove existing hive containers (both old and new architectures)
            containers_to_remove = [
                "hive-postgres-workspace",
                "hive-postgres-agent",
                "hive-postgres-genie",
                "hive-agents-agent",
                "hive-genie",
                "hive-agent-dev-server",
                "hive-agent-unified",
                "hive-genie-unified",
            ]

            for container in containers_to_remove:
                try:
                    # Stop container if running
                    secure_subprocess_call(
                        ["docker", "stop", container], capture_output=True, timeout=30
                    )
                    # Remove container
                    secure_subprocess_call(
                        ["docker", "rm", container], capture_output=True, timeout=30
                    )
                except Exception:
                    # Container might not exist, continue
                    pass

            # Remove orphaned networks
            networks_to_remove = [
                "hive_workspace_network",
                "hive_agent_network",
                "hive_genie_network",
            ]

            for network in networks_to_remove:
                try:
                    secure_subprocess_call(
                        ["docker", "network", "rm", network],
                        capture_output=True,
                        timeout=30,
                    )
                except Exception:
                    # Network might not exist or be in use, continue
                    pass

        except Exception:
            # Don't fail initialization if cleanup fails
            pass
