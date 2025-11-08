"""Automagik Hive V2 - AI-powered multi-agent framework."""

from importlib.metadata import version

try:
    __version__ = version("automagik-hive")
except Exception:
    # Fallback for development environments where package isn't installed
    __version__ = "dev"

__author__ = "Automagik Team"
__license__ = "MIT"

# Convenience exports for YAML-driven component generation
from hive.scaffolder.generator import (
    generate_agent_from_yaml,
    generate_team_from_yaml,
    generate_workflow_from_yaml,
)

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "generate_agent_from_yaml",
    "generate_team_from_yaml",
    "generate_workflow_from_yaml",
]
