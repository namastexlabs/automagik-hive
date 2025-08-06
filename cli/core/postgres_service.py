"""CLI PostgreSQLService Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

from typing import Optional, Dict, Any
from pathlib import Path


class PostgreSQLService:
    """CLI PostgreSQLService stub."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
    
    def execute(self) -> bool:
        """Execute command stub."""
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get status stub."""
        return {"status": "running", "healthy": True}
