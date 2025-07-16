"""
Pooled MCP Tools Wrapper

Provides a transparent wrapper around MCPTools that uses connection pooling
while maintaining the same interface as the original MCPTools class.
"""

import asyncio
import logging
from typing import Any, List, Dict, Optional, AsyncContextManager
from contextlib import asynccontextmanager

from agno.tools.mcp import MCPTools

from .connection_manager import MCPConnectionManager, get_mcp_connection_manager
from .exceptions import MCPConnectionError

logger = logging.getLogger(__name__)


class PooledMCPTools:
    """
    Pooled wrapper for MCPTools that provides the same interface
    but uses connection pooling for better performance and reliability.
    
    This class acts as a drop-in replacement for MCPTools in agent configurations.
    """
    
    def __init__(self, server_name: str, connection_manager: MCPConnectionManager = None):
        """
        Initialize pooled MCP tools.
        
        Args:
            server_name: Name of the MCP server to connect to
            connection_manager: Optional connection manager instance
        """
        self.server_name = server_name
        self._connection_manager = connection_manager
        self._initialized = False
    
    async def _ensure_connection_manager(self) -> MCPConnectionManager:
        """Ensure connection manager is available"""
        if self._connection_manager is None:
            self._connection_manager = await get_mcp_connection_manager()
        return self._connection_manager
    
    @asynccontextmanager
    async def _get_tools(self) -> AsyncContextManager[MCPTools]:
        """Get MCPTools instance from the pool"""
        connection_manager = await self._ensure_connection_manager()
        
        try:
            async with await connection_manager.get_mcp_tools(self.server_name) as tools:
                yield tools
        except Exception as e:
            logger.error(f"Failed to get MCP tools for {self.server_name}: {e}")
            raise MCPConnectionError(f"Failed to get MCP tools: {e}", self.server_name)
    
    # MCPTools interface methods
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        return asyncio.run(self._async_list_tools())
    
    async def _async_list_tools(self) -> List[Dict[str, Any]]:
        """Async implementation of list_tools"""
        async with self._get_tools() as tools:
            # Convert to async if needed
            if hasattr(tools, 'list_tools'):
                result = tools.list_tools()
                if asyncio.iscoroutine(result):
                    return await result
                return result
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool on the MCP server"""
        return asyncio.run(self._async_call_tool(tool_name, arguments))
    
    async def _async_call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Async implementation of call_tool"""
        async with self._get_tools() as tools:
            if hasattr(tools, 'call_tool'):
                result = tools.call_tool(tool_name, arguments or {})
                if asyncio.iscoroutine(result):
                    return await result
                return result
            else:
                raise MCPConnectionError(f"Tool '{tool_name}' not available on {self.server_name}")
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get schema for a specific tool"""
        return asyncio.run(self._async_get_tool_schema(tool_name))
    
    async def _async_get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Async implementation of get_tool_schema"""
        async with self._get_tools() as tools:
            if hasattr(tools, 'get_tool_schema'):
                result = tools.get_tool_schema(tool_name)
                if asyncio.iscoroutine(result):
                    return await result
                return result
            return {}
    
    # Additional methods for compatibility
    
    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to the underlying MCPTools instance.
        
        This ensures compatibility with any additional methods or properties
        that might be added to MCPTools in the future.
        """
        async def _async_proxy(*args, **kwargs):
            async with self._get_tools() as tools:
                attr = getattr(tools, name)
                if callable(attr):
                    result = attr(*args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                return attr
        
        def _sync_proxy(*args, **kwargs):
            return asyncio.run(_async_proxy(*args, **kwargs))
        
        return _sync_proxy
    
    def __str__(self) -> str:
        """String representation"""
        return f"PooledMCPTools(server={self.server_name})"
    
    def __repr__(self) -> str:
        """Debug representation"""
        return f"PooledMCPTools(server_name='{self.server_name}')"


class MCPToolsFactory:
    """
    Factory for creating MCP tools with pooling support.
    
    This factory replaces the direct MCPTools instantiation in the version factory
    to provide transparent connection pooling.
    """
    
    def __init__(self, connection_manager: MCPConnectionManager = None):
        self.connection_manager = connection_manager
    
    def create_mcp_tools(self, server_name: str, server_config: dict = None) -> PooledMCPTools:
        """
        Create pooled MCP tools instance.
        
        Args:
            server_name: Name of the MCP server
            server_config: Server configuration (ignored in pooled version)
            
        Returns:
            PooledMCPTools instance
        """
        return PooledMCPTools(server_name, self.connection_manager)
    
    async def create_direct_mcp_tools(self, server_name: str, server_config: dict = None) -> MCPTools:
        """
        Create direct (non-pooled) MCP tools instance for special cases.
        
        This method creates a direct MCPTools instance without pooling,
        useful for one-off operations or testing.
        
        Args:
            server_name: Name of the MCP server
            server_config: Server configuration dictionary
            
        Returns:
            Direct MCPTools instance
        """
        from .catalog import MCPCatalog
        
        catalog = MCPCatalog()
        server_config_obj = catalog.get_server_config(server_name)
        
        if server_config_obj.is_sse_server:
            return MCPTools(
                url=server_config_obj.url,
                transport="sse",
                env=server_config_obj.env or {}
            )
        elif server_config_obj.is_command_server:
            command_parts = [server_config_obj.command]
            if server_config_obj.args:
                command_parts.extend(server_config_obj.args)
            
            return MCPTools(
                command=" ".join(command_parts),
                transport="stdio",
                env=server_config_obj.env or {}
            )
        else:
            raise MCPConnectionError(f"Unknown server type for {server_name}")


# Global factory instance
_mcp_tools_factory: Optional[MCPToolsFactory] = None


def get_mcp_tools_factory() -> MCPToolsFactory:
    """Get global MCP tools factory instance"""
    global _mcp_tools_factory
    
    if _mcp_tools_factory is None:
        _mcp_tools_factory = MCPToolsFactory()
    
    return _mcp_tools_factory


def create_pooled_mcp_tools(server_name: str) -> PooledMCPTools:
    """
    Convenience function for creating pooled MCP tools.
    
    This is the recommended way to create MCP tools in agent configurations.
    """
    factory = get_mcp_tools_factory()
    return factory.create_mcp_tools(server_name)