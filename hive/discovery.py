"""Agent discovery and registration for Hive V2.

This module discovers and loads agents from:
1. Project directory (ai/agents/) if hive.yaml exists
2. Package examples (hive/examples/agents/) as fallback
"""

import importlib.util
from pathlib import Path

import yaml
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow


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


def discover_workflows() -> list[Workflow]:
    """Discover and load workflows from project or package.

    Discovery order:
    1. If hive.yaml exists: use discovery_path from config
    2. Otherwise: use package examples (hive/examples/workflows/)

    Scans for workflow directories containing:
    - workflow.py: Factory function (get_*_workflow)
    - config.yaml: Workflow configuration (optional)

    Returns:
        List[Workflow]: Loaded workflow instances ready for AgentOS

    Example:
        >>> workflows = discover_workflows()
        >>> print(f"Found {len(workflows)} workflows")
        Found 2 workflows
    """
    workflows: list[Workflow] = []

    # Try to find project root with hive.yaml
    project_root = _find_project_root()

    if project_root:
        # User project mode - use discovery_path from hive.yaml
        config_path = project_root / "hive.yaml"
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            discovery_path = config.get("workflows", {}).get("discovery_path", "ai/workflows")
            workflows_dir = project_root / discovery_path
            print(f"🔍 Discovering workflows in project: {workflows_dir}")
        except Exception as e:
            print(f"⚠️  Failed to load hive.yaml: {e}")
            return workflows
    else:
        # Package mode - use builtin examples
        workflows_dir = Path(__file__).parent / "examples" / "workflows"
        print(f"🔍 Discovering workflows in package: {workflows_dir}")

    if not workflows_dir.exists():
        print(f"  ℹ️  Workflows directory not found: {workflows_dir}")
        return workflows

    # Scan workflow directories
    for workflow_path in workflows_dir.iterdir():
        # Skip non-directories and private directories
        if not workflow_path.is_dir() or workflow_path.name.startswith("_"):
            continue

        factory_file = workflow_path / "workflow.py"
        if not factory_file.exists():
            print(f"  ⏭️  Skipping {workflow_path.name} (no workflow.py)")
            continue

        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(f"hive.workflows.{workflow_path.name}", factory_file)
            if spec is None or spec.loader is None:
                print(f"  ❌ Failed to load spec for {workflow_path.name}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find factory function (get_*_workflow)
            factory_found = False
            for name in dir(module):
                if name.startswith("get_") and name.endswith("_workflow") and callable(getattr(module, name)):
                    factory = getattr(module, name)
                    # Try to call it - if it returns a Workflow, use it
                    try:
                        result = factory()
                        if isinstance(result, Workflow):
                            workflows.append(result)
                            workflow_id = getattr(result, "id", result.name)
                            print(f"  ✅ Loaded workflow: {result.name} (id: {workflow_id})")
                            factory_found = True
                            break
                    except Exception as e:
                        # Not a valid factory, log and continue searching
                        print(f"  ⚠️  Factory {name} failed: {e}")
                        continue

            if not factory_found:
                print(f"  ⚠️  No get_*_workflow() function found in {workflow_path.name}/workflow.py")

        except Exception as e:
            print(f"  ❌ Failed to load workflow from {workflow_path.name}: {e}")
            continue

    print(f"\n🎯 Total workflows loaded: {len(workflows)}")
    return workflows


def discover_teams() -> list[Team]:
    """Discover and load teams from project or package.

    Discovery order:
    1. If hive.yaml exists: use discovery_path from config
    2. Otherwise: use package examples (hive/examples/teams/)

    Scans for team directories containing:
    - team.py: Factory function (get_*_team)
    - config.yaml: Team configuration (optional)

    Returns:
        List[Team]: Loaded team instances ready for AgentOS

    Example:
        >>> teams = discover_teams()
        >>> print(f"Found {len(teams)} teams")
        Found 1 teams
    """
    teams: list[Team] = []

    # Try to find project root with hive.yaml
    project_root = _find_project_root()

    if project_root:
        # User project mode - use discovery_path from hive.yaml
        config_path = project_root / "hive.yaml"
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            discovery_path = config.get("teams", {}).get("discovery_path", "ai/teams")
            teams_dir = project_root / discovery_path
            print(f"🔍 Discovering teams in project: {teams_dir}")
        except Exception as e:
            print(f"⚠️  Failed to load hive.yaml: {e}")
            return teams
    else:
        # Package mode - use builtin examples
        teams_dir = Path(__file__).parent / "examples" / "teams"
        print(f"🔍 Discovering teams in package: {teams_dir}")

    if not teams_dir.exists():
        print(f"  ℹ️  Teams directory not found: {teams_dir}")
        return teams

    # Scan team directories
    for team_path in teams_dir.iterdir():
        # Skip non-directories and private directories
        if not team_path.is_dir() or team_path.name.startswith("_"):
            continue

        factory_file = team_path / "team.py"
        if not factory_file.exists():
            print(f"  ⏭️  Skipping {team_path.name} (no team.py)")
            continue

        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(f"hive.teams.{team_path.name}", factory_file)
            if spec is None or spec.loader is None:
                print(f"  ❌ Failed to load spec for {team_path.name}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find factory function (get_*_team)
            factory_found = False
            for name in dir(module):
                if name.startswith("get_") and name.endswith("_team") and callable(getattr(module, name)):
                    factory = getattr(module, name)
                    # Try to call it - if it returns a Team, use it
                    try:
                        result = factory()
                        if isinstance(result, Team):
                            teams.append(result)
                            team_id = getattr(result, "id", result.name)
                            print(f"  ✅ Loaded team: {result.name} (id: {team_id})")
                            factory_found = True
                            break
                    except Exception as e:
                        # Not a valid factory, log and continue searching
                        print(f"  ⚠️  Factory {name} failed: {e}")
                        continue

            if not factory_found:
                print(f"  ⚠️  No get_*_team() function found in {team_path.name}/team.py")

        except Exception as e:
            print(f"  ❌ Failed to load team from {team_path.name}: {e}")
            continue

    print(f"\n🎯 Total teams loaded: {len(teams)}")
    return teams


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
