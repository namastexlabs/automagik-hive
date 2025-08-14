"""CLI UninstallCommands Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

from pathlib import Path
from typing import Any, Dict, Optional


class UninstallCommands:
    """CLI UninstallCommands implementation."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
    
    def uninstall_current_workspace(self) -> bool:
        """Uninstall current workspace."""
        print("🗑️ Uninstalling current workspace")
        return True
    
    def uninstall_global(self) -> bool:
        """Uninstall global installation."""
        print("🗑️ Uninstalling global installation")
        return True
    
    def execute(self) -> bool:
        """Execute command stub."""
        return True
    
    def uninstall_agent(self) -> bool:
        """Uninstall agent stub."""
        return True
    
    def uninstall_workspace(self) -> bool:
        """Uninstall workspace stub."""
        return True
    
    def status(self) -> dict[str, Any]:
        """Get status stub."""
        return {"status": "running", "healthy": True}
