# Generic Agent Registry for Multi-Agent Systems
# Dynamic agent loading from factory functions

from typing import Dict, Optional, Any
from agno.agent import Agent
import os
from common.version_factory import create_versioned_agent
from core.mcp.catalog import MCPCatalog

_agent_modules = {
    "pagbank": "ai.agents.pagbank.agent",
    "adquirencia": "ai.agents.adquirencia.agent", 
    "emissao": "ai.agents.emissao.agent",
    "human-handoff": "ai.agents.human_handoff.agent",
    "finalizacao": "ai.agents.finalizacao.agent"
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
        # Normalize hyphens to underscores for factory function names
        safe_name = agent_name.replace('-', '_')
        factory = getattr(module, f"get_{safe_name}_agent")
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
    Includes MCP (Model Context Protocol) integration.
    """
    
    _mcp_catalog = None
    
    @classmethod
    def get_mcp_catalog(cls) -> MCPCatalog:
        """Get or create MCP catalog instance."""
        if cls._mcp_catalog is None:
            cls._mcp_catalog = MCPCatalog()
        return cls._mcp_catalog
    
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
        user_id: Optional[str] = None,  # Agno native parameter
        pb_phone_number: Optional[str] = None,  # PagBank business parameter
        pb_cpf: Optional[str] = None  # PagBank business parameter
    ) -> Agent:
        """
        Get agent instance by ID - Generic factory pattern with versioning support.
        
        Args:
            agent_id: Agent identifier (e.g., 'pagbank', 'adquirencia')
            version: Specific version to load
            session_id: Session ID for conversation tracking
            debug_mode: Enable debug mode
            db_url: Database URL override
            user_id: Agno native user identifier for shared team context
            pb_phone_number: PagBank business parameter - phone number
            pb_cpf: PagBank business parameter - CPF document
            
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
                user_id=user_id,
                pb_phone_number=pb_phone_number,
                pb_cpf=pb_cpf
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
                user_id=user_id,
                pb_phone_number=pb_phone_number,
                pb_cpf=pb_cpf
            )
    
    @classmethod
    def get_all_agents(
        cls,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None,
        memory: Optional[Any] = None
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
                    db_url=db_url,
                    memory=memory
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
    
    @classmethod
    def list_mcp_servers(cls) -> list[str]:
        """List all available MCP servers."""
        return cls.get_mcp_catalog().list_servers()
    
    @classmethod
    def get_mcp_server_info(cls, server_name: str) -> Dict[str, Any]:
        """Get information about an MCP server."""
        return cls.get_mcp_catalog().get_server_info(server_name)
    
    @classmethod
    def reload_mcp_catalog(cls) -> None:
        """Reload the MCP catalog from configuration."""
        cls._mcp_catalog = None  # Force reload on next access


# Generic factory function - main entry point
def get_agent(
    name: str,
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None,
    memory: Optional[Any] = None,
    user_id: Optional[str] = None,  # Agno native parameter
    pb_user_name: Optional[str] = None,  # PagBank business parameter
    pb_phone_number: Optional[str] = None,  # PagBank business parameter
    pb_cpf: Optional[str] = None  # PagBank business parameter
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
        user_id=user_id,
        pb_user_name=pb_user_name,
        pb_phone_number=pb_phone_number,
        pb_cpf=pb_cpf
    )


# Team convenience function
def get_team_agents(
    agent_names: list[str],
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None,
    memory: Optional[Any] = None,
    user_id: Optional[str] = None,  # Agno native parameter
    pb_user_name: Optional[str] = None,  # PagBank business parameter
    pb_phone_number: Optional[str] = None,  # PagBank business parameter
    pb_cpf: Optional[str] = None  # PagBank business parameter
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
            user_id=user_id,
            pb_user_name=pb_user_name,
            pb_phone_number=pb_phone_number,
            pb_cpf=pb_cpf
        )
        for name in agent_names
    ]


# MCP convenience functions
def list_mcp_servers() -> list[str]:
    """List all available MCP servers."""
    return AgentRegistry.list_mcp_servers()


def get_mcp_server_info(server_name: str) -> Dict[str, Any]:
    """Get information about an MCP server."""
    return AgentRegistry.get_mcp_server_info(server_name)


def reload_mcp_catalog() -> None:
    """Reload the MCP catalog from configuration."""
    AgentRegistry.reload_mcp_catalog()