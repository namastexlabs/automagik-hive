"""
Template Agent - Foundational agent template for specialized agent development
"""

from agno.agent import Agent


def get_template_agent() -> Agent:
    """
    Create and return a template agent instance.

    This agent serves as a foundational template for creating
    specialized domain-specific agents with standardized patterns.

    Returns:
        Agent: Configured template agent instance
    """
    return Agent.from_yaml(__file__.replace("agent.py", "config.yaml"))


# Export the agent creation function
__all__ = ["get_template_agent"]
