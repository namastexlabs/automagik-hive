"""
MCP Exceptions - Simple Implementation

Basic exception classes for MCP integration.
"""


class MCPException(Exception):
    """Base exception for MCP operations"""


class MCPConnectionError(MCPException):
    """Exception raised when MCP connection fails"""

    def __init__(self, message: str, server_name: str | None = None):
        super().__init__(message)
        self.server_name = server_name
