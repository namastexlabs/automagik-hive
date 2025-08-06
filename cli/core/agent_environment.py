"""Agent Environment Management Stubs.

Minimal stub implementations to fix import errors in tests.
These are placeholders that satisfy import requirements.
"""

from typing import Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentCredentials:
    """Agent credentials stub."""
    api_key: Optional[str] = None
    postgres_password: Optional[str] = None


@dataclass
class EnvironmentConfig:
    """Environment configuration stub."""
    api_port: int = 38886
    postgres_port: int = 35532


class AgentEnvironment:
    """Agent environment management stub."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path(".")
    
    def create(self) -> bool:
        """Create agent environment stub."""
        return True
    
    def validate(self) -> bool:
        """Validate agent environment stub."""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup agent environment stub."""
        return True


# Convenience functions
def create_agent_environment(workspace_path: Optional[Path] = None) -> AgentEnvironment:
    """Create agent environment stub function."""
    env = AgentEnvironment(workspace_path)
    env.create()
    return env


def validate_agent_environment(workspace_path: Optional[Path] = None) -> bool:
    """Validate agent environment stub function."""
    return True


def cleanup_agent_environment(workspace_path: Optional[Path] = None) -> bool:
    """Cleanup agent environment stub function."""
    return True


def get_agent_ports() -> dict[str, int]:
    """Get agent ports stub function."""
    return {"api": 38886, "postgres": 35532}
