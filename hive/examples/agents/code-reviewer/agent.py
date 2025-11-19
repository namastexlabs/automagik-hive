"""
Code Reviewer Agent

Expert code quality reviewer providing constructive feedback and security analysis.
Uses ConfigGenerator for consistent YAML-driven configuration with automatic storage support.
"""

from pathlib import Path

from agno.agent import Agent

from hive.scaffolder.generator import generate_agent_from_yaml


def get_code_reviewer_agent(**kwargs) -> Agent:
    """Create code-reviewer agent with YAML configuration.

    This factory uses ConfigGenerator to automatically handle:
    - Model initialization from YAML config
    - Tool loading (builtin and custom)
    - Knowledge base setup
    - Database storage (if configured in YAML)
    - All runtime settings

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Agent: Fully configured agent instance with storage support
    """
    config_path = Path(__file__).parent / "config.yaml"
    return generate_agent_from_yaml(str(config_path), **kwargs)


# Quick test function
if __name__ == "__main__":
    print("Testing code-reviewer agent...")

    agent = get_code_reviewer_agent()
    print(f"✅ Agent created: {agent.name}")
    print(f"✅ Model: {agent.model.id}")
    print(f"✅ Agent ID: {agent.id}")
    print(f"✅ Database: {'Enabled' if agent.db else 'Disabled'}")

    # Test with a code review query
    response = agent.run("Review this function for security issues: def process_user_input(data): exec(data)")
    print(f"\n📝 Response:\n{response.content}")
