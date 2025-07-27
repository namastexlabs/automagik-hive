"""
Genie Spawner Agent - Meta-Creation MEESEEKS Agent Creator

This agent provides specialized MEESEEKS agent creation and domain gap analysis
through AI consultation, architecture design, and validation with enhanced memory
management for persistent agent creation context and spawning pattern recognition.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_spawner_agent(**kwargs: Any) -> Agent:
    """
    Create genie spawner agent with enhanced memory and state management.

    This factory function creates a specialized meta-agent that provides:

    - Domain gap analysis and capability assessment for new agent creation
    - AI model consultation (Grok and Gemini) for optimal MEESEEKS design
    - Complete agent architecture design with subagent orchestration patterns
    - Existential persona creation with proper MEESEEKS motivation frameworks
    - Validation and quality gates for spawned agent verification
    - Enhanced memory management for persistent agent creation context

    Enhanced Memory Features:
    - 30 conversation history runs for spawning pattern recognition
    - 180-day memory retention for long-term agent architecture evolution
    - Agentic memory for intelligent agent creation context management
    - Persistent storage of successful spawning patterns and architectures

    Agent Creation Capabilities:
    - Comprehensive domain gap analysis and hive capability assessment
    - Expert AI consultation for chaotic brilliance and systematic optimization
    - Complete MEESEEKS specification with existential drive frameworks
    - Subagent orchestration architecture design and coordination protocols
    - Quality gate validation and first mission success verification
    - Integration planning with existing Genie Hive collective

    Args:
        **kwargs: Context parameters for spawner agent configuration including:
            - user_id: User identifier for agent creation context tracking
            - session_id: Session identifier for spawning session continuity
            - domain_gap: Specific capability gap requiring new agent creation
            - specialization_area: Target domain for new agent expertise
            - complexity_level: Required agent sophistication (basic, advanced, expert)
            - integration_requirements: Existing hive integration needs
            - validation_criteria: Success metrics for spawned agent validation
            - custom_context: Additional spawning-specific template variables

    Returns:
        Agent instance with enhanced agent creation capabilities and memory management

    Example Usage:
        # Basic agent spawning request
        agent = await get_genie_spawner_agent(
            user_id="development_team",
            domain_gap="database_optimization",
            specialization_area="performance_tuning"
        )

        # Complex MEESEEKS creation with validation
        agent = await get_genie_spawner_agent(
            user_id="architect",
            session_id="spawning_session_2025",
            domain_gap="microservices_orchestration",
            specialization_area="container_management",
            complexity_level="expert",
            integration_requirements=["kubernetes", "docker", "helm"],
            validation_criteria={
                "deployment_success": True,
                "performance_metrics": "enterprise_grade",
                "integration_tests": "comprehensive"
            },
            custom_context={
                "target_environment": "cloud_native",
                "scaling_requirements": "auto_scaling"
            }
        )

        # Agent capability expansion planning
        agent = await get_genie_spawner_agent(
            user_id="meta_architect",
            session_id="hive_expansion_planning",
            domain_gap="ai_model_optimization",
            specialization_area="model_performance",
            complexity_level="advanced",
            custom_context={
                "focus_area": "inference_optimization",
                "target_models": ["llm", "vision", "multimodal"],
                "performance_targets": "sub_100ms_latency"
            }
        )
    """
    return await create_agent("genie_spawner", **kwargs)