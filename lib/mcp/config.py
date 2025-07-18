"""
MCP Configuration - Simple Implementation

Basic configuration for MCP integration without overengineering.
"""

import os
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class MCPSettings(BaseSettings):
    """Simple MCP settings from environment variables"""
    
    # Basic settings
    mcp_enabled: bool = Field(True, env="MCP_ENABLED")
    mcp_connection_timeout: float = Field(30.0, env="MCP_CONNECTION_TIMEOUT")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
_settings: Optional[MCPSettings] = None


def get_mcp_settings() -> MCPSettings:
    """Get global MCP settings"""
    global _settings
    if _settings is None:
        _settings = MCPSettings()
    return _settings