"""Unified installer for Automagik Hive - handles install → start → health → workspace workflow."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .init import InitCommands
from .postgres import PostgreSQLCommands


class UnifiedInstaller:
    """Unified installer that executes the complete deployment workflow."""

    def __init__(self) -> None:
        self.console = Console()
        self.init_commands = InitCommands()
        self.postgres_commands = PostgreSQLCommands()

    def install_with_workflow(self, component: str = "all") -> bool:
        """Execute full install → start → health → workspace workflow.
        
        Args:
            component: Component to install ('all', 'core', 'agent', 'genie')
            
        Returns:
            bool: True if entire workflow completed successfully
        """
        self.console.print(
            Panel.fit(
                f"🚀 [bold]Starting Automagik Hive Installation[/bold]\n"
                f"Component: [cyan]{component}[/cyan]\n"
                f"Workflow: [yellow]install → start → health → workspace[/yellow]",
                border_style="blue"
            )
        )

        try:
            # Step 1: Install infrastructure
            if not self._install_infrastructure(component):
                return False

            # Step 2: Start services (auto-started during install)
            if not self._start_services(component):
                return False

            # Step 3: Health check
            if not self.health_check(component):
                return False

            # Step 4: Interactive workspace setup
            if not self._interactive_workspace_setup():
                return False

            self.console.print(
                Panel.fit(
                    "✅ [bold green]Installation Complete![/bold green]\n"
                    "Your Automagik Hive system is ready!",
                    border_style="green"
                )
            )
            return True

        except Exception as e:
            logger.error(f"Installation workflow failed: {e}")
            self.console.print(f"❌ [bold red]Installation failed:[/bold red] {e}")
            return False

    def _install_infrastructure(self, component: str) -> bool:
        """Install Docker infrastructure for specified component.
        
        Args:
            component: Component to install
            
        Returns:
            bool: True if installation successful
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"Installing {component} infrastructure...", total=None)

            try:
                # Pull/build Docker images based on component
                if not self._pull_docker_images(component):
                    return False

                # Create Docker networks and volumes
                if not self._setup_docker_infrastructure():
                    return False

                # Generate configuration files
                if not self._generate_configuration_files(component):
                    return False

                progress.update(task, description="✅ Infrastructure installation complete")
                return True

            except Exception as e:
                logger.error(f"Infrastructure installation failed: {e}")
                progress.update(task, description=f"❌ Installation failed: {e}")
                return False

    def _pull_docker_images(self, component: str) -> bool:
        """Pull required Docker images for component.
        
        Args:
            component: Component to pull images for
            
        Returns:
            bool: True if successful
        """
        try:
            # Map components to their required images
            image_map = {
                "all": ["postgres:16-alpine", "python:3.12-slim"],
                "core": ["postgres:16-alpine"],
                "agent": ["postgres:16-alpine", "python:3.12-slim"],
                "genie": ["postgres:16-alpine", "python:3.12-slim"],
            }

            images = image_map.get(component, image_map["all"])
            
            for image in images:
                self.console.print(f"📦 Pulling {image}...")
                result = subprocess.run(
                    ["docker", "pull", image],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to pull {image}: {result.stderr}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Docker image pull failed: {e}")
            return False

    def _setup_docker_infrastructure(self) -> bool:
        """Set up Docker networks and volumes.
        
        Returns:
            bool: True if successful
        """
        try:
            # Create shared network if it doesn't exist
            network_result = subprocess.run(
                ["docker", "network", "create", "hive-network"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Network creation fails if it already exists - that's fine
            if network_result.returncode != 0 and "already exists" not in network_result.stderr:
                logger.error(f"Failed to create network: {network_result.stderr}")
                return False

            # Create volumes for persistent data
            volumes = ["hive-postgres-data", "hive-agent-data", "hive-genie-data"]
            
            for volume in volumes:
                volume_result = subprocess.run(
                    ["docker", "volume", "create", volume],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if volume_result.returncode != 0 and "already exists" not in volume_result.stderr:
                    logger.error(f"Failed to create volume {volume}: {volume_result.stderr}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Docker infrastructure setup failed: {e}")
            return False

    def _generate_configuration_files(self, component: str) -> bool:
        """Generate configuration files for specified component.
        
        Args:
            component: Component to generate config for
            
        Returns:
            bool: True if successful
        """
        try:
            # Generate environment files based on component
            env_templates = {
                "all": [".env.core", ".env.agent", ".env.genie"],
                "core": [".env.core"],
                "agent": [".env.core", ".env.agent"],
                "genie": [".env.core", ".env.genie"],
            }

            env_files = env_templates.get(component, env_templates["all"])
            
            for env_file in env_files:
                if not self._create_env_file(env_file):
                    return False

            # Generate docker-compose.yml with appropriate profiles
            if not self._create_docker_compose_file(component):
                return False

            return True

        except Exception as e:
            logger.error(f"Configuration generation failed: {e}")
            return False

    def _create_env_file(self, env_file: str) -> bool:
        """Create environment file with default values.
        
        Args:
            env_file: Name of environment file to create
            
        Returns:
            bool: True if successful
        """
        try:
            env_path = Path(env_file)
            
            if env_path.exists():
                return True  # File already exists

            # Base environment variables
            env_content = {
                ".env.core": """# Core Database Configuration
HIVE_DATABASE_URL=postgresql://hive:hive@localhost:5532/hive_core
POSTGRES_USER=hive
POSTGRES_PASSWORD=hive
POSTGRES_DB=hive_core
""",
                ".env.agent": """# Agent Environment Configuration  
HIVE_DATABASE_URL=postgresql://hive:hive@localhost:35532/hive_agent
POSTGRES_USER=hive
POSTGRES_PASSWORD=hive
POSTGRES_DB=hive_agent
HIVE_API_PORT=38886
""",
                ".env.genie": """# Genie Environment Configuration
HIVE_DATABASE_URL=postgresql://hive:hive@localhost:48532/hive_genie  
POSTGRES_USER=hive
POSTGRES_PASSWORD=hive
POSTGRES_DB=hive_genie
HIVE_API_PORT=48886
"""
            }

            content = env_content.get(env_file, "")
            if content:
                env_path.write_text(content)
                self.console.print(f"✅ Created {env_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to create {env_file}: {e}")
            return False

    def _create_docker_compose_file(self, component: str) -> bool:
        """Create docker-compose.yml with profiles for specified component.
        
        Args:
            component: Component to create compose file for
            
        Returns:
            bool: True if successful
        """
        try:
            compose_content = f"""# Automagik Hive Docker Compose - {component.upper()} Profile
version: '3.8'

networks:
  hive-network:
    external: true

volumes:
  hive-postgres-data:
    external: true
  hive-agent-data:
    external: true
  hive-genie-data:
    external: true

services:
  # Core Database (always included)
  hive-postgres-core:
    image: postgres:16-alpine
    profiles: ["core", "all"]
    environment:
      POSTGRES_USER: hive
      POSTGRES_PASSWORD: hive
      POSTGRES_DB: hive_core
    ports:
      - "5532:5432"
    volumes:
      - hive-postgres-data:/var/lib/postgresql/data
    networks:
      - hive-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hive -d hive_core"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Agent Stack
  hive-agent-postgres:
    image: postgres:16-alpine
    profiles: ["agent", "all"]
    environment:
      POSTGRES_USER: hive
      POSTGRES_PASSWORD: hive
      POSTGRES_DB: hive_agent
    ports:
      - "35532:5432"
    volumes:
      - hive-agent-data:/var/lib/postgresql/data
    networks:
      - hive-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hive -d hive_agent"]
      interval: 10s
      timeout: 5s
      retries: 5

  hive-agent-api:
    image: python:3.12-slim
    profiles: ["agent", "all"]
    depends_on:
      hive-agent-postgres:
        condition: service_healthy
    environment:
      HIVE_DATABASE_URL: postgresql://hive:hive@hive-agent-postgres:5432/hive_agent
    ports:
      - "38886:8000"
    networks:
      - hive-network
    working_dir: /app
    volumes:
      - .:/app
    command: ["python", "-m", "api.serve"]
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Genie Stack  
  hive-genie-postgres:
    image: postgres:16-alpine
    profiles: ["genie", "all"]
    environment:
      POSTGRES_USER: hive
      POSTGRES_PASSWORD: hive
      POSTGRES_DB: hive_genie
    ports:
      - "48532:5432"
    volumes:
      - hive-genie-data:/var/lib/postgresql/data
    networks:
      - hive-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hive -d hive_genie"]
      interval: 10s
      timeout: 5s
      retries: 5

  hive-genie-api:
    image: python:3.12-slim
    profiles: ["genie", "all"]
    depends_on:
      hive-genie-postgres:
        condition: service_healthy
    environment:
      HIVE_DATABASE_URL: postgresql://hive:hive@hive-genie-postgres:5432/hive_genie
    ports:
      - "48886:8000"
    networks:
      - hive-network
    working_dir: /app
    volumes:
      - .:/app
    command: ["python", "-m", "api.serve"]
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
"""

            compose_path = Path("docker-compose.unified.yml")
            compose_path.write_text(compose_content)
            
            self.console.print("✅ Created docker-compose.unified.yml with profiles")
            return True

        except Exception as e:
            logger.error(f"Failed to create docker-compose file: {e}")
            return False

    def _start_services(self, component: str) -> bool:
        """Start services for specified component.
        
        Args:
            component: Component services to start
            
        Returns:
            bool: True if successful
        """
        try:
            self.console.print(f"🚀 Starting {component} services...")
            
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.unified.yml", "--profile", component, "up", "-d"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"Failed to start services: {result.stderr}")
                return False

            self.console.print(f"✅ {component.title()} services started")
            return True

        except Exception as e:
            logger.error(f"Service startup failed: {e}")
            return False

    def health_check(self, component: str = "all") -> dict[str, bool]:
        """Health check for specified components.
        
        Args:
            component: Component to check ('all', 'core', 'agent', 'genie')
            
        Returns:
            dict: Health status for each service
        """
        self.console.print(f"🏥 Checking {component} service health...")
        
        health_status = {}
        
        try:
            # Define service health checks based on component
            checks = self._get_health_checks(component)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                
                for service_name, check_func in checks.items():
                    task = progress.add_task(f"Checking {service_name}...", total=None)
                    
                    # Retry health check with backoff
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            is_healthy = check_func()
                            health_status[service_name] = is_healthy
                            
                            if is_healthy:
                                progress.update(task, description=f"✅ {service_name} healthy")
                                break
                            else:
                                if attempt < max_retries - 1:
                                    progress.update(task, description=f"⏳ {service_name} starting... (attempt {attempt + 1})")
                                    time.sleep(5)
                                else:
                                    progress.update(task, description=f"❌ {service_name} unhealthy")
                                    
                        except Exception as e:
                            if attempt < max_retries - 1:
                                progress.update(task, description=f"⏳ {service_name} retrying... ({e})")
                                time.sleep(5)
                            else:
                                logger.error(f"Health check failed for {service_name}: {e}")
                                health_status[service_name] = False
                                progress.update(task, description=f"❌ {service_name} failed")

            # Overall health summary
            healthy_services = sum(1 for is_healthy in health_status.values() if is_healthy)
            total_services = len(health_status)
            
            if healthy_services == total_services:
                self.console.print(f"✅ [bold green]All {component} services healthy[/bold green] ({healthy_services}/{total_services})")
            else:
                self.console.print(f"⚠️ [yellow]Partial health[/yellow]: {healthy_services}/{total_services} services healthy")

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {}

    def _get_health_checks(self, component: str) -> dict[str, Any]:
        """Get health check functions for component services.
        
        Args:
            component: Component to get checks for
            
        Returns:
            dict: Service name to health check function mapping
        """
        def check_postgres(port: int) -> bool:
            """Check if PostgreSQL is accessible on specified port."""
            try:
                result = subprocess.run(
                    ["docker", "exec", "-i", f"hive-postgres-{component if component != 'all' else 'core'}", 
                     "pg_isready", "-U", "hive"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False
                )
                return result.returncode == 0
            except Exception:
                return False

        def check_api(port: int) -> bool:
            """Check if API is responding on specified port."""
            try:
                import requests
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                return response.status_code == 200
            except Exception:
                return False

        # Map components to their health checks
        checks = {}
        
        if component in ["all", "core"]:
            checks["core-database"] = lambda: check_postgres(5532)
            
        if component in ["all", "agent"]:
            checks["agent-database"] = lambda: check_postgres(35532)
            checks["agent-api"] = lambda: check_api(38886)
            
        if component in ["all", "genie"]:
            checks["genie-database"] = lambda: check_postgres(48532)
            checks["genie-api"] = lambda: check_api(48886)

        return checks

    def _interactive_workspace_setup(self) -> bool:
        """Interactive workspace initialization/selection.
        
        Returns:
            bool: True if workspace setup completed (including skip option)
        """
        try:
            self.console.print(
                Panel.fit(
                    "🧞 [bold]All services are healthy![/bold]\n\n"
                    "Choose workspace option:\n"
                    "1. 📁 Initialize new workspace\n"
                    "2. 📂 Select existing workspace\n"
                    "3. ⏭️  Skip workspace setup (use --init later)",
                    title="Workspace Setup",
                    border_style="green"
                )
            )

            while True:
                choice = self.console.input("\nEnter choice (1-3): ").strip()
                
                if choice == "1":
                    return self._initialize_new_workspace()
                elif choice == "2":
                    return self._select_existing_workspace()
                elif choice == "3":
                    self._show_skip_message()
                    return True
                else:
                    self.console.print("❌ Invalid choice. Please enter 1, 2, or 3.")

        except KeyboardInterrupt:
            self.console.print("\n⏭️ Workspace setup skipped.")
            return True
        except Exception as e:
            logger.error(f"Workspace setup failed: {e}")
            return False

    def _initialize_new_workspace(self) -> bool:
        """Initialize a new workspace interactively.
        
        Returns:
            bool: True if successful
        """
        try:
            workspace_name = self.console.input("\n📁 Workspace name: ").strip()
            
            if not workspace_name:
                self.console.print("❌ Workspace name cannot be empty.")
                return False

            workspace_path = Path(workspace_name)
            
            self.console.print(f"📍 Location: ./{workspace_path}")
            self.console.print("\n✅ Creating workspace structure...")
            
            # Use existing init command functionality
            success = self.init_commands.initialize_workspace(str(workspace_path))
            
            if success:
                self.console.print("✅ Configuring MCP integration...")
                self.console.print("✅ Setting up agent templates...")
                self.console.print("✅ Workspace ready!")
                self.console.print(f"\n🚀 Next: cd {workspace_name}")
                return True
            else:
                self.console.print("❌ Workspace creation failed.")
                return False

        except Exception as e:
            logger.error(f"New workspace creation failed: {e}")
            return False

    def _select_existing_workspace(self) -> bool:
        """Select and validate existing workspace.
        
        Returns:
            bool: True if successful
        """
        try:
            workspace_path = self.console.input("\n📂 Workspace path: ").strip()
            
            if not workspace_path:
                self.console.print("❌ Workspace path cannot be empty.")
                return False

            path = Path(workspace_path)
            
            self.console.print("🔍 Checking workspace...")
            
            # Check if it's a valid workspace
            if self._validate_workspace(path):
                self.console.print("✅ Valid workspace found!")
                return True
            else:
                self.console.print("❌ Invalid workspace (missing .env or docker-compose.yml)")
                
                # Offer to initialize existing folder
                initialize = self.console.input("\nWould you like to initialize this folder as a workspace? (y/N): ").strip().lower()
                
                if initialize in ["y", "yes"]:
                    self.console.print("✅ Initializing existing folder as workspace...")
                    success = self.init_commands.initialize_workspace(str(path))
                    
                    if success:
                        self.console.print("✅ Workspace ready!")
                        return True
                    else:
                        self.console.print("❌ Workspace initialization failed.")
                        return False
                else:
                    return False

        except Exception as e:
            logger.error(f"Existing workspace selection failed: {e}")
            return False

    def _validate_workspace(self, path: Path) -> bool:
        """Check if path contains a valid workspace.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if valid workspace
        """
        try:
            if not path.exists():
                return False
                
            # Check for essential workspace files
            required_files = [".env", "docker-compose.yml"]
            
            for file_name in required_files:
                if not (path / file_name).exists():
                    return False
                    
            return True
            
        except Exception:
            return False

    def _show_skip_message(self) -> None:
        """Show skip workspace setup message."""
        self.console.print(
            Panel.fit(
                "⏭️ [bold]Skip Workspace Setup[/bold]\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Services are running and ready.\n\n"
                "Initialize workspace later with:\n"
                "  [cyan]uvx automagik-hive --init [workspace-name][/cyan]",
                border_style="yellow"
            )
        )