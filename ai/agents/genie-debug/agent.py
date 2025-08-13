"""
Genie Debug Agent - Specialized debugging agent for systematic issue investigation
"""

from agno.agent import Agent


def get_genie_debug_agent() -> Agent:
    """
    Create and return a genie debug agent instance.

    This agent specializes in systematic debugging, root cause analysis,
    and comprehensive problem resolution with database-driven investigation.

    Returns:
        Agent: Configured genie debug agent instance
    """
    return Agent.from_yaml(__file__.replace("agent.py", "config.yaml"))


# Export the agent creation function
__all__ = ["get_genie_debug_agent"]