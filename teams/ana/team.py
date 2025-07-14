# Ana Team Factory - Generic Multi-Agent Router
# Based on Agno Team(mode="route") pattern
# Generic implementation for any agent system

from typing import Optional
import yaml
from pathlib import Path
from agno.team import Team
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage

# V2 Database infrastructure (from agno-demo-app pattern)
from db.session import db_url

# Import generic agent factory
from agents.registry import get_agent


def get_ana_team(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
    agent_names: Optional[list[str]] = None,
):
    """
    Ana Team factory - Generic Agno Team(mode="route") implementation.
    
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
        agent_names = ["adquirencia", "emissao", "pagbank", "human_handoff"]
    
    # Load member agents using generic get_agent factory
    members = [
        get_agent(name, session_id=session_id, debug_mode=debug_mode, db_url=db_url)
        for name in agent_names
    ]
    
    # Use model override if provided (agno-demo-app pattern)
    model_id = model_id or config["model"]["id"]
    
    # Create Team with route mode (Agno docs pattern)
    return Team(
        name=config["team"]["name"],                    # From YAML
        team_id=config["team"]["team_id"],              # From YAML  
        mode="route",                                   # Key Agno pattern
        members=members,                                # Generic agent loading
        instructions=config["instructions"],            # From YAML (routing logic)
        session_id=session_id,
        user_id=user_id,
        description=config["team"]["description"],
        model=Claude(
            id=model_id,
            max_tokens=config["model"]["max_tokens"],
            temperature=config["model"]["temperature"],
            thinking=config["model"]["thinking"]
        ),
        success_criteria=config["success_criteria"],
        enable_agentic_context=config["enable_agentic_context"],
        expected_output=config["expected_output"],
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            mode=config["storage"]["mode"],
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"],
        ),
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
    
    # Load member agents using generic get_agent factory
    members = [
        get_agent(name, session_id=session_id, debug_mode=debug_mode, db_url=db_url)
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
        debug_mode=debug_mode,
    )