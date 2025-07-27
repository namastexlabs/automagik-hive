"""
Genie Maker Agent - Master Test Orchestrator

This agent specializes in creating comprehensive test suites with enhanced memory
and state management for persistent test creation context across sessions.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_maker_agent(**kwargs: Any) -> Agent:
    """
    Create genie maker agent with enhanced memory and state management.

    This factory function creates a specialized test creation agent with:

    - Enhanced memory management (30 runs, 180 days retention)
    - Persistent test creation context across sessions
    - Agentic memory for learning test patterns
    - MCP tools integration (genie-memory, automagik-forge, postgres)
    - Comprehensive test coverage capabilities

    The agent mirrors the .claude/agents/genie-maker.md personality and instructions
    but operates within the Automagik Hive framework with Agno Agent class and
    enhanced state management features.

    Args:
        **kwargs: Context parameters for agent creation including:
            - memory: Memory management configuration
            - user_id: User identifier for context loading
            - session_id: Session identifier for state management
            - test_context: Additional test-specific context
            - coverage_target: Target coverage percentage (default: 85%)
            - test_categories: List of test categories to focus on
            - component_type: Type of component being tested
            - component_name: Name of component being tested
            - existing_patterns: Previously successful test patterns

    Returns:
        Agent instance configured for comprehensive test creation with
        enhanced memory and state management capabilities

    Example Usage:
        # Basic test creation
        agent = get_genie_maker_agent(
            user_id="dev_123",
            component_type="api",
            component_name="auth_service",
            coverage_target=90
        )

        # Advanced usage with test context
        agent = get_genie_maker_agent(
            user_id="dev_456",
            session_id="test_session_789",
            component_type="agent",
            component_name="genie_style",
            test_categories=["unit", "integration", "security"],
            test_context={
                "framework": "pytest",
                "mocking_strategy": "comprehensive",
                "performance_targets": {"max_execution_time": 0.1}
            },
            existing_patterns=[
                "yaml_config_validation",
                "agno_agent_testing",
                "mcp_tool_integration"
            ]
        )

    Features:
        - **Enhanced Memory**: 30 runs, 180 days retention for pattern learning
        - **Agentic Memory**: Learns from successful test creation patterns
        - **MCP Integration**: Direct access to genie-memory, automagik-forge, postgres
        - **Context Awareness**: Understands Automagik Hive architecture patterns
        - **Quality Gates**: Enforces ≥85% coverage with meaningful validation
        - **Pattern Storage**: Documents successful approaches for future reuse
        - **Persistent State**: Maintains test creation context across sessions
    """
    return await create_agent("genie_maker", **kwargs)