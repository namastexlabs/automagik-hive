"""
ShellTools Wrapper for Automagik Hive

Provides shell command execution capabilities using Agno's native ShellTools.
This is a wrapper that makes ShellTools available through our tool registry system.
"""

from agno.tools.shell import ShellTools


class ShellToolkit:
    """Wrapper for Agno's native ShellTools to integrate with our tool registry."""

    def __init__(self):
        """Initialize the ShellTools wrapper."""
        self._shell_tools = ShellTools()

    def get_tools(self):
        """Return the underlying Agno ShellTools instance."""
        return self._shell_tools


# Export the toolkit for auto-discovery
__all__ = ["ShellToolkit"]
