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
from ai.agents.tools.finishing_tools import (
    finalize_conversation
)

# User context management - simple helper for session_state
from core.utils.user_context_helper import create_user_context_state


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
    
    # Create agent tools - use the already imported tool object
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
    
    # Create user context session_state (Agno's built-in way)
    user_context_state = create_user_context_state(
        user_id=user_id,
        user_name=user_name,
        phone_number=phone_number,
        cpf=cpf,
        **{k: v for k, v in kwargs.items() if k.startswith('user_') or k in ['customer_name', 'customer_phone', 'customer_cpf']}
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
        # Behavioral parameters from YAML configuration
        markdown=config.get("markdown", True),
        show_tool_calls=config.get("show_tool_calls", True),
        add_state_in_messages=config.get("add_state_in_messages", True),
        # User context stored in session_state (Agno's built-in persistence)
        session_state=user_context_state if user_context_state.get('user_context') else None,
        # Memory configuration from YAML
        add_history_to_messages=config["memory"]["add_history_to_messages"],
        num_history_runs=config["memory"]["num_history_runs"]
    )
    
    logger.info(f"✅ Finalizacao specialist agent created successfully")
    return agent


# Convenience function following existing patterns
def finalizacao_specialist_agent(**kwargs) -> Agent:
    """Convenience function for creating finalizacao specialist agent"""
    return get_finalizacao_agent(**kwargs)