"""
🧞 Genie Test Fixer - The Relentless Meeseeks

Enhanced Agno agent with persistent memory and state management for test fixing.
This is the "dull subagent" version with full Agno benefits while .claude/agents
handle the heavy lifting via claude-mcp.
"""

import yaml
from pathlib import Path
from typing import Optional
from agno import Agent
from agno.storage import PostgresStorage
from agno.memory import AgentMemory

def get_genie_test_fixer(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True
) -> Agent:
    """
    Factory function for Genie Test Fixer agent with enhanced memory and state management.
    
    This agent mirrors .claude/agents/genie-test-fixer.md functionality but adds:
    - Persistent memory across sessions
    - Enhanced state management via Agno
    - Context sharing capabilities
    - MEESEEKS philosophy with issue reporting
    """
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    agent_config = config["agent"]
    model_config = config["model"]
    storage_config = config["storage"]
    memory_config = config["memory"]
    
    # Enhanced memory configuration
    memory = AgentMemory(
        create_user_memories=memory_config.get("enable_user_memories", True),
        create_session_summary=memory_config.get("enable_session_summaries", True),
        add_references_to_user_messages=memory_config.get("add_memory_references", True),
        add_references_to_session_summary=memory_config.get("add_session_summary_references", True)
    )
    
    # PostgreSQL storage with auto-upgrade
    storage = PostgresStorage(
        table_name=storage_config["table_name"],
        auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
    )
    
    # Create the enhanced Genie Test Fixer agent
    agent = Agent(
        name=agent_config["name"],
        agent_id=agent_config["agent_id"],
        model=f"{model_config['provider']}:{model_config['id']}",
        description=agent_config["description"],
        
        # Enhanced memory and state management
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
        debug_mode=debug_mode
    )
    
    return agent

# Export the factory function for registry
__all__ = ["get_genie_test_fixer"]