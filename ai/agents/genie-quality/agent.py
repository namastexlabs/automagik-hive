"""
Genie Quality Agent - Code Quality Domain Specialist

This agent serves as a strategic coordinator for code quality tasks, providing intelligent
analysis and routing to specialized .claude/agents for actual execution.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_quality_agent(**kwargs: Any) -> Agent:
    """
    Create genie quality agent for strategic code quality coordination.

    This factory function creates a domain specialist agent that analyzes code quality
    requirements and routes tasks to appropriate .claude/agents based on strategic analysis.

    Strategic Routing Intelligence:
    - Simple formatting tasks → genie-quality-ruff (.claude/agents)
    - Type safety focused → genie-quality-mypy (.claude/agents)
    - Comprehensive operations → genie-quality-format (.claude/agents)

    Args:
        **kwargs: Context parameters for agent configuration

    Returns:
        Agent instance configured for strategic quality coordination
    """
    return await create_agent("genie_quality", **kwargs)
