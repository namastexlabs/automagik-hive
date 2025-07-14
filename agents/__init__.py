"""Generic Agents Module - Dynamic agent loading and team composition."""

# Export the main generic factory function
from .registry import get_agent, get_team_agents, AgentRegistry

__all__ = [
    "get_agent",
    "get_team_agents", 
    "AgentRegistry"
]