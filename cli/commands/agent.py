"""Agent CLI Commands for Automagik Hive.

This module provides CLI commands for Agent environment management,
integrating with the Agent service layer for high-level operations.
"""

from pathlib import Path

from cli.core.agent_service import AgentService


class AgentCommands:
    """Agent CLI command implementations.
    
    Provides user-friendly CLI commands for Agent environment
    lifecycle management and workspace validation.
    """

    def __init__(self):
        self.agent_service = AgentService()

    def install(self, workspace_path: str | None = None) -> bool:
        """Install complete agent environment with isolated ports and database.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if installation successful, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"🤖 Installing agent environment in workspace: {workspace}")

        if self.agent_service.install_agent_environment(workspace):
            print("✅ Agent environment installation completed successfully")
            return True
        print("❌ Agent environment installation failed")
        return False

    def serve(self, workspace_path: str | None = None) -> bool:
        """Start agent server in background (non-blocking).
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if started successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"🚀 Starting agent server in workspace: {workspace}")

        if self.agent_service.serve_agent(workspace):
            print("✅ Agent server started successfully")
            return True
        print("❌ Failed to start agent server")
        return False

    def stop(self, workspace_path: str | None = None) -> bool:
        """Stop agent server cleanly.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if stopped successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"🛑 Stopping agent server in workspace: {workspace}")

        if self.agent_service.stop_agent(workspace):
            print("✅ Agent server stopped successfully")
            return True
        print("❌ Failed to stop agent server")
        return False

    def restart(self, workspace_path: str | None = None) -> bool:
        """Restart agent server.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if restarted successfully, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"🔄 Restarting agent server in workspace: {workspace}")

        if self.agent_service.restart_agent(workspace):
            print("✅ Agent server restarted successfully")
            return True
        print("❌ Failed to restart agent server")
        return False

    def logs(self, workspace_path: str | None = None, tail: int = 50) -> bool:
        """Show agent server logs.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            tail: Number of lines to show
            
        Returns:
            True if logs displayed, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"📋 Showing agent logs from workspace: {workspace}")

        return self.agent_service.show_agent_logs(workspace, tail)

    def status(self, workspace_path: str | None = None) -> bool:
        """Check agent environment status.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if status displayed, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"🔍 Checking agent status in workspace: {workspace}")

        status_info = self.agent_service.get_agent_status(workspace)
        
        print("\n📊 Agent Environment Status:")
        print("┌─────────────────────────┬──────────────────────────────────────┐")
        print("│ Agent Service           │ Status                               │")
        print("├─────────────────────────┼──────────────────────────────────────┤")
        
        for service, status in status_info.items():
            service_display = service.replace("-", " ").title()[:23]
            status_display = status[:36]
            print(f"│ {service_display:<23} │ {status_display:<36} │")
            
        print("└─────────────────────────┴──────────────────────────────────────┘")

        # Show recent activity if available
        if Path("logs/agent-server.log").exists():
            print("\n📋 Recent agent activity:")
            try:
                import subprocess
                result = subprocess.run(
                    ["tail", "-5", "logs/agent-server.log"],
                    capture_output=True, text=True, check=False
                )
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        print(f"  {line}")
                else:
                    print("  No recent activity")
            except:
                print("  No recent activity")

        return True

    def reset(self, workspace_path: str | None = None) -> bool:
        """Reset agent environment (destructive reinstall).
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if reset successful, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        print(f"🔄 Resetting agent environment in workspace: {workspace}")

        if self.agent_service.reset_agent_environment(workspace):
            print("✅ Agent environment reset completed successfully")
            return True
        print("❌ Agent environment reset failed")
        return False


# Convenience functions for direct CLI usage
def agent_install_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent install command."""
    commands = AgentCommands()
    success = commands.install(workspace)
    return 0 if success else 1


def agent_serve_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent serve command."""
    commands = AgentCommands()
    success = commands.serve(workspace)
    return 0 if success else 1


def agent_stop_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent stop command."""
    commands = AgentCommands()
    success = commands.stop(workspace)
    return 0 if success else 1


def agent_restart_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent restart command."""
    commands = AgentCommands()
    success = commands.restart(workspace)
    return 0 if success else 1


def agent_logs_cmd(workspace: str | None = None, tail: int = 50) -> int:
    """CLI entry point for agent logs command."""
    commands = AgentCommands()
    success = commands.logs(workspace, tail)
    return 0 if success else 1


def agent_status_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent status command."""
    commands = AgentCommands()
    success = commands.status(workspace)
    return 0 if success else 1


def agent_reset_cmd(workspace: str | None = None) -> int:
    """CLI entry point for agent reset command."""
    commands = AgentCommands()
    success = commands.reset(workspace)
    return 0 if success else 1