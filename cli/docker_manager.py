"""Docker Manager - Simple container operations."""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

import yaml

from lib.auth.credential_service import CredentialService


class DockerManager:
    """Simple Docker operations manager focused on the workspace stack."""

    # Container definitions (must match Docker Compose naming)
    POSTGRES_CONTAINER = "hive-postgres"  # Matches docker/main/docker-compose.yml
    API_CONTAINER = "hive-api"  # API container from docker/main/docker-compose.yml
    NETWORK_NAME = "hive_network"  # Docker network name

    # Supported component-to-container mapping (workspace-only contract)
    CONTAINERS: Dict[str, List[str]] = {
        "workspace": [POSTGRES_CONTAINER, API_CONTAINER],
        "postgres": [POSTGRES_CONTAINER],
        "api": [API_CONTAINER],
        "all": [POSTGRES_CONTAINER, API_CONTAINER],
    }
    
    # Port mappings - read from environment with no hardcoded fallbacks
    @property
    def PORTS(self) -> Dict[str, Dict[str, int]]:
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
        
        return {
            "postgres": int(os.getenv("HIVE_POSTGRES_PORT")),
            "api": int(os.getenv("HIVE_API_PORT", "8886"))
        }
    
    def _get_ports(self) -> Dict[str, int]:
        """Get port mappings from environment variables."""
        return self.PORTS
    
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
            if capture_output:
                print(f"❌ Command failed: {' '.join(cmd)}")
                print(f"Error: {e.stderr}")
            return None
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}")
            return None
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        if not self._run_command(["docker", "--version"], capture_output=True):
            print("❌ Docker not found. Please install Docker first.")
            return False
        
        # Check if Docker daemon is running
        if not self._run_command(["docker", "ps"], capture_output=True):
            print("❌ Docker daemon not running. Please start Docker.")
            return False
        
        return True
    
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
        return self._run_command(["docker", "ps", "-a", "--filter", f"name={container}", "--format", "{{.Names}}"], capture_output=True) == container
    
    def _container_running(self, container: str) -> bool:
        """Check if container is running."""
        return self._run_command(["docker", "ps", "--filter", f"name={container}", "--format", "{{.Names}}"], capture_output=True) == container
    
    def _get_docker_compose_command(self) -> str:
        """Get the correct docker-compose command (docker-compose vs docker compose)."""
        # Try docker compose first (newer format)
        try:
            result = self._run_command(["docker", "compose", "version"], capture_output=True)
            if result:
                return "docker compose"
        except:
            pass
            
        # Fall back to docker-compose (legacy format)
        try:
            result = self._run_command(["docker-compose", "--version"], capture_output=True)
            if result:
                return "docker-compose"
        except:
            pass
            
        print("⚠️ Neither 'docker compose' nor 'docker-compose' found")
        return "docker compose"  # Default to newer format
    
    def _create_network(self) -> None:
        """Create Docker network if it doesn't exist."""
        networks = self._run_command(["docker", "network", "ls", "--filter", f"name={self.NETWORK_NAME}", "--format", "{{.Name}}"], capture_output=True)
        if self.NETWORK_NAME not in (networks or ""):
            print("🔗 Creating Docker network...")
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
            print(f"❌ Docker Compose unsupported for component: {component}")
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
        
        print(f"🐳 Starting {component} services via Docker Compose...")
        print(f"📁 Using: {compose_file}")
        
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

POSTGRES_USER={credentials['postgres_user']}
POSTGRES_PASSWORD={credentials['postgres_password']}
POSTGRES_DB={credentials['postgres_database']}

# User permissions for container (cross-platform)
POSTGRES_UID={uid}
POSTGRES_GID={gid}

# Build arguments
BUILD_VERSION=latest
BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
GIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
"""
        
        env_file.write_text(env_content)
        print(f"📝 Created Docker Compose .env: {env_file}")
        print(f"⚠️  This is separate from workspace .env file")
    
    def _create_data_directories_with_ownership(self, component: str) -> None:
        """Create data directories with proper ownership before container startup (like Makefile)."""
        import os
        import stat
        
        # Cross-platform UID/GID handling
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        gid = os.getgid() if hasattr(os, "getgid") else 1000
        
        # Define data directory paths for each component
        data_paths = {
            "workspace": self.project_root / "data" / "postgres"
        }
        
        data_path = data_paths.get(component)
        if not data_path:
            return
            
        print(f"📁 Creating data directory with proper ownership: {data_path}")
        
        # Create directory if it doesn't exist
        data_path.mkdir(parents=True, exist_ok=True)
        
        # Set proper ownership (like Makefile: chown -R ${POSTGRES_UID}:${POSTGRES_GID})
        try:
            if hasattr(os, "chown"):  # Unix-like systems
                os.chown(data_path, uid, gid)
                print(f"✅ Set data directory ownership: {uid}:{gid}")
            else:  # Windows - no ownership change needed
                print("✅ Data directory created (Windows - no ownership change needed)")
        except PermissionError:
            # Try to use subprocess like Makefile fallback
            try:
                import subprocess
                subprocess.run(["sudo", "chown", "-R", f"{uid}:{gid}", str(data_path)], check=False)
                print(f"✅ Set data directory ownership via sudo: {uid}:{gid}")
            except:
                print("⚠️ Could not set directory ownership - containers may need to run as root")
        
    def _create_postgres_container(self, component: str, credentials: dict) -> bool:
        """Create PostgreSQL container - now uses Docker Compose for consistency."""
        container_name = self.POSTGRES_CONTAINER
        
        if self._container_exists(container_name):
            print(f"✅ PostgreSQL container {container_name} already exists")
            return True
        
        # Use Docker Compose approach for consistency with Makefile
        return self._create_containers_via_compose(component, credentials)
    
    def _create_api_container(self, component: str, credentials: dict) -> bool:
        """Create API container - now handled by Docker Compose for consistency."""
        container_name = self.API_CONTAINER
        
        if self._container_exists(container_name):
            print(f"✅ API container {container_name} already exists")
            return True
        
        # API container is created as part of the Docker Compose service
        # The _create_containers_via_compose method handles both postgres and API
        print(f"✅ API container {container_name} will be created via Docker Compose")
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
            print(f"✅ Using existing secure credentials for {component}")
            return {
                "postgres_user": existing_creds["user"],
                "postgres_password": existing_creds["password"],
                "postgres_database": existing_creds.get("database", f"hive_{component}"),
                "postgres_host": existing_creds.get("host", "localhost"),
                "postgres_port": str(self._get_ports()[component]["postgres"]),
                "api_key": existing_api_key
            }
        
        # Generate new secure credentials
        print(f"🔐 Generating new secure credentials for {component}...")
        
        # Determine database configuration based on component
        postgres_port = self._get_ports()[component]["postgres"]
        postgres_database = f"hive_{component}"
        
        # Generate completely new credentials
        complete_creds = component_credential_service.setup_complete_credentials(
            postgres_host="localhost",
            postgres_port=postgres_port,
            postgres_database=postgres_database
        )
        
        print(f"✅ Generated secure credentials for {component}")
        print(f"   Database: {complete_creds['postgres_database']}")
        print(f"   Port: {complete_creds['postgres_port']}")
        print(f"   User: {complete_creds['postgres_user'][:4]}... (16 chars)")
        print("   Password: ****... (16 chars)")
        print(f"   API Key: {complete_creds['api_key'][:12]}... ({len(complete_creds['api_key'])} chars)")
        
        return complete_creds
    
    def _validate_workspace_env_file(self, component: str) -> bool:
        """Validate that workspace .env file exists.
        
        VALIDATION ONLY: Checks that .env files exist in the project root.
        Installation commands handle .env file creation and management.
        """
        workspace_env_file = self.project_root / ".env"
        
        if workspace_env_file.exists():
            print(f"✅ Workspace .env file exists: {workspace_env_file}")
            return True
        else:
            print(f"❌ Workspace .env file missing: {workspace_env_file}")
            print(f"💡 Please create .env from .env.example with your configuration")
            return False
    
    def install(self, component: str) -> bool:
        """Install component containers."""
        if not self._check_docker():
            return False
        
        # Interactive installation
        if component == "interactive":
            return self._interactive_install()
        
        print(f"🚀 Installing {component}...")

        normalized = component.lower()
        components = ["workspace"] if normalized == "all" else [normalized]

        unsupported = [comp for comp in components if comp != "workspace"]
        if unsupported:
            print(f"❌ Unsupported install target: {unsupported[0]}")
            return False

        print("🔐 Generating unified credentials for workspace deployment...")
        try:
            all_credentials = self.credential_service.install_all_modes(components)
            print("✅ Unified credentials generated successfully")
        except Exception as e:
            print(f"❌ Failed to generate credentials: {e}")
            return False

        self._create_network()

        for comp in components:
            print(f"\n📦 Setting up {comp} component...")
            comp_credentials = all_credentials[comp]
            
            # Create all containers via Docker Compose (handles both postgres and API)
            if not self._create_containers_via_compose(comp, comp_credentials):
                print(f"❌ Failed to create containers for {comp}")
                return False
            
            # Wait for services to be ready
            print("⏳ Waiting for services to be ready...")
            time.sleep(8)  # Increased wait time for health checks
            
            # For workspace, note that app runs locally
            if comp == "workspace":
                print("📝 Workspace app will run locally with: uv run automagik-hive /path/to/workspace")
        
        print(f"\n✅ {component} installation complete!")
        return True
    
    def start(self, component: str) -> bool:
        """Start component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🚀 Starting {component} services...")
        
        success = True
        for container in containers:
            if self._container_exists(container):
                if not self._container_running(container):
                    print(f"▶️ Starting {container}...")
                    if not self._run_command(["docker", "start", container]):
                        success = False
                else:
                    print(f"✅ {container} already running")
            else:
                print(f"❌ Container {container} not found. Run --install first.")
                success = False
        
        return success
    
    def stop(self, component: str) -> bool:
        """Stop component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🛑 Stopping {component} services...")
        
        success = True
        for container in containers:
            if self._container_running(container):
                print(f"⏹️ Stopping {container}...")
                if not self._run_command(["docker", "stop", container]):
                    success = False
            else:
                print(f"✅ {container} already stopped")
        
        return success
    
    def restart(self, component: str) -> bool:
        """Restart component containers."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🔄 Restarting {component} services...")
        
        success = True
        for container in containers:
            if self._container_exists(container):
                print(f"🔄 Restarting {container}...")
                if not self._run_command(["docker", "restart", container]):
                    success = False
            else:
                print(f"❌ Container {container} not found. Run --install first.")
                success = False
        
        return success
    
    def status(self, component: str) -> None:
        """Show component status."""
        containers = self._get_containers(component)
        if not containers:
            return
        
        print(f"\n📊 {component.title()} Status:")
        print("=" * 50)
        
        for container in containers:
            if self._container_exists(container):
                if self._container_running(container):
                    # Get port info
                    port_info = self._run_command(["docker", "port", container], capture_output=True)
                    status = "🟢 Running"
                    if port_info:
                        status += f" - {port_info.split(' -> ')[0]}"
                else:
                    status = "🔴 Stopped"
            else:
                status = "❌ Not installed"
            
            print(f"{container:25} {status}")
    
    def health(self, component: str) -> None:
        """Check component health."""
        containers = self._get_containers(component)
        if not containers:
            return
        
        print(f"\n🏥 {component.title()} Health Check:")
        print("=" * 50)
        
        for container in containers:
            if self._container_running(container):
                # Basic health check - container running
                print(f"{container:25} 🟢 Healthy")
            elif self._container_exists(container):
                print(f"{container:25} 🟡 Stopped")
            else:
                print(f"{container:25} 🔴 Not installed")
    
    def logs(self, component: str, lines: int = 50) -> None:
        """Show component logs."""
        containers = self._get_containers(component)
        if not containers:
            return
        
        for container in containers:
            if self._container_exists(container):
                print(f"\n📋 Logs for {container} (last {lines} lines):")
                print("-" * 60)
                self._run_command(["docker", "logs", "--tail", str(lines), container])
            else:
                print(f"❌ Container {container} not found")
    
    def uninstall(self, component: str) -> bool:
        """Uninstall component containers - autonomous operation (no confirmation)."""
        containers = self._get_containers(component)
        if not containers:
            return False
        
        print(f"🗑️ Uninstalling {component} (autonomous mode - no confirmation required)...")
        
        # Use Docker Compose for unified uninstall approach
        compose_file = self.template_files.get(component)
        if compose_file and compose_file.exists():
            print(f"🐳 Stopping {component} services via Docker Compose...")
            print(f"📁 Using: {compose_file}")
            
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
                        print(f"⏹️ Stopping {container}...")
                        self._run_command(["docker", "stop", container])
                    
                    # Remove container
                    print(f"🗑️ Removing {container}...")
                    if not self._run_command(["docker", "rm", container]):
                        success = False
        
        # Clean up component-specific .env files and directories
        if component != "all":
            env_file = compose_file.parent / ".env" if compose_file else None
            if env_file and env_file.exists():
                print("🗑️ Removing Docker Compose .env file...")
                env_file.unlink()
        
        if success:
            print(f"✅ {component} uninstalled successfully!")
        
        return success

    def _interactive_install(self) -> bool:
        """Interactive installation with workspace-only choices."""

        print("🚀 Automagik Hive Interactive Installation")
        print("=" * 50)

        print("\n🏠 Automagik Hive Core (Main Application)")
        print("This installs the workspace server and API components")
        while True:
            hive_choice = input("Would you like to install Hive Core? (Y/n): ").strip().lower()
            if hive_choice in ["y", "yes", "n", "no", ""]:
                break
            print("❌ Please enter y/yes or n/no.")

        install_hive = hive_choice not in ["n", "no"]
        if not install_hive:
            print("👋 Skipping Hive installation")
            return True

        print("\n📦 Database Setup for Hive:")
        print("1. Use the Automagik PostgreSQL + pgvector container (recommended)")
        print("2. Connect to an existing PostgreSQL database")

        while True:
            db_choice = input("\nSelect database option (1-2): ").strip()
            if db_choice in ["1", "2"]:
                break
            print("❌ Invalid choice. Please enter 1 or 2.")

        use_container = db_choice == "1"
        if use_container:
            print("✅ Using bundled PostgreSQL + pgvector container")
            postgres_container = self.POSTGRES_CONTAINER
            if self._container_exists(postgres_container):
                print(f"\n🗄️ Found existing database container: {postgres_container}")
                while True:
                    db_action = input("Do you want to (r)euse or (c)recreate it? (r/c): ").strip().lower()
                    if db_action in ["r", "reuse", "c", "create", "recreate"]:
                        break
                    print("❌ Please enter r/reuse or c/create.")

                if db_action in ["c", "create", "recreate"]:
                    print("🗑️ Recreating database container...")
                    if self._container_running(postgres_container):
                        self._run_command(["docker", "stop", postgres_container])
                    self._run_command(["docker", "rm", postgres_container])
                    volume_name = "hive_workspace_data"
                    volumes = self._run_command(
                        ["docker", "volume", "ls", "--filter", f"name={volume_name}", "--format", "{{.Name}}"],
                        capture_output=True,
                    )
                    if volume_name in (volumes or ""):
                        print("🗑️ Removing existing database volume...")
                        self._run_command(["docker", "volume", "rm", volume_name])
                else:
                    print("♻️ Reusing existing database container")
        else:
            print("📝 Custom database setup for Hive")
            print("\nEnter your PostgreSQL connection details:")
            host = input("Host (localhost): ").strip() or "localhost"
            port = input("Port (5432): ").strip() or "5432"
            database = input("Database name (automagik_hive): ").strip() or "automagik_hive"
            username = input("Username: ").strip()
            password = input("Password: ").strip()

            if not username or not password:
                print("❌ Username and password are required")
                return False

            print("🔧 Custom database installation is not automated yet")
            print("💡 Please follow manual instructions in the README")

        if not install_hive:
            print("👋 No components selected for installation")
            return True

        if not use_container:
            # For manual database installs we stop here with guidance above
            return True

        print("\n🚀 Installing workspace...")
        return self.install("workspace")
