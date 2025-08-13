"""Airbnb Agent - Accommodation search specialist."""

import yaml
from pathlib import Path
from typing import Optional, Any

from agno.agent import Agent
from agno.models import ModelConfig
from agno.storage import PostgresStorage
from agno.tools.mcp import MCPTools


def get_airbnb_agent(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    **kwargs
) -> Agent:
    """
    Factory function to create an Airbnb search agent.
    
    Args:
        model_id: Optional model override
        user_id: User identifier for personalization
        session_id: Session identifier for context
        debug_mode: Enable debug logging
        **kwargs: Additional agent parameters
    
    Returns:
        Configured Airbnb agent instance
    """
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Extract agent configuration
    agent_config = config["agent"]
    model_config = config["model"]
    storage_config = config["storage"]
    memory_config = config["memory"]
    
    # Override model if specified
    if model_id:
        model_config["id"] = model_id
    
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
        memory={
            "num_history_runs": memory_config.get("num_history_runs", 10),
            "enable_user_memories": memory_config.get("enable_user_memories", True),
            "enable_agentic_memory": memory_config.get("enable_agentic_memory", True),
            "add_history_to_messages": memory_config.get("add_history_to_messages", True),
            "enable_session_summaries": memory_config.get("enable_session_summaries", True)
        },
        mcp_servers=config.get("mcp_servers", ["airbnb:*"]),
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        markdown=config.get("display", {}).get("markdown", True),
        show_tool_calls=config.get("display", {}).get("show_tool_calls", True),
        add_datetime_to_instructions=config.get("display", {}).get("add_datetime_to_instructions", True),
        **kwargs
    )