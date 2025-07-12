# Ana Team Factory - PagBank Customer Service Assistant
# COPIED from agno-demo-app/teams/finance_researcher.py lines 83-117
# Modified 20% for PagBank business requirements

from typing import Optional
import yaml
from pathlib import Path
from agno.team import Team
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage

# V2 Database infrastructure (from agno-demo-app pattern)
from db.session import db_url

# Import agent registry for dynamic agent loading
from agents.registry import AgentRegistry


def get_ana_team(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
):
    """
    Ana Team factory - COPIED from finance_researcher.py pattern
    Modified for PagBank multi-agent routing system
    """
    
    # Load static config from YAML (agno-demo-app pattern)
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Load member agents from registry (PagBank modification)
    members = [
        AgentRegistry.get_agent("adquirencia_specialist", db_url=db_url),
        AgentRegistry.get_agent("emissao_specialist", db_url=db_url), 
        AgentRegistry.get_agent("pagbank_specialist", db_url=db_url),
        AgentRegistry.get_agent("human_handoff_specialist", db_url=db_url)
    ]
    
    # Use model override if provided (agno-demo-app pattern)
    model_id = model_id or config["model"]["id"]
    
    return Team(
        name=config["team"]["name"],                    # From YAML
        team_id=config["team"]["team_id"],              # From YAML  
        mode=config["team"]["mode"],                    # From YAML ("route")
        members=members,                                # From agent registry
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
    debug_mode: bool = False
) -> Team:
    """Get latest Ana team configuration"""
    return get_ana_team(user_id=user_id, session_id=session_id, debug_mode=debug_mode)


def get_ana_team_development(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Team:
    """Get Ana team with development settings"""
    return get_ana_team(
        user_id=user_id, 
        session_id=session_id, 
        debug_mode=True,
        model_id="claude-sonnet-4-20250514"  # Force specific model for development
    )