"""
Service Manager - Unified service lifecycle management for Automagik Hive components.

Handles start, stop, restart, status, logs, and uninstall operations for:
- all: Complete system (workspace + agent + genie)
- workspace: Local uvx process
- agent: Docker services (postgres + api on ports 35532/38886)
- genie: Docker services (postgres + api on ports 48532/48886)
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

from cli.core.docker_service import DockerService
from cli.core.postgres_service import PostgreSQLService


class ServiceManager:
    """Unified service lifecycle management for all Hive components."""

    def __init__(self):
        self.docker_service = DockerService()
        self.postgres_service = PostgreSQLService()
        self.workspace_process = None

    def start_services(self, component: str = "all") -> bool:
        """
        Start specified services with proper dependency ordering.

        Args:
            component: Service component to start (all|workspace|agent|genie)

        Returns:
            bool: True if all requested services started successfully
        """
        print(f"🚀 Starting {component} services...")

        try:
            if component == "all":
                return self._start_all_services()
            elif component == "workspace":
                return self._start_workspace()
            elif component == "agent":
                return self._start_agent_services()
            elif component == "genie":
                return self._start_genie_services()
            else:
                print(f"❌ Unknown component: {component}")
                return False

        except Exception as e:
            print(f"❌ Error starting {component} services: {e}")
            return False

    def stop_services(self, component: str = "all") -> bool:
        """
        Stop specified services gracefully.

        Args:
            component: Service component to stop (all|workspace|agent|genie)

        Returns:
            bool: True if all requested services stopped successfully
        """
        print(f"🛑 Stopping {component} services...")

        try:
            if component == "all":
                return self._stop_all_services()
            elif component == "workspace":
                return self._stop_workspace()
            elif component == "agent":
                return self._stop_agent_services()
            elif component == "genie":
                return self._stop_genie_services()
            else:
                print(f"❌ Unknown component: {component}")
                return False

        except Exception as e:
            print(f"❌ Error stopping {component} services: {e}")
            return False

    def restart_services(self, component: str = "all") -> bool:
        """
        Restart specified services (stop + start).

        Args:
            component: Service component to restart (all|workspace|agent|genie)

        Returns:
            bool: True if restart completed successfully
        """
        print(f"🔄 Restarting {component} services...")

        # Stop first
        if not self.stop_services(component):
            print(f"❌ Failed to stop {component} services")
            return False

        # Brief pause for cleanup
        time.sleep(2)

        # Start again
        return self.start_services(component)

    def get_status(self, component: str = "all") -> Dict[str, str]:
        """
        Get status of specified services.

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

        except Exception as e:
            print(f"❌ Error getting {component} status: {e}")
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
        """
        Show logs for specified services.

        Args:
            component: Service component to show logs for (all|workspace|agent|genie)
            lines: Number of log lines to display

        Returns:
            bool: True if logs displayed successfully
        """
        print(f"📋 Showing {component} logs ({lines} lines)...")

        try:
            if component == "all":
                return self._show_all_logs(lines)
            elif component == "workspace":
                return self._show_workspace_logs(lines)
            elif component == "agent":
                return self._show_agent_logs(lines)
            elif component == "genie":
                return self._show_genie_logs(lines)
            else:
                print(f"❌ Unknown component: {component}")
                return False

        except Exception as e:
            print(f"❌ Error showing {component} logs: {e}")
            return False

    def uninstall(self, component: str = "all") -> bool:
        """
        Uninstall specified components (stop + remove containers/volumes/configs).

        Args:
            component: Service component to uninstall (all|workspace|agent|genie)

        Returns:
            bool: True if uninstall completed successfully
        """
        print(f"🗑️  Uninstalling {component} components...")

        try:
            # Stop services first
            if not self.stop_services(component):
                print(f"⚠️  Warning: Failed to stop {component} services cleanly")

            if component == "all":
                return self._uninstall_all()
            elif component == "workspace":
                return self._uninstall_workspace()
            elif component == "agent":
                return self._uninstall_agent()
            elif component == "genie":
                return self._uninstall_genie()
            else:
                print(f"❌ Unknown component: {component}")
                return False

        except Exception as e:
            print(f"❌ Error uninstalling {component}: {e}")
            return False

    # Private implementation methods

    def _start_all_services(self) -> bool:
        """Start all services in proper order."""
        success = True

        # Start Docker services first
        if not self._start_agent_services():
            print("⚠️  Agent services failed to start")
            success = False

        if not self._start_genie_services():
            print("⚠️  Genie services failed to start")
            success = False

        # Start workspace last
        if not self._start_workspace():
            print("⚠️  Workspace service failed to start")
            success = False

        return success

    def _stop_all_services(self) -> bool:
        """Stop all services gracefully."""
        success = True

        # Stop workspace first
        if not self._stop_workspace():
            print("⚠️  Workspace service failed to stop")
            success = False

        # Stop Docker services
        if not self._stop_agent_services():
            print("⚠️  Agent services failed to stop")
            success = False

        if not self._stop_genie_services():
            print("⚠️  Genie services failed to stop")
            success = False

        return success

    def _start_workspace(self) -> bool:
        """Start workspace uvx process."""
        try:
            # Check if already running
            if self._get_workspace_status() == "healthy":
                print("✅ Workspace already running")
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
                print("✅ Workspace started successfully")
                self.workspace_process = process
                return True
            else:
                print("❌ Workspace failed to start")
                return False

        except Exception as e:
            print(f"❌ Error starting workspace: {e}")
            return False

    def _stop_workspace(self) -> bool:
        """Stop workspace uvx process."""
        try:
            # Try to stop gracefully via process
            if self.workspace_process and self.workspace_process.poll() is None:
                self.workspace_process.terminate()
                self.workspace_process.wait(timeout=10)
                print("✅ Workspace stopped")
                return True

            # Fallback: kill by process name
            result = subprocess.run(
                ["pkill", "-f", "uvx.*automagik-hive"], capture_output=True, text=True
            )

            if result.returncode == 0:
                print("✅ Workspace stopped")
                return True
            else:
                print("ℹ️  Workspace was not running")
                return True

        except Exception as e:
            print(f"❌ Error stopping workspace: {e}")
            return False

    def _start_agent_services(self) -> bool:
        """Start agent Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("❌ docker-compose.unified.yml not found")
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
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Agent services started")
                return True
            else:
                print(f"❌ Failed to start agent services: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error starting agent services: {e}")
            return False

    def _stop_agent_services(self) -> bool:
        """Stop agent Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("⚠️  docker-compose.unified.yml not found")
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
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Agent services stopped")
                return True
            else:
                print(f"⚠️  Agent services stop warning: {result.stderr}")
                return True  # Don't fail on stop warnings

        except Exception as e:
            print(f"❌ Error stopping agent services: {e}")
            return False

    def _start_genie_services(self) -> bool:
        """Start genie Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("❌ docker-compose.unified.yml not found")
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
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Genie services started")
                return True
            else:
                print(f"❌ Failed to start genie services: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error starting genie services: {e}")
            return False

    def _stop_genie_services(self) -> bool:
        """Stop genie Docker services."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("⚠️  docker-compose.unified.yml not found")
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
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Genie services stopped")
                return True
            else:
                print(f"⚠️  Genie services stop warning: {result.stderr}")
                return True  # Don't fail on stop warnings

        except Exception as e:
            print(f"❌ Error stopping genie services: {e}")
            return False

    def _get_workspace_status(self) -> str:
        """Get workspace service status."""
        try:
            # Check if uvx process is running
            result = subprocess.run(
                ["pgrep", "-f", "uvx.*automagik-hive"], capture_output=True, text=True
            )

            if result.returncode == 0:
                return "healthy"
            else:
                return "stopped"

        except Exception:
            return "unknown"

    def _get_agent_status(self) -> Dict[str, str]:
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

    def _get_genie_status(self) -> Dict[str, str]:
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

        print("📋 Workspace logs:")
        if not self._show_workspace_logs(lines):
            success = False

        print("\n📋 Agent logs:")
        if not self._show_agent_logs(lines):
            success = False

        print("\n📋 Genie logs:")
        if not self._show_genie_logs(lines):
            success = False

        return success

    def _show_workspace_logs(self, lines: int) -> bool:
        """Show workspace logs."""
        try:
            # For now, show recent uvx output
            print("ℹ️  Workspace logs not yet implemented")
            return True
        except Exception as e:
            print(f"❌ Error showing workspace logs: {e}")
            return False

    def _show_agent_logs(self, lines: int) -> bool:
        """Show agent service logs."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("⚠️  docker-compose.unified.yml not found")
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
                capture_output=False,
                text=True,
            )

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error showing agent logs: {e}")
            return False

    def _show_genie_logs(self, lines: int) -> bool:
        """Show genie service logs."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("⚠️  docker-compose.unified.yml not found")
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
                capture_output=False,
                text=True,
            )

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error showing genie logs: {e}")
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
        except Exception as e:
            print(f"❌ Error uninstalling workspace: {e}")
            return False

    def _uninstall_agent(self) -> bool:
        """Uninstall agent components."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("✅ Agent already uninstalled (no compose file)")
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
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Agent components uninstalled")
                return True
            else:
                print(f"⚠️  Agent uninstall warning: {result.stderr}")
                return True  # Don't fail on uninstall warnings

        except Exception as e:
            print(f"❌ Error uninstalling agent: {e}")
            return False

    def _uninstall_genie(self) -> bool:
        """Uninstall genie components."""
        compose_file = Path.cwd() / "docker-compose.unified.yml"
        if not compose_file.exists():
            print("✅ Genie already uninstalled (no compose file)")
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
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Genie components uninstalled")
                return True
            else:
                print(f"⚠️  Genie uninstall warning: {result.stderr}")
                return True  # Don't fail on uninstall warnings

        except Exception as e:
            print(f"❌ Error uninstalling genie: {e}")
            return False
