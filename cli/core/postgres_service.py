"""
PostgreSQL Service for CLI Operations.

This module provides high-level PostgreSQL service operations
for CLI commands, wrapping the PostgreSQLManager functionality.
"""

from typing import Optional
from pathlib import Path

from docker.lib.postgres_manager import PostgreSQLManager, ContainerStatus
from lib.auth.credential_service import CredentialService


class PostgreSQLService:
    """
    High-level PostgreSQL service operations for CLI.
    
    Provides user-friendly PostgreSQL container management
    with integrated credential handling and workspace validation.
    """
    
    def __init__(self):
        self.credential_service = CredentialService()
        self.postgres_manager = PostgreSQLManager(self.credential_service)
        
    def setup_postgres(self, workspace_path: str, interactive: bool = True) -> bool:
        """
        Setup PostgreSQL for workspace initialization.
        
        Args:
            workspace_path: Path to workspace directory
            interactive: Whether to prompt user for confirmation
            
        Returns:
            True if setup successful, False otherwise
        """
        workspace = Path(workspace_path)
        if not workspace.exists():
            print(f"❌ Workspace directory does not exist: {workspace_path}")
            return False
            
        return self.postgres_manager.setup_postgres_container(
            interactive=interactive, 
            workspace_path=str(workspace)
        )
        
    def start_postgres(self, workspace_path: str) -> bool:
        """
        Start PostgreSQL container for existing workspace.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if started successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.postgres_manager.start_container(str(workspace))
        
    def stop_postgres(self, workspace_path: str) -> bool:
        """
        Stop PostgreSQL container.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.postgres_manager.stop_container(str(workspace))
        
    def restart_postgres(self, workspace_path: str) -> bool:
        """
        Restart PostgreSQL container.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if restarted successfully, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.postgres_manager.restart_container(str(workspace))
        
    def get_postgres_status(self, workspace_path: str) -> str:
        """
        Get human-readable PostgreSQL status.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Human-readable status string
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace, check_compose=False):
            return "❌ Invalid workspace"
            
        status = self.postgres_manager.check_container_status()
        
        status_messages = {
            ContainerStatus.RUNNING: "✅ Running",
            ContainerStatus.STOPPED: "🛑 Stopped", 
            ContainerStatus.NOT_EXISTS: "❌ Not created",
            ContainerStatus.UNHEALTHY: "⚠️ Unhealthy",
            ContainerStatus.STARTING: "⏳ Starting"
        }
        
        base_status = status_messages.get(status, "❓ Unknown")
        
        # Add health check if running
        if status == ContainerStatus.RUNNING:
            if self.postgres_manager.validate_container_health(str(workspace)):
                return f"{base_status} and healthy"
            else:
                return f"{base_status} but not accepting connections"
                
        return base_status
        
    def show_postgres_logs(self, workspace_path: str, tail: int = 50) -> bool:
        """
        Show PostgreSQL container logs.
        
        Args:
            workspace_path: Path to workspace directory
            tail: Number of lines to show
            
        Returns:
            True if logs displayed, False if error
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        logs = self.postgres_manager.get_container_logs(tail, str(workspace))
        if logs:
            print("📋 PostgreSQL Logs (last {} lines):".format(tail))
            print("-" * 50)
            print(logs)
            return True
        else:
            print("❌ Could not retrieve PostgreSQL logs")
            return False
            
    def validate_postgres_health(self, workspace_path: str) -> bool:
        """
        Validate PostgreSQL health and connectivity.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            True if healthy and connectable, False otherwise
        """
        workspace = Path(workspace_path)
        if not self._validate_workspace(workspace):
            return False
            
        return self.postgres_manager.validate_container_health(str(workspace))
        
    def get_postgres_connection_info(self, workspace_path: str) -> Optional[dict]:
        """
        Get PostgreSQL connection information.
        
        Args:
            workspace_path: Path to workspace directory
            
        Returns:
            Dict with connection info, None if error
        """
        workspace = Path(workspace_path)
        env_file = workspace / ".env"
        
        if not env_file.exists():
            return None
            
        try:
            # Temporarily change to workspace directory to use existing credential service
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(str(workspace))
                credentials = self.credential_service.extract_postgres_credentials_from_env()
                if not credentials:
                    return None
                    
                return {
                    "host": "localhost",
                    "port": 5532,
                    "database": credentials.get("database", "hive"),
                    "user": credentials.get("user"),
                    "password": credentials.get("password"),
                    "url": credentials.get("url")
                }
            finally:
                os.chdir(original_cwd)
            
        except Exception:
            return None
            
    def _validate_workspace(self, workspace: Path, check_compose: bool = True) -> bool:
        """
        Validate workspace directory and required files.
        
        Args:
            workspace: Path to workspace directory
            check_compose: Whether to check for docker-compose.yml
            
        Returns:
            True if valid workspace, False otherwise
        """
        if not workspace.exists():
            print(f"❌ Workspace directory does not exist: {workspace}")
            return False
            
        if not workspace.is_dir():
            print(f"❌ Workspace path is not a directory: {workspace}")
            return False
            
        # Check for required files
        env_file = workspace / ".env"
        if not env_file.exists():
            print(f"❌ Missing .env file in workspace: {workspace}")
            print("💡 Run 'uvx automagik-hive --init' to initialize workspace")
            return False
            
        if check_compose:
            compose_file = workspace / "docker-compose.yml"
            if not compose_file.exists():
                print(f"❌ Missing docker-compose.yml in workspace: {workspace}")
                print("💡 Run 'uvx automagik-hive --init' to initialize workspace")
                return False
                
        return True