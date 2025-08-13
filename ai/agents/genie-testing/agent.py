"""
🧞 Genie Testing - The Testing Domain Specialist

Enhanced Agno agent with persistent memory and state management for testing coordination.
This is the "dull subagent" version with full Agno benefits while .claude/agents
handle the heavy lifting via claude-mcp.
"""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.memory import AgentMemory
from agno.storage.postgres import PostgresStorage


def get_genie_testing(
    model_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    debug_mode: bool = True,
) -> Agent:
    """
    Factory function for Genie Testing agent with comprehensive memory and state management.

    This agent coordinates testing operations by intelligently routing tasks to specialized
    .claude/agents while maintaining strategic oversight and quality assurance.

    Key Features:
    - Strategic testing analysis and coordination
    - Intelligent routing to genie-testing-fixer and genie-testing-maker
    - Persistent memory for testing patterns and strategies
    - Comprehensive state management via Agno
    - Quality gate enforcement and coverage tracking
    """

    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    agent_config = config["agent"]
    model_config = config["model"]
    storage_config = config["storage"]
    memory_config = config["memory"]

    # Comprehensive memory configuration
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

    # PostgreSQL storage with auto-upgrade
    storage = PostgresStorage(
        table_name=storage_config["table_name"],
        auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True),
    )

    # Create the comprehensive Genie Testing agent
    return Agent(
        name=agent_config["name"],
        agent_id=agent_config["agent_id"],
        model=f"{model_config['provider']}:{model_config['id']}",
        description=agent_config["description"],
        # Comprehensive memory and state management
        memory=memory,
        storage=storage,
        # Session and user context
        session_id=session_id,
        user_id=user_id,
        # Instructions from config
        instructions=config["instructions"],
        # Enhanced capabilities
        add_history_to_messages=True,
        num_history_responses=memory_config.get("num_history_runs", 30),
        # Streaming and display
        stream_intermediate_steps=config["streaming"]["stream_intermediate_steps"],
        show_tool_calls=config["display"]["show_tool_calls"],
        # Model parameters
        temperature=model_config.get("temperature", 0.3),
        max_tokens=model_config.get("max_tokens", 4000),
        # Debug mode
        debug_mode=debug_mode,
    )


# Export the factory function for registry
__all__ = ["get_genie_testing"]
