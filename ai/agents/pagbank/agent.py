# PagBank Digital Banking Agent Factory
# Native Agno knowledge integration with POC business unit filters

from typing import Optional, Any
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from core.knowledge.pagbank_knowledge_factory import get_knowledge_base

# User context management - simple helper for session_state
from core.utils.user_context_helper import create_user_context_state


def get_pagbank_agent(
    version: Optional[int] = None,        # API parameter - specific version
    session_id: Optional[str] = None,     # API parameter - session management  
    debug_mode: bool = False,             # API parameter - debugging
    db_url: Optional[str] = None,         # API parameter - database connection
    memory: Optional[Any] = None,         # API parameter - memory instance from team
    # User context parameters - will be stored in session_state
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Agent:
    """
    Factory function for PagBank digital banking specialist agent.
    Uses native Agno knowledge integration with exact POC business unit filtering.
    
    Args:
        version: Specific agent version to load (defaults to latest)
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode for development
        db_url: Database URL for storage (defaults to environment)
        
    Returns:
        Configured PagBank Agent instance with native knowledge integration
    """
    # Load configuration (in V2 this will come from database)
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Apply version if specified (future: load from database)
    if version:
        # TODO: Load specific version from database
        # config = load_agent_version("pagbank-specialist", version)
        pass
    
    # Create model instance
    model_config = config["model"]
    model = Claude(
        id=model_config["id"],
        temperature=model_config.get("temperature", 0.7),
        max_tokens=model_config.get("max_tokens", 2000)
    )
    
    # Ensure we have a database URL
    if db_url is None:
        from db.session import db_url as default_db_url
        db_url = default_db_url
    
    # Use shared knowledge base with agent-specific max_results
    max_results = config["knowledge_filter"]["max_results"]
    knowledge_base = get_knowledge_base(db_url, num_documents=max_results)
    
    # Get knowledge configuration from YAML
    knowledge_config = config["knowledge"]
    
    # Load business unit filter from YAML config
    business_unit_filter = config["knowledge_filter"]["business_unit"]
    
    # Create user context session_state (Agno's built-in way)
    user_context_state = create_user_context_state(
        user_id=user_id,
        user_name=user_name,
        phone_number=phone_number,
        cpf=cpf,
        **{k: v for k, v in kwargs.items() if k.startswith('user_') or k in ['customer_name', 'customer_phone', 'customer_cpf']}
    )
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=model,
        # Native Agno knowledge integration with exact POC filtering
        knowledge=knowledge_base,
        search_knowledge=knowledge_config["search_knowledge"],
        enable_agentic_knowledge_filters=knowledge_config["enable_agentic_knowledge_filters"],
        knowledge_filters={"business_unit": business_unit_filter},
        # POC memory integration - exactly like POC base_agent.py line 95
        memory=memory,
        enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
        enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True)
        ),
        session_id=session_id,
        debug_mode=debug_mode,
        # Additional Agno parameters from config
        markdown=config.get("markdown", False),
        show_tool_calls=config.get("show_tool_calls", True),
        add_datetime_to_instructions=config.get("add_datetime_to_instructions", True),
        add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
        num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
        # User context stored in session_state (Agno's built-in persistence)
        session_state=user_context_state if user_context_state.get('user_context') else None,
        # Make user context available in instructions
        add_state_in_messages=config.get("add_state_in_messages", True),  # This allows {user_name}, {user_id}, etc. in instructions
        # CRITICAL: Response constraints from YAML configuration (dynamic, not hardcoded)
        success_criteria=config.get("success_criteria"),
        expected_output=config.get("expected_output")
    )


# Convenience functions for different use cases
def get_pagbank_agent_latest(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get latest version of PagBank agent"""
    return get_pagbank_agent(session_id=session_id, debug_mode=debug_mode)


def get_pagbank_agent_v32(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get specific v32 of PagBank agent for testing/rollback"""
    return get_pagbank_agent(version=32, session_id=session_id, debug_mode=debug_mode)