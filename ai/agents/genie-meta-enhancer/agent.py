"""
Genie Meta-Enhancer - Agent enhancement and optimization specialist
"""

from typing import List
from agno import Agent

def get_genie_meta_enhancer() -> Agent:
    """
    Create and return a genie meta-enhancer agent instance.
    
    This agent specializes in systematically improving and optimizing
    .claude/agents through targeted enhancements, pattern improvements,
    and capability upgrades.
    
    Returns:
        Agent: Configured genie meta-enhancer agent instance
    """
    return Agent.from_yaml(__file__.replace("agent.py", "config.yaml"))

# Export the agent creation function
__all__ = ["get_genie_meta_enhancer"]