# Agent Registry for PagBank V2
# Dynamic agent loading from factory functions

from typing import Dict, Optional
from agno.agent import Agent
import os

# Import all agent factories
try:
    from agents.pagbank.agent import get_pagbank_agent
except ImportError:
    print("⚠️ PagBank agent not found")
    get_pagbank_agent = None

try:
    from agents.adquirencia.agent import get_adquirencia_agent
except ImportError:
    print("⚠️ Adquirência agent not found")
    get_adquirencia_agent = None

try:
    from agents.emissao.agent import get_emissao_agent
except ImportError:
    print("⚠️ Emissão agent not found")
    get_emissao_agent = None

try:
    from agents.human_handoff.agent import get_human_handoff_agent
except ImportError:
    print("⚠️ Human handoff agent not found")
    get_human_handoff_agent = None


class AgentRegistry:
    """
    Registry for managing agent creation and versioning.
    Follows agno-demo-app patterns for dynamic agent loading.
    """
    
    # Agent factory mapping (only include available agents)
    _agent_factories = {}
    
    @classmethod
    def _initialize_factories(cls):
        """Initialize agent factories, only including available ones"""
        if get_pagbank_agent:
            cls._agent_factories["pagbank_specialist"] = get_pagbank_agent
            cls._agent_factories["pagbank"] = get_pagbank_agent
            
        if get_adquirencia_agent:
            cls._agent_factories["adquirencia_specialist"] = get_adquirencia_agent
            cls._agent_factories["adquirencia"] = get_adquirencia_agent
            
        if get_emissao_agent:
            cls._agent_factories["emissao_specialist"] = get_emissao_agent
            cls._agent_factories["emissao"] = get_emissao_agent
            
        if get_human_handoff_agent:
            cls._agent_factories["human_handoff_specialist"] = get_human_handoff_agent
            cls._agent_factories["human_handoff"] = get_human_handoff_agent
    
    @classmethod
    def get_agent(
        cls,
        agent_id: str,
        version: Optional[int] = None,
        session_id: Optional[str] = None,
        debug_mode: bool = False,
        db_url: Optional[str] = None
    ) -> Agent:
        """
        Get agent instance by ID.
        
        Args:
            agent_id: Agent identifier (e.g., 'pagbank_specialist')
            version: Specific version to load
            session_id: Session ID for conversation tracking
            debug_mode: Enable debug mode
            db_url: Database URL override
            
        Returns:
            Configured Agent instance
            
        Raises:
            KeyError: If agent_id not found
        """
        # Initialize factories if not done yet
        if not cls._agent_factories:
            cls._initialize_factories()
            
        if agent_id not in cls._agent_factories:
            available_agents = list(cls._agent_factories.keys())
            raise KeyError(f"Agent '{agent_id}' not found. Available: {available_agents}")
        
        factory = cls._agent_factories[agent_id]
        
        # Use environment database URL if not provided
        if db_url is None:
            db_url = os.getenv("DATABASE_URL")
        
        return factory(
            version=version,
            session_id=session_id,
            debug_mode=debug_mode,
            db_url=db_url
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
        
        # Get the unique agent IDs (remove aliases)
        unique_agents = [
            "pagbank_specialist",
            "adquirencia_specialist", 
            "emissao_specialist",
            "human_handoff_specialist"
        ]
        
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
                # Continue loading other agents
                continue
        
        return agents
    
    @classmethod
    def list_available_agents(cls) -> list[str]:
        """Get list of available agent IDs."""
        return list(cls._agent_factories.keys())
    
    @classmethod
    def register_agent(cls, agent_id: str, factory_function):
        """
        Register a new agent factory function.
        
        Args:
            agent_id: Unique agent identifier
            factory_function: Function that returns Agent instance
        """
        cls._agent_factories[agent_id] = factory_function


# Convenience functions
def get_pagbank_team_agents(
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None
) -> list[Agent]:
    """Get all agents for the PagBank team."""
    return [
        AgentRegistry.get_agent("pagbank_specialist", session_id=session_id, debug_mode=debug_mode, db_url=db_url),
        AgentRegistry.get_agent("adquirencia_specialist", session_id=session_id, debug_mode=debug_mode, db_url=db_url),
        AgentRegistry.get_agent("emissao_specialist", session_id=session_id, debug_mode=debug_mode, db_url=db_url),
        AgentRegistry.get_agent("human_handoff_specialist", session_id=session_id, debug_mode=debug_mode, db_url=db_url),
    ]