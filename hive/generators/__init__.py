"""AI-powered generation system for Hive agents.

Core Components:
- AgentGenerator: Main interface for agent generation
- MetaAgentGenerator: LLM-powered analysis and generation
- GenerationResult: Complete generation output
- AgentConfig: Structured agent configuration

Example:
    from hive.generators import AgentGenerator

    generator = AgentGenerator()
    result = generator.generate(
        name="support-bot",
        description="Customer support bot with knowledge base"
    )
    print(result.yaml_content)
"""

from hive.generators.agent_generator import (
    AgentConfig,
    AgentGenerator,
    GenerationResult,
)
from hive.generators.meta_agent import (
    GenerationError,
    MetaAgentGenerator,
)

__all__ = [
    "AgentGenerator",
    "AgentConfig",
    "GenerationResult",
    "MetaAgentGenerator",
    "GenerationError",
]
