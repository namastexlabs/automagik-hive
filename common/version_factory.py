"""
Unified Version Factory - Single Implementation for All Component Types

Eliminates 80% code duplication across agents/teams/workflows version factories.
"""

from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger

from db.session import get_db, db_url
from db.services.component_version_service import ComponentVersionService


class UnifiedVersionFactory:
    """
    Single factory for creating versioned components of any type.
    Eliminates code duplication across agent/team/workflow factories.
    """
    
    def __init__(self, db_session: Session = None):
        """Initialize with optional database session."""
        self.db = db_session or next(get_db())
        self.component_service = ComponentVersionService(self.db)
    
    def create_versioned_component(
        self,
        component_id: str,
        component_type: str,  # "agent", "team", "workflow"
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        # User context parameters
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        cpf: Optional[str] = None,
        **kwargs
    ) -> Union[Agent, Team, Workflow]:
        """
        Create any component type with version support.
        
        Args:
            component_id: Component identifier
            component_type: "agent", "team", or "workflow"
            version: Version number (None for active)
            session_id: Session ID for tracking
            debug_mode: Enable debug mode
            user_id, user_name, phone_number, cpf: User context
            
        Returns:
            Configured component instance
        """
        
        # Load version configuration
        if version is not None:
            version_record = self.component_service.get_version(component_id, version)
            if not version_record:
                raise ValueError(f"Version {version} not found for {component_id}")
        else:
            version_record = self.component_service.get_active_version(component_id)
            if not version_record:
                raise ValueError(f"No active version found for {component_id}")
        
        config = version_record.config
        
        # Validate component type matches
        if version_record.component_type != component_type:
            raise ValueError(f"Component {component_id} is type {version_record.component_type}, not {component_type}")
        
        # Create component based on type
        if component_type == "agent":
            return self._create_agent(component_id, config, session_id, debug_mode, 
                                    user_id, user_name, phone_number, cpf, **kwargs)
        elif component_type == "team":
            return self._create_team(component_id, config, session_id, debug_mode,
                                   user_id, user_name, phone_number, cpf, **kwargs)
        elif component_type == "workflow":
            return self._create_workflow(component_id, config, session_id, debug_mode,
                                       user_id, user_name, phone_number, cpf, **kwargs)
        else:
            raise ValueError(f"Unsupported component type: {component_type}")
    
    def _create_agent(self, component_id: str, config: Dict[str, Any], 
                     session_id: Optional[str], debug_mode: bool,
                     user_id: Optional[str], user_name: Optional[str],
                     phone_number: Optional[str], cpf: Optional[str],
                     **kwargs) -> Agent:
        """Create versioned agent."""
        
        # Import memory system
        from context.memory.memory_manager import create_memory_manager
        
        # Initialize memory
        memory = None
        try:
            memory_manager = create_memory_manager()
            memory = memory_manager.memory
        except Exception as e:
            logger.warning(f"Memory initialization failed: {e}")
        
        # Load agent tools
        tools = self._load_agent_tools(config.get("tools", []))
        
        return Agent(
            name=config["agent"]["name"],
            agent_id=config["agent"]["agent_id"],
            role=config["agent"].get("role"),
            instructions=config["instructions"],
            model=Claude(
                id=config["model"]["id"],
                temperature=config["model"].get("temperature", 0.7),
                max_tokens=config["model"].get("max_tokens", 2000)
            ),
            tools=tools,
            storage=PostgresStorage(
                table_name=config["storage"]["table_name"],
                db_url=db_url,
                auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True)
            ),
            memory=memory,
            session_id=session_id,
            user_id=user_id,
            debug_mode=debug_mode,
            markdown=config.get("markdown", True)
        )
    
    def _create_team(self, component_id: str, config: Dict[str, Any],
                    session_id: Optional[str], debug_mode: bool,
                    user_id: Optional[str], user_name: Optional[str], 
                    phone_number: Optional[str], cpf: Optional[str],
                    **kwargs) -> Team:
        """Create versioned team."""
        
        # Import dependencies
        from agents.registry import get_agent
        from context.memory.memory_manager import create_memory_manager
        from context.user_context_helper import create_user_context_state
        
        # Initialize memory
        memory = None
        try:
            memory_manager = create_memory_manager()
            memory = memory_manager.memory
        except Exception as e:
            logger.warning(f"Memory initialization failed: {e}")
        
        # Create user context
        user_context_state = create_user_context_state(
            user_id=user_id, user_name=user_name,
            phone_number=phone_number, cpf=cpf, **kwargs
        )
        
        # Load member agents
        agent_names = config.get("members", [])
        members = [
            get_agent(name, session_id=session_id, debug_mode=debug_mode,
                     db_url=db_url, memory=memory, user_id=user_id,
                     user_name=user_name, phone_number=phone_number, cpf=cpf)
            for name in agent_names
        ]
        
        return Team(
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
            storage=PostgresStorage(
                table_name=config["storage"]["table_name"],
                db_url=db_url,
                mode=config["storage"].get("mode", "team"),
                auto_upgrade_schema=config["storage"].get("auto_upgrade_schema", True)
            ),
            session_state=user_context_state if user_context_state.get('user_context') else None,
            memory=memory,
            debug_mode=debug_mode
        )
    
    def _create_workflow(self, component_id: str, config: Dict[str, Any],
                        session_id: Optional[str], debug_mode: bool,
                        user_id: Optional[str], user_name: Optional[str],
                        phone_number: Optional[str], cpf: Optional[str],
                        **kwargs) -> Workflow:
        """Create versioned workflow."""
        
        # Import specific workflow factory functions
        try:
            if component_id == "human_handoff" or component_id == "human-handoff":
                from workflows.human_handoff.workflow import get_human_handoff_workflow
                return get_human_handoff_workflow()
            elif component_id == "conversation_typification":
                from workflows.conversation_typification import get_conversation_typification_workflow
                return get_conversation_typification_workflow(debug_mode=debug_mode)
            else:
                raise ValueError(f"Unknown workflow: {component_id}")
        except ImportError as e:
            logger.error(f"Failed to import workflow {component_id}: {e}")
            raise ValueError(f"Workflow {component_id} not available: {e}")
    
    def _load_agent_tools(self, tool_names: list) -> list:
        """Load agent tools from configuration."""
        tools = []
        
        for tool_name in tool_names:
            if tool_name == "search_knowledge_base":
                from context.knowledge.csv_knowledge_tool import search_knowledge_base
                tools.append(search_knowledge_base)
            # Add other tools as needed
        
        return tools


# Convenience functions for backward compatibility
def create_versioned_agent(agent_id: str, version: Optional[int] = None, **kwargs) -> Agent:
    """Create versioned agent using unified factory."""
    factory = UnifiedVersionFactory()
    return factory.create_versioned_component(agent_id, "agent", version, **kwargs)


def create_versioned_team(team_id: str, version: Optional[int] = None, **kwargs) -> Team:
    """Create versioned team using unified factory."""
    factory = UnifiedVersionFactory()
    return factory.create_versioned_component(team_id, "team", version, **kwargs)


def create_versioned_workflow(workflow_id: str, version: Optional[int] = None, **kwargs) -> Workflow:
    """Create versioned workflow using unified factory."""
    factory = UnifiedVersionFactory()
    return factory.create_versioned_component(workflow_id, "workflow", version, **kwargs)