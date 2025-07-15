# Ana Team Factory - Generic Multi-Agent Router
# Based on Agno Team(mode="route") pattern
# Generic implementation for any agent system

import os
from typing import Optional, Union
import yaml
from pathlib import Path
from agno.team import Team
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

# V2 Database infrastructure (from agno-demo-app pattern)
from db.session import db_url

# Import generic agent factory
from agents.registry import get_agent

# Memory system integration
from context.memory.memory_manager import create_memory_manager

# Demo logging is now handled by global patching in serve.py


def get_ana_team(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
    agent_names: Optional[list[str]] = None,
) -> Team:
    """
    Ana Team factory - Generic Agno Team(mode="route") implementation.
    Demo logging is handled by global patching in serve.py.
    
    Args:
        model_id: Override model configuration
        user_id: User ID for session tracking
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        agent_names: List of agent names to include (defaults to config)
        
    Returns:
        Configured Team instance with route mode
    """
    
    # Load static config from YAML (agno-demo-app pattern)
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Use provided agent names or default from config/system
    if agent_names is None:
        agent_names = ["adquirencia", "emissao", "pagbank", "human_handoff"]  # Added back human_handoff for routing
    
    # Use model override if provided (agno-demo-app pattern)
    model_id = model_id or config["model"]["id"]
    
    # Initialize memory system from YAML config - use Agno Memory V2 correctly
    memory_manager = None
    memory = None
    memory_db = None
    if config.get("memory"):
        try:
            memory_manager = create_memory_manager()
            # Get the shared memory instance for both team and agents
            memory = memory_manager.memory
            # Also get the memory database for agents that need it
            memory_db = memory_manager.memory_db
        except Exception as e:
            print(f"⚠️ Memory system initialization failed: {e}")
            print("Continuing without memory system...")
    
    # Load member agents using generic get_agent factory
    members = [
        get_agent(name, session_id=session_id, debug_mode=debug_mode, db_url=db_url, memory=memory, memory_db=memory_db)
        for name in agent_names
    ]
    
    # Load workflow tools for escalation triggers
    tools = []
    if "tools" in config:
        try:
            from agents.tools.workflow_tools import trigger_human_handoff_workflow
            if "trigger_human_handoff_workflow" in config["tools"]:
                tools.append(trigger_human_handoff_workflow)
        except ImportError as e:
            logger.warning(f"Could not load workflow tools for Ana team: {e}")
            # Continue without tools
    
    # Create Team with route mode (Agno docs pattern)
    # Demo logging is handled by global patching
    return Team(
        name=config["team"]["name"],                    # From YAML
        team_id=config["team"]["team_id"],              # From YAML  
        mode="route",                                   # Key Agno pattern
        members=members,                                # Generic agent loading
        instructions=config["instructions"],            # From YAML (routing logic)
        tools=tools if tools else None,                     # Workflow trigger tools
        session_id=session_id,
        user_id=user_id,
        description=config["team"]["description"],
        model=Claude(
            id=model_id,
            max_tokens=config["model"]["max_tokens"],
            temperature=config["model"]["temperature"],
            thinking=config["model"]["thinking"]
        ),
        success_criteria=config.get("success_criteria"),
        expected_output=config.get("expected_output"),
        # CRITICAL: Team-specific parameters (VERIFIED from Agno docs - dynamically configured)
        show_members_responses=config.get("show_members_responses", True),  # Show specialist responses
        stream_intermediate_steps=config.get("stream_intermediate_steps", True),  # Stream routing process
        stream_member_events=config.get("stream_member_events", True),  # Stream member events
        store_events=config.get("store_events", False),  # Don't store streaming events
        enable_agentic_context=config.get("enable_agentic_context", True),
        share_member_interactions=config.get("share_member_interactions", True),
        markdown=config.get("markdown", True),
        show_tool_calls=config.get("show_tool_calls", True),
        add_datetime_to_instructions=config.get("add_datetime_to_instructions", True),
        add_member_tools_to_system_message=config.get("add_member_tools_to_system_message", True),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            mode=config["storage"]["mode"],
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"],
        ),
        # Agno Memory V2 configuration - provide Memory object for team
        memory=memory,  # Team needs the Memory object, not the memory database
        # Memory configuration from YAML
        enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
        enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
        add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
        num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
        debug_mode=debug_mode,
    )


# Convenience functions following agno-demo-app patterns
def get_ana_team_latest(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None, 
    debug_mode: bool = False,
    agent_names: Optional[list[str]] = None
) -> Team:
    """Get latest Ana team configuration with generic agent support"""
    return get_ana_team(
        user_id=user_id, 
        session_id=session_id, 
        debug_mode=debug_mode,
        agent_names=agent_names
    )


def get_ana_team_development(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_names: Optional[list[str]] = None
) -> Team:
    """Get Ana team with development settings and generic agent support"""
    return get_ana_team(
        user_id=user_id, 
        session_id=session_id, 
        debug_mode=True,
        model_id="claude-sonnet-4-20250514",  # Force specific model for development
        agent_names=agent_names
    )


def get_custom_team(
    team_name: str,
    agent_names: list[str],
    instructions: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False
) -> Team:
    """
    Create a custom team with any agents - fully generic implementation.
    
    Args:
        team_name: Name for the team
        agent_names: List of agent names to include
        instructions: Routing/coordination instructions
        user_id: User ID for session tracking
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        
    Returns:
        Configured Team instance with route mode
    """
    
    # Load base config for storage/model settings
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Initialize memory for custom team - use Agno Memory V2 correctly
    memory_manager = None
    memory = None
    memory_db = None
    try:
        memory_manager = create_memory_manager()
        # Get the shared memory instance for both team and agents
        memory = memory_manager.memory
        # Also get the memory database for agents that need it
        memory_db = memory_manager.memory_db
    except Exception as e:
        print(f"⚠️ Memory system initialization failed: {e}")
        print("Continuing without memory system...")
    
    # Load member agents using generic get_agent factory
    members = [
        get_agent(name, session_id=session_id, debug_mode=debug_mode, db_url=db_url, memory=memory, memory_db=memory_db)
        for name in agent_names
    ]
    
    return Team(
        name=team_name,
        team_id=f"{team_name.lower().replace(' ', '-')}-team",
        mode="route",                                   # Key Agno pattern
        members=members,                                # Generic agent loading
        instructions=instructions,                      # Custom routing logic
        session_id=session_id,
        user_id=user_id,
        description=f"Custom {team_name} team with {len(agent_names)} specialists",
        model=Claude(
            id=config["model"]["id"],
            max_tokens=config["model"]["max_tokens"],
            temperature=config["model"]["temperature"],
            thinking=config["model"]["thinking"]
        ),
        storage=PostgresStorage(
            table_name=f"{team_name.lower().replace(' ', '_')}_team",
            db_url=db_url,
            mode=config["storage"]["mode"],
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"],
        ),
        # Agno Memory V2 configuration - provide Memory object for team
        memory=memory,  # Team needs the Memory object, not the memory database
        # Memory configuration from YAML
        enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
        enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
        add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
        num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
        debug_mode=debug_mode,
    )