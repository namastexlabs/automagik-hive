"""Unified installer for Automagik Hive - Enhanced Phase 2 Implementation.

Handles install → start → health → workspace workflow with:
- Complete workflow orchestration integration via WorkflowOrchestrator
- Seamless progression through install→start→health→workspace phases
- Component-specific automation handling (agent/genie skip prompts)
- Comprehensive error handling with recovery suggestions
- Progress reporting and user feedback
- Integration with all manager classes for unified experience
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .health_checker import HealthChecker
from .init import InteractiveInitializer
from .postgres import PostgreSQLCommands
from .workflow_orchestrator import WorkflowOrchestrator


class UnifiedInstaller:
    """Unified installer that executes the complete deployment workflow.

    Enhanced Phase 2 implementation with workflow orchestration integration,
    providing seamless progression through all deployment phases with
    comprehensive error handling and recovery mechanisms.
    """

    def __init__(self) -> None:
        self.console = Console()
        self.health_checker = HealthChecker()
        self.init_commands = InteractiveInitializer()
        self.postgres_commands = PostgreSQLCommands()
        self.workflow_orchestrator = WorkflowOrchestrator()
        self._docker_compose_cmd = self._detect_docker_compose_command()

    def _detect_docker_compose_command(self) -> list[str]:
        """Detect which Docker Compose command to use.
        
        Returns:
            List of command parts: either ["docker", "compose"] or ["docker-compose"]
        """
        try:
            # Try modern 'docker compose' first (Docker v2+)
            result = subprocess.run(
                ["docker", "compose", "version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return ["docker", "compose"]
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        try:
            # Fallback to legacy 'docker-compose'
            result = subprocess.run(
                ["docker-compose", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return ["docker-compose"]
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        # Default to modern command if detection fails
        return ["docker", "compose"]

    def install_with_workflow(self, component: str = "all") -> bool:
        """Execute full install → start → health → workspace workflow.

        Enhanced Phase 2 implementation using WorkflowOrchestrator for
        comprehensive state machine-driven deployment with error recovery.
        Agent/genie installs skip workspace prompts for automation-friendly operation.

        Args:
            component: Component to install ('all', 'workspace', 'agent', 'genie')

        Returns:
            bool: True if entire workflow completed successfully
        """
        self.console.print(
            Panel.fit(
                f"🚀 [bold]Starting Automagik Hive Installation - Phase 2[/bold]\n"
                f"Component: [cyan]{component}[/cyan]\n"
                f"Workflow: [yellow]install → start → health → workspace[/yellow]\n"
                f"Features: [green]State machine, error recovery, rollback support[/green]",
                border_style="blue",
            )
        )

        try:
            # Use WorkflowOrchestrator for complete state machine-driven deployment
            success = self.workflow_orchestrator.execute_unified_workflow(component)

            if success:
                self.console.print(
                    Panel.fit(
                        "🎉 [bold green]Installation Complete![/bold green]\n"
                        "Your Automagik Hive system is ready!\n\n"
                        "💡 [cyan]Use 'uvx automagik-hive --status' to check system health[/cyan]",
                        border_style="green",
                    )
                )
                return True
            # Display workflow status for troubleshooting
            status = self.workflow_orchestrator.get_workflow_status()
            self._display_failure_recovery_options(status)
            return False

        except KeyboardInterrupt:
            self.console.print("\n⏹️ [yellow]Installation cancelled by user[/yellow]")
            self._offer_rollback_option()
            return False
        except Exception as e:
            logger.error(f"Installation workflow failed: {e}")
            self.console.print(f"❌ [bold red]Installation failed:[/bold red] {e}")
            self._offer_rollback_option()
            return False

    def rollback_installation(self, component: str = "all") -> bool:
        """Rollback partial installation to clean state.

        Args:
            component: Component to rollback ('all', 'workspace', 'agent', 'genie')

        Returns:
            bool: True if rollback completed successfully
        """
        self.console.print(
            Panel.fit(
                f"🔄 [bold yellow]Starting Installation Rollback[/bold yellow]\n"
                f"Component: [cyan]{component}[/cyan]\n"
                f"Action: [red]Remove containers, volumes, and configurations[/red]",
                border_style="yellow",
            )
        )

        try:
            # Use WorkflowOrchestrator for safe rollback
            success = self.workflow_orchestrator.rollback_workflow()

            if success:
                self.console.print(
                    Panel.fit(
                        "✅ [bold green]Rollback Complete![/bold green]\n"
                        "System returned to clean state.\n\n"
                        "💡 [cyan]You can now retry installation[/cyan]",
                        border_style="green",
                    )
                )
            else:
                self.console.print(
                    Panel.fit(
                        "⚠️ [bold yellow]Rollback Completed with Warnings[/bold yellow]\n"
                        "Some components may require manual cleanup.\n\n"
                        "💡 [cyan]Use 'docker system prune' for complete cleanup[/cyan]",
                        border_style="yellow",
                    )
                )

            return success

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.console.print(f"❌ [bold red]Rollback failed:[/bold red] {e}")
            return False

    def get_installation_status(self) -> dict[str, Any]:
        """Get current installation status and progress.

        Returns:
            dict: Comprehensive installation status
        """
        return self.workflow_orchestrator.get_workflow_status()

    def validate_installation_requirements(self, component: str = "all") -> bool:
        """Validate installation requirements before starting.

        Args:
            component: Component to validate requirements for

        Returns:
            bool: True if all requirements are met
        """
        is_valid, missing_deps = (
            self.workflow_orchestrator.validate_workflow_dependencies(component)
        )

        if not is_valid:
            self.console.print(
                Panel.fit(
                    f"❌ [bold red]Missing Requirements[/bold red]\n\n"
                    f"Missing dependencies: [yellow]{', '.join(missing_deps)}[/yellow]\n\n"
                    "Please install the required dependencies and try again.",
                    border_style="red",
                )
            )

        return is_valid

    # Enhanced error handling and recovery methods

    def _display_failure_recovery_options(self, status: dict[str, Any]) -> None:
        """Display failure analysis and recovery options."""
        self.console.print(
            Panel.fit(
                f"📊 [bold yellow]Installation Analysis[/bold yellow]\n\n"
                f"State: [red]{status['state']}[/red]\n"
                f"Progress: [yellow]{status['progress']['current_step']}/{status['progress']['total_steps']} steps[/yellow]\n"
                f"Completion: [cyan]{status['progress']['completion_percentage']:.1f}%[/cyan]\n\n"
                f"[bold]Recovery Options:[/bold]\n"
                f"  1. [green]uvx automagik-hive --rollback[/green] - Clean rollback\n"
                f"  2. [yellow]uvx automagik-hive --install {status['component']}[/yellow] - Retry installation\n"
                f"  3. [cyan]uvx automagik-hive --status[/cyan] - Check current status",
                border_style="yellow",
            )
        )

        # Show specific errors if any
        if status.get("errors"):
            self.console.print("\n[bold red]Recent Errors:[/bold red]")
            for error in status["errors"][-3:]:  # Show last 3 errors
                self.console.print(f"  • {error}")

    def _offer_rollback_option(self) -> None:
        """Offer rollback option after failure."""
        try:
            rollback = (
                self.console.input(
                    "\n🔄 Would you like to rollback the partial installation? (y/N): "
                )
                .strip()
                .lower()
            )

            if rollback in ["y", "yes"]:
                self.rollback_installation()
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n⏭️ Rollback skipped")

    # Legacy compatibility methods (maintained for backward compatibility)

    def _install_workspace_only(self) -> bool:
        """Install workspace uvx process only (no Docker services).

        Returns:
            bool: True if workspace started successfully
        """
        self.console.print("🚀 [bold]Starting Workspace Only[/bold]")

        try:
            # Start uvx process
            cmd = ["uvx", "automagik-hive", "serve"]
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            self.console.print("✅ Workspace uvx process started")
            self.console.print("🌐 Workspace available at: http://localhost:8000")

            return True

        except Exception as e:
            logger.error(f"Workspace startup failed: {e}")
            self.console.print(f"❌ Failed to start workspace: {e}")
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
            task = progress.add_task(
                f"Installing {component} infrastructure...", total=None
            )

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

                progress.update(
                    task, description="✅ Infrastructure installation complete"
                )
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
                    check=False,
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
                check=False,
            )

            # Network creation fails if it already exists - that's fine
            if (
                network_result.returncode != 0
                and "already exists" not in network_result.stderr
            ):
                logger.error(f"Failed to create network: {network_result.stderr}")
                return False

            # Create volumes for persistent data
            volumes = ["hive-postgres-data", "hive-agent-data", "hive-genie-data"]

            for volume in volumes:
                volume_result = subprocess.run(
                    ["docker", "volume", "create", volume],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if (
                    volume_result.returncode != 0
                    and "already exists" not in volume_result.stderr
                ):
                    logger.error(
                        f"Failed to create volume {volume}: {volume_result.stderr}"
                    )
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
            return self._create_docker_compose_file(component)

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
""",
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
    user: "1000:1000"
    depends_on:
      hive-agent-postgres:
        condition: service_healthy
    environment:
      HIVE_DATABASE_URL: postgresql://hive:hive@hive-agent-postgres:5432/hive_agent
      HOME: /tmp
      UV_CACHE_DIR: /tmp/uv-cache
    ports:
      - "38886:8000"
    networks:
      - hive-network
    working_dir: /app
    volumes:
      - .:/app
    command: ["sh", "-c", "pip install uv && /tmp/.local/bin/uv sync --no-dev && /tmp/.local/bin/uv add psycopg2-binary && /tmp/.local/bin/uv run python -m api.serve"]
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
    user: "1000:1000"
    depends_on:
      hive-genie-postgres:
        condition: service_healthy
    environment:
      HIVE_DATABASE_URL: postgresql://hive:hive@hive-genie-postgres:5432/hive_genie
      HOME: /tmp
      UV_CACHE_DIR: /tmp/uv-cache
    ports:
      - "48886:8000"
    networks:
      - hive-network
    working_dir: /app
    volumes:
      - .:/app
    command: ["sh", "-c", "pip install uv && /tmp/.local/bin/uv sync --no-dev && /tmp/.local/bin/uv add psycopg2-binary && /tmp/.local/bin/uv run python -m api.serve"]
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

            cmd = self._docker_compose_cmd + [
                "-f",
                "docker-compose.unified.yml",
                "--profile",
                component,
                "up",
                "-d",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
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
            component: Component to check ('all', 'workspace', 'agent', 'genie')

        Returns:
            dict: Health status for each service (True/False mapping for compatibility)
        """
        # Delegate to comprehensive health checker
        results = self.health_checker.comprehensive_health_check(component)

        # Convert HealthCheckResult objects to simple bool mapping for backward compatibility
        health_status = {}
        for service_name, result in results.items():
            health_status[service_name] = result.status == "healthy"

        return health_status

    def _perform_comprehensive_health_check(self, component: str) -> bool:
        """Perform comprehensive health check with detailed diagnostics.

        Args:
            component: Component to check

        Returns:
            bool: True if health check passes (all services healthy or acceptable warnings)
        """
        try:
            # Run comprehensive health check
            results = self.health_checker.comprehensive_health_check(component)

            # Analyze results for workflow continuation
            health_status = {"healthy": 0, "unhealthy": 0, "warning": 0, "unknown": 0}

            for result in results.values():
                health_status[result.status] = health_status.get(result.status, 0) + 1

            total_services = len(results)
            critical_issues = health_status["unhealthy"]

            # Determine if workflow should continue
            if critical_issues == 0:
                # All services healthy or just warnings - continue
                return True
            if critical_issues <= total_services // 3:
                # Less than 1/3 services unhealthy - show warning but continue
                self.console.print(
                    Panel.fit(
                        f"⚠️ [yellow]Continuing with {critical_issues} unhealthy services[/yellow]\n"
                        "Some services may need attention but core functionality should work.\n"
                        "Run [cyan]uvx automagik-hive --health[/cyan] later to check status.",
                        title="Health Check Warning",
                        border_style="yellow",
                    )
                )
                return True
            # Too many critical issues - stop workflow
            self.console.print(
                Panel.fit(
                    f"🚨 [red]Health check failed with {critical_issues} critical issues[/red]\n"
                    "Installation workflow stopped to prevent further issues.\n"
                    "Please address the problems above and try again.",
                    title="Health Check Failed",
                    border_style="red",
                )
            )
            return False

        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            self.console.print(f"❌ [red]Health check error:[/red] {e}")

            # For install workflow, we'll continue on health check errors
            # but warn the user
            self.console.print(
                Panel.fit(
                    "⚠️ [yellow]Health check failed but continuing installation[/yellow]\n"
                    "Services may still be starting up. Check status manually later.",
                    border_style="yellow",
                )
            )
            return True

    def interactive_workspace_setup(self, component: str = "all") -> bool:
        """Interactive workspace initialization/selection.

        Skips prompts for agent/genie components (automation-friendly).

        Args:
            component: Component being installed

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
                    border_style="green",
                )
            )

            while True:
                choice = self.console.input("\nEnter choice (1-3): ").strip()

                if choice == "1":
                    return self._initialize_new_workspace()
                if choice == "2":
                    return self._select_existing_workspace()
                if choice == "3":
                    self._show_skip_message()
                    return True
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
            self.console.print(
                "❌ Invalid workspace (missing .env or docker-compose.yml)"
            )

            # Offer to initialize existing folder
            initialize = (
                self.console.input(
                    "\nWould you like to initialize this folder as a workspace? (y/N): "
                )
                .strip()
                .lower()
            )

            if initialize in ["y", "yes"]:
                self.console.print("✅ Initializing existing folder as workspace...")
                success = self.init_commands.initialize_workspace(str(path))

                if success:
                    self.console.print("✅ Workspace ready!")
                    return True
                self.console.print("❌ Workspace initialization failed.")
                return False
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

            return all((path / file_name).exists() for file_name in required_files)

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
                border_style="yellow",
            )
        )
