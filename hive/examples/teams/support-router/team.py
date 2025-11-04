"""Support Router team factory."""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team


def get_support_router_team(**kwargs) -> Team:
    """
    Create support router team with specialist agents.

    This is a routing team that automatically directs queries to the right specialist:
    - Billing specialist for payment-related questions
    - Technical specialist for technical issues
    - Sales specialist for sales inquiries

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Team: Configured routing team instance
    """
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    team_config = config.get("team", {})
    model_config = config.get("model", {})

    # Create model for the team
    model = OpenAIChat(
        id=model_config.get("id", "gpt-4o-mini"),
        temperature=model_config.get("temperature", 0.7),
    )

    # Create specialist agents
    billing_specialist = Agent(
        name="Billing Specialist",
        model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
        instructions="""You are a billing specialist.

        You handle:
        - Payment processing and issues
        - Invoice questions and disputes
        - Refund requests and policies
        - Subscription and pricing questions

        Be clear, professional, and resolve billing issues efficiently.""",
        description="Handles all billing and payment inquiries",
    )
    billing_specialist.agent_id = "billing-specialist"

    technical_specialist = Agent(
        name="Technical Specialist",
        model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
        instructions="""You are a technical support specialist.

        You handle:
        - Bug reports and error messages
        - Integration and API issues
        - Performance and optimization
        - Configuration and setup problems

        Be technical yet clear, provide actionable solutions and workarounds.""",
        description="Handles technical support and troubleshooting",
    )
    technical_specialist.agent_id = "technical-specialist"

    sales_specialist = Agent(
        name="Sales Specialist",
        model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
        instructions="""You are a sales specialist.

        You handle:
        - Product features and capabilities
        - Pricing and plan comparisons
        - Demo requests and trials
        - Upgrade and expansion opportunities

        Be consultative, understand needs, and provide value-focused solutions.""",
        description="Handles sales inquiries and product questions",
    )
    sales_specialist.agent_id = "sales-specialist"

    # Create routing team
    # Note: Agno Team uses 'role' for coordination behavior, not 'mode'
    team = Team(
        name=team_config.get("name"),
        role="You are an intelligent routing coordinator that directs queries to the right specialist.",
        members=[billing_specialist, technical_specialist, sales_specialist],
        model=model,
        instructions=config.get("instructions"),
        description=team_config.get("description"),
        **kwargs,
    )

    # Set team_id and mode as attributes
    if team_config.get("team_id"):
        team.team_id = team_config.get("team_id")
    if team_config.get("mode"):
        team.mode = team_config.get("mode")  # Store mode as metadata

    return team
