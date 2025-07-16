"""
MCP (Model Context Protocol) Integration Package

Simple MCP integration with connection pooling for the Genie Agents system.
No backward compatibility - clean, modern implementation only.
"""

from .catalog import MCPCatalog, MCPServerConfig
from .connection_manager import (
    MCPConnectionManager, MCPConnectionPool, 
    get_mcp_connection_manager, shutdown_mcp_connection_manager
)
from .pooled_tools import (
    PooledMCPTools, MCPToolsFactory,
    create_pooled_mcp_tools, get_mcp_tools_factory
)
from .exceptions import (
    MCPException, MCPConnectionError, MCPPoolExhaustedException,
    MCPHealthCheckError, MCPServerNotFoundError, MCPToolError,
    MCPConfigurationError, CircuitBreakerOpenError, MCPTimeoutError,
    MCPValidationError
)
from .config import (
    MCPSettings, PoolConfig, get_mcp_settings
)
from .metrics import (
    MCPMetricsCollector, get_metrics_collector, PoolStatus
)

__all__ = [
    # Catalog
    "MCPCatalog",
    "MCPServerConfig",
    
    # Connection Management
    "MCPConnectionManager",
    "MCPConnectionPool", 
    "get_mcp_connection_manager",
    "shutdown_mcp_connection_manager",
    
    # Pooled Tools
    "PooledMCPTools",
    "MCPToolsFactory",
    "create_pooled_mcp_tools",
    "get_mcp_tools_factory",
    
    # Configuration
    "MCPSettings",
    "PoolConfig",
    "get_mcp_settings",
    
    # Metrics
    "MCPMetricsCollector",
    "get_metrics_collector",
    "PoolStatus",
    
    # Exceptions
    "MCPException",
    "MCPConnectionError",
    "MCPPoolExhaustedException", 
    "MCPHealthCheckError",
    "MCPServerNotFoundError",
    "MCPToolError",
    "MCPConfigurationError",
    "CircuitBreakerOpenError",
    "MCPTimeoutError",
    "MCPValidationError",
]