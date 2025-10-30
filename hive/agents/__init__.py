"""Agent discovery and registration for Hive V2.

This module discovers and loads agents from hive/examples/agents/
using their factory functions (get_*_agent).
"""

from pathlib import Path
import importlib.util
from typing import List
from agno.agent import Agent


def discover_agents() -> List[Agent]:
    """Discover and load all agents from hive/examples/agents/.

    Scans for agent directories containing:
    - agent.py: Factory function (get_*_agent)
    - config.yaml: Agent configuration

    Returns:
        List[Agent]: Loaded agent instances ready for AgentOS

    Example:
        >>> agents = discover_agents()
        >>> print(f"Found {len(agents)} agents")
        Found 3 agents
    """
    agents = []
    agents_dir = Path(__file__).parent.parent / "examples" / "agents"

    if not agents_dir.exists():
        print(f"⚠️  Agent directory not found: {agents_dir}")
        return agents

    print(f"🔍 Discovering agents in: {agents_dir}")

    for agent_path in agents_dir.iterdir():
        # Skip non-directories and private directories
        if not agent_path.is_dir() or agent_path.name.startswith("_"):
            continue

        factory_file = agent_path / "agent.py"
        if not factory_file.exists():
            print(f"  ⏭️  Skipping {agent_path.name} (no agent.py)")
            continue

        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(
                f"hive.agents.{agent_path.name}",
                factory_file
            )
            if spec is None or spec.loader is None:
                print(f"  ❌ Failed to load spec for {agent_path.name}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find factory function (get_*_agent)
            factory_found = False
            for name in dir(module):
                if name.startswith("get_") and name.endswith("_agent"):
                    factory = getattr(module, name)
                    agent = factory()
                    agents.append(agent)
                    print(f"  ✅ Loaded agent: {agent.name} (id: {agent.agent_id})")
                    factory_found = True
                    break

            if not factory_found:
                print(f"  ⚠️  No factory function found in {agent_path.name}/agent.py")

        except Exception as e:
            print(f"  ❌ Failed to load agent from {agent_path.name}: {e}")
            continue

    print(f"\n🎯 Total agents loaded: {len(agents)}")
    return agents


def get_agent_by_id(agent_id: str, agents: List[Agent]) -> Agent | None:
    """Get agent by ID from list of agents.

    Args:
        agent_id: Agent identifier
        agents: List of loaded agents

    Returns:
        Agent if found, None otherwise
    """
    for agent in agents:
        if agent.agent_id == agent_id:
            return agent
    return None
