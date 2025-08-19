"""Docker Manager - Simple container operations."""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from lib.auth.credential_service import CredentialService


class DockerManager:
    """Simple Docker operations manager."""
    
    # Container definitions (must match Docker Compose naming)
    CONTAINERS = {
        "agent": {
            "postgres": "hive-agent-postgres",  # Matches docker/agent/docker-compose.yml
            "api": "hive-agent-api"             # Matches docker/agent/docker-compose.yml
        },
        "workspace": {
            "postgres": "hive-main-postgres"    # Matches docker/main/docker-compose.yml
            # Note: workspace app runs locally, no API container
        }
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
            "HIVE_WORKSPACE_POSTGRES_PORT": "workspace postgres",
            "HIVE_AGENT_POSTGRES_PORT": "agent postgres",
            "HIVE_AGENT_API_PORT": "agent api",
            "HIVE_GENIE_POSTGRES_PORT": "genie postgres",
            "HIVE_GENIE_API_PORT": "genie api"
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
            "workspace": {
                "postgres": int(os.getenv("HIVE_WORKSPACE_POSTGRES_PORT"))
            },
            "agent": {
                "postgres": int(os.getenv("HIVE_AGENT_POSTGRES_PORT")),
                "api": int(os.getenv("HIVE_AGENT_API_PORT"))
            },
            "genie": {
                "postgres": int(os.getenv("HIVE_GENIE_POSTGRES_PORT")),
                "api": int(os.getenv("HIVE_GENIE_API_PORT"))
            }
        }
    
    def _get_ports(self) -> Dict[str, Dict[str, int]]:
        """Get port mappings from environment variables."""
        return self.PORTS
    
    def __init__(self):
        self.project_root = Path.cwd()
        
        # Map component to docker template file
        self.template_files = {
            "workspace": self.project_root / "docker/main/docker-compose.yml",
            "agent": self.project_root / "docker/agent/docker-compose.yml"
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
        """Get container names for component."""
        if component == "all":
            containers = []
            for comp in self.CONTAINERS:
                containers.extend(self.CONTAINERS[comp].values())
            return containers
        if component in self.CONTAINERS:
            return list(self.CONTAINERS[component].values())
        print(f"❌ Unknown component: {component}")
        return []
    
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
        networks = self._run_command(["docker", "network", "ls", "--filter", "name=hive-network", "--format", "{{.Name}}"], capture_output=True)
        if "hive-network" not in (networks or ""):
            print("🔗 Creating Docker network...")
            self._run_command(["docker", "network", "create", "hive-network"])
    
    def _get_dockerfile_path(self, component: str) -> Path:
        """Get the Dockerfile path for a component."""
        dockerfile_mapping = {
            "workspace": self.project_root / "docker" / "main" / "Dockerfile",
            "agent": self.project_root / "docker" / "agent" / "Dockerfile.api"
        }
        
        return dockerfile_mapping.get(component, self.project_root / "docker" / "main" / "Dockerfile")
    
    def _get_postgres_image(self, component: str) -> str:
        """Get PostgreSQL image from docker compose template."""
        template_file = self.template_files.get(component)
        if not template_file or not template_file.exists():
            # Fallback to defaults
            fallback_images = {
                "workspace": "agnohq/pgvector:16",
                "agent": "pgvector/pgvector:pg16"
            }
            return fallback_images.get(component, "agnohq/pgvector:16")
        
        try:
            with open(template_file) as f:
                compose_data = yaml.safe_load(f)
            
            # Look for postgres service image
            services = compose_data.get("services", {})
            for service_name, service_config in services.items():
                if "postgres" in service_name.lower() or service_name == "postgres":
                    return service_config.get("image", "agnohq/pgvector:16")
            
            # Fallback if no postgres service found
            return "agnohq/pgvector:16"
            
        except Exception:
            # Fallback on any error
            return "agnohq/pgvector:16"
    
    def _create_containers_via_compose(self, component: str, credentials: dict) -> bool:
        """Create containers using Docker Compose for consistency with Makefile."""
        compose_file = self.template_files.get(component)
        if not compose_file or not compose_file.exists():
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
            "agent": self.project_root / "data" / "postgres-agent",
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
        container_name = self.CONTAINERS[component]["postgres"]
        
        if self._container_exists(container_name):
            print(f"✅ PostgreSQL container {container_name} already exists")
            return True
        
        # Use Docker Compose approach for consistency with Makefile
        return self._create_containers_via_compose(component, credentials)
    
    def _create_api_container(self, component: str, credentials: dict) -> bool:
        """Create API container - now handled by Docker Compose for consistency."""
        container_name = self.CONTAINERS[component]["api"]
        
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
        
        # For agent component, try to reuse workspace credentials if available
        if component == "agent":
            workspace_env = self.project_root / "docker" / "main" / ".env"
            if workspace_env.exists():
                workspace_service = CredentialService(workspace_env)
                workspace_creds = workspace_service.extract_postgres_credentials_from_env()
                if workspace_creds.get("user") and workspace_creds.get("password"):
                    print("🔗 Reusing workspace credentials for agent (unified approach)")
                    api_key = component_credential_service.generate_hive_api_key()
                    
                    # Build credentials in format expected by CredentialService
                    postgres_creds_for_save = {
                        "user": workspace_creds["user"],
                        "password": workspace_creds["password"],
                        "database": postgres_database,
                        "host": "localhost",
                        "port": str(postgres_port),
                        "url": f"postgresql+psycopg://{workspace_creds['user']}:{workspace_creds['password']}@localhost:{postgres_port}/{postgres_database}"
                    }
                    
                    # Save to component .env file
                    component_credential_service.save_credentials_to_env(
                        postgres_creds=postgres_creds_for_save,
                        api_key=api_key,
                        create_if_missing=True
                    )
                    
                    # Return in format expected by DockerManager
                    credentials = {
                        "postgres_user": workspace_creds["user"],
                        "postgres_password": workspace_creds["password"],
                        "postgres_database": postgres_database,
                        "postgres_host": "localhost",
                        "postgres_port": str(postgres_port),
                        "api_key": api_key
                    }
                    return credentials
        
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
        
        # Generate unified credentials ONCE for all modes
        components = ["agent", "workspace"] if component == "all" else [component]
        
        print("🔐 Generating unified credentials for all deployment modes...")
        try:
            all_credentials = self.credential_service.install_all_modes(components)
            print("✅ Unified credentials generated successfully")
        except Exception as e:
            print(f"❌ Failed to generate credentials: {e}")
            return False
        
        self._create_network()
        
        for comp in components:
            if comp not in self.CONTAINERS:
                print(f"❌ Unknown component: {comp}")
                return False
            
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
        """Interactive installation with user choices."""
        print("🚀 Automagik Hive Interactive Installation")
        print("=" * 50)
        
        # 1. Main Hive installation
        print("\n🏠 Automagik Hive Core (Main Application)")
        print("This includes the workspace server and web interface")
        while True:
            hive_choice = input("Would you like to install Hive Core? (Y/n): ").strip().lower()
            if hive_choice in ["y", "yes", "n", "no", ""]:
                break
            print("❌ Please enter y/yes or n/no.")
        
        install_hive = hive_choice not in ["n", "no"]
        
        if not install_hive:
            print("👋 Skipping Hive installation")
            return True
        
        # Database setup for Hive
        print("\n📦 Database Setup for Hive:")
        print("1. Use our PostgreSQL + pgvector container (recommended)")
        print("   → PostgreSQL 15 with pgvector extension for AI/RAG capabilities")
        print("2. Use existing PostgreSQL database")
        print("   → Connect to your own PostgreSQL instance")
        
        while True:
            db_choice = input("\nSelect database option (1-2): ").strip()
            if db_choice in ["1", "2"]:
                break
            print("❌ Invalid choice. Please enter 1 or 2.")
        
        if db_choice == "1":
            print("✅ Using PostgreSQL + pgvector container for Hive")
            use_container = True
            
            # Check if database already exists and prompt for reuse/recreate
            postgres_container = self.CONTAINERS["workspace"]["postgres"]
            if self._container_exists(postgres_container):
                print(f"\n🗄️ Found existing database container: {postgres_container}")
                while True:
                    db_action = input("Do you want to (r)euse existing database or (c)recreate it? (r/c): ").strip().lower()
                    if db_action in ["r", "reuse", "c", "create", "recreate"]:
                        break
                    print("❌ Please enter r/reuse or c/create.")
                
                if db_action in ["c", "create", "recreate"]:
                    print("🗑️ Recreating database container...")
                    # Stop and remove existing container
                    if self._container_running(postgres_container):
                        self._run_command(["docker", "stop", postgres_container])
                    self._run_command(["docker", "rm", postgres_container])
                    # Remove volume to ensure clean slate
                    volume_name = "hive_workspace_data"
                    volumes = self._run_command(["docker", "volume", "ls", "--filter", f"name={volume_name}", "--format", "{{.Name}}"], capture_output=True)
                    if volume_name in (volumes or ""):
                        print("🗑️ Removing existing database volume...")
                        self._run_command(["docker", "volume", "rm", volume_name])
                else:
                    print("♻️ Reusing existing database container")
        else:
            print("📝 Custom database setup for Hive")
            use_container = False
            
            # Ask for credentials
            print("\nEnter your PostgreSQL connection details:")
            host = input("Host (localhost): ").strip() or "localhost"
            port = input("Port (5432): ").strip() or "5432"
            database = input("Database name (automagik_hive): ").strip() or "automagik_hive"
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            if not username or not password:
                print("❌ Username and password are required")
                return False
        
        # Get input for additional components only if Hive is being installed
        install_genie = False
        install_agent = False
        
        if install_hive:
            # 2. Genie installation
            print("\n🧞 Genie (AI Agent Assistant)")
            while True:
                genie_choice = input("Would you like to install Genie? (y/N): ").strip().lower()
                if genie_choice in ["y", "yes", "n", "no", ""]:
                    break
                print("❌ Please enter y/yes or n/no.")
            
            install_genie = genie_choice in ["y", "yes"]
            
            # 3. Agent Workspace installation
            print("\n🤖 Agent Workspace (Optional)")
            print("Separate isolated testing environment for agents (different from main Hive)")
            while True:
                agent_choice = input("Would you like to install Agent Workspace? (y/N): ").strip().lower()
                if agent_choice in ["y", "yes", "n", "no", ""]:
                    break
                print("❌ Please enter y/yes or n/no.")
            
            install_agent = agent_choice in ["y", "yes"]
        
        # Determine what to install
        components_to_install = []
        if install_hive:
            components_to_install.append("workspace")
        if install_agent:
            components_to_install.append("agent")
        
        if not components_to_install:
            print("👋 No components selected for installation")
            return True
        
        # Install selected components
        success = True
        for component in components_to_install:
            print(f"\n🚀 Installing {component}...")
            if use_container:
                if not self.install(component):
                    success = False
                    break
            else:
                # Custom database installation (simplified for now)
                print("🔧 Custom database installation not fully implemented yet")
                print(f"💡 For now, please use: uv run python -m cli.main --install {component}")
        
        if install_genie:
            print("\n🧞 Genie installation not yet implemented")
            print("💡 Coming soon in future updates!")
        
        return success
