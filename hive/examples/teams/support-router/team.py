"""
Support Router Team

Intelligent routing team that directs queries to specialist agents.
Hybrid approach: manually create member agents, use ConfigGenerator for team storage.
"""

from pathlib import Path

import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team

from hive.scaffolder.generator import ConfigGenerator


def get_support_router_team(**kwargs) -> Team:
    """Create support router team with specialist agents.

    This factory creates member agents inline and uses ConfigGenerator
    for storage configuration and team setup.

    The team includes specialist agents for:
    - Billing: Payment processing, invoices, refunds, subscriptions
    - Technical: Bug reports, API issues, performance, configuration
    - Sales: Product features, pricing, demos, upgrades

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Team: Fully configured routing team instance with storage support
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

    # Create routing team with storage
    team = Team(
        name=team_config.get("name"),
        members=[billing_specialist, technical_specialist, sales_specialist],
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
    print("Testing support-router team...")

    team = get_support_router_team()
    print(f"✅ Team created: {team.name}")
    print(f"✅ Model: {team.model.id if team.model else 'Default'}")
    print(f"✅ Members: {len(team.members)}")
    print(f"✅ Database: {'Enabled' if team.db else 'Disabled'}")

    # Test with a support query
    response = team.run("I need help with a failed payment on my recent invoice")
    print(f"\n📝 Response:\n{response.content}")
