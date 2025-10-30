"""Support Bot agent factory."""

import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_support_bot(**kwargs) -> Agent:
    """Create support bot agent."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Create model
    model = OpenAIChat(
        id=model_config.get("id", "gpt-4o-mini"),
        temperature=model_config.get("temperature", 0.7),
    )

    # Create agent
    agent = Agent(
        name=agent_config.get("name"),
        model=model,
        instructions=config.get("instructions"),
        description=agent_config.get("description"),
        **kwargs
    )

    # Set agent_id
    if agent_config.get("agent_id"):
        agent.agent_id = agent_config.get("agent_id")

    return agent
