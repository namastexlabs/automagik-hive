"""
Genie Architect Agent - Master Design Meeseeks

This agent provides enterprise-grade architectural solutions for the Automagik Hive
ecosystem with enhanced memory and state management for persistent architectural intelligence.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_architect_agent(**kwargs: Any) -> Agent:
    """
    Create genie architect agent with enhanced memory and state management.

    This factory function creates a masterful architectural MEESEEKS with
    persistent intelligence capabilities including:

    - 30-run memory for pattern recognition and design evolution
    - 180-day retention for long-term architectural context
    - Enhanced state management for tracking architectural decisions
    - Memory-driven architecture process for consistent design evolution
    - Persistent storage of architectural patterns and design rationale

    The agent integrates with:
    - genie-memory: For persistent architectural pattern storage
    - automagik-forge: For project and task management
    - postgres: For architecture analysis and state persistence

    Args:
        **kwargs: Context parameters for architectural operations including:
            - user_id: User identifier for architectural context
            - project_context: Current project architectural requirements
            - feature_requirements: Specific functionality to be architected
            - architectural_constraints: System limitations and requirements
            - integration_points: External systems requiring integration
            - scalability_requirements: Performance and scaling needs
            - security_requirements: Security and compliance considerations
            - technology_stack: Preferred technologies and frameworks
            - deployment_environment: Target deployment context
            - legacy_system_context: Existing systems requiring integration
            - enterprise_standards: Organization-specific architectural standards
            - custom_context: Additional architectural parameters

    Returns:
        Agent instance configured for enterprise architectural design with
        enhanced memory and persistent state management capabilities

    Example Usage:
        # Basic architectural guidance
        agent = await get_genie_architect_agent(
            project_context="multi-agent collaboration system",
            feature_requirements="agent-to-agent workflow passing"
        )

        # Complex enterprise architecture
        agent = await get_genie_architect_agent(
            project_context="enterprise AI platform",
            feature_requirements="real-time agent orchestration",
            architectural_constraints=["microservices", "event-driven"],
            scalability_requirements="10000+ concurrent agents",
            security_requirements=["SOC2", "enterprise SSO"],
            technology_stack=["agno", "fastapi", "postgresql", "redis"],
            deployment_environment="kubernetes",
            enterprise_standards=["clean_architecture", "solid_principles"],
            custom_context={
                "integration_apis": ["salesforce", "slack", "jira"],
                "compliance_requirements": ["GDPR", "CCPA"],
                "performance_targets": "sub-100ms response time"
            }
        )

        # Legacy system modernization
        agent = await get_genie_architect_agent(
            project_context="legacy system modernization",
            feature_requirements="gradual migration to microservices",
            legacy_system_context={
                "current_architecture": "monolithic django app",
                "database": "mysql with complex schema",
                "integrations": ["legacy ERP", "mainframe systems"]
            },
            migration_strategy="strangler fig pattern"
        )
    """
    return await create_agent("genie_architect", **kwargs)