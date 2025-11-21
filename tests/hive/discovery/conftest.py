"""Test fixtures for discovery tests."""

import sys
from pathlib import Path

import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory with hive.yaml."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create hive.yaml config
    hive_config = {
        "agents": {"discovery_path": "ai/agents"},
        "teams": {"discovery_path": "ai/teams"},
        "workflows": {"discovery_path": "ai/workflows"},
    }
    (project / "hive.yaml").write_text(yaml.dump(hive_config))

    return project


@pytest.fixture
def temp_agents_dir(temp_project_dir):
    """Create temporary agents directory for testing."""
    agents_dir = temp_project_dir / "ai" / "agents"
    agents_dir.mkdir(parents=True)
    return agents_dir


@pytest.fixture
def temp_teams_dir(temp_project_dir):
    """Create temporary teams directory for testing."""
    teams_dir = temp_project_dir / "ai" / "teams"
    teams_dir.mkdir(parents=True)
    return teams_dir


@pytest.fixture
def temp_workflows_dir(temp_project_dir):
    """Create temporary workflows directory for testing."""
    workflows_dir = temp_project_dir / "ai" / "workflows"
    workflows_dir.mkdir(parents=True)
    return workflows_dir


@pytest.fixture
def yaml_only_agent_config():
    """Sample YAML config for agents (matching ConfigGenerator format)."""
    return {
        "agent": {
            "name": "test-agent",
            "id": "test-agent",
            "version": "1.0.0",
            "description": "Test agent description",
            "model": "openai:gpt-4o-mini",  # Model nested under agent
        },
        "instructions": "Test agent instructions",
    }


@pytest.fixture
def yaml_only_team_config():
    """Sample YAML config for teams (matching ConfigGenerator format)."""
    return {
        "team": {
            "name": "test-team",
            "team_id": "test-team",
            "version": "1.0.0",
            "description": "Test team description",
            "mode": "collaboration",  # Valid mode value
            "model": "openai:gpt-4o-mini",  # Model nested under team as string
        },
        "instructions": "Test team instructions",
        "members": [],  # Empty for simple tests
    }


@pytest.fixture
def yaml_only_workflow_config():
    """Sample YAML config for workflows (matching ConfigGenerator format)."""
    return {
        "workflow": {
            "name": "test-workflow",
            "workflow_id": "test-workflow",
            "version": "1.0.0",
            "description": "Test workflow description",
        },
        "instructions": "Test workflow instructions",
        "steps": [{"name": "step1", "description": "First step", "type": "function"}],
    }


def create_yaml_only_agent(agents_dir: Path, name: str, config: dict) -> Path:
    """Helper to create YAML-only agent.

    Args:
        agents_dir: Directory to create agent in
        name: Agent name
        config: Agent configuration dict

    Returns:
        Path to created agent directory
    """
    agent_dir = agents_dir / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "config.yaml").write_text(yaml.dump(config))
    return agent_dir


def create_python_agent(agents_dir: Path, name: str, config: dict) -> Path:
    """Helper to create Python factory agent.

    Args:
        agents_dir: Directory to create agent in
        name: Agent name
        config: Agent configuration dict

    Returns:
        Path to created agent directory
    """
    agent_dir = agents_dir / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Write config.yaml
    (agent_dir / "config.yaml").write_text(yaml.dump(config))

    # Write agent.py factory
    factory_code = f'''"""Agent factory for {name}."""
from agno import Agent
from pathlib import Path
import yaml


def get_{name.replace("-", "_")}_agent() -> Agent:
    """Create and return {name} agent."""
    config_path = Path(__file__).parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    agent_config = config.get("agent", {{}})
    return Agent(
        name=agent_config.get("name", "{name}"),
        model=agent_config.get("model", "openai:gpt-4o-mini"),
        instructions=config.get("instructions", "Default instructions"),
    )
'''
    (agent_dir / "agent.py").write_text(factory_code)
    return agent_dir


def create_yaml_only_team(teams_dir: Path, name: str, config: dict) -> Path:
    """Helper to create YAML-only team.

    Args:
        teams_dir: Directory to create team in
        name: Team name
        config: Team configuration dict

    Returns:
        Path to created team directory
    """
    team_dir = teams_dir / name
    team_dir.mkdir(parents=True, exist_ok=True)
    (team_dir / "config.yaml").write_text(yaml.dump(config))
    return team_dir


def create_python_team(teams_dir: Path, name: str, config: dict) -> Path:
    """Helper to create Python factory team.

    Args:
        teams_dir: Directory to create team in
        name: Team name
        config: Team configuration dict

    Returns:
        Path to created team directory
    """
    team_dir = teams_dir / name
    team_dir.mkdir(parents=True, exist_ok=True)

    # Write config.yaml
    (team_dir / "config.yaml").write_text(yaml.dump(config))

    # Write team.py factory
    factory_code = f'''"""Team factory for {name}."""
from agno import Team
from pathlib import Path
import yaml


def get_{name.replace("-", "_")}_team() -> Team:
    """Create and return {name} team."""
    config_path = Path(__file__).parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    team_config = config.get("team", {{}})
    return Team(
        name=team_config.get("name", "{name}"),
        members=[],  # Would load members here
    )
'''
    (team_dir / "team.py").write_text(factory_code)
    return team_dir


def create_yaml_only_workflow(workflows_dir: Path, name: str, config: dict) -> Path:
    """Helper to create YAML-only workflow.

    Args:
        workflows_dir: Directory to create workflow in
        name: Workflow name
        config: Workflow configuration dict

    Returns:
        Path to created workflow directory
    """
    workflow_dir = workflows_dir / name
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "config.yaml").write_text(yaml.dump(config))
    return workflow_dir


def create_python_workflow(workflows_dir: Path, name: str, config: dict) -> Path:
    """Helper to create Python factory workflow.

    Args:
        workflows_dir: Directory to create workflow in
        name: Workflow name
        config: Workflow configuration dict

    Returns:
        Path to created workflow directory
    """
    workflow_dir = workflows_dir / name
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Write config.yaml
    (workflow_dir / "config.yaml").write_text(yaml.dump(config))

    # Write workflow.py factory
    factory_code = f'''"""Workflow factory for {name}."""
from agno import Workflow
from pathlib import Path
import yaml


def get_{name.replace("-", "_")}_workflow() -> Workflow:
    """Create and return {name} workflow."""
    config_path = Path(__file__).parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    workflow_config = config.get("workflow", {{}})
    return Workflow(
        name=workflow_config.get("name", "{name}"),
        description=workflow_config.get("description", "Default workflow description"),
    )
'''
    (workflow_dir / "workflow.py").write_text(factory_code)
    return workflow_dir
