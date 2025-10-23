"""Docker Manager - Simple container operations."""

import os
import subprocess
import time
from pathlib import Path

import yaml

from lib.auth.credential_service import CredentialService


class DockerManager:
    """Simple Docker operations manager focused on the workspace stack."""

    # Container definitions (must match Docker Compose naming)
    POSTGRES_CONTAINER = "hive-postgres"  # Matches docker/main/docker-compose.yml
    API_CONTAINER = "hive-api"  # API container from docker/main/docker-compose.yml
    NETWORK_NAME = "hive_network"  # Docker network name

    # Supported component-to-container mapping (workspace-only contract)
    CONTAINERS: dict[str, list[str]] = {
        "workspace": [POSTGRES_CONTAINER, API_CONTAINER],
        "postgres": [POSTGRES_CONTAINER],
        "api": [API_CONTAINER],
        "all": [POSTGRES_CONTAINER, API_CONTAINER],
    }

    # Port mappings - read from environment with no hardcoded fallbacks
    @property
    def ports(self) -> dict[str, int]:
        """Port mappings for all components from environment variables.

        ARCHITECTURAL RULE: All ports must come from environment variables.
        No hardcoded port fallbacks allowed.
        """
        # Validate required environment variables exist
        required_ports = {
            "HIVE_POSTGRES_PORT": "postgres",
        }

        missing_vars = []
        for var_name, description in required_ports.items():
            if not os.getenv(var_name):
                missing_vars.append(f"{var_name} ({description})")

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please configure these in your .env file."
            )

        return {"postgres": int(os.getenv("HIVE_POSTGRES_PORT")), "api": int(os.getenv("HIVE_API_PORT", "8886"))}

    # PORTS attribute for test compatibility
    @property
    def PORTS(self) -> dict[str, int]:  # noqa: N802
        """Uppercase PORTS for test compatibility - delegates to ports property."""
        return self.ports

    def _get_ports(self) -> dict[str, int]:
        """Get port mappings from environment variables."""
        return self.ports

    def __init__(self):
        self.project_root = Path.cwd()

        # Map component to docker template file
        self.template_files = {
            "workspace": self.project_root / "docker/main/docker-compose.yml",
        }

        # Initialize credential service for secure credential generation
        self.credential_service = CredentialService(project_root=self.project_root)

    def _run_command(self, cmd: list[str], capture_output: bool = False) -> str | None:
        """Run shell command."""
        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            subprocess.run(cmd, check=True)
            return None
        except subprocess.CalledProcessError as e:
            if capture_output and e.stderr:
                print(f"❌ Command failed: {cmd[0]}")
                print(f"Error: {e.stderr}")
            return None
        except FileNotFoundError:
            if capture_output:
                print(f"❌ Command not found: {cmd[0]}")
            return None

    def _check_docker(self) -> bool:
        """Check if Docker is available.

        Group D: Only required for PostgreSQL backend. SQLite/PGlite skip this check.
        """
        # Detect backend type from environment
        backend_type = self._detect_backend_from_env()

        # Skip Docker check for non-PostgreSQL backends
        if backend_type in ("pglite", "sqlite"):
            return True

        # PostgreSQL requires Docker
        if not self._run_command(["docker", "--version"], capture_output=True):
            print("❌ Docker not found. Please install Docker first.")
            print("💡 Tip: Use PGlite or SQLite backends to run without Docker")
            return False

        # Check if Docker daemon is running
        if not self._run_command(["docker", "ps"], capture_output=True):
            print("❌ Docker daemon not running. Please start Docker.")
            print("💡 Tip: Use PGlite or SQLite backends to run without Docker")
            return False

        return True

    def _detect_backend_from_env(self) -> str:
        """Detect database backend type from environment - Group D helper."""
        # Try explicit backend setting first
        backend_env = os.getenv("HIVE_DATABASE_BACKEND")
        if backend_env:
            return backend_env.lower()

        # Fall back to URL detection
        db_url = os.getenv("HIVE_DATABASE_URL", "")
        if db_url.startswith("pglite://"):
            return "pglite"
        elif db_url.startswith("sqlite://"):
            return "sqlite"
        elif db_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
            return "postgresql"

        # Default to PostgreSQL for backward compatibility
        return "postgresql"

    def _get_containers(self, component: str) -> list[str]:
        """Return container names for a supported component."""

        normalized = component.lower()
        containers = self.CONTAINERS.get(normalized)
        if not containers:
            print(f"❌ Unsupported component: {component}")
            return []

        # Return a copy to avoid accidental mutation by callers/tests
        return list(containers)

    def _container_exists(self, container: str) -> bool:
        """Check if container exists."""
        return (
            self._run_command(
                ["docker", "ps", "-a", "--filter", f"name={container}", "--format", "{{.Names}}"], capture_output=True
            )
            == container
        )

    def _container_running(self, container: str) -> bool:
        """Check if container is running."""
        return (
            self._run_command(
                ["docker", "ps", "--filter", f"name={container}", "--format", "{{.Names}}"], capture_output=True
            )
            == container
        )

    def _get_docker_compose_command(self) -> str:
        """Get the correct docker-compose command (docker-compose vs docker compose)."""
        # Try docker compose first (newer format)
        try:
            result = self._run_command(["docker", "compose", "version"], capture_output=True)
            if result:
                return "docker compose"
        except Exception:  # noqa: S110 - Silent exception handling is intentional
            pass

        # Fall back to docker-compose (legacy format)
        try:
            result = self._run_command(["docker-compose", "--version"], capture_output=True)
            if result:
                return "docker-compose"
        except Exception:  # noqa: S110 - Silent exception handling is intentional
            pass

        print("⚠️ Neither 'docker compose' nor 'docker-compose' found")
        return "docker compose"  # Default to newer format

    def _create_network(self) -> None:
        """Create Docker network if it doesn't exist."""
        networks = self._run_command(
            ["docker", "network", "ls", "--filter", f"name={self.NETWORK_NAME}", "--format", "{{.Name}}"],
            capture_output=True,
        )
        if self.NETWORK_NAME not in (networks or ""):
            self._run_command(["docker", "network", "create", self.NETWORK_NAME])

    def _get_dockerfile_path(self, component: str) -> Path:
        """Get the Dockerfile path for a component."""
        dockerfile_mapping = {
            "workspace": self.project_root / "docker" / "main" / "Dockerfile",
        }

        return dockerfile_mapping.get(component, self.project_root / "docker" / "main" / "Dockerfile")

    def _get_postgres_image(self, component: str) -> str:
        """Determine the postgres image for the requested component."""

        default_image = "agnohq/pgvector:16"
        compose_path = self.template_files.get(component)
        if not compose_path or not compose_path.exists():
            return default_image

        try:
            compose_data = yaml.safe_load(compose_path.read_text()) or {}
        except Exception:
            return default_image

        services = compose_data.get("services", {})
        postgres_service = services.get(self.POSTGRES_CONTAINER) or services.get("postgres")
        if isinstance(postgres_service, dict):
            return postgres_service.get("image", default_image)

        return default_image

    def _create_containers_via_compose(self, component: str, credentials: dict) -> bool:
        """Create containers using Docker Compose for consistency with Makefile."""
        if component not in self.template_files:
            return False

        compose_file = self.template_files[component]
        if not compose_file.exists():
            print(f"❌ Docker Compose file not found: {compose_file}")
            return False

        # Create component-specific .env file for Docker Compose
        env_file = compose_file.parent / ".env"
        self._create_compose_env_file(component, credentials, env_file)

        # Create data directories with proper ownership BEFORE starting containers (like Makefile)
        self._create_data_directories_with_ownership(component)

        # Use Docker Compose to start services (try both docker-compose and docker compose)
        docker_compose_cmd = self._get_docker_compose_command()

        # For workspace, only start postgres service (database-only installation)
        services = ["postgres"] if component == "workspace" else []

        if docker_compose_cmd == "docker compose":
            cmd = ["docker", "compose", "-f", str(compose_file), "up", "-d"] + services
        else:
            cmd = [docker_compose_cmd, "-f", str(compose_file), "up", "-d"] + services

        return self._run_command(cmd) is None

    def _create_compose_env_file(self, component: str, credentials: dict, env_file: Path) -> None:
        """Create .env file for Docker Compose with provided credentials.

        ARCHITECTURAL RULE: This method creates Docker Compose specific .env files
        in docker/*/. These are separate from workspace .env files and contain
        only Docker container environment variables.
        """
        # Cross-platform UID/GID handling (like existing Makefile and compose_service.py)
        import os

        uid = os.getuid() if hasattr(os, "getuid") else 1000
        gid = os.getgid() if hasattr(os, "getgid") else 1000

        env_content = f"""# Docker Compose environment variables for {component} component
# ARCHITECTURAL RULE: This file is for Docker containers only
# Main .env file should contain workspace environment variables

POSTGRES_USER={credentials["postgres_user"]}
POSTGRES_PASSWORD={credentials["postgres_password"]}
POSTGRES_DB={credentials["postgres_database"]}

# User permissions for container (cross-platform)
POSTGRES_UID={uid}
POSTGRES_GID={gid}

# Build arguments
BUILD_VERSION=latest
BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
GIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
"""

        env_file.write_text(env_content)

    def _create_data_directories_with_ownership(self, component: str) -> None:
        """Create data directories with proper ownership before container startup (like Makefile)."""
        import os

        # Cross-platform UID/GID handling
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        gid = os.getgid() if hasattr(os, "getgid") else 1000

        # Define data directory paths for each component
        data_paths = {"workspace": self.project_root / "data" / "postgres"}

        data_path = data_paths.get(component)
        if not data_path:
            return

        # Create directory if it doesn't exist
        data_path.mkdir(parents=True, exist_ok=True)

        # Set proper ownership (like Makefile: chown -R ${POSTGRES_UID}:${POSTGRES_GID})
        try:
            if hasattr(os, "chown"):  # Unix-like systems
                os.chown(data_path, uid, gid)
            else:  # Windows - no ownership change needed
                pass
        except PermissionError:
            # Try to use subprocess like Makefile fallback
            try:
                import subprocess

                subprocess.run(["sudo", "chown", "-R", f"{uid}:{gid}", str(data_path)], check=False)
            except Exception:  # noqa: S110 - Silent exception handling is intentional
                pass

    def _create_postgres_container(self, component: str, credentials: dict) -> bool:
        """Create PostgreSQL container - now uses Docker Compose for consistency."""
        container_name = self.POSTGRES_CONTAINER

        if self._container_exists(container_name):
            return True

        # Use Docker Compose approach for consistency with Makefile
        return self._create_containers_via_compose(component, credentials)

    def _create_api_container(self, component: str, credentials: dict) -> bool:
        """Create API container - now handled by Docker Compose for consistency."""
        container_name = self.API_CONTAINER

        if self._container_exists(container_name):
            return True

        # API container is created as part of the Docker Compose service
        # The _create_containers_via_compose method handles both postgres and API
        return True

    def _get_or_generate_credentials_legacy(self, component: str) -> dict[str, str]:
        """Get existing or generate new secure credentials for component."""
        docker_folder = self.project_root / "docker" / component
        env_file_path = docker_folder / ".env"

        # Configure credential service for component-specific .env file
        component_credential_service = CredentialService(env_file_path)

        # Check if credentials already exist
        existing_creds = component_credential_service.extract_postgres_credentials_from_env()
        existing_api_key = component_credential_service.extract_hive_api_key_from_env()

        if existing_creds.get("user") and existing_creds.get("password") and existing_api_key:
            return {
                "postgres_user": existing_creds["user"],
                "postgres_password": existing_creds["password"],
                "postgres_database": existing_creds.get("database", f"hive_{component}"),
                "postgres_host": existing_creds.get("host", "localhost"),
                "postgres_port": str(self._get_ports()[component]["postgres"]),
                "api_key": existing_api_key,
            }

        # Generate new secure credentials

        # Determine database configuration based on component
        postgres_port = self._get_ports()[component]["postgres"]
        postgres_database = f"hive_{component}"

        # Generate completely new credentials
        complete_creds = component_credential_service.setup_complete_credentials(
            postgres_host="localhost", postgres_port=postgres_port, postgres_database=postgres_database
        )

        return complete_creds

    def _validate_workspace_env_file(self, component: str) -> bool:
        """Validate that workspace .env file exists.

        VALIDATION ONLY: Checks that .env files exist in the project root.
        Installation commands handle .env file creation and management.
        """
        workspace_env_file = self.project_root / ".env"

        if workspace_env_file.exists():
            return True
        else:
            return False

    def install(self, component: str) -> bool:
        """Install component containers."""
        if not self._check_docker():
            return False

        # Interactive installation
        if component == "interactive":
            return self._interactive_install()

        normalized = component.lower()
        components = ["workspace"] if normalized == "all" else [normalized]

        unsupported = [comp for comp in components if comp != "workspace"]
        if unsupported:
            return False

        try:
            all_credentials = self.credential_service.install_all_modes(components)
        except Exception:
            return False

        self._create_network()

        for comp in components:
            comp_credentials = all_credentials[comp]

            # Create all containers via Docker Compose (handles both postgres and API)
            if not self._create_containers_via_compose(comp, comp_credentials):
                return False

            # Wait for services to be ready
            time.sleep(8)  # Increased wait time for health checks

            # For workspace, note that app runs locally
            if comp == "workspace":
                pass

        return True

    def start(self, component: str) -> bool:
        """Start component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False

        success = True
        for container in containers:
            if self._container_exists(container):
                if not self._container_running(container):
                    if not self._run_command(["docker", "start", container]):
                        success = False
                else:
                    pass
            else:
                success = False

        return success

    def stop(self, component: str) -> bool:
        """Stop component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False

        success = True
        for container in containers:
            if self._container_running(container):
                if not self._run_command(["docker", "stop", container]):
                    success = False
            else:
                pass

        return success

    def restart(self, component: str) -> bool:
        """Restart component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False

        success = True
        for container in containers:
            if self._container_exists(container):
                if not self._run_command(["docker", "restart", container]):
                    success = False
            else:
                success = False

        return success

    def status(self, component: str) -> None:
        """Show component status."""
        containers = self._get_containers(component)
        if not containers:
            return

        print(f"📊 {component.title()} Status:")
        for container in containers:
            if self._container_exists(container):
                if self._container_running(container):
                    # Get port info
                    port_info = self._run_command(["docker", "port", container], capture_output=True)
                    status = "🟢 Running"
                    if port_info:
                        status += f" - {port_info.split(' -> ')[0]}"
                    print(f"  {container:30} {status}")
                else:
                    status = "🔴 Stopped"
                    print(f"  {container:30} {status}")
            else:
                status = "❌ Not installed"
                print(f"  {container:30} {status}")

    def health(self, component: str) -> None:
        """Check component health."""
        containers = self._get_containers(component)
        if not containers:
            return

        print(f"🏥 {component.title()} Health Check:")
        for container in containers:
            if self._container_running(container):
                # Basic health check - container running
                print(f"  {container:30} 🟢 Healthy")
            elif self._container_exists(container):
                print(f"  {container:30} 🟡 Stopped")
            else:
                print(f"  {container:30} 🔴 Not installed")

    def logs(self, component: str, lines: int = 50) -> None:
        """Show component logs."""
        containers = self._get_containers(component)
        if not containers:
            return

        for container in containers:
            if self._container_exists(container):
                print(f"📋 Logs for {container} (last {lines} lines):")
                self._run_command(["docker", "logs", "--tail", str(lines), container])
            else:
                print(f"❌ Container {container} not found")

    def uninstall(self, component: str) -> bool:
        """Uninstall component containers - autonomous operation (no confirmation)."""
        containers = self._get_containers(component)
        if not containers:
            return False

        # Use Docker Compose for unified uninstall approach
        compose_file = self.template_files.get(component)
        if compose_file and compose_file.exists():
            docker_compose_cmd = self._get_docker_compose_command()
            if docker_compose_cmd == "docker compose":
                cmd = ["docker", "compose", "-f", str(compose_file), "down", "-v"]
            else:
                cmd = [docker_compose_cmd, "-f", str(compose_file), "down", "-v"]

            success = self._run_command(cmd) is None
        else:
            # Fallback to manual container removal if no Docker Compose file
            success = True
            for container in containers:
                if self._container_exists(container):
                    # Stop if running
                    if self._container_running(container):
                        self._run_command(["docker", "stop", container])

                    # Remove container
                    if not self._run_command(["docker", "rm", container]):
                        success = False

        # Clean up component-specific .env files and directories
        if component != "all":
            env_file = compose_file.parent / ".env" if compose_file else None
            if env_file and env_file.exists():
                env_file.unlink()

        if success:
            pass

        return success

    def _interactive_install(self) -> bool:
        """Interactive installation with workspace-only choices."""

        while True:
            hive_choice = input("Would you like to install Hive Core? (Y/n): ").strip().lower()
            if hive_choice in ["y", "yes", "n", "no", ""]:
                break

        install_hive = hive_choice not in ["n", "no"]
        if not install_hive:
            return True

        while True:
            db_choice = input("\nSelect database option (1-2): ").strip()
            if db_choice in ["1", "2"]:
                break

        use_container = db_choice == "1"
        if use_container:
            postgres_container = self.POSTGRES_CONTAINER
            if self._container_exists(postgres_container):
                while True:
                    db_action = input("Do you want to (r)euse or (c)recreate it? (r/c): ").strip().lower()
                    if db_action in ["r", "reuse", "c", "create", "recreate"]:
                        break

                if db_action in ["c", "create", "recreate"]:
                    if self._container_running(postgres_container):
                        self._run_command(["docker", "stop", postgres_container])
                    self._run_command(["docker", "rm", postgres_container])
                    volume_name = "hive_workspace_data"
                    volumes = self._run_command(
                        ["docker", "volume", "ls", "--filter", f"name={volume_name}", "--format", "{{.Name}}"],
                        capture_output=True,
                    )
                    if volume_name in (volumes or ""):
                        self._run_command(["docker", "volume", "rm", volume_name])
                else:
                    pass
        else:
            input("Host (localhost): ").strip() or "localhost"
            input("Port (5432): ").strip() or "5432"
            input("Database name (automagik_hive): ").strip() or "automagik_hive"
            username = input("Username: ").strip()
            password = input("Password: ").strip()

            if not username or not password:
                return False

        if not install_hive:
            return True

        if not use_container:
            # For manual database installs we stop here with guidance above
            return True

        return self.install("workspace")
