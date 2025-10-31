"""
Researcher Agent

Generated using Automagik Hive meta-agent generator.
"""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.file import FileTools
from agno.tools.python import PythonTools


def get_researcher_agent(**kwargs) -> Agent:
    """Create researcher agent with YAML configuration.

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Agent: Configured agent instance
    """
    # Load YAML configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract config sections
    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Create Model instance
    model = OpenAIChat(id=model_config.get("id"), temperature=model_config.get("temperature", 0.7))

    # Prepare tools
    tools = [PythonTools(), FileTools()]

    # Build agent parameters
    agent_params = {
        "name": agent_config.get("name"),
        "model": model,
        "instructions": config.get("instructions"),
        "description": agent_config.get("description"),
        "tools": tools if tools else None,
        **kwargs,
    }

    # Create agent
    agent = Agent(**agent_params)

    # Set agent id as instance attribute (NOT in constructor)
    if agent_config.get("id"):
        agent.id = agent_config.get("id")

    return agent


# Quick test function
if __name__ == "__main__":
    print("Testing researcher agent...")

    agent = get_researcher_agent()
    print(f"✅ Agent created: {agent.name}")
    print(f"✅ Model: {agent.model.id}")
    print(f"✅ Agent ID: {agent.id}")

    # Test with a simple query
    response = agent.run("Hello, what can you help me with?")
    print(f"\n📝 Response:\n{response.content}")
