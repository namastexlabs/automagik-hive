"""
MCP Configuration Management

Provides comprehensive configuration classes for MCP connection pooling,
health monitoring, and operational settings.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseSettings, Field, validator
from enum import Enum


class MCPTransportType(str, Enum):
    """MCP transport types"""
    SSE = "sse"
    STDIO = "stdio"
    WEBSOCKET = "websocket"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheckConfig:
    """Health check configuration"""
    enabled: bool = True
    interval_seconds: float = 60.0
    timeout_seconds: float = 10.0
    failure_threshold: int = 3
    success_threshold: int = 2
    check_method: str = "list_tools"  # 'list_tools', 'ping', 'custom'


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    timeout: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class PoolConfig:
    """Connection pool configuration with comprehensive settings"""
    min_connections: int = 2
    max_connections: int = 10
    max_idle_time: float = 300.0  # 5 minutes
    connection_timeout: float = 30.0
    acquire_timeout: float = 10.0
    validate_on_acquire: bool = True
    validate_on_return: bool = False
    retry_attempts: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    max_retry_delay: float = 30.0
    
    # Health monitoring
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    
    # Circuit breaker
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    # Cleanup settings
    cleanup_interval: float = 60.0
    max_connection_age: float = 3600.0  # 1 hour
    
    def __post_init__(self):
        """Validate configuration values"""
        if self.min_connections < 0:
            raise ValueError("min_connections must be >= 0")
        if self.max_connections < self.min_connections:
            raise ValueError("max_connections must be >= min_connections")
        if self.connection_timeout <= 0:
            raise ValueError("connection_timeout must be > 0")
        if self.acquire_timeout <= 0:
            raise ValueError("acquire_timeout must be > 0")


@dataclass
class ServerSpecificConfig:
    """Server-specific configuration overrides"""
    server_name: str
    pool_config: Optional[PoolConfig] = None
    priority: int = 0  # Higher priority servers get more resources
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Server-specific overrides
    max_concurrent_requests: Optional[int] = None
    request_timeout: Optional[float] = None
    rate_limit_requests_per_second: Optional[float] = None
    
    # Custom environment variables
    custom_env: Dict[str, str] = field(default_factory=dict)


class MCPSettings(BaseSettings):
    """
    Global MCP settings using Pydantic for validation and environment variable support.
    
    Environment variables should be prefixed with MCP_ (e.g., MCP_LOG_LEVEL=debug)
    """
    
    # Logging configuration
    log_level: LogLevel = Field(default=LogLevel.INFO, env="MCP_LOG_LEVEL")
    enable_debug_logging: bool = Field(default=False, env="MCP_DEBUG")
    log_file_path: Optional[str] = Field(default=None, env="MCP_LOG_FILE")
    
    # Global pool configuration
    global_pool_config: PoolConfig = Field(default_factory=PoolConfig)
    
    # Connection management
    max_total_connections: int = Field(default=100, env="MCP_MAX_TOTAL_CONNECTIONS")
    connection_pool_cleanup_interval: float = Field(default=300.0, env="MCP_CLEANUP_INTERVAL")
    
    # Metrics and monitoring
    enable_metrics: bool = Field(default=True, env="MCP_ENABLE_METRICS")
    metrics_export_interval: float = Field(default=60.0, env="MCP_METRICS_INTERVAL")
    enable_detailed_metrics: bool = Field(default=False, env="MCP_DETAILED_METRICS")
    
    # Error handling
    default_retry_attempts: int = Field(default=3, env="MCP_DEFAULT_RETRIES")
    enable_circuit_breakers: bool = Field(default=True, env="MCP_ENABLE_CIRCUIT_BREAKERS")
    
    # Configuration file paths
    mcp_config_path: str = Field(default=".mcp.json", env="MCP_CONFIG_PATH")
    server_configs_path: Optional[str] = Field(default=None, env="MCP_SERVER_CONFIGS_PATH")
    
    # Development/testing settings
    enable_mock_servers: bool = Field(default=False, env="MCP_ENABLE_MOCKS")
    force_single_connection: bool = Field(default=False, env="MCP_SINGLE_CONNECTION")
    disable_health_checks: bool = Field(default=False, env="MCP_DISABLE_HEALTH_CHECKS")
    
    # Security settings
    enable_request_validation: bool = Field(default=True, env="MCP_VALIDATE_REQUESTS")
    enable_response_validation: bool = Field(default=True, env="MCP_VALIDATE_RESPONSES")
    max_request_size: int = Field(default=10485760, env="MCP_MAX_REQUEST_SIZE")  # 10MB
    max_response_size: int = Field(default=52428800, env="MCP_MAX_RESPONSE_SIZE")  # 50MB
    
    @validator('log_level', pre=True)
    def validate_log_level(cls, v):
        """Validate log level"""
        if isinstance(v, str):
            return LogLevel(v.lower())
        return v
    
    @validator('max_total_connections')
    def validate_max_total_connections(cls, v):
        """Validate max total connections"""
        if v <= 0:
            raise ValueError("max_total_connections must be > 0")
        return v
    
    @validator('metrics_export_interval')
    def validate_metrics_interval(cls, v):
        """Validate metrics export interval"""
        if v <= 0:
            raise ValueError("metrics_export_interval must be > 0")
        return v
    
    class Config:
        env_prefix = "MCP_"
        case_sensitive = False
        use_enum_values = True


@dataclass
class MCPManagerConfig:
    """
    Complete MCP manager configuration combining all settings.
    
    This class provides a unified configuration interface for the MCP connection manager.
    """
    
    # Global settings
    settings: MCPSettings = field(default_factory=MCPSettings)
    
    # Server-specific configurations
    server_configs: Dict[str, ServerSpecificConfig] = field(default_factory=dict)
    
    # Global pool configuration override
    global_pool_config: Optional[PoolConfig] = None
    
    def get_pool_config_for_server(self, server_name: str) -> PoolConfig:
        """
        Get pool configuration for a specific server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            PoolConfig for the server (server-specific or global)
        """
        # Check for server-specific config
        if server_name in self.server_configs:
            server_config = self.server_configs[server_name]
            if server_config.pool_config:
                return server_config.pool_config
        
        # Return global config override or default
        return self.global_pool_config or self.settings.global_pool_config
    
    def add_server_config(self, server_config: ServerSpecificConfig):
        """Add server-specific configuration"""
        self.server_configs[server_config.server_name] = server_config
    
    def remove_server_config(self, server_name: str):
        """Remove server-specific configuration"""
        if server_name in self.server_configs:
            del self.server_configs[server_name]
    
    def get_server_config(self, server_name: str) -> Optional[ServerSpecificConfig]:
        """Get server-specific configuration"""
        return self.server_configs.get(server_name)
    
    def list_configured_servers(self) -> List[str]:
        """List all servers with specific configurations"""
        return list(self.server_configs.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'settings': self.settings.dict(),
            'server_configs': {
                name: {
                    'server_name': config.server_name,
                    'pool_config': config.pool_config.__dict__ if config.pool_config else None,
                    'priority': config.priority,
                    'tags': config.tags,
                    'metadata': config.metadata,
                    'max_concurrent_requests': config.max_concurrent_requests,
                    'request_timeout': config.request_timeout,
                    'rate_limit_requests_per_second': config.rate_limit_requests_per_second,
                    'custom_env': config.custom_env
                }
                for name, config in self.server_configs.items()
            },
            'global_pool_config': self.global_pool_config.__dict__ if self.global_pool_config else None
        }


def load_mcp_config() -> MCPManagerConfig:
    """
    Load MCP configuration from environment variables and defaults.
    
    Returns:
        MCPManagerConfig instance with all settings loaded
    """
    settings = MCPSettings()
    return MCPManagerConfig(settings=settings)


def create_pool_config(**kwargs) -> PoolConfig:
    """
    Create a pool configuration with custom settings.
    
    Args:
        **kwargs: Pool configuration parameters
        
    Returns:
        PoolConfig instance
    """
    return PoolConfig(**kwargs)


def create_server_config(
    server_name: str,
    pool_config: Optional[PoolConfig] = None,
    **kwargs
) -> ServerSpecificConfig:
    """
    Create server-specific configuration.
    
    Args:
        server_name: Name of the server
        pool_config: Optional pool configuration
        **kwargs: Additional server configuration parameters
        
    Returns:
        ServerSpecificConfig instance
    """
    return ServerSpecificConfig(
        server_name=server_name,
        pool_config=pool_config,
        **kwargs
    )