"""Unified Workflow State Machine for Automagik Hive - Phase 2 Implementation.

Orchestrates the complete install→start→health→workspace workflow with:
- State machine implementation for unified workflow progression
- Component-specific workflow paths (all, workspace, agent, genie)
- Progress tracking and status reporting with rich console integration
- Error recovery and rollback mechanisms with detailed error handling
- Workflow validation and dependency checking
- Integration with all manager classes (ServiceManager, WorkspaceManager, etc.)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .service_manager import ServiceManager
from .workspace_manager import WorkspaceManager

if TYPE_CHECKING:
    from collections.abc import Callable


class WorkflowState(Enum):
    """Workflow state enumeration for state machine progression."""

    INITIAL = auto()
    INSTALLING = auto()
    INSTALLED = auto()
    STARTING = auto()
    STARTED = auto()
    HEALTH_CHECKING = auto()
    HEALTHY = auto()
    WORKSPACE_SETUP = auto()
    COMPLETED = auto()
    FAILED = auto()
    ROLLBACK = auto()


class ComponentType(Enum):
    """Component types for workflow orchestration."""

    ALL = "all"
    WORKSPACE = "workspace"
    AGENT = "agent"
    GENIE = "genie"


@dataclass
class WorkflowStep:
    """Individual workflow step with execution details."""

    name: str
    description: str
    function: Callable[..., bool]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    required: bool = True
    rollback_function: Callable[..., bool] | None = None
    rollback_args: tuple[Any, ...] = field(default_factory=tuple)
    rollback_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowProgress:
    """Workflow progress tracking data."""

    current_step: int = 0
    total_steps: int = 0
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)
    start_time: float | None = None
    end_time: float | None = None


class WorkflowOrchestrator:
    """Unified workflow state machine for install→start→health→workspace flow.

    Provides comprehensive orchestration of the complete Automagik Hive deployment
    workflow with state management, error recovery, and component-specific handling.
    """

    def __init__(self) -> None:
        """Initialize workflow orchestrator with manager dependencies."""
        self.console = Console()
        self.service_manager = ServiceManager()
        self.workspace_manager = WorkspaceManager()

        # State machine state
        self.current_state = WorkflowState.INITIAL
        self.component = ComponentType.ALL
        self.progress = WorkflowProgress()

        # Workflow steps registry
        self.workflow_steps: list[WorkflowStep] = []
        self.state_transitions: dict[WorkflowState, list[WorkflowState]] = {
            WorkflowState.INITIAL: [WorkflowState.INSTALLING],
            WorkflowState.INSTALLING: [WorkflowState.INSTALLED, WorkflowState.FAILED],
            WorkflowState.INSTALLED: [WorkflowState.STARTING, WorkflowState.FAILED],
            WorkflowState.STARTING: [WorkflowState.STARTED, WorkflowState.FAILED],
            WorkflowState.STARTED: [
                WorkflowState.HEALTH_CHECKING,
                WorkflowState.FAILED,
            ],
            WorkflowState.HEALTH_CHECKING: [
                WorkflowState.HEALTHY,
                WorkflowState.FAILED,
            ],
            WorkflowState.HEALTHY: [
                WorkflowState.WORKSPACE_SETUP,
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
            ],
            WorkflowState.WORKSPACE_SETUP: [
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
            ],
            WorkflowState.FAILED: [WorkflowState.ROLLBACK, WorkflowState.INITIAL],
            WorkflowState.ROLLBACK: [WorkflowState.INITIAL, WorkflowState.FAILED],
            WorkflowState.COMPLETED: [],
        }

    def execute_unified_workflow(self, component: str = "all") -> bool:
        """Execute the complete unified workflow for specified component.

        Orchestrates the full install→start→health→workspace flow with
        state machine progression, error handling, and rollback capabilities.

        Args:
            component: Component to deploy ('all', 'workspace', 'agent', 'genie')

        Returns:
            bool: True if entire workflow completed successfully
        """
        try:
            # Initialize workflow for component
            self.component = ComponentType(component)
            self._initialize_workflow()

            # Display workflow overview
            self._display_workflow_overview()

            # Execute workflow state machine
            success = self._execute_state_machine()

            # Display final results
            self._display_workflow_results(success)

            return success

        except Exception as e:
            logger.error(f"Workflow orchestration failed: {e}")
            self.console.print(f"❌ [bold red]Workflow failed:[/bold red] {e}")
            return False

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status and progress information.

        Returns:
            dict: Comprehensive workflow status including state, progress, and metrics
        """
        duration = None
        if self.progress.start_time:
            end_time = self.progress.end_time or time.time()
            duration = end_time - self.progress.start_time

        return {
            "state": self.current_state.name,
            "component": self.component.value,
            "progress": {
                "current_step": self.progress.current_step,
                "total_steps": self.progress.total_steps,
                "completed_steps": self.progress.completed_steps,
                "failed_steps": self.progress.failed_steps,
                "completion_percentage": (
                    len(self.progress.completed_steps) / self.progress.total_steps * 100
                    if self.progress.total_steps > 0
                    else 0
                ),
            },
            "timing": {
                "start_time": self.progress.start_time,
                "end_time": self.progress.end_time,
                "duration": duration,
            },
            "errors": self.progress.error_messages,
        }

    def rollback_workflow(self) -> bool:
        """Execute workflow rollback to clean up partial installation.

        Returns:
            bool: True if rollback completed successfully
        """
        self.console.print(
            "🔄 [bold yellow]Starting workflow rollback...[/bold yellow]"
        )

        try:
            self._transition_state(WorkflowState.ROLLBACK)

            # Execute rollback steps in reverse order
            rollback_success = True
            for step_name in reversed(self.progress.completed_steps):
                step = self._find_step_by_name(step_name)
                if step and step.rollback_function:
                    try:
                        self.console.print(f"🔄 Rolling back: {step.name}")
                        if not step.rollback_function(
                            *step.rollback_args, **step.rollback_kwargs
                        ):
                            self.console.print(f"⚠️ Rollback warning: {step.name}")
                            rollback_success = False
                    except Exception as e:
                        logger.error(f"Rollback step failed: {step.name}: {e}")
                        rollback_success = False

            if rollback_success:
                self.console.print(
                    "✅ [bold green]Rollback completed successfully[/bold green]"
                )
                self._transition_state(WorkflowState.INITIAL)
            else:
                self.console.print(
                    "⚠️ [bold yellow]Rollback completed with warnings[/bold yellow]"
                )

            return rollback_success

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.console.print(f"❌ [bold red]Rollback failed:[/bold red] {e}")
            return False

    def validate_workflow_dependencies(self, component: str) -> tuple[bool, list[str]]:
        """Validate workflow dependencies with interactive installation support.

        Args:
            component: Component to validate dependencies for

        Returns:
            Tuple[bool, List[str]]: (is_valid, missing_dependencies)
        """
        missing_deps = []

        try:
            import subprocess

            # Check Docker availability for non-workspace components
            if component != "workspace":
                result = subprocess.run(
                    ["docker", "--version"], capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    missing_deps.append("docker")

                # Check Docker Compose availability (modern and legacy support)
                if not self._check_docker_compose_available():
                    missing_deps.append("docker-compose")

            # Check uvx availability for workspace components
            if component in ["all", "workspace"]:
                result = subprocess.run(
                    ["uvx", "--version"], capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    missing_deps.append("uvx")

            # Check disk space (basic check for available space)
            import shutil

            free_space = shutil.disk_usage(".").free
            required_space = 1024 * 1024 * 1024  # 1GB minimum
            if free_space < required_space:
                missing_deps.append("disk_space")

            return len(missing_deps) == 0, missing_deps

        except Exception as e:
            logger.error(f"Dependency validation failed: {e}")
            return False, ["validation_error"]

    def _check_docker_compose_available(self) -> bool:
        """Check if Docker Compose is available (modern or legacy).
        
        Tries modern 'docker compose' first, then falls back to legacy 'docker-compose'.
        
        Returns:
            bool: True if either version is available
        """
        try:
            import subprocess
            
            # Try modern 'docker compose' first (Docker v2+)
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

            # Fallback to legacy 'docker-compose'
            try:
                result = subprocess.run(
                    ["docker-compose", "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

            return False

        except Exception as e:
            logger.error(f"Docker Compose availability check failed: {e}")
            return False

    def _prompt_docker_installation(self, missing_deps: list[str]) -> bool:
        """Prompt user for interactive Docker installation when missing.
        
        Args:
            missing_deps: List of missing dependencies
            
        Returns:
            bool: True if user wants to proceed with installation, False to cancel
        """
        if not missing_deps:
            return True
            
        # Only handle Docker-related missing dependencies interactively
        docker_deps = [dep for dep in missing_deps if dep in ["docker", "docker-compose"]]
        if not docker_deps:
            return False
            
        self.console.print("\n🐳 [bold yellow]Docker Installation Required[/bold yellow]")
        self.console.print(f"Missing dependencies: {', '.join(docker_deps)}")
        self.console.print()
        
        # Provide platform-specific installation guidance
        import platform
        system = platform.system().lower()
        
        if system == "linux":
            self.console.print("📋 [bold]Linux Installation Options:[/bold]")
            self.console.print("1. [cyan]Ubuntu/Debian:[/cyan] sudo apt-get update && sudo apt-get install docker.io docker-compose")
            self.console.print("2. [cyan]RHEL/CentOS:[/cyan] sudo yum install docker docker-compose")
            self.console.print("3. [cyan]Docker Desktop:[/cyan] Download from https://docs.docker.com/desktop/linux/")
        elif system == "darwin":
            self.console.print("📋 [bold]macOS Installation Options:[/bold]")
            self.console.print("1. [cyan]Docker Desktop:[/cyan] Download from https://docs.docker.com/desktop/mac/")
            self.console.print("2. [cyan]Homebrew:[/cyan] brew install --cask docker")
        elif system == "windows":
            self.console.print("📋 [bold]Windows Installation Options:[/bold]")
            self.console.print("1. [cyan]Docker Desktop:[/cyan] Download from https://docs.docker.com/desktop/windows/")
            self.console.print("2. [cyan]WSL2 + Docker:[/cyan] Install WSL2 first, then Docker Desktop")
        else:
            self.console.print("📋 [bold]Installation:[/bold] Please install Docker from https://docs.docker.com/get-docker/")

        self.console.print()
        self.console.print("🔄 [bold]After installation:[/bold]")
        self.console.print("   • Restart your terminal")
        self.console.print("   • Run this command again")
        self.console.print()
        
        # Ask user if they want to proceed or cancel
        try:
            response = input("❓ Would you like to continue with installation after installing Docker? (y/N): ").strip().lower()
            return response in ["y", "yes"]
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n🛑 Installation cancelled by user")
            return False

    # Private implementation methods

    def _initialize_workflow(self) -> None:
        """Initialize workflow steps based on component type."""
        self.progress = WorkflowProgress()
        self.progress.start_time = time.time()
        self.workflow_steps = []

        # Build component-specific workflow steps
        if self.component == ComponentType.WORKSPACE:
            self._build_workspace_workflow()
        elif self.component == ComponentType.AGENT:
            self._build_agent_workflow()
        elif self.component == ComponentType.GENIE:
            self._build_genie_workflow()
        else:  # ALL
            self._build_complete_workflow()

        self.progress.total_steps = len(self.workflow_steps)

    def _build_workspace_workflow(self) -> None:
        """Build workflow steps for workspace-only deployment."""
        self.workflow_steps = [
            WorkflowStep(
                name="validate_dependencies",
                description="Validate workspace dependencies",
                function=self._validate_workspace_dependencies,
                rollback_function=lambda: True,  # No rollback needed for validation
            ),
            WorkflowStep(
                name="start_workspace",
                description="Start workspace uvx process",
                function=self._start_workspace_process,
                rollback_function=self._stop_workspace_process,
            ),
            WorkflowStep(
                name="health_check_workspace",
                description="Verify workspace health",
                function=self._health_check_workspace,
                rollback_function=lambda: True,  # No rollback needed
            ),
        ]

    def _build_agent_workflow(self) -> None:
        """Build workflow steps for agent deployment."""
        self.workflow_steps = [
            WorkflowStep(
                name="validate_dependencies",
                description="Validate agent dependencies",
                function=self._validate_agent_dependencies,
                rollback_function=lambda: True,
            ),
            WorkflowStep(
                name="install_infrastructure",
                description="Install agent Docker infrastructure",
                function=self._install_agent_infrastructure,
                rollback_function=self._uninstall_agent_infrastructure,
            ),
            WorkflowStep(
                name="start_services",
                description="Start agent services",
                function=self._start_agent_services,
                rollback_function=self._stop_agent_services,
            ),
            WorkflowStep(
                name="health_check",
                description="Verify agent service health",
                function=self._health_check_agent,
                rollback_function=lambda: True,
            ),
        ]

    def _build_genie_workflow(self) -> None:
        """Build workflow steps for genie deployment."""
        self.workflow_steps = [
            WorkflowStep(
                name="validate_dependencies",
                description="Validate genie dependencies",
                function=self._validate_genie_dependencies,
                rollback_function=lambda: True,
            ),
            WorkflowStep(
                name="install_infrastructure",
                description="Install genie Docker infrastructure",
                function=self._install_genie_infrastructure,
                rollback_function=self._uninstall_genie_infrastructure,
            ),
            WorkflowStep(
                name="start_services",
                description="Start genie services",
                function=self._start_genie_services,
                rollback_function=self._stop_genie_services,
            ),
            WorkflowStep(
                name="health_check",
                description="Verify genie service health",
                function=self._health_check_genie,
                rollback_function=lambda: True,
            ),
        ]

    def _build_complete_workflow(self) -> None:
        """Build workflow steps for complete system deployment."""
        self.workflow_steps = [
            WorkflowStep(
                name="validate_dependencies",
                description="Validate all system dependencies",
                function=self._validate_all_dependencies,
                rollback_function=lambda: True,
            ),
            WorkflowStep(
                name="install_infrastructure",
                description="Install complete Docker infrastructure",
                function=self._install_complete_infrastructure,
                rollback_function=self._uninstall_complete_infrastructure,
            ),
            WorkflowStep(
                name="start_services",
                description="Start all services",
                function=self._start_all_services,
                rollback_function=self._stop_all_services,
            ),
            WorkflowStep(
                name="health_check",
                description="Verify all service health",
                function=self._health_check_all,
                rollback_function=lambda: True,
            ),
            WorkflowStep(
                name="workspace_setup",
                description="Interactive workspace setup",
                function=self._interactive_workspace_setup,
                required=False,  # Optional step
                rollback_function=lambda: True,
            ),
        ]

    def _execute_state_machine(self) -> bool:
        """Execute the workflow state machine with proper state transitions."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Main workflow execution loop
            while self.current_state not in [
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
            ]:
                if self.current_state == WorkflowState.INITIAL:
                    self._transition_state(WorkflowState.INSTALLING)

                elif self.current_state == WorkflowState.INSTALLING:
                    task = progress.add_task("Installing infrastructure...", total=None)
                    if self._execute_install_phase():
                        progress.update(task, description="✅ Installation complete")
                        self._transition_state(WorkflowState.INSTALLED)
                    else:
                        progress.update(task, description="❌ Installation failed")
                        self._transition_state(WorkflowState.FAILED)

                elif self.current_state == WorkflowState.INSTALLED:
                    self._transition_state(WorkflowState.STARTING)

                elif self.current_state == WorkflowState.STARTING:
                    task = progress.add_task("Starting services...", total=None)
                    if self._execute_start_phase():
                        progress.update(task, description="✅ Services started")
                        self._transition_state(WorkflowState.STARTED)
                    else:
                        progress.update(task, description="❌ Service startup failed")
                        self._transition_state(WorkflowState.FAILED)

                elif self.current_state == WorkflowState.STARTED:
                    self._transition_state(WorkflowState.HEALTH_CHECKING)

                elif self.current_state == WorkflowState.HEALTH_CHECKING:
                    task = progress.add_task("Checking service health...", total=None)
                    if self._execute_health_phase():
                        progress.update(task, description="✅ All services healthy")
                        self._transition_state(WorkflowState.HEALTHY)
                    else:
                        progress.update(task, description="❌ Health check failed")
                        self._transition_state(WorkflowState.FAILED)

                elif self.current_state == WorkflowState.HEALTHY:
                    if self.component == ComponentType.ALL:
                        self._transition_state(WorkflowState.WORKSPACE_SETUP)
                    else:
                        self._transition_state(WorkflowState.COMPLETED)

                elif self.current_state == WorkflowState.WORKSPACE_SETUP:
                    task = progress.add_task("Setting up workspace...", total=None)
                    if self._execute_workspace_phase():
                        progress.update(task, description="✅ Workspace setup complete")
                        self._transition_state(WorkflowState.COMPLETED)
                    else:
                        progress.update(task, description="⏭️ Workspace setup skipped")
                        self._transition_state(WorkflowState.COMPLETED)

        self.progress.end_time = time.time()
        return self.current_state == WorkflowState.COMPLETED

    def _execute_install_phase(self) -> bool:
        """Execute the installation phase of the workflow."""
        install_steps = [
            step
            for step in self.workflow_steps
            if step.name in ["validate_dependencies", "install_infrastructure"]
        ]

        return all(self._execute_workflow_step(step) for step in install_steps)

    def _execute_start_phase(self) -> bool:
        """Execute the service startup phase of the workflow."""
        start_steps = [
            step for step in self.workflow_steps if step.name == "start_services"
        ]

        return all(self._execute_workflow_step(step) for step in start_steps)

    def _execute_health_phase(self) -> bool:
        """Execute the health check phase of the workflow."""
        health_steps = [
            step for step in self.workflow_steps if step.name.startswith("health_check")
        ]

        return all(self._execute_workflow_step(step) for step in health_steps)

    def _execute_workspace_phase(self) -> bool:
        """Execute the workspace setup phase of the workflow."""
        workspace_steps = [
            step for step in self.workflow_steps if step.name == "workspace_setup"
        ]

        for step in workspace_steps:
            # Workspace setup is optional and can be skipped
            try:
                return self._execute_workflow_step(step)
            except KeyboardInterrupt:
                self.console.print("\n⏭️ Workspace setup skipped by user")
                return True  # Allow continuation

        return True

    def _execute_workflow_step(self, step: WorkflowStep) -> bool:
        """Execute a single workflow step with error handling."""
        try:
            self.progress.current_step += 1

            logger.info(f"Executing workflow step: {step.name}")
            success = step.function(*step.args, **step.kwargs)

            if success:
                self.progress.completed_steps.append(step.name)
                return True
            if step.required:
                self.progress.failed_steps.append(step.name)
                self.progress.error_messages.append(
                    f"Required step failed: {step.name}"
                )
                return False
            # Optional step failure is not fatal
            logger.warning(f"Optional step failed: {step.name}")
            return True

        except Exception as e:
            logger.error(f"Workflow step execution failed: {step.name}: {e}")
            self.progress.failed_steps.append(step.name)
            self.progress.error_messages.append(f"Step exception: {step.name}: {e!s}")
            return False

    def _transition_state(self, new_state: WorkflowState) -> bool:
        """Transition workflow state with validation."""
        if new_state not in self.state_transitions[self.current_state]:
            logger.error(
                f"Invalid state transition: {self.current_state} -> {new_state}"
            )
            return False

        logger.info(f"Workflow state transition: {self.current_state} -> {new_state}")
        self.current_state = new_state
        return True

    def _display_workflow_overview(self) -> None:
        """Display workflow overview and planned steps."""
        table = Table(title=f"Workflow Overview - {self.component.value.title()}")
        table.add_column("Step", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Required", style="yellow")

        for i, step in enumerate(self.workflow_steps, 1):
            table.add_row(
                f"{i}. {step.name}",
                step.description,
                "✓" if step.required else "Optional",
            )

        self.console.print(table)
        self.console.print()

    def _display_workflow_results(self, success: bool) -> None:
        """Display final workflow results and status."""
        if success:
            panel_content = (
                "✅ [bold green]Workflow Completed Successfully![/bold green]\n\n"
                f"Component: [cyan]{self.component.value}[/cyan]\n"
                f"Steps completed: [green]{len(self.progress.completed_steps)}/{self.progress.total_steps}[/green]\n"
                f"Duration: [yellow]{self._format_duration()}[/yellow]"
            )

            if self.component != ComponentType.WORKSPACE:
                panel_content += "\n\n🌐 [bold]Services Available:[/bold]"
                if self.component in [ComponentType.ALL, ComponentType.AGENT]:
                    panel_content += "\n  • Agent API: http://localhost:38886"
                if self.component in [ComponentType.ALL, ComponentType.GENIE]:
                    panel_content += "\n  • Genie API: http://localhost:48886"
                if self.component == ComponentType.ALL:
                    panel_content += "\n  • Workspace: Use --init to setup"

            self.console.print(Panel.fit(panel_content, border_style="green"))
        else:
            panel_content = (
                "❌ [bold red]Workflow Failed![/bold red]\n\n"
                f"Component: [cyan]{self.component.value}[/cyan]\n"
                f"Failed at step: [red]{self.progress.current_step}/{self.progress.total_steps}[/red]\n"
                f"Errors: [red]{len(self.progress.error_messages)}[/red]"
            )

            if self.progress.error_messages:
                panel_content += "\n\n[bold]Error Details:[/bold]"
                for error in self.progress.error_messages[-3:]:  # Show last 3 errors
                    panel_content += f"\n  • {error}"

            panel_content += "\n\n💡 [yellow]Try rollback with: --rollback[/yellow]"
            self.console.print(Panel.fit(panel_content, border_style="red"))

    def _format_duration(self) -> str:
        """Format workflow duration for display."""
        if not self.progress.start_time or not self.progress.end_time:
            return "Unknown"

        duration = self.progress.end_time - self.progress.start_time
        if duration < 60:
            return f"{duration:.1f}s"
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes}m {seconds}s"

    def _find_step_by_name(self, step_name: str) -> WorkflowStep | None:
        """Find workflow step by name."""
        for step in self.workflow_steps:
            if step.name == step_name:
                return step
        return None

    # Component-specific workflow step implementations

    def _validate_workspace_dependencies(self) -> bool:
        """Validate dependencies for workspace deployment with interactive installation."""
        is_valid, missing = self.validate_workflow_dependencies("workspace")
        if not is_valid:
            # For workspace, we only need uvx - show error for critical missing deps
            critical_missing = [dep for dep in missing if dep not in ["docker", "docker-compose"]]
            if critical_missing:
                self.console.print(f"❌ Missing critical dependencies: {', '.join(critical_missing)}")
                return False
        return True  # Workspace deployment doesn't require Docker

    def _validate_agent_dependencies(self) -> bool:
        """Validate dependencies for agent deployment with interactive Docker installation."""
        is_valid, missing = self.validate_workflow_dependencies("agent")
        if not is_valid:
            # Check if we can handle missing dependencies interactively
            if not self._prompt_docker_installation(missing):
                return False
            # After interactive prompt, user chose to continue - proceed with installation
            self.console.print("🔄 [bold blue]Proceeding with installation...[/bold blue]")
        return True

    def _validate_genie_dependencies(self) -> bool:
        """Validate dependencies for genie deployment with interactive Docker installation."""
        is_valid, missing = self.validate_workflow_dependencies("genie")
        if not is_valid:
            # Check if we can handle missing dependencies interactively
            if not self._prompt_docker_installation(missing):
                return False
            # After interactive prompt, user chose to continue - proceed with installation
            self.console.print("🔄 [bold blue]Proceeding with installation...[/bold blue]")
        return True

    def _validate_all_dependencies(self) -> bool:
        """Validate dependencies for complete system deployment with interactive Docker installation."""
        is_valid, missing = self.validate_workflow_dependencies("all")
        if not is_valid:
            # Check if we can handle missing dependencies interactively
            if not self._prompt_docker_installation(missing):
                return False
            # After interactive prompt, user chose to continue - proceed with installation
            self.console.print("🔄 [bold blue]Proceeding with installation...[/bold blue]")
        return True

    def _start_workspace_process(self) -> bool:
        """Start workspace uvx process."""
        return self.service_manager.start_services("workspace")

    def _start_agent_services(self) -> bool:
        """Start agent Docker services."""
        return self.service_manager.start_services("agent")

    def _start_genie_services(self) -> bool:
        """Start genie Docker services."""
        return self.service_manager.start_services("genie")

    def _start_all_services(self) -> bool:
        """Start all system services."""
        return self.service_manager.start_services("all")

    def _health_check_workspace(self) -> bool:
        """Perform health check for workspace."""
        status = self.service_manager.get_status("workspace")
        return status.get("workspace") == "healthy"

    def _health_check_agent(self) -> bool:
        """Perform health check for agent services."""
        status = self.service_manager.get_status("agent")
        return all(s == "healthy" for s in status.values())

    def _health_check_genie(self) -> bool:
        """Perform health check for genie services."""
        status = self.service_manager.get_status("genie")
        return all(s == "healthy" for s in status.values())

    def _health_check_all(self) -> bool:
        """Perform health check for all services."""
        status = self.service_manager.get_status("all")
        return all(s == "healthy" for s in status.values())

    def _interactive_workspace_setup(self) -> bool:
        """Execute interactive workspace setup."""
        try:
            action, path = self.workspace_manager.prompt_workspace_choice()

            if action == "skip":
                return True  # Successful skip
            if action == "new":
                return self.workspace_manager.initialize_workspace(path)
            if action == "existing":
                return self.workspace_manager.validate_existing_workspace(path)

            return False
        except KeyboardInterrupt:
            return True  # Allow skip on interrupt

    # Infrastructure management methods (delegated to UnifiedInstaller)

    def _install_agent_infrastructure(self) -> bool:
        """Install agent infrastructure - delegated to UnifiedInstaller."""
        from .unified_installer import UnifiedInstaller

        installer = UnifiedInstaller()
        return installer._install_infrastructure("agent")

    def _install_genie_infrastructure(self) -> bool:
        """Install genie infrastructure - delegated to UnifiedInstaller."""
        from .unified_installer import UnifiedInstaller

        installer = UnifiedInstaller()
        return installer._install_infrastructure("genie")

    def _install_complete_infrastructure(self) -> bool:
        """Install complete infrastructure - delegated to UnifiedInstaller."""
        from .unified_installer import UnifiedInstaller

        installer = UnifiedInstaller()
        return installer._install_infrastructure("all")

    # Rollback methods

    def _stop_workspace_process(self) -> bool:
        """Stop workspace process for rollback."""
        return self.service_manager.stop_services("workspace")

    def _stop_agent_services(self) -> bool:
        """Stop agent services for rollback."""
        return self.service_manager.stop_services("agent")

    def _stop_genie_services(self) -> bool:
        """Stop genie services for rollback."""
        return self.service_manager.stop_services("genie")

    def _stop_all_services(self) -> bool:
        """Stop all services for rollback."""
        return self.service_manager.stop_services("all")

    def _uninstall_agent_infrastructure(self) -> bool:
        """Uninstall agent infrastructure for rollback."""
        return self.service_manager.uninstall("agent")

    def _uninstall_genie_infrastructure(self) -> bool:
        """Uninstall genie infrastructure for rollback."""
        return self.service_manager.uninstall("genie")

    def _uninstall_complete_infrastructure(self) -> bool:
        """Uninstall complete infrastructure for rollback."""
        return self.service_manager.uninstall("all")
