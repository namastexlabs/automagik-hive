"""CLI PostgreSQL Service - Real Docker Container Management.

Provides PostgreSQL service management functionality using DockerManager integration.
This service coordinates with PostgreSQL commands for unified container management.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ..commands.postgres import PostgreSQLCommands


class PostgreSQLService:
    """CLI PostgreSQL Service implementation with real Docker functionality."""
    
    def __init__(self, workspace_path: Path | None = None):
        """Initialize PostgreSQL service."""
        self.workspace_path = workspace_path or Path()
        self.postgres_commands = PostgreSQLCommands(workspace_path)
    
    def execute(self) -> bool:
        """Execute PostgreSQL service operations."""
        return True
    
    def status(self) -> dict[str, Any]:
        """Get comprehensive PostgreSQL status."""
        try:
            workspace_str = str(self.workspace_path)
            
            # Get the target container name
            container_name = self.postgres_commands._get_postgres_container_for_workspace(workspace_str)
            if not container_name:
                return {
                    "status": "not_found",
                    "healthy": False,
                    "container": None,
                    "message": "No PostgreSQL container found"
                }
            
            # Check if container exists
            if not self.postgres_commands.docker_manager._container_exists(container_name):
                return {
                    "status": "not_installed",
                    "healthy": False,
                    "container": container_name,
                    "message": "PostgreSQL container not installed"
                }
            
            # Check if container is running
            is_running = self.postgres_commands.docker_manager._container_running(container_name)
            
            if not is_running:
                return {
                    "status": "stopped",
                    "healthy": False,
                    "container": container_name,
                    "message": "PostgreSQL container exists but is stopped"
                }
            
            # Get health status if available
            health_status = self.postgres_commands.docker_manager._run_command([
                "docker", "inspect", "--format", "{{.State.Health.Status}}", container_name
            ], capture_output=True)
            
            # Get port information
            port_info = self.postgres_commands.docker_manager._run_command([
                "docker", "port", container_name, "5432"
            ], capture_output=True)
            
            # Determine overall health
            healthy = is_running and (not health_status or health_status == "healthy")
            
            return {
                "status": "running",
                "healthy": healthy,
                "container": container_name,
                "health_status": health_status or "unknown",
                "port_mapping": port_info,
                "message": "PostgreSQL container is running"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "container": None,
                "message": f"Error checking PostgreSQL status: {e}"
            }
    
    def start(self) -> bool:
        """Start PostgreSQL service."""
        return self.postgres_commands.postgres_start(str(self.workspace_path))
    
    def stop(self) -> bool:
        """Stop PostgreSQL service."""
        return self.postgres_commands.postgres_stop(str(self.workspace_path))
    
    def restart(self) -> bool:
        """Restart PostgreSQL service."""
        return self.postgres_commands.postgres_restart(str(self.workspace_path))
    
    def logs(self, lines: int = 50) -> bool:
        """Get PostgreSQL logs."""
        return self.postgres_commands.postgres_logs(str(self.workspace_path), lines)
    
    def health_check(self) -> bool:
        """Perform PostgreSQL health check."""
        return self.postgres_commands.postgres_health(str(self.workspace_path))
