"""Agent discovery and registration for Hive V2.

This module discovers and loads agents from:
1. Project directory (ai/agents/) if hive.yaml exists
2. Package examples (hive/examples/agents/) as fallback
"""

import importlib.util
from pathlib import Path

import yaml
from agno.agent import Agent


def _find_project_root() -> Path | None:
    """Find project root by locating hive.yaml.

    Searches upward from current directory.
    Returns None if not in a Hive project.
    """
    current = Path.cwd()

    # Try current directory and up to 5 levels up
    for _ in range(5):
        if (current / "hive.yaml").exists():
            return current
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent

    return None


def discover_agents() -> list[Agent]:
    """Discover and load agents from project or package.

    Discovery order:
    1. If hive.yaml exists: use discovery_path from config
    2. Otherwise: use package examples (hive/examples/agents/)

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
    agents: list[Agent] = []

    # Try to find project root with hive.yaml
    project_root = _find_project_root()

    if project_root:
        # User project mode - use discovery_path from hive.yaml
        config_path = project_root / "hive.yaml"
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            discovery_path = config.get("agents", {}).get("discovery_path", "ai/agents")
            agents_dir = project_root / discovery_path
            print(f"🔍 Discovering agents in project: {agents_dir}")
        except Exception as e:
            print(f"⚠️  Failed to load hive.yaml: {e}")
            return agents
    else:
        # Package mode - use builtin examples
        agents_dir = Path(__file__).parent / "examples" / "agents"
        print(f"🔍 Discovering agents in package: {agents_dir}")

    if not agents_dir.exists():
        print(f"⚠️  Agent directory not found: {agents_dir}")
        return agents

    # Directories to scan: main dir + examples subdir if it exists
    dirs_to_scan = [agents_dir]
    examples_dir = agents_dir / "examples"
    if examples_dir.exists():
        dirs_to_scan.append(examples_dir)
        print(f"  📂 Also scanning examples: {examples_dir}")

    for scan_dir in dirs_to_scan:
        for agent_path in scan_dir.iterdir():
            # Skip non-directories and private directories
            if not agent_path.is_dir() or agent_path.name.startswith("_"):
                continue

            # Skip "examples" directory itself (not its contents)
            if agent_path.name == "examples":
                continue

            factory_file = agent_path / "agent.py"
            if not factory_file.exists():
                print(f"  ⏭️  Skipping {agent_path.name} (no agent.py)")
                continue

            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(f"hive.agents.{agent_path.name}", factory_file)
                if spec is None or spec.loader is None:
                    print(f"  ❌ Failed to load spec for {agent_path.name}")
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find factory function (get_*)
                factory_found = False
                for name in dir(module):
                    if name.startswith("get_") and callable(getattr(module, name)):
                        factory = getattr(module, name)
                        # Try to call it - if it returns an Agent, use it
                        try:
                            result = factory()
                            if isinstance(result, Agent):
                                agents.append(result)
                                agent_id = getattr(result, "id", result.name)
                                print(f"  ✅ Loaded agent: {result.name} (id: {agent_id})")
                                factory_found = True
                                break
                        except Exception as e:
                            # Not a valid factory, log and continue searching
                            print(f"  ⚠️  Factory {name} failed: {e}")
                            continue

                if not factory_found:
                    print(f"  ⚠️  No factory function found in {agent_path.name}/agent.py")

            except Exception as e:
                print(f"  ❌ Failed to load agent from {agent_path.name}: {e}")
                continue

    print(f"\n🎯 Total agents loaded: {len(agents)}")
    return agents


def get_agent_by_id(agent_id: str, agents: list[Agent]) -> Agent | None:
    """Get agent by ID from list of agents.

    Args:
        agent_id: Agent identifier
        agents: List of loaded agents

    Returns:
        Agent if found, None otherwise
    """
    for agent in agents:
        agent_attr_id = getattr(agent, "id", agent.name)
        if agent_attr_id == agent_id:
            return agent
    return None
