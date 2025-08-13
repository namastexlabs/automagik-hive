"""
Genie Dev Agent - Development Domain Specialist

This agent provides intelligent routing and coordination for development tasks within
the Automagik Hive ecosystem, delegating to specialized .claude/agents for focused execution.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_dev_agent(**kwargs: Any) -> Agent:
    """
    Create genie dev agent with intelligent development task routing.

    This factory function creates a development domain specialist that analyzes
    development requests and routes them to appropriate .claude/agents:

    - 30-run memory for development pattern recognition and task evolution
    - 180-day retention for long-term development context
    - Enhanced state management for tracking development workflows
    - Memory-driven development process for consistent task execution
    - Intelligent routing to specialized .claude/agents for heavy lifting

    The agent routes to these specialized .claude/agents:
    - genie-dev-planner: Requirements analysis and technical specifications
    - genie-dev-designer: System architecture and design decisions
    - genie-dev-coder: Code implementation and feature development
    - genie-dev-fixer: Debugging, error resolution, and issue fixes

    The agent integrates with:
    - claude-mcp: For spawning and coordinating .claude/agents
    - postgres: For development analytics and state persistence

    Args:
        **kwargs: Context parameters for development operations including:
            - user_id: User identifier for development context
            - project_context: Current project development requirements
            - task_type: Type of development task (planning, design, coding, fixing)
            - feature_requirements: Specific functionality to be developed
            - technical_constraints: System limitations and requirements
            - code_quality_standards: Quality and style requirements
            - testing_requirements: Test coverage and validation needs
            - deployment_requirements: Deployment and CI/CD considerations
            - legacy_code_context: Existing codebase requiring integration
            - development_methodology: Agile, TDD, or other approaches
            - performance_requirements: Performance and optimization needs
            - custom_context: Additional development parameters

    Returns:
        Agent instance configured for development task routing with
        comprehensive memory and intelligent delegation capabilities

    Example Usage:
        # Requirements analysis and planning
        agent = await get_genie_dev_agent(
            project_context="multi-agent collaboration system",
            task_type="planning",
            feature_requirements="agent-to-agent workflow passing"
        )

        # System design and architecture
        agent = await get_genie_dev_agent(
            project_context="enterprise AI platform",
            task_type="design",
            feature_requirements="real-time agent orchestration",
            technical_constraints=["microservices", "event-driven"],
            performance_requirements="sub-100ms response time"
        )

        # Feature implementation
        agent = await get_genie_dev_agent(
            project_context="authentication system",
            task_type="coding",
            feature_requirements="OAuth2 integration with JWT tokens",
            code_quality_standards=["clean_code", "solid_principles"],
            testing_requirements="unit tests with 90% coverage"
        )

        # Bug fixing and debugging
        agent = await get_genie_dev_agent(
            project_context="payment processing service",
            task_type="fixing",
            issue_description="intermittent timeout errors in payment flow",
            legacy_code_context={
                "framework": "fastapi with sqlalchemy",
                "database": "postgresql with complex queries",
                "integrations": ["stripe", "paypal", "bank APIs"]
            }
        )

        # Complex development workflow
        agent = await get_genie_dev_agent(
            project_context="microservices modernization",
            task_type="comprehensive",
            feature_requirements="gradual migration from monolith",
            development_methodology="agile with CI/CD",
            custom_context={
                "migration_strategy": "strangler fig pattern",
                "rollback_requirements": "zero-downtime deployments",
                "monitoring_needs": ["observability", "distributed tracing"]
            }
        )
    """
    return await create_agent("genie_dev", **kwargs)
