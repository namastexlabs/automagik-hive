"""
Team Version Factory - Dynamic Team Creation from Database Configurations

Unified factory for creating teams with specific version configurations
loaded from the database, enabling versioned team instantiation.
"""

from typing import Optional, Dict, Any
from agno.team import Team
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from sqlalchemy.orm import Session

from db.session import get_db, db_url
from db.services.component_version_service import ComponentVersionService


def create_versioned_team(
    team_id: str,
    version: int,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    # User context parameters
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Team:
    """
    Create a team instance using version-specific configuration from database.
    
    Args:
        team_id: Team identifier (e.g., "ana")
        version: Version number to load
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        user_id: User ID for session tracking
        user_name: User name for context
        phone_number: Phone number for context
        cpf: CPF for context
        **kwargs: Additional parameters
        
    Returns:
        Configured Team instance with version-specific configuration
        
    Raises:
        ValueError: If version not found or configuration invalid
    """
    
    # Get database session
    db: Session = next(get_db())
    
    try:
        # Load version-specific configuration
        service = ComponentVersionService(db)
        version_record = service.get_version(team_id, version)
        
        if not version_record:
            raise ValueError(f"Team version {version} not found for {team_id}")
        
        if version_record.component_type != "team":
            raise ValueError(f"Component {team_id} version {version} is not a team")
        
        config = version_record.config
        
        # Load member agents using generic get_agent factory
        from agents.registry import get_agent
        
        # Import memory management
        from context.memory.memory_manager import create_memory_manager
        from context.user_context_helper import create_user_context_state
        
        # Initialize memory system
        memory_manager = None
        memory = None
        if config.get("memory"):
            try:
                memory_manager = create_memory_manager()
                memory = memory_manager.memory
            except Exception as e:
                logger.warning(f"Memory system initialization failed: {e}")
        
        # Create user context session_state
        user_context_state = create_user_context_state(
            user_id=user_id,
            user_name=user_name,
            phone_number=phone_number,
            cpf=cpf,
            **{k: v for k, v in kwargs.items() if k.startswith('user_') or k in ['customer_name', 'customer_phone', 'customer_cpf']}
        )
        
        # Get agent names from config or use defaults
        agent_names = config.get("members", ["adquirencia", "emissao", "pagbank", "human_handoff", "finalizacao"])
        
        # Load member agents
        members = [
            get_agent(
                name, 
                session_id=session_id, 
                debug_mode=debug_mode, 
                db_url=db_url, 
                memory=memory,
                user_id=user_id,
                user_name=user_name,
                phone_number=phone_number,
                cpf=cpf
            )
            for name in agent_names
        ]
        
        # Create Team with version-specific configuration
        team = Team(
            name=config["team"]["name"],
            team_id=config["team"]["team_id"],
            mode=config["team"].get("mode", "route"),
            members=members,
            instructions=config["instructions"],
            session_id=session_id,
            user_id=user_id,
            description=config["team"].get("description"),
            model=Claude(
                id=config["model"]["id"],
                max_tokens=config["model"].get("max_tokens", 2000),
                temperature=config["model"].get("temperature", 0.7),
                thinking=config["model"].get("thinking")
            ),
            # Team-specific parameters from config
            show_members_responses=config.get("show_members_responses", True),
            stream_intermediate_steps=config.get("stream_intermediate_steps", True),
            stream_member_events=config.get("stream_member_events", True),
            store_events=config.get("store_events", False),
            enable_agentic_context=config.get("enable_agentic_context", True),
            share_member_interactions=config.get("share_member_interactions", True),
            markdown=config.get("markdown", True),
            show_tool_calls=config.get("show_tool_calls", True),
            add_datetime_to_instructions=config.get("add_datetime_to_instructions", True),
            add_member_tools_to_system_message=config.get("add_member_tools_to_system_message", True),
            # User context stored in session_state
            session_state=user_context_state if user_context_state.get('user_context') else None,
            add_state_in_messages=True,
            storage=PostgresStorage(
                table_name=config["storage"]["table_name"],
                db_url=db_url,
                mode=config["storage"].get("mode", "team"),
                auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True),
            ),
            # Memory configuration
            memory=memory,
            enable_user_memories=config.get("memory", {}).get("enable_user_memories", True),
            enable_agentic_memory=config.get("memory", {}).get("enable_agentic_memory", True),
            add_history_to_messages=config.get("memory", {}).get("add_history_to_messages", True),
            num_history_runs=config.get("memory", {}).get("num_history_runs", 5),
            debug_mode=debug_mode,
        )
        
        logger.info(f"✅ Created team {team_id} version {version}")
        return team
        
    except Exception as e:
        logger.error(f"❌ Failed to create team {team_id} version {version}: {str(e)}")
        raise
    finally:
        db.close()


def get_team_default_config(team_id: str) -> Dict[str, Any]:
    """
    Get default configuration for a team type.
    
    Args:
        team_id: Team identifier
        
    Returns:
        Default configuration dictionary
    """
    
    # Default team configurations
    defaults = {
        "ana": {
            "team": {
                "name": "Ana - Assistant Virtual",
                "team_id": "ana",
                "mode": "route",
                "description": "Assistente virtual especializada em roteamento inteligente"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 1.0,
                "max_tokens": 2000,
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 1024
                }
            },
            "instructions": [
                "Você é a Ana, assistente virtual especializada em roteamento inteligente.",
                "Analise a mensagem do usuário e direcione para o agente especialista mais adequado:",
                "- Para dúvidas sobre cartões, emissão ou conta PagBank: direcione para 'emissao'",
                "- Para problemas com máquinas, vendas ou recebimentos: direcione para 'adquirencia'", 
                "- Para questões específicas do PagBank ou produtos financeiros: direcione para 'pagbank'",
                "- Se o usuário estiver frustrado ou solicitar atendimento humano: direcione para 'human_handoff'",
                "- Para encerramento de conversa ou despedidas: direcione para 'finalizacao'",
                "Seja silenciosa no roteamento - deixe o especialista responder diretamente ao usuário."
            ],
            "storage": {
                "type": "postgres",
                "table_name": "ana_team",
                "mode": "team",
                "auto_upgrade_schema": True
            },
            "memory": {
                "enable_user_memories": True,
                "enable_agentic_memory": True,
                "add_history_to_messages": True,
                "num_history_runs": 5
            },
            "members": ["adquirencia", "emissao", "pagbank", "human_handoff", "finalizacao"]
        }
    }
    
    return defaults.get(team_id, {})


def sync_team_version_from_yaml(team_id: str, yaml_config: Dict[str, Any]) -> int:
    """
    Sync team configuration from YAML to database.
    
    Args:
        team_id: Team identifier
        yaml_config: Configuration from YAML file
        
    Returns:
        Version number created
    """
    
    db: Session = next(get_db())
    
    try:
        service = ComponentVersionService(db)
        
        # Get current version or default to 1
        current_version = service.get_active_version(team_id)
        next_version = (current_version.version + 1) if current_version else 1
        
        # Create new version
        version_record = service.create_version(
            component_id=team_id,
            component_type="team",
            version=next_version,
            config=yaml_config,
            created_by="yaml_sync",
            description=f"Synced from YAML file",
            is_active=True,
            sync_source="yaml"
        )
        
        logger.info(f"✅ Synced team {team_id} to version {next_version}")
        return version_record.version
        
    except Exception as e:
        logger.error(f"❌ Failed to sync team {team_id}: {str(e)}")
        raise
    finally:
        db.close()