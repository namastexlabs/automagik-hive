"""
Template Agent - Foundational agent template for specialized agent development

IMPORTANT: This agent uses the standard registry/proxy system for creation.
Do NOT implement custom factory functions that bypass AgnoAgentProxy.

The agent is created automatically via:
  AgentRegistry.get_agent("template-agent")
    → create_agent() (version_factory.py)
      → VersionFactory._create_agent()
        → AgnoAgentProxy.create_agent()
          → Agent(**filtered_params)

Configuration is loaded from config.yaml and processed through the proxy system
which handles:
  - Knowledge base attachment (via enable_knowledge: true in config)
  - Memory configuration (via memory: section in config)
  - Storage/database setup (via db: section in config)
  - Model resolution (via model: section in config)
  - All Agno-native parameters

USAGE:
  from ai.agents.registry import AgentRegistry

  agent = await AgentRegistry.get_agent("template-agent", session_id="...")
  response = await agent.arun(input="Hello", session_id="...")

DO NOT create custom factory functions in this file - they will be ignored
by the registry system and can cause message storage bugs.
"""

# This file intentionally left minimal - agent creation handled by registry/proxy
# No custom factory function needed - the registry auto-discovers from config.yaml

__all__ = []  # No exports - agent created via registry
