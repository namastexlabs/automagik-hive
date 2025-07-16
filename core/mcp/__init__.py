"""
MCP (Model Context Protocol) Integration Package

Provides comprehensive MCP integration with connection pooling, health monitoring,
and transparent interface compatibility for the Genie Agents system.

Key components:
- MCPCatalog: Loads and manages MCP servers from .mcp.json
- MCPConnectionManager: Global connection manager with pooling
- PooledMCPTools: Transparent wrapper maintaining MCPTools interface
- MCPHealthMonitor: Health monitoring and alerting
- CircuitBreaker: Fault tolerance and automatic recovery
"""

from .catalog import MCPCatalog, MCPServerConfig
from .connection_manager import (
    MCPConnectionManager, MCPConnectionPool, PoolConfig,
    get_mcp_connection_manager, shutdown_mcp_connection_manager
)
from .pooled_tools import (
    PooledMCPTools, MCPToolsFactory,
    create_pooled_mcp_tools, get_mcp_tools_factory
)
from .exceptions import (
    MCPException, MCPConnectionError, MCPPoolExhaustedException,
    MCPHealthCheckError, MCPServerNotFoundError, MCPToolError,
    MCPConfigurationError
)

# Legacy imports for backward compatibility
try:
    from .tools import MCPTool, MCPSSETool, MCPCommandTool
    _legacy_tools_available = True
except ImportError:
    _legacy_tools_available = False

__all__ = [
    # Catalog
    "MCPCatalog",
    "MCPServerConfig",
    
    # Connection Management
    "MCPConnectionManager",
    "MCPConnectionPool", 
    "PoolConfig",
    "get_mcp_connection_manager",
    "shutdown_mcp_connection_manager",
    
    # Pooled Tools
    "PooledMCPTools",
    "MCPToolsFactory",
    "create_pooled_mcp_tools",
    "get_mcp_tools_factory",
    
    # Exceptions
    "MCPException",
    "MCPConnectionError",
    "MCPPoolExhaustedException", 
    "MCPHealthCheckError",
    "MCPServerNotFoundError",
    "MCPToolError",
    "MCPConfigurationError",
]

# Add legacy tools if available
if _legacy_tools_available:
    __all__.extend(["MCPTool", "MCPSSETool", "MCPCommandTool"])