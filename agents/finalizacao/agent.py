# Finalizacao Specialist Agent Factory
# Handles conversation finalization with protocol and farewell messages

from typing import Optional
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

# Import tools
from agents.tools.finishing_tools import (
    finalize_conversation
)


def get_finalizacao_agent(
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None,
    memory=None,
    # User context parameters
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Agent:
    """
    Finalizacao Specialist Agent factory - handles conversation finalization.
    
    Args:
        version: Specific version to load
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        db_url: Database URL override
        memory: Memory system instance
        user_id: User identifier for session state
        user_name: User name for session state
        phone_number: User phone for session state
        cpf: User CPF for session state
        
    Returns:
        Configured Agent instance
    """
    
    # Load configuration from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Override version if provided
    if version:
        config["agent"]["version"] = version
    
    logger.info(f"🎯 Creating finalizacao specialist agent v{config['agent']['version']}")
    
    # Create agent tools
    tools = [
        finalize_conversation
    ]
    
    # Create storage
    storage = None
    if db_url:
        storage = PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"]
        )
    
    # Create agent
    agent = Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        role=config["agent"]["role"],
        description=config["agent"]["description"],
        instructions=config["instructions"],
        model=Claude(
            id=config["model"]["id"],
            temperature=config["model"]["temperature"],
            max_tokens=config["model"]["max_tokens"]
        ),
        tools=tools,
        storage=storage,
        memory=memory,
        session_id=session_id,
        debug_mode=debug_mode,
        markdown=True,
        show_tool_calls=True,
        # User context will be available in session_state
        add_history_to_messages=config["memory"]["add_history_to_messages"],
        num_history_runs=config["memory"]["num_history_runs"]
    )
    
    logger.info(f"✅ Finalizacao specialist agent created successfully")
    return agent


# Convenience function following existing patterns
def finalizacao_specialist_agent(**kwargs) -> Agent:
    """Convenience function for creating finalizacao specialist agent"""
    return get_finalizacao_agent(**kwargs)