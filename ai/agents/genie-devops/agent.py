"""
Genie DevOps Agent - DevOps Domain Specialist

This agent serves as a strategic coordinator for DevOps tasks, providing intelligent
analysis and routing to specialized .claude/agents for actual execution.
"""

from typing import Any

from agno.agent import Agent

from lib.utils.version_factory import create_agent


async def get_genie_devops_agent(**kwargs: Any) -> Agent:
    """
    Create genie devops agent for strategic DevOps coordination.

    This factory function creates a domain specialist agent that analyzes DevOps
    requirements and routes tasks to appropriate .claude/agents based on strategic analysis.

    Strategic Routing Intelligence:
    - Pre-commit automation → genie-devops-precommit (.claude/agents)
    - CI/CD pipeline tasks → genie-devops-cicd (.claude/agents)  
    - Configuration management → genie-devops-config (.claude/agents)
    - Infrastructure automation → genie-devops-infra (.claude/agents)
    - Task runner automation → genie-devops-tasks (.claude/agents)

    Args:
        **kwargs: Context parameters for agent configuration

    Returns:
        Agent instance configured for strategic DevOps coordination
    """
    return await create_agent("genie_devops", **kwargs)
EOF < /dev/null
