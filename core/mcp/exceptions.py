"""
MCP Exception Classes

Custom exceptions for MCP operations to provide clear error handling
and debugging information.
"""

from typing import Optional


class MCPException(Exception):
    """Base exception for MCP operations"""
    
    def __init__(self, message: str, server_name: Optional[str] = None):
        super().__init__(message)
        self.server_name = server_name


class MCPServerNotFoundError(MCPException):
    """Raised when an MCP server is not found in the catalog"""
    
    def __init__(self, server_name: str):
        super().__init__(f"MCP server '{server_name}' not found in catalog", server_name)


class MCPToolError(MCPException):
    """Raised when MCP tool operation fails"""
    
    def __init__(self, message: str, server_name: Optional[str] = None, tool_name: Optional[str] = None):
        super().__init__(message, server_name)
        self.tool_name = tool_name


class MCPConfigurationError(MCPException):
    """Raised when MCP configuration is invalid"""
    
    def __init__(self, message: str, config_path: Optional[str] = None):
        super().__init__(message)
        self.config_path = config_path


class MCPConnectionError(MCPException):
    """Raised when MCP server connection fails"""
    
    def __init__(self, message: str, server_name: str, url: Optional[str] = None):
        super().__init__(message, server_name)
        self.url = url