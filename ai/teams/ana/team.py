"""Ana Team Factory - Clean Agno Implementation

Minimal team implementation following Agno framework best practices.
Based on the multi-language team pattern from Agno documentation.
"""

from typing import Optional, Union
import yaml
from pathlib import Path
from agno.team import Team
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from ai.agents.registry import get_agent
from .models import UserContext
import os


def _create_team_memory(config: dict, db_url: str):
    """Create Memory instance for team if enabled."""
    memory_config = config.get("memory", {})
    if memory_config.get("enable_user_memories", False):
        from lib.memory.memory_factory import create_team_memory
        team_id = config["team"]["team_id"]
        return create_team_memory(team_id, db_url)
    return None


def get_ana_team(
    user_context: Optional[Union[UserContext, dict]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    debug_mode: bool = False
) -> Team:
    """Create Ana team with clean Agno implementation.
    
    Args:
        user_context: User context data (UserContext model or dict)
        session_id: Optional session ID for conversation tracking
        user_id: Optional user ID for session management
        debug_mode: Enable debug mode for development
        
    Returns:
        Configured Team instance with route mode
    """
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Convert user_context dict to UserContext model if needed
    if isinstance(user_context, dict):
        user_context = UserContext(**user_context)
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/genie_agents")
    
    # Load member agents from registry
    members = []
    for agent_name in config["members"]:
        agent = get_agent(
            agent_name,
            session_id=session_id,
            debug_mode=debug_mode,
            db_url=db_url,
            # Pass user context to agents if available
            user_id=user_id,
            pb_phone_number=user_context.pb_phone_number if user_context else None,
            pb_cpf=user_context.pb_cpf if user_context else None
        )
        members.append(agent)
    
    # Create team with all Agno parameters from config
    team = Team(
        # Core team settings
        name=config["team"]["name"],
        team_id=config["team"]["team_id"],
        mode=config["team"]["mode"],
        description=config["team"]["description"],
        
        # Model configuration
        model=Claude(
            id=config["model"]["id"],
            temperature=config["model"]["temperature"],
            max_tokens=config["model"]["max_tokens"],
            thinking=config["model"]["thinking"]
        ),
        
        # Members
        members=members,
        
        # Instructions and criteria
        instructions=config["instructions"],
        success_criteria=config["success_criteria"],
        expected_output=config["expected_output"],
        
        # Session management
        session_id=session_id,
        user_id=user_id,
        
        # Memory instance (create if enabled)
        memory=_create_team_memory(config, db_url),
        
        # Memory configuration
        **{k: v for k, v in config["memory"].items() if k not in ["enable_user_memories", "enable_agentic_memory"]},
        enable_user_memories=config["memory"].get("enable_user_memories", False),
        enable_agentic_memory=config["memory"].get("enable_agentic_memory", False),
        
        # Streaming configuration
        **config["streaming"],
        
        # Event configuration
        **config["events"],
        
        # Context configuration
        **config["context"],
        
        # Display configuration
        **config["display"],
        
        # Storage configuration
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            mode=config["storage"]["mode"],
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"]
        ),
        
        # Debug mode
        debug_mode=debug_mode
    )
    
    return team


# Simple convenience function for latest configuration
def get_ana_team_latest(**kwargs) -> Team:
    """Get Ana team with latest configuration."""
    return get_ana_team(**kwargs)