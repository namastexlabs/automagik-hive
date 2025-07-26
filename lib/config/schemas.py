"""
Configuration Schema Definitions

Pydantic models for validating and managing configuration data.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class MCPToolConfig(BaseModel):
    """Configuration for a single MCP tool reference"""

    server_name: str = Field(..., description="Name of the MCP server")
    tool_name: str | None = Field(
        None, description="Specific tool name (if different from server)"
    )
    parameters: dict[str, Any] | None = Field(
        default_factory=dict, description="Default parameters for the tool"
    )
    enabled: bool = Field(True, description="Whether the tool is enabled")

    @field_validator("server_name")
    @classmethod
    def validate_server_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("server_name must be a non-empty string")
        return v


class AgentInfo(BaseModel):
    """Agent metadata section"""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    version: int = Field(1, description="Agent version number")
    name: str = Field(..., description="Display name for the agent")
    role: str | None = Field(None, description="Agent role description")
    description: str | None = Field(None, description="Agent description")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError("version must be a positive integer")
        return v


class AgentConfig(BaseModel):
    """Standard agent configuration schema"""

    # Agent info section (nested structure from YAML)
    agent: AgentInfo = Field(..., description="Agent information section")

    # Model configuration
    model: dict[str, Any] = Field(..., description="Model configuration")

    # Instructions
    instructions: str | list[str] = Field(..., description="Agent instructions")

    # Tools (mixed regular and MCP tools)
    tools: list[str] = Field(
        default_factory=list, description="List of tools including MCP tools"
    )

    # Knowledge filtering
    knowledge_filter: dict[str, Any] | None = Field(
        None, description="Knowledge base filtering"
    )

    # Storage configuration
    storage: dict[str, Any] | None = Field(None, description="Storage configuration")

    # Memory configuration
    memory: dict[str, Any] | None = Field(None, description="Memory configuration")

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, v):
        if not isinstance(v, list):
            raise ValueError("tools must be a list")
        return v


class TeamConfig(BaseModel):
    """Team configuration schema"""

    team_id: str = Field(..., description="Unique identifier for the team")
    name: str = Field(..., description="Display name for the team")
    mode: str = Field("route", description="Team mode (route, etc.)")
    description: str | None = Field(None, description="Team description")

    # Model configuration
    model: dict[str, Any] = Field(..., description="Model configuration")

    # Instructions
    instructions: str | list[str] = Field(..., description="Team instructions")

    # Storage configuration
    storage: dict[str, Any] | None = Field(None, description="Storage configuration")

    # Memory configuration
    memory: dict[str, Any] | None = Field(None, description="Memory configuration")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        allowed_modes = ["route", "consensus", "sequential"]
        if v not in allowed_modes:
            raise ValueError(f"mode must be one of: {allowed_modes}")
        return v


class AgentConfigMCP(BaseModel):
    """Extended agent configuration with parsed MCP tools"""

    # Standard agent config
    config: AgentConfig = Field(..., description="Standard agent configuration")

    # Parsed tools
    regular_tools: list[str] = Field(
        default_factory=list, description="Regular (non-MCP) tools"
    )
    mcp_tools: list[MCPToolConfig] = Field(
        default_factory=list, description="Parsed MCP tools"
    )

    @property
    def all_tools(self) -> list[str]:
        """Get all tools (regular + MCP) as string list"""
        return self.regular_tools + [
            f"mcp.{tool.server_name}" for tool in self.mcp_tools
        ]

    @property
    def mcp_server_names(self) -> list[str]:
        """Get list of MCP server names referenced"""
        return [tool.server_name for tool in self.mcp_tools]

    def has_mcp_tools(self) -> bool:
        """Check if this agent has any MCP tools configured"""
        return len(self.mcp_tools) > 0
