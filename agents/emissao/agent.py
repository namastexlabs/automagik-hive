# Emissão Card Services Agent Factory
# Based on agno-demo-app patterns for dynamic agent creation

from typing import Optional
import yaml
from pathlib import Path
from agno import Agent, ModelConfig
from agno.storage.postgresql import PostgresStorage


def get_emissao_agent(
    version: Optional[int] = None,        # API parameter - specific version
    session_id: Optional[str] = None,     # API parameter - session management  
    debug_mode: bool = False,             # API parameter - debugging
    db_url: Optional[str] = None          # API parameter - database connection
) -> Agent:
    """
    Factory function for Emissão card services specialist agent.
    
    Args:
        version: Specific agent version to load (defaults to latest)
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode for development
        db_url: Database URL for storage (defaults to environment)
        
    Returns:
        Configured Emissão Agent instance
    """
    # Load configuration (in V2 this will come from database)
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Apply version if specified (future: load from database)
    if version:
        # TODO: Load specific version from database
        # config = load_agent_version("emissao-specialist", version)
        pass
    
    # Create model configuration
    model_config = config["model"]
    if "id" in model_config:
        model_config["name"] = model_config.pop("id")  # Agno uses 'name' not 'id'
    
    return Agent(
        name=config["agent"]["name"],
        agent_id=config["agent"]["agent_id"],
        instructions=config["instructions"],
        model=ModelConfig(**model_config),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url or config["storage"].get("db_url"),
            auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True)
        ),
        session_id=session_id,
        debug_mode=debug_mode,
        # Additional Agno parameters from config
        markdown=config.get("markdown", False),
        show_tool_calls=config.get("show_tool_calls", True),
        add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
        num_history_runs=config.get("memory", {}).get("num_history_runs", 5)
    )


# Convenience functions for different use cases
def get_emissao_agent_latest(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get latest version of Emissão agent"""
    return get_emissao_agent(session_id=session_id, debug_mode=debug_mode)


def get_emissao_agent_v27(session_id: Optional[str] = None, debug_mode: bool = False) -> Agent:
    """Get specific v27 of Emissão agent for testing/rollback"""
    return get_emissao_agent(version=27, session_id=session_id, debug_mode=debug_mode)