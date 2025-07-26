"""
Configuration Management Package

Provides configuration loading, validation, and management for the Automagik Hive system.
Includes support for YAML configuration files with MCP tool parsing.
"""

from .schemas import AgentConfig, MCPToolConfig, TeamConfig
from .yaml_parser import AgentConfigMCP, YAMLConfigParser

__all__ = [
    "AgentConfig",
    "AgentConfigMCP",
    "MCPToolConfig",
    "TeamConfig",
    "YAMLConfigParser",
]
