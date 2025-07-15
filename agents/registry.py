# Generic Agent Registry for Multi-Agent Systems
# Dynamic agent loading from factory functions

from typing import Dict, Optional, Any
from agno.agent import Agent
import os
from .version_factory import create_versioned_agent

# Dynamic import system for agent discovery
_agent_modules = {
    "pagbank": "agents.pagbank.agent",
    "adquirencia": "agents.adquirencia.agent", 
    "emissao": "agents.emissao.agent",
    "human_handoff": "agents.human_handoff.agent",
    "finalizacao": "agents.finalizacao.agent"
}

# Cache for imported agent factories
_imported_factories = {}


def _import_agent_factory(agent_name: str):
    """Dynamically import agent factory function"""
    if agent_name in _imported_factories:
        return _imported_factories[agent_name]
    
    if agent_name not in _agent_modules:
        return None
        
    try:
        module_path = _agent_modules[agent_name]
        module = __import__(module_path, fromlist=[f"get_{agent_name}_agent"])
        factory = getattr(module, f"get_{agent_name}_agent")
        _imported_factories[agent_name] = factory
        return factory
    except (ImportError, AttributeError) as e:
        print(f"⚠️ {agent_name.title()} agent not found: {e}")
        _imported_factories[agent_name] = None
        return None


class AgentRegistry:
    """
    Generic registry for managing agent creation and versioning.
    Supports any agent system, not just PagBank.
    """
    
    @classmethod
    def _get_available_agents(cls) -> Dict[str, callable]:
        """Get all available agent factories"""
        factories = {}
        
        for agent_name in _agent_modules.keys():
            factory = _import_agent_factory(agent_name)
            if factory:
                # Register both full name and alias
                factories[f"{agent_name}_specialist"] = factory
                factories[agent_name] = factory
                
        return factories
    
    @classmethod
    def get_agent(
        cls,
        agent_id: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None,
        memory: Optional[Any] = None,
        # User context parameters - forwarded to agent factories
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        cpf: Optional[str] = None,
        **kwargs
    ) -> Agent:
        """
        Get agent instance by ID - Generic factory pattern with versioning support.
        
        Args:
            agent_id: Agent identifier (e.g., 'pagbank', 'adquirencia')
            version: Specific version to load
            session_id: Session ID for conversation tracking
            debug_mode: Enable debug mode
            db_url: Database URL override
            user_id: User identifier for session state
            user_name: User name for session state
            phone_number: User phone for session state
            cpf: User CPF for session state
            
        Returns:
            Configured Agent instance
            
        Raises:
            KeyError: If agent_id not found
        """
        # Try database-driven versioning first (includes knowledge base and auto-update)
        try:
            return create_versioned_agent(
                agent_id=f"{agent_id}-specialist" if not agent_id.endswith("-specialist") else agent_id,
                version=version,
                session_id=session_id,
                debug_mode=debug_mode,
                db_url=db_url,
                memory=memory,
                # Forward user context parameters
                user_id=user_id,
                user_name=user_name,
                phone_number=phone_number,
                cpf=cpf,
                **kwargs
            )
        except ValueError:
            # Fall back to agent factories if versioning fails
            available_factories = cls._get_available_agents()
            
            if agent_id not in available_factories:
                available_agents = list(available_factories.keys())
                raise KeyError(f"Agent '{agent_id}' not found. Available: {available_agents}")
            
            factory = available_factories[agent_id]
            
            # Use environment database URL if not provided
            if db_url is None:
                db_url = os.getenv("DATABASE_URL")
            
            return factory(
                version=version,
                session_id=session_id,
                debug_mode=debug_mode,
                db_url=db_url,
                memory=memory,
                # Forward user context parameters
                user_id=user_id,
                user_name=user_name,
                phone_number=phone_number,
                cpf=cpf,
                **kwargs
            )
    
    @classmethod
    def get_all_agents(
        cls,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None
    ) -> Dict[str, Agent]:
        """
        Get all available agents.
        
        Returns:
            Dictionary mapping agent_id to Agent instance
        """
        agents = {}
        available_factories = cls._get_available_agents()
        
        # Get unique agent names (no duplicates for aliases)
        unique_agents = set()
        for agent_name in _agent_modules.keys():
            if f"{agent_name}_specialist" in available_factories:
                unique_agents.add(f"{agent_name}_specialist")
        
        for agent_id in unique_agents:
            try:
                agents[agent_id] = cls.get_agent(
                    agent_id=agent_id,
                    session_id=session_id,
                    debug_mode=debug_mode,
                    db_url=db_url
                )
            except Exception as e:
                print(f"⚠️ Failed to load agent {agent_id}: {e}")
                continue
        
        return agents
    
    @classmethod
    def list_available_agents(cls) -> list[str]:
        """Get list of available agent IDs."""
        return list(cls._get_available_agents().keys())
    
    @classmethod
    def register_agent(cls, agent_name: str, module_path: str):
        """
        Register a new agent module.
        
        Args:
            agent_name: Agent name (e.g., 'pagbank')
            module_path: Import path to agent module
        """
        _agent_modules[agent_name] = module_path


# Generic factory function - main entry point
def get_agent(
    name: str,
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None,
    memory: Optional[Any] = None,
    # User context parameters - forwarded to agent factories
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Agent:
    """
    Generic agent factory - main entry point for any agent system.
    
    Args:
        name: Agent name (e.g., 'pagbank', 'adquirencia')
        version: Specific version to load
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        db_url: Database URL override
        
    Returns:
        Configured Agent instance
    """
    return AgentRegistry.get_agent(
        agent_id=name,
        version=version,
        session_id=session_id,
        debug_mode=debug_mode,
        db_url=db_url,
        memory=memory,
        # Forward user context parameters
        user_id=user_id,
        user_name=user_name,
        phone_number=phone_number,
        cpf=cpf,
        **kwargs
    )


# Team convenience function
def get_team_agents(
    agent_names: list[str],
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None,
    memory: Optional[Any] = None,
    # User context parameters - forwarded to agent factories
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> list[Agent]:
    """
    Get multiple agents for team composition.
    
    Args:
        agent_names: List of agent names to load
        session_id: Session ID for conversation tracking
        debug_mode: Enable debug mode
        db_url: Database URL override
        
    Returns:
        List of configured Agent instances
    """
    return [
        get_agent(
            name, 
            session_id=session_id, 
            debug_mode=debug_mode, 
            db_url=db_url, 
            memory=memory,
            # Forward user context parameters
            user_id=user_id,
            user_name=user_name,
            phone_number=phone_number,
            cpf=cpf,
            **kwargs
        )
        for name in agent_names
    ]