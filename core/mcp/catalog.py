"""
MCP Catalog System

Loads and manages MCP servers from the standard .mcp.json configuration file.
Provides simple access to MCP tool configurations and server information.
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from .exceptions import MCPConfigurationError, MCPServerNotFoundError


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server"""
    
    name: str
    type: str  # "sse", "command", etc.
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        # Ensure args is a list
        if self.args is None:
            self.args = []
        
        # Ensure env is a dict
        if self.env is None:
            self.env = {}
    
    @property
    def is_sse_server(self) -> bool:
        """Check if this is an SSE server"""
        return self.type == "sse"
    
    @property
    def is_command_server(self) -> bool:
        """Check if this is a command-based server"""
        return self.type == "command" or (self.command is not None)


class MCPCatalog:
    """
    MCP Catalog manages the available MCP servers and tools.
    
    Loads configuration from the standard .mcp.json file and provides
    access to server configurations for tool instantiation.
    """
    
    def __init__(self, mcp_json_path: str = ".mcp.json"):
        """
        Initialize MCP catalog from configuration file.
        
        Args:
            mcp_json_path: Path to the .mcp.json configuration file
            
        Raises:
            MCPConfigurationError: If the configuration file is invalid
        """
        self.config_path = Path(mcp_json_path)
        self.catalog: Dict[str, Any] = {}
        self.available_servers: Dict[str, MCPServerConfig] = {}
        
        self._load_catalog()
        self._discover_servers()
    
    def _load_catalog(self) -> None:
        """Load the MCP catalog from .mcp.json file"""
        try:
            if not self.config_path.exists():
                raise MCPConfigurationError(
                    f"MCP configuration file not found: {self.config_path}",
                    str(self.config_path)
                )
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.catalog = json.load(f)
                
            if not isinstance(self.catalog, dict):
                raise MCPConfigurationError(
                    "Invalid MCP configuration: root must be a JSON object",
                    str(self.config_path)
                )
                
        except json.JSONDecodeError as e:
            raise MCPConfigurationError(
                f"Invalid JSON in MCP configuration: {e}",
                str(self.config_path)
            )
        except Exception as e:
            raise MCPConfigurationError(
                f"Error loading MCP configuration: {e}",
                str(self.config_path)
            )
    
    def _discover_servers(self) -> None:
        """Discover available MCP servers from the catalog"""
        mcp_servers = self.catalog.get("mcpServers", {})
        
        if not isinstance(mcp_servers, dict):
            raise MCPConfigurationError(
                "Invalid MCP configuration: 'mcpServers' must be an object",
                str(self.config_path)
            )
        
        for server_name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                print(f"Warning: Invalid server config for '{server_name}', skipping")
                continue
            
            try:
                # Determine server type
                server_type = server_config.get("type", "command")
                
                # Handle command-based servers (default)
                if server_type == "command" or "command" in server_config:
                    config = MCPServerConfig(
                        name=server_name,
                        type="command",
                        command=server_config.get("command"),
                        args=server_config.get("args", []),
                        env=server_config.get("env", {})
                    )
                
                # Handle SSE servers
                elif server_type == "sse":
                    config = MCPServerConfig(
                        name=server_name,
                        type="sse",
                        url=server_config.get("url"),
                        env=server_config.get("env", {})
                    )
                
                else:
                    print(f"Warning: Unknown server type '{server_type}' for '{server_name}', skipping")
                    continue
                
                self.available_servers[server_name] = config
                
            except Exception as e:
                print(f"Warning: Error processing server '{server_name}': {e}")
                continue
    
    def get_server_config(self, server_name: str) -> MCPServerConfig:
        """
        Get configuration for a specific MCP server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            MCPServerConfig: Server configuration
            
        Raises:
            MCPServerNotFoundError: If server is not found
        """
        if server_name not in self.available_servers:
            raise MCPServerNotFoundError(server_name)
        
        return self.available_servers[server_name]
    
    def list_servers(self) -> List[str]:
        """
        List all available MCP server names.
        
        Returns:
            List of server names
        """
        return list(self.available_servers.keys())
    
    def has_server(self, server_name: str) -> bool:
        """
        Check if a server exists in the catalog.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            True if server exists, False otherwise
        """
        return server_name in self.available_servers
    
    def get_server_info(self, server_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            Dictionary with server information
        """
        config = self.get_server_config(server_name)
        
        return {
            "name": config.name,
            "type": config.type,
            "command": config.command,
            "args": config.args,
            "env": config.env,
            "url": config.url,
            "is_sse_server": config.is_sse_server,
            "is_command_server": config.is_command_server
        }
    
    def reload_catalog(self) -> None:
        """
        Reload the MCP catalog from the configuration file.
        
        This is useful for hot-reloading configuration changes.
        """
        self.catalog = {}
        self.available_servers = {}
        self._load_catalog()
        self._discover_servers()
    
    def __str__(self) -> str:
        """String representation of the catalog"""
        return f"MCPCatalog({len(self.available_servers)} servers: {', '.join(self.list_servers())})"
    
    def __repr__(self) -> str:
        """Debug representation of the catalog"""
        return f"MCPCatalog(config_path='{self.config_path}', servers={list(self.available_servers.keys())})"