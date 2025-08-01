"""
YAML Configuration Parser with MCP Support

Parses agent and team YAML configuration files with support for MCP tools
in the mcp.toolname format.
"""

from pathlib import Path
from typing import Any

import yaml

from lib.logging import logger
from lib.mcp.catalog import MCPCatalog

from .schemas import AgentConfig, AgentConfigMCP, MCPToolConfig, TeamConfig


class YAMLConfigParser:
    """
    YAML Configuration Parser with MCP tool support.

    Parses agent and team YAML configuration files and separates
    regular tools from MCP tools, validating MCP tool references
    against the MCP catalog.
    """

    def __init__(self, mcp_catalog: MCPCatalog | None = None):
        """
        Initialize YAML parser with MCP catalog.

        Args:
            mcp_catalog: MCP catalog for validating MCP tool references
        """
        self.mcp_catalog = mcp_catalog or MCPCatalog()

    def parse_agent_config(self, config_path: str) -> AgentConfigMCP:
        """
        Parse agent configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            AgentConfigMCP: Parsed configuration with separated tools

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If configuration file doesn't exist
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_path}: {e}")

        if not isinstance(raw_config, dict):
            raise ValueError(
                f"Configuration file must contain a YAML object: {config_path}"
            )

        # Extract tools list
        tools_list = raw_config.get("tools", [])
        if not isinstance(tools_list, list):
            raise ValueError(f"'tools' must be a list in {config_path}")

        # Parse and separate tools
        regular_tools, mcp_tools = self._parse_tools(tools_list)

        # Validate MCP tools
        validated_mcp_tools = self._validate_mcp_tools(mcp_tools)

        # Create standard agent config
        agent_config = AgentConfig(**raw_config)

        # Create extended config with parsed tools
        return AgentConfigMCP(
            config=agent_config,
            regular_tools=regular_tools,
            mcp_tools=validated_mcp_tools,
        )

    def parse_team_config(self, config_path: str) -> TeamConfig:
        """
        Parse team configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            TeamConfig: Parsed team configuration

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If configuration file doesn't exist
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_path}: {e}")

        if not isinstance(raw_config, dict):
            raise ValueError(
                f"Configuration file must contain a YAML object: {config_path}"
            )

        return TeamConfig(**raw_config)

    def _parse_tools(self, tools_list: list[str]) -> tuple[list[str], list[str]]:
        """
        Separate regular tools from MCP tools.

        Args:
            tools_list: List of tool names from YAML

        Returns:
            Tuple of (regular_tools, mcp_tool_names)
        """
        regular_tools = []
        mcp_tool_names = []

        for tool in tools_list:
            if not isinstance(tool, str):
                logger.warning("Invalid tool entry, must be string", tool=tool)
                continue

            tool = tool.strip()
            if tool.startswith("mcp."):
                # MCP tool - extract server name
                server_name = tool[4:]  # Remove 'mcp.' prefix
                if server_name:
                    mcp_tool_names.append(server_name)
                else:
                    logger.warning("Empty MCP tool name", tool=tool)
            else:
                # Regular tool
                regular_tools.append(tool)

        return regular_tools, mcp_tool_names

    def _validate_mcp_tools(self, mcp_tool_names: list[str]) -> list[MCPToolConfig]:
        """
        Validate MCP tool references against the catalog.

        Args:
            mcp_tool_names: List of MCP server names

        Returns:
            List of validated MCPToolConfig objects
        """
        validated_tools = []

        for server_name in mcp_tool_names:
            try:
                # Check if server exists in catalog
                if self.mcp_catalog.has_server(server_name):
                    tool_config = MCPToolConfig(server_name=server_name, enabled=True)
                    validated_tools.append(tool_config)
                else:
                    logger.warning(
                        "MCP server not found in catalog", server_name=server_name
                    )
                    # Still add it but mark as disabled
                    tool_config = MCPToolConfig(server_name=server_name, enabled=False)
                    validated_tools.append(tool_config)

            except Exception as e:
                logger.warning(
                    "Error validating MCP tool", server_name=server_name, error=str(e)
                )
                continue

        return validated_tools

    def update_agent_config(self, config_path: str, updates: dict[str, Any]) -> None:
        """
        Update agent configuration file with new values.

        Args:
            config_path: Path to the YAML configuration file
            updates: Dictionary of updates to apply
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Apply updates
            config.update(updates)

            # Write back to file
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

        except Exception as e:
            raise ValueError(f"Error updating configuration file {config_path}: {e}")

    def get_mcp_tools_summary(self, config: AgentConfigMCP) -> dict[str, Any]:
        """
        Get a summary of MCP tools for an agent configuration.

        Args:
            config: Agent configuration with MCP tools

        Returns:
            Dictionary with MCP tools summary
        """
        return {
            "total_tools": len(config.all_tools),
            "regular_tools": len(config.regular_tools),
            "mcp_tools": len(config.mcp_tools),
            "mcp_servers": config.mcp_server_names,
            "enabled_mcp_tools": [
                tool.server_name for tool in config.mcp_tools if tool.enabled
            ],
            "disabled_mcp_tools": [
                tool.server_name for tool in config.mcp_tools if not tool.enabled
            ],
        }

    def validate_config_file(self, config_path: str) -> dict[str, Any]:
        """
        Validate a configuration file and return validation results.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Dictionary with validation results
        """
        try:
            config = self.parse_agent_config(config_path)

            return {
                "valid": True,
                "config_path": config_path,
                "agent_id": config.config.agent_id,
                "version": config.config.version,
                "tools_summary": self.get_mcp_tools_summary(config),
                "errors": [],
                "warnings": [],
            }

        except Exception as e:
            return {
                "valid": False,
                "config_path": config_path,
                "agent_id": None,
                "version": None,
                "tools_summary": None,
                "errors": [str(e)],
                "warnings": [],
            }

    def reload_mcp_catalog(self) -> None:
        """Reload the MCP catalog from configuration file"""
        self.mcp_catalog.reload_catalog()

    def __str__(self) -> str:
        """String representation of the parser"""
        return f"YAMLConfigParser(mcp_servers={len(self.mcp_catalog.list_servers())})"
