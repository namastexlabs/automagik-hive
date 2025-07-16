"""
MCP Tool Wrapper Classes

Provides wrapper classes for different types of MCP tools, enabling
seamless integration with the Agno framework.
"""

import asyncio
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from agno.tools.mcp import MCPTools
from .exceptions import MCPToolError, MCPConnectionError


@dataclass
class MCPToolResult:
    """Result from an MCP tool execution"""
    
    success: bool
    data: Any
    error: Optional[str] = None
    server_name: Optional[str] = None
    tool_name: Optional[str] = None


class MCPTool(ABC):
    """
    Base class for MCP tool wrappers.
    
    This provides a common interface for all MCP tools regardless
    of their underlying implementation (SSE, command, etc.).
    """
    
    def __init__(self, server_name: str, server_config: 'MCPServerConfig'):
        """
        Initialize MCP tool wrapper.
        
        Args:
            server_name: Name of the MCP server
            server_config: Configuration for the MCP server
        """
        self.server_name = server_name
        self.server_config = server_config
        self.is_connected = False
        self._agno_tools: Optional[MCPTools] = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the MCP server"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server"""
        pass
    
    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> MCPToolResult:
        """Execute an MCP tool"""
        pass
    
    def get_agno_tools(self) -> MCPTools:
        """
        Get the Agno MCPTools instance for this server.
        
        Returns:
            MCPTools instance for use with Agno agents
        """
        if self._agno_tools is None:
            raise MCPToolError(
                f"MCP tools not initialized for server '{self.server_name}'. Call connect() first.",
                self.server_name
            )
        return self._agno_tools


class MCPSSETool(MCPTool):
    """
    MCP tool wrapper for SSE (Server-Sent Events) servers.
    
    Handles MCP servers that communicate via SSE protocol.
    """
    
    def __init__(self, server_name: str, server_config: 'MCPServerConfig'):
        super().__init__(server_name, server_config)
        
        if not server_config.url:
            raise MCPToolError(
                f"SSE server '{server_name}' requires a URL",
                server_name
            )
        
        self.url = server_config.url
    
    async def connect(self) -> None:
        """Connect to the SSE MCP server"""
        try:
            # For SSE servers, we don't need to maintain a persistent connection
            # but we can validate the URL is accessible
            self.is_connected = True
            
            # Create Agno MCPTools instance for SSE server
            # Note: SSE servers typically don't use command/args pattern
            self._agno_tools = MCPTools(
                server_name=self.server_name,
                url=self.url
            )
            
        except Exception as e:
            raise MCPConnectionError(
                f"Failed to connect to SSE server '{self.server_name}': {e}",
                self.server_name,
                self.url
            )
    
    async def disconnect(self) -> None:
        """Disconnect from the SSE MCP server"""
        if self._agno_tools:
            # Close the MCP tools connection
            await self._agno_tools.close()
            self._agno_tools = None
        
        self.is_connected = False
    
    async def execute(self, tool_name: str, **kwargs) -> MCPToolResult:
        """Execute an MCP tool on the SSE server"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Execute the tool using Agno MCPTools
            result = await self._agno_tools.execute_tool(tool_name, **kwargs)
            
            return MCPToolResult(
                success=True,
                data=result,
                server_name=self.server_name,
                tool_name=tool_name
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e),
                server_name=self.server_name,
                tool_name=tool_name
            )


class MCPCommandTool(MCPTool):
    """
    MCP tool wrapper for command-based servers.
    
    Handles MCP servers that are launched via command line.
    """
    
    def __init__(self, server_name: str, server_config: 'MCPServerConfig'):
        super().__init__(server_name, server_config)
        
        if not server_config.command:
            raise MCPToolError(
                f"Command server '{server_name}' requires a command",
                server_name
            )
        
        self.command = server_config.command
        self.args = server_config.args or []
        self.env = server_config.env or {}
    
    async def connect(self) -> None:
        """Connect to the command-based MCP server"""
        try:
            # Create Agno MCPTools instance for command server
            self._agno_tools = MCPTools(
                command=self.command,
                args=self.args,
                env=self.env
            )
            
            # Initialize the MCP tools connection
            await self._agno_tools.initialize()
            
            self.is_connected = True
            
        except Exception as e:
            raise MCPConnectionError(
                f"Failed to connect to command server '{self.server_name}': {e}",
                self.server_name
            )
    
    async def disconnect(self) -> None:
        """Disconnect from the command-based MCP server"""
        if self._agno_tools:
            await self._agno_tools.close()
            self._agno_tools = None
        
        self.is_connected = False
    
    async def execute(self, tool_name: str, **kwargs) -> MCPToolResult:
        """Execute an MCP tool on the command server"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Execute the tool using Agno MCPTools
            result = await self._agno_tools.execute_tool(tool_name, **kwargs)
            
            return MCPToolResult(
                success=True,
                data=result,
                server_name=self.server_name,
                tool_name=tool_name
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e),
                server_name=self.server_name,
                tool_name=tool_name
            )


class MCPToolFactory:
    """
    Factory for creating MCP tool instances based on server configuration.
    """
    
    @staticmethod
    def create_tool(server_name: str, server_config: 'MCPServerConfig') -> MCPTool:
        """
        Create an appropriate MCP tool instance based on server configuration.
        
        Args:
            server_name: Name of the MCP server
            server_config: Configuration for the MCP server
            
        Returns:
            MCPTool: Appropriate tool instance
            
        Raises:
            MCPToolError: If server type is unknown
        """
        if server_config.is_sse_server:
            return MCPSSETool(server_name, server_config)
        elif server_config.is_command_server:
            return MCPCommandTool(server_name, server_config)
        else:
            raise MCPToolError(
                f"Unknown server type '{server_config.type}' for server '{server_name}'",
                server_name
            )


# Context manager for automatic connection management
class MCPToolContext:
    """
    Context manager for MCP tools that handles connection lifecycle.
    """
    
    def __init__(self, mcp_tool: MCPTool):
        self.mcp_tool = mcp_tool
    
    async def __aenter__(self) -> MCPTool:
        await self.mcp_tool.connect()
        return self.mcp_tool
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mcp_tool.disconnect()