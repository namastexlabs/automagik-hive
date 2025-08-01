"""
Docker Service for CLI Operations.

This module provides high-level Docker service operations
for CLI commands, wrapping Docker Compose functionality.
"""

import subprocess
from typing import Dict, List
from pathlib import Path

from docker.lib.compose_manager import DockerComposeManager, ServiceStatus


class DockerService:
    """
    High-level Docker service operations for CLI.
    
    Provides user-friendly Docker container management
    with integrated workspace validation and service orchestration.
    """
    
    def __init__(self):
        self.compose_manager = DockerComposeManager()
        
    def is_docker_available(self) -> bool:
        """
        Check if Docker is installed and available.
        
        Returns:
            True if Docker is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
            
    def is_docker_running(self) -> bool:
        """
        Check if Docker daemon is running.
        
        Returns:
            True if Docker daemon is running, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
        
    def start_service(self, service: str, workspace_path: str) -> bool:
        """
        Start specific service in workspace.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory
            
        Returns:
            True if started successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.compose_manager.start_service(service, str(workspace))
        
    def stop_service(self, service: str, workspace_path: str) -> bool:
        """
        Stop specific service in workspace.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory
            
        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.compose_manager.stop_service(service, str(workspace))
        
    def restart_service(self, service: str, workspace_path: str) -> bool:
        """
        Restart specific service in workspace.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory
            
        Returns:
            True if restarted successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.compose_manager.restart_service(service, str(workspace))
        
    def get_service_status(self, service: str, workspace_path: str) -> str:
        """
        Get human-readable service status.
        
        Args:
            service: Service name (e.g., 'postgres', 'app') 
            workspace_path: Path to workspace directory
            
        Returns:
            Human-readable status string
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return "❌ Invalid workspace"
            
        status = self.compose_manager.get_service_status(service, str(workspace))
        
        status_messages = {
            ServiceStatus.RUNNING: "✅ Running",
            ServiceStatus.STOPPED: "🛑 Stopped",
            ServiceStatus.RESTARTING: "🔄 Restarting", 
            ServiceStatus.PAUSED: "⏸️ Paused",
            ServiceStatus.EXITED: "❌ Exited",
            ServiceStatus.DEAD: "💀 Dead",
            ServiceStatus.NOT_EXISTS: "❌ Not found"
        }
        
        return status_messages.get(status, "❓ Unknown")
        
    def show_service_logs(self, service: str, workspace_path: str, tail: int = 50) -> bool:
        """
        Show service logs.
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory
            tail: Number of lines to show
            
        Returns:
            True if logs displayed, False if error
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False
            
        logs = self.compose_manager.get_service_logs(service, tail, str(workspace))
        if logs:
            print(f"📋 {service.title()} Logs (last {tail} lines):")
            print("-" * 50)
            print(logs)
            return True
        else:
            print(f"❌ Could not retrieve {service} logs")
            return False
            
    def stream_service_logs(self, service: str, workspace_path: str) -> bool:
        """
        Stream service logs (blocking).
        
        Args:
            service: Service name (e.g., 'postgres', 'app')
            workspace_path: Path to workspace directory
            
        Returns:
            True if streaming started, False if error
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False
            
        return self.compose_manager.stream_service_logs(service, str(workspace))
        
    def get_all_services_status(self, workspace_path: str) -> Dict[str, str]:
        """
        Get status of all services in workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Dict mapping service names to human-readable status
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return {}
            
        services_info = self.compose_manager.get_all_services_status(str(workspace))
        
        status_map = {}
        for service_name, service_info in services_info.items():
            status_messages = {
                ServiceStatus.RUNNING: "✅ Running",
                ServiceStatus.STOPPED: "🛑 Stopped",
                ServiceStatus.RESTARTING: "🔄 Restarting",
                ServiceStatus.PAUSED: "⏸️ Paused", 
                ServiceStatus.EXITED: "❌ Exited",
                ServiceStatus.DEAD: "💀 Dead",
                ServiceStatus.NOT_EXISTS: "❌ Not found"
            }
            status_map[service_name] = status_messages.get(
                service_info.status, "❓ Unknown"
            )
            
        return status_map
        
    def start_all_services(self, workspace_path: str) -> bool:
        """
        Start all services in workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if all started successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.compose_manager.start_all_services(str(workspace))
        
    def stop_all_services(self, workspace_path: str) -> bool:
        """
        Stop all services in workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if all stopped successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False
            
        return self.compose_manager.stop_all_services(str(workspace))
        
    def get_available_services(self, workspace_path: str) -> List[str]:
        """
        Get list of available services in workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            List of service names
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return []
            
        return self.compose_manager.get_compose_services(str(workspace))
        
    def validate_compose_file(self, workspace_path: str) -> bool:
        """
        Validate docker-compose.yml syntax and structure.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if valid, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_env=False):
            return False
            
        return self.compose_manager.validate_compose_file(str(workspace))
        
    def _validate_workspace(self, workspace: Path, check_env: bool = True) -> bool:
        """
        Validate workspace directory and required files.
        
        Args:
            workspace: Path to workspace directory
            check_env: Whether to check for .env file
            
        Returns:
            True if valid workspace, False otherwise
        """
        if not workspace.exists():
            print(f"❌ Workspace directory does not exist: {workspace}")
            return False
            
        if not workspace.is_dir():
            print(f"❌ Workspace path is not a directory: {workspace}")
            return False
            
        # Check for docker-compose.yml
        compose_file = workspace / "docker-compose.yml"
        if not compose_file.exists():
            print(f"❌ Missing docker-compose.yml in workspace: {workspace}")
            print("💡 Run 'uvx automagik-hive --init' to initialize workspace")
            return False
            
        # Check for .env file if requested
        if check_env:
            env_file = workspace / ".env"
            if not env_file.exists():
                print(f"❌ Missing .env file in workspace: {workspace}")
                print("💡 Run 'uvx automagik-hive --init' to initialize workspace")
                return False
                
        return True