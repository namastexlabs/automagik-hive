"""
Shared Toolkit Registry - Auto-discovery of shared tools

Automatically discovers and registers all shared toolkits for
reuse across agents, teams, and workflows.
"""

from .code_editing_toolkit import *
from .code_understanding_toolkit import *
from .file_management_toolkit import *

# Auto-discovery registry for shared tools
SHARED_TOOLS = {
    "code_editing_toolkit": "code_editing_toolkit",
    "code_understanding_toolkit": "code_understanding_toolkit",
    "file_management_toolkit": "file_management_toolkit",
}

__all__ = ["SHARED_TOOLS"]
