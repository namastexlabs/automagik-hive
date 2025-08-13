"""Agent Commands Implementation.

Real implementation connecting to AgentService for actual functionality.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from cli.core.agent_service import AgentService


class AgentCommands:
    """Agent commands implementation."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
        self.agent_service = AgentService(self.workspace_path)
    
    def install(self, workspace: str = ".") -> bool:
        """Install agent services."""
        try:
            print(f"🚀 Installing agent services in: {workspace}")
            return self.agent_service.install_agent_environment(workspace)
        except Exception:
            return False
    
    def start(self, workspace: str = ".") -> bool:
        """Start agent services."""
        try:
            print(f"🚀 Starting agent services in: {workspace}")
            result = self.agent_service.serve_agent(workspace)
            return bool(result)
        except Exception:
            return False
    
    def serve(self, workspace: str = ".") -> bool:
        """Start agent server (alias for start)."""
        return self.start(workspace)
    
    def stop(self, workspace: str = ".") -> bool:
        """Stop agent services."""
        try:
            print(f"🛑 Stopping agent services in: {workspace}")
            return self.agent_service.stop_agent(workspace)
        except Exception:
            return False
    
    def restart(self, workspace: str = ".") -> bool:
        """Restart agent services."""
        try:
            print(f"🔄 Restarting agent services in: {workspace}")
            return self.agent_service.restart_agent(workspace)
        except Exception:
            return False
    
    def status(self, workspace: str = ".") -> bool:
        """Check agent status."""
        try:
            print(f"🔍 Checking agent status in: {workspace}")
            status = self.agent_service.get_agent_status(workspace)
            
            # Display status for each service
            for service, service_status in status.items():
                print(f"  {service}: {service_status}")
            
            return True
        except Exception:
            return False
    
    def logs(self, workspace: str = ".", tail: int = 50) -> bool:
        """Show agent logs."""
        try:
            print(f"📋 Showing agent logs from: {workspace} (last {tail} lines)")
            return self.agent_service.show_agent_logs(workspace, tail)
        except Exception:
            return False
    
    def health(self, workspace: str = ".") -> Dict[str, Any]:
        """Agent health command."""
        try:
            print(f"🔍 Checking agent health in: {workspace}")
            status = self.agent_service.get_agent_status(workspace)
            return {"status": "healthy" if status else "unhealthy", "workspace": workspace, "services": status}
        except Exception:
            return {"status": "error", "workspace": workspace}
    
    def reset(self, workspace: str = ".") -> bool:
        """Reset agent services."""
        try:
            print(f"🔄 Resetting agent services in: {workspace}")
            return self.agent_service.reset_agent_environment(workspace)
        except Exception:
            return False
