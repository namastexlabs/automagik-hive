"""Service Manager - Unified service lifecycle management for Automagik Hive components.

Handles start, stop, restart, status, logs, and uninstall operations for:
- all: Complete system (workspace + agent + genie)
- workspace: Local uvx process
- agent: Docker services (postgres + api on ports 35532/38886)
- genie: Docker services (postgres + api on ports 48532/48886)
"""

import subprocess
import time
from pathlib import Path

from cli.core.docker_service import DockerService
from cli.core.postgres_service import PostgreSQLService


class ServiceManager:
    """Unified service lifecycle management for all Hive components."""

    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()
        self.workspace_process = None

    def start_services(self, component: str = "all") -> bool:
        """Start specified services with proper dependency ordering.

        Args:
            component: Service component to start (all|workspace|agent|genie)

        Returns:
            bool: True if all requested services started successfully
        """
        try:
            if component == "all":
                return self._start_all_services()
            if component == "workspace":
                return self._start_workspace()
            if component == "agent":
                return self._start_agent_services()
            if component == "genie":
                return self._start_genie_services()
            return False

        except Exception:
            return False

    def stop_services(self, component: str = "all") -> bool:
        """Stop specified services gracefully.

        Args:
            component: Service component to stop (all|workspace|agent|genie)

        Returns:
            bool: True if all requested services stopped successfully
        """
        try:
            if component == "all":
                return self._stop_all_services()
            if component == "workspace":
                return self._stop_workspace()
            if component == "agent":
                return self._stop_agent_services()
            if component == "genie":
                return self._stop_genie_services()
            return False

        except Exception:
            return False

    def restart_services(self, component: str = "all") -> bool:
        """Restart specified services (stop + start).

        Args:
            component: Service component to restart (all|workspace|agent|genie)

        Returns:
            bool: True if restart completed successfully
        """
        # Stop first
        if not self.stop_services(component):
            return False

        # Brief pause for cleanup
        time.sleep(2)

        # Start again
        return self.start_services(component)

    def get_status(self, component: str = "all") -> dict[str, str]:
        """Get status of specified services.

        Args:
            component: Service component to check (all|workspace|agent|genie)

        Returns:
            Dict mapping component names to status strings:
            - "healthy": Service running and responding
            - "unhealthy": Service running but not responding
            - "stopped": Service not running
            - "unknown": Status cannot be determined
        """
        status = {}

        try:
            if component in ["all", "workspace"]:
                status["workspace"] = self._get_workspace_status()

            if component in ["all", "agent"]:
                status.update(self._get_agent_status())

            if component in ["all", "genie"]:
                status.update(self._get_genie_status())

        except Exception:
            # Return unknown status for requested components
            if component == "all":
                status = {
                    "workspace": "unknown",
                    "agent-postgres": "unknown",
                    "agent-api": "unknown",
                    "genie-postgres": "unknown",
                    "genie-api": "unknown",
                }
            else:
                status[component] = "unknown"

        return status

    def show_logs(self, component: str = "all", lines: int = 50) -> bool:
        """Show logs for specified services.

        Args:
            component: Service component to show logs for (all|workspace|agent|genie)
            lines: Number of log lines to display

        Returns:
            bool: True if logs displayed successfully
        """
        try:
            if component == "all":
                return self._show_all_logs(lines)
            if component == "workspace":
                return self._show_workspace_logs(lines)
            if component == "agent":
                return self._show_agent_logs(lines)
            if component == "genie":
                return self._show_genie_logs(lines)
            return False

        except Exception:
            return False

    def uninstall(self, component: str = "all") -> bool:
        """Uninstall specified components (stop + remove containers/volumes/configs).

        Args:
            component: Service component to uninstall (all|workspace|agent|genie)

        Returns:
            bool: True if uninstall completed successfully
        """
        try:
            # Stop services first
            if not self.stop_services(component):
                pass

            if component == "all":
                return self._uninstall_all()
            if component == "workspace":
                return self._uninstall_workspace()
            if component == "agent":
                return self._uninstall_agent()
            if component == "genie":
                return self._uninstall_genie()
            return False

        except Exception:
            return False

    # Private implementation methods

    def _start_all_services(self) -> bool:
        """Start all services in proper order."""
        success = True

        # Start Docker services first
        if not self._start_agent_services():
            success = False

        if not self._start_genie_services():
            success = False

        # Start workspace last
        if not self._start_workspace():
            success = False

        return success

    def _stop_all_services(self) -> bool:
        """Stop all services gracefully."""
        success = True

        # Stop workspace first
        if not self._stop_workspace():
            success = False

        # Stop Docker services
        if not self._stop_agent_services():
            success = False

        if not self._stop_genie_services():
            success = False

        return success

    def _start_workspace(self) -> bool:
        """Start workspace uvx process."""
        try:
            # Check if already running
            if self._get_workspace_status() == "healthy":
                return True

            # Start uvx process in background
            cmd = ["uvx", "automagik-hive", "serve"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            # Give it time to start
            time.sleep(3)

            # Check if it's running
            if process.poll() is None:
                self.workspace_process = process
                return True
            return False

        except Exception:
            return False

    def _stop_workspace(self) -> bool:
        """Stop workspace uvx process."""
        try:
            # Try to stop gracefully via process
            if self.workspace_process and self.workspace_process.poll() is None:
                self.workspace_process.terminate()
                self.workspace_process.wait(timeout=10)
                return True

            # Fallback: kill by process name
            result = subprocess.run(
                ["pkill", "-f", "uvx.*automagik-hive"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True
            return True

        except Exception:
            return False

    def _start_agent_services(self) -> bool:
        """Start agent Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return False

        try:
            # Start agent profile services
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "agent",
                    "up",
                    "-d",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            return result.returncode == 0

        except Exception:
            return False

    def _stop_agent_services(self) -> bool:
        """Stop agent Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return True  # Nothing to stop

        try:
            # Stop agent profile services
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "agent",
                    "down",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True
            return True  # Don't fail on stop warnings

        except Exception:
            return False

    def _start_genie_services(self) -> bool:
        """Start genie Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return False

        try:
            # Start genie profile services
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "genie",
                    "up",
                    "-d",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            return result.returncode == 0

        except Exception:
            return False

    def _stop_genie_services(self) -> bool:
        """Stop genie Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return True  # Nothing to stop

        try:
            # Stop genie profile services
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "genie",
                    "down",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True
            return True  # Don't fail on stop warnings

        except Exception:
            return False

    def _get_workspace_status(self) -> str:
        """Get workspace service status."""
        try:
            # Check if uvx process is running
            result = subprocess.run(
                ["pgrep", "-f", "uvx.*automagik-hive"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return "healthy"
            return "stopped"

        except Exception:
            return "unknown"

    def _get_agent_status(self) -> dict[str, str]:
        """Get agent services status."""
        status = {}

        try:
            # Check agent containers
            containers = ["hive-agent-postgres", "hive-agent-api"]
            for container in containers:
                result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        container,
                        "--format",
                        "{{.State.Health.Status}}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    health = result.stdout.strip()
                    if health == "healthy":
                        status[container.replace("hive-", "")] = "healthy"
                    elif health in ["starting", "none"]:
                        status[container.replace("hive-", "")] = "unhealthy"
                    else:
                        status[container.replace("hive-", "")] = "unhealthy"
                else:
                    status[container.replace("hive-", "")] = "stopped"

        except Exception:
            status["agent-postgres"] = "unknown"
            status["agent-api"] = "unknown"

        return status

    def _get_genie_status(self) -> dict[str, str]:
        """Get genie services status."""
        status = {}

        try:
            # Check genie containers
            containers = ["hive-genie-postgres", "hive-genie-api"]
            for container in containers:
                result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        container,
                        "--format",
                        "{{.State.Health.Status}}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    health = result.stdout.strip()
                    if health == "healthy":
                        status[container.replace("hive-", "")] = "healthy"
                    elif health in ["starting", "none"]:
                        status[container.replace("hive-", "")] = "unhealthy"
                    else:
                        status[container.replace("hive-", "")] = "unhealthy"
                else:
                    status[container.replace("hive-", "")] = "stopped"

        except Exception:
            status["genie-postgres"] = "unknown"
            status["genie-api"] = "unknown"

        return status

    def _show_all_logs(self, lines: int) -> bool:
        """Show logs for all services."""
        success = True

        if not self._show_workspace_logs(lines):
            success = False

        if not self._show_agent_logs(lines):
            success = False

        if not self._show_genie_logs(lines):
            success = False

        return success

    def _show_workspace_logs(self, lines: int) -> bool:
        """Show workspace logs."""
        try:
            # For now, show recent uvx output
            return True
        except Exception:
            return False

    def _show_agent_logs(self, lines: int) -> bool:
        """Show agent service logs."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return False

        try:
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "agent",
                    "logs",
                    "--tail",
                    str(lines),
                ],
                check=False,
                capture_output=False,
                text=True,
            )

            return result.returncode == 0

        except Exception:
            return False

    def _show_genie_logs(self, lines: int) -> bool:
        """Show genie service logs."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return False

        try:
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "genie",
                    "logs",
                    "--tail",
                    str(lines),
                ],
                check=False,
                capture_output=False,
                text=True,
            )

            return result.returncode == 0

        except Exception:
            return False

    def _uninstall_all(self) -> bool:
        """Uninstall all components."""
        success = True

        if not self._uninstall_workspace():
            success = False

        if not self._uninstall_agent():
            success = False

        if not self._uninstall_genie():
            success = False

        return success

    def _uninstall_workspace(self) -> bool:
        """Uninstall workspace components."""
        try:
            # Just stop the process - no files to remove for workspace component
            return self._stop_workspace()
        except Exception:
            return False

    def _uninstall_agent(self) -> bool:
        """Uninstall agent components."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return True

        try:
            # Remove containers and volumes
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "agent",
                    "down",
                    "-v",
                    "--remove-orphans",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True
            return True  # Don't fail on uninstall warnings

        except Exception:
            return False

    def _uninstall_genie(self) -> bool:
        """Uninstall genie components."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            return True

        try:
            # Remove containers and volumes
            result = subprocess.run(
                [
                    "docker-compose",
                    "-f",
                    str(compose_file),
                    "--profile",
                    "genie",
                    "down",
                    "-v",
                    "--remove-orphans",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True
            return True  # Don't fail on uninstall warnings

        except Exception:
            return False

    # CLI compatibility methods
    def get_logs(self, component: str = "all", lines: int = 50) -> dict[str, str]:
        """Get logs for specified component (CLI compatibility wrapper).
        
        Args:
            component: Component to get logs for
            lines: Number of lines to retrieve
            
        Returns:
            dict: Component logs as {component: log_content}
        """
        # Delegate to existing show_logs method and capture output
        self.show_logs(component, lines)
        return {"status": "logs_displayed"}
    
    def display_logs(self, logs: dict[str, str]) -> None:
        """Display logs (CLI compatibility - logs already displayed by get_logs)."""
        # Logs already displayed by show_logs
        
    def display_status(self, status: dict[str, str]) -> None:
        """Display service status in formatted output.
        
        Args:
            status: Status dictionary from get_status()
        """
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        table = Table(title="Service Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        for component, stat in status.items():
            # Color code status
            if stat == "healthy":
                status_text = f"[green]{stat}[/green]"
            elif stat == "running":
                status_text = f"[yellow]{stat}[/yellow]"
            elif stat == "stopped":
                status_text = f"[red]{stat}[/red]"
            else:
                status_text = f"[dim]{stat}[/dim]"
                
            table.add_row(component, status_text)
            
        console.print(table)
