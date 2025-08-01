"""Docker Compose Management for Automagik Hive.

This module provides Docker Compose orchestration capabilities,
specifically optimized for PostgreSQL and multi-service container management.
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml


class ServiceStatus(Enum):
    """Docker Compose service status states."""

    RUNNING = "running"
    STOPPED = "stopped"
    RESTARTING = "restarting"
    PAUSED = "paused"
    EXITED = "exited"
    DEAD = "dead"
    NOT_EXISTS = "not_exists"


@dataclass
class ServiceInfo:
    """Docker Compose service information."""

    name: str
    status: ServiceStatus
    ports: list[str]
    image: str
    container_name: str | None = None


class DockerComposeManager:
    """Docker Compose orchestration for multi-service container management.

    Provides high-level operations for managing PostgreSQL and other services
    using existing docker-compose.yml files as foundation.
    """

    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self._compose_cmd = None  # Cached compose command

    def start_service(self, service: str, workspace_path: str = ".") -> bool:
        """Start specific service from docker-compose.yml.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if started successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "up", "-d", service],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def stop_service(self, service: str, workspace_path: str = ".") -> bool:
        """Stop specific service from docker-compose.yml.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "stop", service],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def restart_service(self, service: str, workspace_path: str = ".") -> bool:
        """Restart specific service from docker-compose.yml.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if restarted successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "restart", service],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def get_service_logs(
        self, service: str, tail: int = 50, workspace_path: str = "."
    ) -> str | None:
        """Get logs for specific service.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            tail: Number of lines to retrieve
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            Service logs as string, None if error
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return None

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return None
            result = subprocess.run(
                [
                    *compose_cmd,
                    "-f",
                    str(compose_file_path),
                    "logs",
                    "--tail",
                    str(tail),
                    service,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return result.stdout
            return None

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    def stream_service_logs(self, service: str, workspace_path: str = ".") -> bool:
        """Stream logs for specific service (non-blocking).

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if streaming started successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "logs", "-f", service],
                check=False,
                timeout=None,
            )  # No timeout for streaming

            return True

        except KeyboardInterrupt:
            return True
        except subprocess.SubprocessError:
            return False

    def get_service_status(
        self, service: str, workspace_path: str = "."
    ) -> ServiceStatus:
        """Get status of specific service.

        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            ServiceStatus indicating current state
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return ServiceStatus.NOT_EXISTS

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return ServiceStatus.NOT_EXISTS
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "ps", service],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return ServiceStatus.NOT_EXISTS

            output = result.stdout.strip()
            if not output or "No containers found" in output:
                return ServiceStatus.NOT_EXISTS

            # Parse docker-compose ps output
            lines = output.split("\n")
            if len(lines) < 2:  # Header + at least one service line
                return ServiceStatus.NOT_EXISTS

            # Look for service status in output
            service_line = None
            for line in lines[1:]:  # Skip header
                if service in line:
                    service_line = line
                    break

            if not service_line:
                return ServiceStatus.NOT_EXISTS

            # Parse status from the line
            if "Up" in service_line:
                return ServiceStatus.RUNNING
            if "Exit" in service_line:
                return ServiceStatus.EXITED
            if "Restarting" in service_line:
                return ServiceStatus.RESTARTING
            if "Paused" in service_line:
                return ServiceStatus.PAUSED
            return ServiceStatus.STOPPED

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return ServiceStatus.NOT_EXISTS

    def get_all_services_status(
        self, workspace_path: str = "."
    ) -> dict[str, ServiceInfo]:
        """Get status of all services in docker-compose.yml.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            Dict mapping service names to ServiceInfo
        """
        services = {}

        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return services

            # Parse docker-compose.yml to get service names
            with open(compose_file_path) as f:
                compose_config = yaml.safe_load(f)

            if "services" not in compose_config:
                return services

            # Get status for each service
            for service_name in compose_config["services"]:
                status = self.get_service_status(service_name, workspace_path)
                service_config = compose_config["services"][service_name]

                # Extract service information
                ports = []
                if "ports" in service_config:
                    ports = service_config["ports"]

                image = service_config.get("image", "unknown")
                if "build" in service_config:
                    image = f"built:{service_name}"

                container_name = service_config.get("container_name")

                services[service_name] = ServiceInfo(
                    name=service_name,
                    status=status,
                    ports=ports,
                    image=image,
                    container_name=container_name,
                )

        except Exception:
            pass

        return services

    def start_all_services(self, workspace_path: str = ".") -> bool:
        """Start all services from docker-compose.yml.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if all services started successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "up", "-d"],
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def stop_all_services(self, workspace_path: str = ".") -> bool:
        """Stop all services from docker-compose.yml.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if all services stopped successfully, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "down"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def validate_compose_file(self, workspace_path: str = ".") -> bool:
        """Validate docker-compose.yml file syntax and structure.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            True if valid, False otherwise
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return False

            # Validate syntax with docker-compose config
            compose_cmd = self._get_compose_command()
            if not compose_cmd:
                return False
            result = subprocess.run(
                [*compose_cmd, "-f", str(compose_file_path), "config"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def get_compose_services(self, workspace_path: str = ".") -> list[str]:
        """Get list of service names from docker-compose.yml.

        Args:
            workspace_path: Path to workspace with docker-compose.yml

        Returns:
            List of service names
        """
        try:
            compose_file_path = Path(workspace_path) / self.compose_file
            if not compose_file_path.exists():
                return []

            with open(compose_file_path) as f:
                compose_config = yaml.safe_load(f)

            if "services" not in compose_config:
                return []

            return list(compose_config["services"].keys())

        except Exception:
            return []

    def _get_compose_command(self) -> list[str] | None:
        """Get the appropriate Docker Compose command with fallback.

        Returns:
            List of command parts for docker compose, None if not available
        """
        if self._compose_cmd is not None:
            return self._compose_cmd

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
                self._compose_cmd = ["docker", "compose"]
                return self._compose_cmd
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
                self._compose_cmd = ["docker-compose"]
                return self._compose_cmd
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return None
