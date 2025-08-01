"""
PostgreSQL CLI Commands for Automagik Hive.

This module provides CLI commands for PostgreSQL container management,
integrating with the PostgreSQL service layer for high-level operations.
"""

import sys
from pathlib import Path
from typing import Optional

from cli.core.postgres_service import PostgreSQLService


class PostgreSQLCommands:
    """
    PostgreSQL CLI command implementations.
    
    Provides user-friendly CLI commands for PostgreSQL container
    lifecycle management and workspace validation.
    """
    
    def __init__(self):
        self.postgres_service = PostgreSQLService()
        
    def postgres_status(self, workspace_path: Optional[str] = None) -> bool:
        """
        Show PostgreSQL container status.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if command executed successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())
        
        print(f"🔍 Checking PostgreSQL status in workspace: {workspace}")
        
        status = self.postgres_service.get_postgres_status(workspace)
        print(f"PostgreSQL Status: {status}")
        
        # Show connection info if running
        if "Running" in status:
            conn_info = self.postgres_service.get_postgres_connection_info(workspace)
            if conn_info:
                print("\n📋 Connection Information:")
                print(f"   Host: {conn_info['host']}")
                print(f"   Port: {conn_info['port']}")
                print(f"   Database: {conn_info['database']}")
                print(f"   User: {conn_info['user']}")
                
        return True
        
    def postgres_start(self, workspace_path: Optional[str] = None) -> bool:
        """
        Start PostgreSQL container.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if started successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())
        
        print(f"🚀 Starting PostgreSQL in workspace: {workspace}")
        
        if self.postgres_service.start_postgres(workspace):
            print("✅ PostgreSQL started successfully")
            return True
        else:
            print("❌ Failed to start PostgreSQL")
            return False
            
    def postgres_stop(self, workspace_path: Optional[str] = None) -> bool:
        """
        Stop PostgreSQL container.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())
        
        print(f"🛑 Stopping PostgreSQL in workspace: {workspace}")
        
        if self.postgres_service.stop_postgres(workspace):
            print("✅ PostgreSQL stopped successfully")
            return True
        else:
            print("❌ Failed to stop PostgreSQL")
            return False
            
    def postgres_restart(self, workspace_path: Optional[str] = None) -> bool:
        """
        Restart PostgreSQL container.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if restarted successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())
        
        print(f"🔄 Restarting PostgreSQL in workspace: {workspace}")
        
        if self.postgres_service.restart_postgres(workspace):
            print("✅ PostgreSQL restarted successfully")
            return True
        else:
            print("❌ Failed to restart PostgreSQL")
            return False
            
    def postgres_logs(self, workspace_path: Optional[str] = None, tail: int = 50) -> bool:
        """
        Show PostgreSQL container logs.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            tail: Number of lines to show
            
        Returns:
            True if logs displayed, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())
        
        print(f"📋 Showing PostgreSQL logs from workspace: {workspace}")
        
        return self.postgres_service.show_postgres_logs(workspace, tail)
        
    def postgres_health(self, workspace_path: Optional[str] = None) -> bool:
        """
        Check PostgreSQL health and connectivity.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if healthy, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())
        
        print(f"🩺 Checking PostgreSQL health in workspace: {workspace}")
        
        if self.postgres_service.validate_postgres_health(workspace):
            print("✅ PostgreSQL is healthy and accepting connections")
            return True
        else:
            print("❌ PostgreSQL is not healthy or not accepting connections")
            return False
            
    def postgres_setup(self, workspace_path: str, interactive: bool = True) -> bool:
        """
        Setup PostgreSQL for workspace initialization.
        
        Args:
            workspace_path: Path to workspace directory
            interactive: Whether to prompt for user confirmation
            
        Returns:
            True if setup successful, False otherwise
        """
        workspace = str(Path(workspace_path).resolve())
        
        print(f"🛠️ Setting up PostgreSQL for workspace: {workspace}")
        
        if self.postgres_service.setup_postgres(workspace, interactive):
            print("✅ PostgreSQL setup completed successfully")
            return True
        else:
            print("❌ PostgreSQL setup failed")
            return False


# Convenience functions for direct CLI usage
def postgres_status_cmd(workspace: Optional[str] = None) -> int:
    """CLI entry point for postgres status command."""
    commands = PostgreSQLCommands()
    success = commands.postgres_status(workspace)
    return 0 if success else 1


def postgres_start_cmd(workspace: Optional[str] = None) -> int:
    """CLI entry point for postgres start command."""
    commands = PostgreSQLCommands()
    success = commands.postgres_start(workspace)
    return 0 if success else 1


def postgres_stop_cmd(workspace: Optional[str] = None) -> int:
    """CLI entry point for postgres stop command."""
    commands = PostgreSQLCommands()
    success = commands.postgres_stop(workspace)
    return 0 if success else 1


def postgres_restart_cmd(workspace: Optional[str] = None) -> int:
    """CLI entry point for postgres restart command."""
    commands = PostgreSQLCommands()
    success = commands.postgres_restart(workspace)
    return 0 if success else 1


def postgres_logs_cmd(workspace: Optional[str] = None, tail: int = 50) -> int:
    """CLI entry point for postgres logs command."""
    commands = PostgreSQLCommands()
    success = commands.postgres_logs(workspace, tail)
    return 0 if success else 1


def postgres_health_cmd(workspace: Optional[str] = None) -> int:
    """CLI entry point for postgres health command."""
    commands = PostgreSQLCommands()
    success = commands.postgres_health(workspace)
    return 0 if success else 1