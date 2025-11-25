"""Agent discovery and registration for Hive V2.

This module discovers and loads agents from:
1. Project directory (ai/agents/) if hive.yaml exists
2. Package examples (hive/examples/agents/) as fallback
3. Genie markdown agents (.genie/agents/, .genie/code/agents/)

Supports three loading strategies (in priority order):
1. Python factory files (agent.py) - advanced, optional
2. Markdown with frontmatter (.md files) - Genie format, human-readable
3. YAML-only configs (config.yaml) - Hive format, fallback

All formats are supported in ai/agents/ and .genie/ directories.
Python is never required - use YAML or frontmatter for simple agents.
"""

import importlib.util
from pathlib import Path

import yaml
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow

from hive.scaffolder.frontmatter_parser import parse_markdown_frontmatter
from hive.scaffolder.genie_mapper import map_genie_to_hive
from hive.scaffolder.validator import ConfigValidator

# Genie agent discovery paths (relative to project root)
GENIE_DISCOVERY_PATHS = [
    ".genie/agents",
    ".genie/code/agents",
]


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


def derive_genie_agent_id(file_path: str) -> str:
    """Derive agent ID from Genie markdown file path.

    Converts file paths to agent IDs using pattern: genie-<collection>-<name>
    Uses hyphens (-) as separators for URL-safe agent IDs.

    Args:
        file_path: Path to Genie .md file

    Returns:
        Agent ID in format "genie-<name>" or "genie-code-<name>"

    Examples:
        >>> derive_genie_agent_id(".genie/agents/review.md")
        'genie-review'
        >>> derive_genie_agent_id(".genie/code/agents/fix.md")
        'genie-code-fix'
        >>> derive_genie_agent_id("/abs/path/.genie/agents/test.md")
        'genie-test'
    """
    path = Path(file_path)

    # Find which Genie base path this file is under
    for base_path in GENIE_DISCOVERY_PATHS:
        base_parts = Path(base_path).parts

        # Check if base_path exists in the file path
        path_parts = path.parts
        for i in range(len(path_parts) - len(base_parts) + 1):
            if path_parts[i : i + len(base_parts)] == base_parts:
                # Get path after base_path, remove .md extension
                relative_parts = path_parts[i + len(base_parts) :]
                agent_name = "-".join(relative_parts).replace(".md", "")

                # Build agent ID based on which base path matched (URL-safe with hyphens)
                if base_path == ".genie/agents":
                    return f"genie-{agent_name}"
                elif base_path == ".genie/code/agents":
                    return f"genie-code-{agent_name}"

    # Fallback: use filename without extension
    return f"genie-{path.stem}"


def discover_agents_with_frontmatter(project_root: Path) -> list[Agent]:
    """Discover and load Genie agents from markdown files with frontmatter.

    Searches GENIE_DISCOVERY_PATHS for .md files, parses frontmatter,
    validates schema, maps to Hive config, and generates Agent instances.

    Args:
        project_root: Project root directory containing .genie/ directories

    Returns:
        List of Agent instances loaded from Genie markdown files

    Example:
        >>> project_root = Path("/path/to/project")
        >>> agents = discover_agents_with_frontmatter(project_root)
        >>> print(f"Found {len(agents)} Genie agents")
        Found 3 Genie agents
    """
    agents: list[Agent] = []

    # Search each Genie discovery path
    for base_path in GENIE_DISCOVERY_PATHS:
        genie_dir = project_root / base_path

        if not genie_dir.exists():
            continue

        print(f"  📂 Scanning Genie agents: {genie_dir}")

        # Find all .md files recursively
        for md_file in genie_dir.rglob("*.md"):
            # Skip files starting with underscore (private/templates)
            if md_file.name.startswith("_"):
                continue

            # Skip common documentation files (not agents)
            if md_file.name.upper() in ("README.MD", "CHANGELOG.MD", "LICENSE.MD", "CONTRIBUTING.MD"):
                continue

            try:
                # Parse frontmatter and content
                parsed = parse_markdown_frontmatter(str(md_file))
                frontmatter = parsed["frontmatter"]
                content = parsed["content"]

                # Validate Genie schema
                ConfigValidator.validate_genie_agent(frontmatter)

                # Map to Hive config
                hive_config = map_genie_to_hive(frontmatter, content)

                # Derive agent ID from file path
                agent_id = derive_genie_agent_id(str(md_file))
                hive_config["agent"]["id"] = agent_id

                # Generate Agent instance
                from hive.scaffolder.generator import ConfigGenerator

                agent = ConfigGenerator.generate_agent_from_dict(hive_config, validate=True)

                agents.append(agent)
                print(f"  ✅ Loaded Genie agent: {agent.name} (id: {agent_id})")

            except ValueError as e:
                print(f"  ⚠️  Skipping {md_file.name}: {e}")
            except Exception as e:  # noqa: S112
                print(f"  ❌ Failed to load {md_file.name}: {e}")

    return agents


def discover_agents() -> list[Agent]:
    """Discover and load agents from project or package.

    Discovery order:
    1. If hive.yaml exists: use discovery_path from config
    2. Otherwise: use package examples (hive/examples/agents/)
    3. Additionally scan Genie markdown agents (.genie/agents/, .genie/code/agents/)

    Scans for agent directories containing (in priority order):
    1. agent.py: Python factory function (get_*_agent) - advanced, optional
    2. *.md: Markdown with YAML frontmatter - Genie format, human-readable
    3. config.yaml: YAML configuration - Hive format, fallback

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

            # Strategy 1: Try Python factory first (advanced, optional)
            factory_file = agent_path / "agent.py"
            if factory_file.exists():
                try:
                    agent = _load_agent_from_python(factory_file, agent_path)
                    if agent:
                        agents.append(agent)
                        continue
                except Exception:  # noqa: S112
                    # Broken Python file - don't fall back to other formats
                    continue

            # Strategy 2: Markdown with frontmatter (Genie format)
            md_files = list(agent_path.glob("*.md"))
            # Filter out documentation files
            md_files = [
                f
                for f in md_files
                if f.name.upper() not in ("README.MD", "CHANGELOG.MD", "LICENSE.MD", "CONTRIBUTING.MD")
                and not f.name.startswith("_")
            ]
            if md_files:
                # Use first valid .md file found
                for md_file in md_files:
                    agent = _load_agent_from_frontmatter(md_file, agent_path)
                    if agent:
                        agents.append(agent)
                        break
                if agent:
                    continue

            # Strategy 3: Fallback to YAML-only loading (Hive format)
            config_file = agent_path / "config.yaml"
            if config_file.exists():
                agent = _load_agent_from_yaml(config_file, agent_path)
                if agent:
                    agents.append(agent)
                continue

            # None found
            print(f"  ⏭️  Skipping {agent_path.name} (no agent.py, *.md, or config.yaml)")

    # Strategy 3: Discover Genie markdown agents (only in project mode)
    if project_root:
        genie_agents = discover_agents_with_frontmatter(project_root)
        agents.extend(genie_agents)

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

        # Strategy 1: Try Python factory first (backward compatibility)
        factory_file = workflow_path / "workflow.py"
        if factory_file.exists():
            try:
                workflow = _load_workflow_from_python(factory_file, workflow_path)
                if workflow:
                    workflows.append(workflow)
                    continue
            except Exception:  # noqa: S112
                # Broken Python file - don't fall back to YAML
                continue

        # Strategy 2: Fallback to YAML-only loading
        config_file = workflow_path / "config.yaml"
        if config_file.exists():
            workflow = _load_workflow_from_yaml(config_file, workflow_path)
            if workflow:
                workflows.append(workflow)
            continue

        # Neither found
        print(f"  ⏭️  Skipping {workflow_path.name} (no workflow.py or config.yaml)")

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

        # Strategy 1: Try Python factory first (backward compatibility)
        factory_file = team_path / "team.py"
        if factory_file.exists():
            try:
                team = _load_team_from_python(factory_file, team_path)
                if team:
                    teams.append(team)
                    continue
            except Exception:  # noqa: S112
                # Broken Python file - don't fall back to YAML
                continue

        # Strategy 2: Fallback to YAML-only loading
        config_file = team_path / "config.yaml"
        if config_file.exists():
            team = _load_team_from_yaml(config_file, team_path)
            if team:
                teams.append(team)
            continue

        # Neither found
        print(f"  ⏭️  Skipping {team_path.name} (no team.py or config.yaml)")

    print(f"\n🎯 Total teams loaded: {len(teams)}")
    return teams


def _load_agent_from_python(factory_file: Path, agent_path: Path) -> Agent | None:
    """Load agent using Python factory file (agent.py).

    Args:
        factory_file: Path to agent.py file
        agent_path: Path to agent directory

    Returns:
        Agent instance if loaded successfully, None otherwise

    Note:
        This is the legacy/advanced pattern. Returns None only if
        factory function not found. Raises exceptions for broken Python.
    """
    try:
        # Load module dynamically
        spec = importlib.util.spec_from_file_location(f"hive.agents.{agent_path.name}", factory_file)
        if spec is None or spec.loader is None:
            print(f"  ❌ Failed to load spec for {agent_path.name}")
            return None

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
                        agent_id = getattr(result, "id", result.name)
                        print(f"  ✅ Loaded agent (Python): {result.name} (id: {agent_id})")
                        return result
                except Exception as e:
                    # Not a valid factory, log and continue searching
                    print(f"  ⚠️  Factory {name} failed: {e}")
                    continue

        if not factory_found:
            print(f"  ⚠️  No factory function found in {agent_path.name}/agent.py")
        return None
    except Exception as e:
        print(f"  ❌ Failed to load agent from {agent_path.name}: {e}")
        # Re-raise to prevent YAML fallback on broken Python files
        raise


def _load_agent_from_yaml(config_file: Path, agent_path: Path) -> Agent | None:
    """Load agent from YAML config only (config.yaml).

    Args:
        config_file: Path to config.yaml file
        agent_path: Path to agent directory

    Returns:
        Agent instance if loaded successfully, None otherwise

    Note:
        This is the YAML-only pattern (no Python factory required).
        Uses ConfigGenerator to convert YAML to Agent.
    """
    try:
        from hive.scaffolder.generator import ConfigGenerator

        agent = ConfigGenerator.generate_agent_from_yaml(str(config_file), validate=True)
        agent_id = getattr(agent, "id", agent.name)
        print(f"  ✅ Loaded agent (YAML-only): {agent.name} (id: {agent_id})")
        return agent
    except Exception as e:
        print(f"  ❌ Failed to load YAML agent from {agent_path.name}: {e}")
        return None


def _load_agent_from_frontmatter(md_file: Path, agent_path: Path) -> Agent | None:
    """Load agent from markdown file with YAML frontmatter (Genie format).

    Args:
        md_file: Path to .md file with frontmatter
        agent_path: Path to agent directory

    Returns:
        Agent instance if loaded successfully, None otherwise

    Note:
        This supports Genie-style agents defined in markdown with YAML frontmatter.
        The frontmatter contains agent config, markdown body contains instructions.
    """
    try:
        from hive.scaffolder.generator import ConfigGenerator

        # Parse frontmatter and content
        parsed = parse_markdown_frontmatter(str(md_file))
        frontmatter = parsed["frontmatter"]
        content = parsed["content"]

        # Validate Genie schema
        ConfigValidator.validate_genie_agent(frontmatter)

        # Map to Hive config
        hive_config = map_genie_to_hive(frontmatter, content)

        # Use directory name as agent ID (consistent with other strategies)
        agent_id = agent_path.name
        hive_config["agent"]["id"] = agent_id

        # Generate Agent instance
        agent = ConfigGenerator.generate_agent_from_dict(hive_config, validate=True)

        print(f"  ✅ Loaded agent (frontmatter): {agent.name} (id: {agent_id})")
        return agent
    except ValueError as e:
        print(f"  ⚠️  Invalid frontmatter in {md_file.name}: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Failed to load frontmatter agent from {agent_path.name}: {e}")
        return None


def _load_team_from_python(factory_file: Path, team_path: Path) -> Team | None:
    """Load team using Python factory file (team.py)."""
    try:
        spec = importlib.util.spec_from_file_location(f"hive.teams.{team_path.name}", factory_file)
        if spec is None or spec.loader is None:
            print(f"  ❌ Failed to load spec for {team_path.name}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find factory function (get_*_team)
        factory_found = False
        for name in dir(module):
            if name.startswith("get_") and name.endswith("_team") and callable(getattr(module, name)):
                factory = getattr(module, name)
                try:
                    result = factory()
                    if isinstance(result, Team):
                        team_id = getattr(result, "id", result.name)
                        print(f"  ✅ Loaded team (Python): {result.name} (id: {team_id})")
                        return result
                except Exception as e:
                    print(f"  ⚠️  Factory {name} failed: {e}")
                    continue

        if not factory_found:
            print(f"  ⚠️  No get_*_team() function found in {team_path.name}/team.py")
        return None
    except Exception as e:
        print(f"  ❌ Failed to load team from {team_path.name}: {e}")
        raise


def _load_team_from_yaml(config_file: Path, team_path: Path) -> Team | None:
    """Load team from YAML config only (config.yaml)."""
    try:
        from hive.scaffolder.generator import ConfigGenerator

        team = ConfigGenerator.generate_team_from_yaml(str(config_file), validate=True)
        team_id = getattr(team, "id", team.name)
        print(f"  ✅ Loaded team (YAML-only): {team.name} (id: {team_id})")
        return team
    except Exception as e:
        print(f"  ❌ Failed to load YAML team from {team_path.name}: {e}")
        return None


def _load_workflow_from_python(factory_file: Path, workflow_path: Path) -> Workflow | None:
    """Load workflow using Python factory file (workflow.py)."""
    try:
        spec = importlib.util.spec_from_file_location(f"hive.workflows.{workflow_path.name}", factory_file)
        if spec is None or spec.loader is None:
            print(f"  ❌ Failed to load spec for {workflow_path.name}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find factory function (get_*_workflow)
        factory_found = False
        for name in dir(module):
            if name.startswith("get_") and name.endswith("_workflow") and callable(getattr(module, name)):
                factory = getattr(module, name)
                try:
                    result = factory()
                    if isinstance(result, Workflow):
                        workflow_id = getattr(result, "id", result.name)
                        print(f"  ✅ Loaded workflow (Python): {result.name} (id: {workflow_id})")
                        return result
                except Exception as e:
                    print(f"  ⚠️  Factory {name} failed: {e}")
                    continue

        if not factory_found:
            print(f"  ⚠️  No get_*_workflow() function found in {workflow_path.name}/workflow.py")
        return None
    except Exception as e:
        print(f"  ❌ Failed to load workflow from {workflow_path.name}: {e}")
        raise


def _load_workflow_from_yaml(config_file: Path, workflow_path: Path) -> Workflow | None:
    """Load workflow from YAML config only (config.yaml)."""
    try:
        from hive.scaffolder.generator import ConfigGenerator

        workflow = ConfigGenerator.generate_workflow_from_yaml(str(config_file), validate=True)
        workflow_id = getattr(workflow, "id", workflow.name)
        print(f"  ✅ Loaded workflow (YAML-only): {workflow.name} (id: {workflow_id})")
        return workflow
    except Exception as e:
        print(f"  ❌ Failed to load YAML workflow from {workflow_path.name}: {e}")
        return None


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
