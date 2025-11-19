"""
Development Team

Collaborative development team with planner, coder, and reviewer specialists.
Hybrid approach: manually create member agents, use ConfigGenerator for team storage.
"""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team

from hive.scaffolder.generator import ConfigGenerator


def get_dev_team(**kwargs) -> Team:
    """Create collaborative development team.

    This factory creates member agents inline and uses ConfigGenerator
    for storage configuration and team setup.

    The team includes:
    - Planner: Analyzes requirements and creates implementation plans
    - Coder: Implements features following best practices
    - Reviewer: Validates quality and provides feedback

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Team: Fully configured collaborative team instance with storage support
    """
    # Load config for model and storage settings
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    team_config = config.get("team", {})
    model_string = config.get("model")

    # Parse model using ConfigGenerator
    model = ConfigGenerator._parse_model(model_string)

    # Setup storage using ConfigGenerator
    db = ConfigGenerator._setup_storage(config.get("storage"))

    # Create team member agents
    planner = Agent(
        name="Planner",
        model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
        instructions="""You are a technical planner and architect.

        Your responsibilities:
        - Analyze feature requirements and user stories
        - Break down work into actionable implementation tasks
        - Identify dependencies, risks, and edge cases
        - Suggest appropriate architecture and design patterns
        - Create clear, detailed implementation plans

        Provide:
        - Clear task breakdown with priorities
        - Technical approach recommendations
        - Testing strategy suggestions
        - Potential risks and mitigation strategies

        Be thorough, pragmatic, and focus on delivering quality solutions.""",
        description="Analyzes requirements and creates implementation plans",
    )
    planner.agent_id = "planner"

    coder = Agent(
        name="Coder",
        model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
        instructions="""You are an expert software developer.

        Your responsibilities:
        - Implement features following the plan
        - Write clean, maintainable, well-documented code
        - Follow best practices and coding standards
        - Implement comprehensive tests (unit, integration)
        - Handle edge cases and error conditions

        Code quality standards:
        - Clear variable and function names
        - Proper error handling and validation
        - Comprehensive docstrings and comments
        - Test coverage for critical paths
        - Security and performance considerations

        Work collaboratively with the planner and respond to reviewer feedback.""",
        description="Implements features following best practices",
    )
    coder.agent_id = "coder"

    reviewer = Agent(
        name="Reviewer",
        model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
        instructions="""You are a code quality reviewer.

        Your responsibilities:
        - Review code for correctness and clarity
        - Validate test coverage and quality
        - Check for security vulnerabilities
        - Ensure performance and scalability
        - Provide constructive, actionable feedback

        Review checklist:
        - Code follows requirements and plan
        - Tests are comprehensive and pass
        - Error handling is robust
        - Documentation is clear and complete
        - No security or performance issues
        - Code is maintainable and follows standards

        Be constructive, specific, and focus on improving quality.
        Acknowledge what's done well, suggest concrete improvements.""",
        description="Reviews code quality and provides feedback",
    )
    reviewer.agent_id = "reviewer"

    # Create collaborative team with storage
    team = Team(
        name=team_config.get("name"),
        members=[planner, coder, reviewer],
        model=model,
        instructions=config.get("instructions"),
        description=team_config.get("description"),
        db=db,  # Storage configured from YAML
        **kwargs,
    )

    # Set team_id and mode as attributes
    if team_config.get("team_id"):
        team.team_id = team_config.get("team_id")
    if team_config.get("mode"):
        team.mode = team_config.get("mode")

    return team


# Quick test function
if __name__ == "__main__":
    print("Testing dev-team...")

    team = get_dev_team()
    print(f"✅ Team created: {team.name}")
    print(f"✅ Model: {team.model.id if team.model else 'Default'}")
    print(f"✅ Members: {len(team.members)}")
    print(f"✅ Database: {'Enabled' if team.db else 'Disabled'}")

    # Test with a development task
    response = team.run("Create a function to validate email addresses with comprehensive tests")
    print(f"\n📝 Response:\n{response.content}")
