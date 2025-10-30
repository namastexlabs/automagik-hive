"""
MCP Configuration - Simple Implementation

Basic configuration for MCP integration without overengineering.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """Simple MCP settings from environment variables"""

    # Basic settings - env vars already have MCP_ prefix in their names
    mcp_enabled: bool = Field(default=True)
    mcp_connection_timeout: float = Field(default=30.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
_settings: MCPSettings | None = None


def get_mcp_settings() -> MCPSettings:
    """Get global MCP settings"""
    global _settings
    if _settings is None:
        _settings = MCPSettings()
    return _settings
