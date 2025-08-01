"""Docker SDK Proof-of-Concept Implementation.

This module demonstrates Docker SDK for Python integration to replace
subprocess calls with native Python Docker operations.

Key Benefits:
- Type safety and IDE support
- Structured error handling
- Better resource management
- Programmatic control over Docker operations
- No shell injection vulnerabilities
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import docker
from docker.errors import (
    APIError,
    ContainerError,
    DockerException,
    ImageNotFound,
    NotFound,
)
from docker.models.containers import Container


class ContainerState(Enum):
    """Container state enumeration."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"


@dataclass
class ContainerInfo:
    """Container information structure."""

    id: str
    name: str
    image: str
    state: ContainerState
    status: str
    ports: dict[str, Any]
    labels: dict[str, str]
    created: str
    started: str | None = None


@dataclass
class ServiceHealth:
    """Service health information."""

    name: str
    container_id: str
    state: ContainerState
    health_status: str | None
    last_health_check: str | None
    is_ready: bool


class DockerSDKManager:
    """Docker SDK-based container management.

    This is a proof-of-concept demonstrating how to replace subprocess
    Docker calls with the Docker SDK for Python.

    Benefits over subprocess approach:
    - Type safety and IDE autocompletion
    - Structured exception handling
    - Better resource management
    - No shell injection vulnerabilities
    - Programmatic access to container/image metadata
    """

    def __init__(self):
        """Initialize Docker SDK client."""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self._available = True
        except DockerException:
            self._available = False
            self.client = None

    @property
    def is_available(self) -> bool:
        """Check if Docker is available and SDK is connected."""
        return self._available and self.client is not None

    def get_container_info(self, name_or_id: str) -> ContainerInfo | None:
        """Get detailed container information using Docker SDK.

        Args:
            name_or_id: Container name or ID

        Returns:
            ContainerInfo object or None if not found
        """
        if not self.is_available:
            return None

        try:
            container = self.client.containers.get(name_or_id)

            # Parse state enum
            state_str = container.attrs["State"]["Status"]
            try:
                state = ContainerState(state_str)
            except ValueError:
                state = ContainerState.EXITED  # Default fallback

            return ContainerInfo(
                id=container.id[:12],  # Short ID like Docker CLI
                name=container.name,
                image=container.image.tags[0]
                if container.image.tags
                else container.image.id[:12],
                state=state,
                status=container.status,
                ports=container.attrs["NetworkSettings"]["Ports"] or {},
                labels=container.labels,
                created=container.attrs["Created"],
                started=container.attrs["State"].get("StartedAt"),
            )

        except NotFound:
            return None
        except APIError:
            return None

    def start_container(
        self,
        image: str,
        name: str,
        ports: dict[str, int] | None = None,
        environment: dict[str, str] | None = None,
        volumes: dict[str, dict[str, str]] | None = None,
        labels: dict[str, str] | None = None,
        restart_policy: dict[str, Any] | None = None,
        detach: bool = True,
    ) -> Container | None:
        """Start container using Docker SDK.

        Args:
            image: Docker image name
            name: Container name
            ports: Port mappings {container_port: host_port}
            environment: Environment variables
            volumes: Volume mappings
            labels: Container labels
            restart_policy: Restart policy configuration
            detach: Run in detached mode

        Returns:
            Container object or None if failed
        """
        if not self.is_available:
            return None

        try:
            # Check if container already exists
            try:
                existing = self.client.containers.get(name)
                if existing.status == "running":
                    return existing
                existing.start()
                return existing
            except NotFound:
                pass  # Container doesn't exist, create new one

            # Create new container

            return self.client.containers.run(
                image=image,
                name=name,
                ports=ports or {},
                environment=environment or {},
                volumes=volumes or {},
                labels=labels or {},
                restart_policy=restart_policy,
                detach=detach,
                remove=False,  # Don't auto-remove for persistence
            )

        except ImageNotFound:
            return None
        except APIError:
            return None
        except ContainerError:
            return None

    def stop_container(self, name_or_id: str, timeout: int = 10) -> bool:
        """Stop container gracefully using Docker SDK.

        Args:
            name_or_id: Container name or ID
            timeout: Seconds to wait before force kill

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_available:
            return False

        try:
            container = self.client.containers.get(name_or_id)

            if container.status != "running":
                return True

            container.stop(timeout=timeout)

            return True

        except NotFound:
            return False
        except APIError:
            return False

    def restart_container(self, name_or_id: str, timeout: int = 10) -> bool:
        """Restart container using Docker SDK.

        Args:
            name_or_id: Container name or ID
            timeout: Seconds to wait for stop before force kill

        Returns:
            True if restarted successfully, False otherwise
        """
        if not self.is_available:
            return False

        try:
            container = self.client.containers.get(name_or_id)

            container.restart(timeout=timeout)

            return True

        except NotFound:
            return False
        except APIError:
            return False

    def get_container_logs(
        self,
        name_or_id: str,
        tail: int = 50,
        follow: bool = False,
        timestamps: bool = False,
    ) -> str | None:
        """Get container logs using Docker SDK.

        Args:
            name_or_id: Container name or ID
            tail: Number of lines to retrieve
            follow: Stream logs continuously
            timestamps: Include timestamps

        Returns:
            Log content as string or None if error
        """
        if not self.is_available:
            return None

        try:
            container = self.client.containers.get(name_or_id)

            logs = container.logs(
                tail=tail,
                follow=follow,
                timestamps=timestamps,
                stream=False,  # Return as bytes, not generator
            )

            return logs.decode("utf-8", errors="replace")

        except NotFound:
            return None
        except APIError:
            return None

    def wait_for_healthy(
        self, name_or_id: str, timeout: int = 60, check_interval: float = 1.0
    ) -> bool:
        """Wait for container to become healthy using Docker SDK.

        Args:
            name_or_id: Container name or ID
            timeout: Maximum wait time in seconds
            check_interval: Check interval in seconds

        Returns:
            True if container is healthy, False if timeout or error
        """
        if not self.is_available:
            return False

        try:
            container = self.client.containers.get(name_or_id)

            start_time = time.time()
            while time.time() - start_time < timeout:
                # Reload container state
                container.reload()

                state = container.attrs["State"]

                # Check if container is running
                if state["Status"] != "running":
                    return False

                # Check health if available
                health = state.get("Health")
                if health:
                    health_status = health.get("Status")
                    if health_status == "healthy":
                        return True
                    if health_status == "unhealthy":
                        return False
                    # Still starting, continue waiting
                else:
                    # No health check defined, just check if running
                    return True

                time.sleep(check_interval)

            return False

        except NotFound:
            return False
        except APIError:
            return False

    def list_containers(self, all: bool = False) -> list[ContainerInfo]:
        """List containers using Docker SDK.

        Args:
            all: Include stopped containers

        Returns:
            List of ContainerInfo objects
        """
        if not self.is_available:
            return []

        try:
            containers = self.client.containers.list(all=all)

            container_list = []
            for container in containers:
                try:
                    state_str = container.attrs["State"]["Status"]
                    try:
                        state = ContainerState(state_str)
                    except ValueError:
                        state = ContainerState.EXITED

                    info = ContainerInfo(
                        id=container.id[:12],
                        name=container.name,
                        image=container.image.tags[0]
                        if container.image.tags
                        else container.image.id[:12],
                        state=state,
                        status=container.status,
                        ports=container.attrs["NetworkSettings"]["Ports"] or {},
                        labels=container.labels,
                        created=container.attrs["Created"],
                        started=container.attrs["State"].get("StartedAt"),
                    )
                    container_list.append(info)

                except Exception:
                    continue

            return container_list

        except APIError:
            return []

    def prune_containers(self) -> dict[str, Any]:
        """Remove stopped containers using Docker SDK.

        Returns:
            Prune results dictionary
        """
        if not self.is_available:
            return {}

        try:
            result = self.client.containers.prune()

            len(result.get("ContainersDeleted", []))
            result.get("SpaceReclaimed", 0)

            return result

        except APIError:
            return {}

    def get_service_health(self, service_name: str) -> ServiceHealth | None:
        """Get comprehensive service health information.

        Args:
            service_name: Name of the service/container

        Returns:
            ServiceHealth object or None if not found
        """
        if not self.is_available:
            return None

        container_info = self.get_container_info(service_name)
        if not container_info:
            return None

        try:
            container = self.client.containers.get(service_name)
            state = container.attrs["State"]
            health = state.get("Health", {})

            return ServiceHealth(
                name=service_name,
                container_id=container_info.id,
                state=container_info.state,
                health_status=health.get("Status"),
                last_health_check=health.get("Log", [{}])[-1].get("Start")
                if health.get("Log")
                else None,
                is_ready=container_info.state == ContainerState.RUNNING
                and (
                    health.get("Status") in ["healthy", None]
                ),  # No health check or healthy
            )

        except (NotFound, APIError):
            return None

    def cleanup(self):
        """Clean up Docker SDK client resources."""
        if self.client:
            self.client.close()
            self._available = False


# Proof-of-concept usage examples
def demonstrate_sdk_vs_subprocess():
    """Demonstrate Docker SDK advantages over subprocess calls."""
    # Initialize SDK manager
    sdk = DockerSDKManager()

    if not sdk.is_available:
        return False

    # Example 1: List containers with rich metadata
    containers = sdk.list_containers(all=True)

    for container in containers[:3]:  # Show first 3
        pass

    # Example 2: Type-safe error handling
    try:
        # Try to get info for non-existent container
        info = sdk.get_container_info("non-existent-container")
        if info is None:
            pass
    except Exception:
        pass

    # Example 3: Programmatic access to container metadata
    postgres_containers = [c for c in containers if "postgres" in c.name.lower()]

    if postgres_containers:
        container = postgres_containers[0]

        # Get service health
        health = sdk.get_service_health(container.name)
        if health:
            pass

    return True


if __name__ == "__main__":
    demonstrate_sdk_vs_subprocess()
