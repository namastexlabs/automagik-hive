"""Web Search Agent - General web research specialist."""

import yaml
from pathlib import Path
from typing import Optional

from agno.agent import Agent
from agno.models import ModelConfig
from agno.storage import PostgresStorage
from agno.tools.duckduckgo import DuckDuckGoTools


def get_web_search_agent(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    **kwargs
) -> Agent:
    """
    Factory function to create a web search agent.
    
    Args:
        model_id: Optional model override
        user_id: User identifier for personalization
        session_id: Session identifier for context
        debug_mode: Enable debug logging
        **kwargs: Additional agent parameters
    
    Returns:
        Configured web search agent instance
    """
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Extract configurations
    agent_config = config["agent"]
    model_config = config["model"]
    storage_config = config["storage"]
    memory_config = config["memory"]
    
    # Override model if specified
    if model_id:
        model_config["id"] = model_id
    
    # Create tools
    tools = []
    for tool_config in config.get("tools", []):
        if tool_config["name"] == "DuckDuckGoTools":
            tools.append(DuckDuckGoTools(
                cache_results=tool_config.get("cache_results", True)
            ))
    
    # Create agent instance
    return Agent(
        name=agent_config["name"],
        agent_id=agent_config["agent_id"],
        instructions=config["instructions"],
        model=ModelConfig(
            provider=model_config["provider"],
            id=model_config["id"],
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 4000)
        ),
        storage=PostgresStorage(
            table_name=storage_config["table_name"],
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        ),
        memory=memory_config,
        tools=tools,
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        markdown=config.get("display", {}).get("markdown", True),
        show_tool_calls=config.get("display", {}).get("show_tool_calls", True),
        add_datetime_to_instructions=config.get("display", {}).get("add_datetime_to_instructions", True),
        **kwargs
    )