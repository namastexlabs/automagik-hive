"""Agent CLI Commands for Automagik Hive.

This module provides CLI commands for Agent environment management,
integrating with the Agent service layer for high-level operations.
"""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.core.agent_service import AgentService


class AgentCommands:
    """Agent CLI command implementations.

    Provides user-friendly CLI commands for Agent environment
    lifecycle management and workspace validation.
    """

    def __init__(self) -> None:
        self._agent_service = None
    
    @property
    def agent_service(self) -> "AgentService":
        """Lazy load AgentService only when needed."""
        if self._agent_service is None:
            from cli.core.agent_service import AgentService
            self._agent_service = AgentService()
        return self._agent_service

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
        result = bool(self.agent_service.install_agent_environment(workspace))
        
        if result:
            print("✅ Agent environment installation completed successfully")
        else:
            print("❌ Agent environment installation failed")
            
        return result

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
        result = bool(self.agent_service.serve_agent(workspace))
        
        if result:
            print("✅ Agent server started successfully")
        else:
            print("❌ Failed to start agent server")
            
        return result

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
        result = bool(self.agent_service.stop_agent(workspace))
        
        if result:
            print("✅ Agent server stopped successfully")
        else:
            print("❌ Failed to stop agent server")
            
        return result

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
        result = bool(self.agent_service.restart_agent(workspace))
        
        if result:
            print("✅ Agent server restarted successfully")
        else:
            print("❌ Failed to restart agent server")
            
        return result

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
        result = bool(self.agent_service.show_agent_logs(workspace, tail))
        
        return result

    def status(self, workspace_path: str | None = None) -> bool:
        """Check agent environment status.

        Args:
            workspace_path: Path to workspace (default: current directory)

        Returns:
            True if status displayed, False otherwise
        """
        workspace = workspace_path or "."
        workspace = str(Path(workspace).resolve())

        status_info = self.agent_service.get_agent_status(workspace)
        
        # Print table header
        print("📊 Agent Environment Status:")
        print("┌─────────────────────────┬──────────────────────────────────────┐")
        print("│ Agent Service           │ Status                               │")
        print("├─────────────────────────┼──────────────────────────────────────┤")
        
        # Print status info
        for service, status in status_info.items():
            service_formatted = service.replace("-", " ").title()[:23].ljust(23)
            status_formatted = f"{status[:35]}".ljust(35)  # 35 chars + 1 space
            print(f"│ {service_formatted} │ {status_formatted} │")
            
        print("└─────────────────────────┴──────────────────────────────────────┘")

        # Show recent activity if available
        if Path("logs/agent-server.log").exists():
            try:
                result = subprocess.run(
                    ["tail", "-5", "logs/agent-server.log"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    print(f"\n📝 Recent Activity (last 5 lines):")
                    print("-" * 45)
                    for line in result.stdout.strip().split("\n"):
                        print(f"  {line}")
                else:
                    print(f"\n📝 Log file exists but no recent activity")
            except (OSError, subprocess.SubprocessError, Exception):
                print(f"\n❌ Error reading log file")
        else:
            print(f"\n📝 No log file found at logs/agent-server.log")

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
        result = bool(self.agent_service.reset_agent_environment(workspace))
        
        if result:
            print("✅ Agent environment reset completed successfully")
        else:
            print("❌ Agent environment reset failed")
            
        return result


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
