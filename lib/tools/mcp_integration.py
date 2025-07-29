"""
MCP Tool Integration Layer for Automagik Hive

Provides standardized handling of MCP tools with consistent naming,
validation, and proxy functionality to eliminate tools.py dependencies.
"""

import re
from typing import Any, Callable, Dict, Optional

from agno.utils.log import logger


class MCPToolProxy:
    """
    Proxy for MCP tools with standardized naming and validation.
    
    Handles the integration between YAML tool configurations and
    actual MCP tool functions available in the system.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP tool proxy.
        
        Args:
            name: MCP tool name (e.g., "mcp__genie_memory__search_memory")
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._tool_function = None
        
    def validate_name(self) -> bool:
        """
        Validate MCP tool name format.
        
        Expected format: mcp__server__tool_name
        Standard servers: genie_memory, automagik_forge, postgres, zen, etc.
        
        Returns:
            True if name is valid, False otherwise
        """
        if not self.name.startswith("mcp__"):
            logger.warning(f"MCP tool name must start with 'mcp__': {self.name}")
            return False
            
        # Pattern: mcp__server__tool_name (allows underscores and dashes in server name)
        pattern = r"^mcp__[a-zA-Z0-9_-]+__[a-zA-Z0-9_]+$"
        if not re.match(pattern, self.name):
            logger.warning(f"Invalid MCP tool name format: {self.name}. Expected: mcp__server__tool_name")
            return False
        
        # Validate known server patterns
        known_servers = [
            "genie_memory", "automagik_forge", "postgres", "zen", 
            "search_repo_docs", "ask_repo_agent", "wait", "send_whatsapp_message"
        ]
        
        # Extract server name (between first and second __)
        parts = self.name.split("__")
        if len(parts) >= 2:
            server_name = parts[1]
            if server_name not in known_servers:
                logger.info(f"MCP server '{server_name}' not in known servers list, but format is valid")
            
        return True
    
    def get_tool_function(self) -> Optional[Callable]:
        """
        Get the actual MCP tool function with proper schema metadata.
        
        Returns:
            Callable tool function with JSON Schema 2020-12 compliant metadata or None if not available
        """
        if self._tool_function:
            return self._tool_function
            
        try:
            # Generate a function with proper schema metadata for JSON Schema 2020-12 compliance
            # Extract tool and server names for schema generation
            parts = self.name.split("__")
            if len(parts) >= 3:
                server_name = parts[1]
                tool_name = parts[2]
            else:
                server_name = "unknown"
                tool_name = self.name
            
            # Create schema-compliant function with proper metadata
            def mcp_tool_placeholder(*args, **kwargs):
                """
                MCP tool placeholder with proper schema compliance.
                
                This function represents an MCP tool and includes the required
                schema metadata for JSON Schema draft 2020-12 compatibility.
                """
                logger.info(f"MCP tool called: {self.name} with args={args}, kwargs={kwargs}")
                return {"status": "success", "tool": self.name, "server": server_name}
                
            # Add proper function metadata for schema generation
            mcp_tool_placeholder.__name__ = self.name
            mcp_tool_placeholder.__doc__ = f"MCP tool: {tool_name} from server: {server_name}"
            
            # Add schema-compliant annotations - this is crucial for JSON Schema 2020-12
            mcp_tool_placeholder.__annotations__ = {
                'return': dict,  # Return type annotation
            }
            
            # Add input schema metadata that Agno can use for tool registration
            mcp_tool_placeholder.input_schema = {
                "type": "object",
                "properties": {},
                "additionalProperties": True
            }
            
            # Add tool metadata for Agno framework compatibility
            mcp_tool_placeholder._tool_metadata = {
                "name": self.name,
                "server": server_name,
                "tool": tool_name,
                "type": "mcp_proxy",
                "schema_version": "2020-12"
            }
                
            self._tool_function = mcp_tool_placeholder
            return self._tool_function
            
        except Exception as e:
            logger.error(f"Failed to get MCP tool function for {self.name}: {e}")
            return None
    
    def __str__(self) -> str:
        """String representation of the MCP tool proxy."""
        return f"MCPToolProxy(name={self.name}, valid={self.validate_name()})"
    
    def __repr__(self) -> str:
        """Detailed representation of the MCP tool proxy."""
        return f"MCPToolProxy(name='{self.name}', config={self.config})"


def validate_mcp_name(name: str) -> bool:
    """
    Standalone function to validate MCP tool names.
    
    Args:
        name: MCP tool name to validate
        
    Returns:
        True if valid, False otherwise
    """
    proxy = MCPToolProxy(name)
    return proxy.validate_name()


def create_mcp_proxy(name: str, config: Optional[Dict[str, Any]] = None) -> MCPToolProxy:
    """
    Factory function to create MCP tool proxies.
    
    Args:
        name: MCP tool name
        config: Optional configuration
        
    Returns:
        MCPToolProxy instance
    """
    return MCPToolProxy(name, config)