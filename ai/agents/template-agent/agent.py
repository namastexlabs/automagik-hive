"""
Template Agent - Foundational agent template for specialized agent development
"""

from pathlib import Path
from agno.agent import Agent
from lib.config.yaml_parser import YAMLConfigParser


def get_template_agent() -> Agent:
    """
    Create and return a template agent instance.

    This agent serves as a foundational template for creating
    specialized domain-specific agents with standardized patterns.

    Returns:
        Agent: Configured template agent instance
    """
    config_path = Path(__file__).parent / "config.yaml"
    parser = YAMLConfigParser()
    agent_config_mcp = parser.parse_agent_config(str(config_path))

    # Create agent with MCP tools support
    return Agent(
        **agent_config_mcp.config.model_dump(),
        mcp_servers=[tool.server_name for tool in agent_config_mcp.mcp_tools]
    )


# Export the agent creation function
__all__ = ["get_template_agent"]
