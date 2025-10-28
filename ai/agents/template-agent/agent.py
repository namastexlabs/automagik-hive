"""
Template Agent - Foundational agent template for specialized agent development
"""

import yaml
from pathlib import Path
from typing import Any

from agno.agent import Agent

from lib.knowledge import get_agentos_knowledge_base
from lib.config.models import resolve_model
from lib.logging import logger


def get_template_agent(**kwargs) -> Agent:
    """
    Create and return a template agent instance with knowledge base.

    This agent serves as a foundational template for creating
    specialized domain-specific agents with standardized patterns.

    **YAML Configuration**: All settings loaded from config.yaml
    - Model configuration (provider, id, temperature, etc.)
    - Agent metadata (name, description, version)
    - Instructions and behavioral patterns
    - Tool configurations
    - Memory and knowledge settings

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Agent: Configured template agent instance with knowledge

    Note:
        This factory function loads configuration from YAML and properly
        instantiates all components. The AgentRegistry also uses this
        pattern internally via the version factory system.
    """
    # Load configuration from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract sections
    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Get AgentOS-compatible knowledge base (pure Agno Knowledge instance)
    knowledge = get_agentos_knowledge_base(
        num_documents=config.get("knowledge_results", 5),
        csv_path=config.get("csv_file_path", "lib/knowledge/data/knowledge_rag.csv"),
    )

    # Create Model instance from YAML config
    # Extract model_id separately from other config params
    model_id = model_config.pop("id", None)
    model_provider = model_config.pop("provider", None)  # Remove provider from kwargs

    # Resolve model using our resolver (creates proper Agno Model instance)
    model = resolve_model(model_id=model_id, **model_config)

    logger.debug(
        f"📋 Template agent loaded from YAML",
        agent_id=agent_config.get("agent_id"),
        model_id=model_id,
        model_class=type(model).__name__,
    )

    # Build agent parameters from YAML + runtime kwargs
    agent_params = {
        "name": agent_config.get("name"),
        # agent_id removed - not accepted by Agent constructor
        "model": model,  # Proper Model instance
        "knowledge": knowledge,
        "instructions": config.get("instructions"),
        "description": agent_config.get("description"),
        # Add other YAML configs as needed
        **kwargs,  # Runtime overrides
    }

    # Create agent
    agent = Agent(**agent_params)

    # Set agent_id as instance attribute after creation (if needed)
    if agent_config.get("agent_id"):
        agent.agent_id = agent_config.get("agent_id")

    return agent


# Export the agent creation function
__all__ = ["get_template_agent"]
