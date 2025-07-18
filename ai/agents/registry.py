# Generic Agent Registry for Multi-Agent Systems
# Database-driven agent loading via version factory

from typing import Dict, Optional, Any
from agno.agent import Agent
import os
from pathlib import Path
from lib.utils.version_factory import create_versioned_agent
from lib.mcp.catalog import MCPCatalog


def _discover_agents() -> list[str]:
    """Dynamically discover available agents from filesystem"""
    import yaml
    
    agents_dir = Path("ai/agents")
    if not agents_dir.exists():
        return []
    
    agent_ids = []
    for agent_path in agents_dir.iterdir():
        config_file = agent_path / "config.yaml"
        if agent_path.is_dir() and config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    agent_id = config.get('agent', {}).get('agent_id')
                    if agent_id:
                        agent_ids.append(agent_id)
            except Exception as e:
                print(f"⚠️ Failed to load agent config {agent_path.name}: {e}")
                continue
    
    return sorted(agent_ids)


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
    def _get_available_agents(cls) -> list[str]:
        """Get all available agent IDs"""
        return _discover_agents()
    
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
        # Database-driven agent creation
        available_agents = cls._get_available_agents()
        
        if agent_id not in available_agents:
            raise KeyError(f"Agent '{agent_id}' not found. Available: {available_agents}")
        
        return create_versioned_agent(
            agent_id=agent_id,
            version=version,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=user_id,
            phone_number=pb_phone_number,
            cpf=pb_cpf
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
        available_agents = cls._get_available_agents()
        
        for agent_id in available_agents:
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
        return cls._get_available_agents()
    
    
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