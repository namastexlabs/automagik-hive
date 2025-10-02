"""
Template Agent - Foundational agent template for specialized agent development
"""

from agno.agent import Agent

from lib.knowledge import get_knowledge_base


def get_template_agent(**kwargs) -> Agent:
    """
    Create and return a template agent instance with knowledge base.

    This agent serves as a foundational template for creating
    specialized domain-specific agents with standardized patterns.
    Includes knowledge base integration for AgentOS discovery.

    Returns:
        Agent: Configured template agent instance with knowledge
    """
    # Get shared knowledge base (thread-safe singleton)
    # This makes the agent visible in AgentOS Knowledge screen
    knowledge = get_knowledge_base(
        num_documents=5,  # Number of relevant documents to retrieve
        csv_path="lib/knowledge/data/knowledge_rag.csv",
    )

    # Pass knowledge directly to Agent initialization (not via YAML)
    # This ensures proper object type instead of dict from YAML parsing
    agent = Agent.from_yaml(
        __file__.replace("agent.py", "config.yaml"), knowledge=knowledge, **kwargs
    )

    return agent


# Export the agent creation function
__all__ = ["get_template_agent"]
