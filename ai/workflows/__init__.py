"""AI Workflows Package - Automatic discovery from filesystem"""

# Registry auto-discovers workflows from ai/workflows/ folders
# No manual imports needed - just use the registry functions

from .registry import (
    get_workflow,
    get_workflow_registry,
    is_workflow_registered,
    list_available_workflows,
)

__all__ = [
    # Registry and factory functions
    "get_workflow_registry",
    "get_workflow",
    "list_available_workflows",
    "is_workflow_registered",
]
