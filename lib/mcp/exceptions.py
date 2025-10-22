"""
MCP Exceptions - Simple Implementation

Basic exception classes for MCP integration.
"""


class MCPError(Exception):
    """Base exception for MCP operations"""


# Alias for backward compatibility
MCPException = MCPError


class MCPConnectionError(MCPError):
    """Exception raised when MCP connection fails"""

    def __init__(self, message: str, server_name: str | None = None):
        super().__init__(message)
        self.server_name = server_name
