"""
MCP Configuration - KISS Implementation

Simple configuration for MCP connection pooling with minimal complexity.
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass
from pydantic import Field
from pydantic_settings import BaseSettings


@dataclass
class PoolConfig:
    """Simple pool configuration"""
    
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: float = 5.0
    max_idle_time: float = 300.0
    health_check_interval: float = 30.0
    failure_threshold: int = 5
    recovery_timeout: float = 30.0


class MCPSettings(BaseSettings):
    """Simple MCP settings from environment variables"""
    
    # Basic settings
    mcp_enabled: bool = Field(True, env="MCP_ENABLED")
    mcp_pool_min_connections: int = Field(2, env="MCP_POOL_MIN_CONNECTIONS")
    mcp_pool_max_connections: int = Field(10, env="MCP_POOL_MAX_CONNECTIONS")
    mcp_connection_timeout: float = Field(5.0, env="MCP_CONNECTION_TIMEOUT")
    mcp_max_idle_time: float = Field(300.0, env="MCP_MAX_IDLE_TIME")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables
    
    def get_pool_config(self) -> PoolConfig:
        """Get pool configuration from settings"""
        return PoolConfig(
            min_connections=self.mcp_pool_min_connections,
            max_connections=self.mcp_pool_max_connections,
            connection_timeout=self.mcp_connection_timeout,
            max_idle_time=self.mcp_max_idle_time
        )


# Global settings instance
_settings: Optional[MCPSettings] = None


def get_mcp_settings() -> MCPSettings:
    """Get global MCP settings"""
    global _settings
    if _settings is None:
        _settings = MCPSettings()
    return _settings