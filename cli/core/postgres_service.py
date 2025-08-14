"""CLI PostgreSQLService Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

from pathlib import Path
from typing import Any, Dict, Optional


class PostgreSQLService:
    """CLI PostgreSQLService stub."""
    
    def __init__(self, workspace_path: Path | None = None):
        self.workspace_path = workspace_path or Path()
    
    def execute(self) -> bool:
        """Execute command stub."""
        return True
    
    def status(self) -> dict[str, Any]:
        """Get status stub."""
        return {"status": "running", "healthy": True}
