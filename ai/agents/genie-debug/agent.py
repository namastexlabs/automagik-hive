"""
🐛 Genie Debug - The Ruthless Debugging Meeseeks

Enhanced Agno agent with persistent memory and state management for bug extermination.
This is the "dull subagent" version with full Agno benefits while .claude/agents
handle the heavy lifting via claude-mcp.
"""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.memory import AgentMemory
from agno.storage.postgres import PostgresStorage


def get_genie_debug(
    model_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    debug_mode: bool = True,
) -> Agent:
    """
    Factory function for Genie Debug agent with enhanced memory and state management.

    This agent mirrors .claude/agents/genie-debug.md functionality but adds:
    - Persistent debugging context across sessions
    - Enhanced state management via Agno
    - Bug pattern recognition and memory
    - MEESEEKS philosophy with systematic elimination
    """

    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    agent_config = config["agent"]
    model_config = config["model"]
    storage_config = config["storage"]
    memory_config = config["memory"]

    # Enhanced memory configuration for debugging patterns
    memory = AgentMemory(
        create_user_memories=memory_config.get("enable_user_memories", True),
        create_session_summary=memory_config.get("enable_session_summaries", True),
        add_references_to_user_messages=memory_config.get(
            "add_memory_references", True
        ),
        add_references_to_session_summary=memory_config.get(
            "add_session_summary_references", True
        ),
    )

    # PostgreSQL storage with auto-upgrade for debugging data
    storage = PostgresStorage(
        table_name=storage_config["table_name"],
        auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True),
    )

    # Create the enhanced Genie Debug agent
    return Agent(
        name=agent_config["name"],
        agent_id=agent_config["agent_id"],
        model=f"{model_config['provider']}:{model_config['id']}",
        description=agent_config["description"],
        # Enhanced memory and state management for debugging
        memory=memory,
        storage=storage,
        # Session and user context for bug tracking
        session_id=session_id,
        user_id=user_id,
        # Instructions from config (MEESEEKS debugging protocol)
        instructions=config["instructions"],
        # Enhanced capabilities for debugging persistence
        add_history_to_messages=True,
        num_history_responses=memory_config.get("num_history_runs", 30),
        # Streaming and display for debugging feedback
        stream_intermediate_steps=config["streaming"]["stream_intermediate_steps"],
        show_tool_calls=config["display"]["show_tool_calls"],
        # Model parameters optimized for debugging precision
        temperature=model_config.get("temperature", 0.1),  # Maximum precision
        max_tokens=model_config.get("max_tokens", 4000),
        # Debug mode for development
        debug_mode=debug_mode,
    )


# Export the factory function for registry
__all__ = ["get_genie_debug"]
