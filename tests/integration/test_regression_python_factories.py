"""Regression tests: Python factory agents still work."""

import pytest
from pathlib import Path
import yaml
from hive.discovery import discover_agents


class TestPythonFactoryRegression:
    """Ensure Python factories still work after YAML-only changes."""

    def test_python_factory_agent_still_works(self, tmp_path, monkeypatch):
        """Existing Python factory pattern unchanged."""
        agents_path = tmp_path / "ai" / "agents"
        agents_path.mkdir(parents=True)

        # Create fake hive.yaml
        hive_yaml = tmp_path / "hive.yaml"
        hive_yaml.write_text(yaml.dump({"agents": {"discovery_path": "ai/agents"}}))
        monkeypatch.chdir(tmp_path)

        agent_dir = agents_path / "legacy-bot"
        agent_dir.mkdir()

        # Config.yaml (should be ignored when agent.py exists)
        (agent_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "agent": {"name": "Config Name", "id": "legacy-bot"},
                }
            )
        )

        # agent.py (takes precedence)
        (agent_dir / "agent.py").write_text(
            """from agno.agent import Agent

def get_legacy_bot():
    return Agent(
        name="Legacy Bot from Python",
        id="legacy-bot",
        model="openai:gpt-4o",
        instructions="Python factory"
    )
"""
        )

        agents = discover_agents()

        # Python factory should be used (not YAML)
        assert len(agents) == 1
        agent = agents[0]
        assert agent.name == "Legacy Bot from Python"
        assert "gpt-4o" in str(agent.model)

    def test_python_factory_takes_precedence_over_yaml(self, tmp_path, monkeypatch):
        """When both agent.py and config.yaml exist, agent.py wins."""
        agents_path = tmp_path / "ai" / "agents"
        agents_path.mkdir(parents=True)

        # Create fake hive.yaml
        hive_yaml = tmp_path / "hive.yaml"
        hive_yaml.write_text(yaml.dump({"agents": {"discovery_path": "ai/agents"}}))
        monkeypatch.chdir(tmp_path)

        agent_dir = agents_path / "hybrid-bot"
        agent_dir.mkdir()

        # YAML config with one name
        (agent_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "agent": {"name": "YAML Name", "id": "hybrid-bot", "model": "openai:gpt-4o-mini"},
                    "instructions": "YAML instructions",
                }
            )
        )

        # Python factory with different name
        (agent_dir / "agent.py").write_text(
            """from agno.agent import Agent

def get_hybrid_bot():
    return Agent(
        name="Python Name",
        id="hybrid-bot",
        model="openai:gpt-4o",
        instructions="Python instructions"
    )
"""
        )

        agents = discover_agents()

        # Python factory should win
        assert len(agents) == 1
        agent = agents[0]
        assert agent.name == "Python Name"
        assert agent.instructions == "Python instructions"

    def test_broken_python_factory_does_not_fallback_to_yaml(self, tmp_path, monkeypatch):
        """If agent.py exists but is broken, don't fallback to YAML."""
        agents_path = tmp_path / "ai" / "agents"
        agents_path.mkdir(parents=True)

        # Create fake hive.yaml
        hive_yaml = tmp_path / "hive.yaml"
        hive_yaml.write_text(yaml.dump({"agents": {"discovery_path": "ai/agents"}}))
        monkeypatch.chdir(tmp_path)

        agent_dir = agents_path / "broken-bot"
        agent_dir.mkdir()

        # Valid YAML config
        (agent_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "agent": {"name": "Valid YAML", "id": "broken-bot", "model": "openai:gpt-4o-mini"},
                    "instructions": "Valid YAML config",
                }
            )
        )

        # Broken Python factory (syntax error)
        (agent_dir / "agent.py").write_text(
            """from agno import Agent

def get_broken_bot():
    # Missing return statement will cause factory to return None
    Agent(
        name="Broken Python",
        id="broken-bot",
        model="openai:gpt-4o",
    )
"""
        )

        agents = discover_agents()

        # Should NOT load the YAML fallback when Python exists but is broken
        # (discovery skips broken agents entirely)
        assert len(agents) == 0

    def test_multiple_python_factories_coexist(self, tmp_path, monkeypatch):
        """Multiple Python factory agents work together."""
        agents_path = tmp_path / "ai" / "agents"
        agents_path.mkdir(parents=True)

        # Create fake hive.yaml
        hive_yaml = tmp_path / "hive.yaml"
        hive_yaml.write_text(yaml.dump({"agents": {"discovery_path": "ai/agents"}}))
        monkeypatch.chdir(tmp_path)

        # Create first Python agent
        agent1_dir = agents_path / "python-agent-1"
        agent1_dir.mkdir()
        (agent1_dir / "agent.py").write_text(
            """from agno.agent import Agent

def get_python_agent_1():
    return Agent(
        name="Python Agent 1",
        id="python-agent-1",
        model="openai:gpt-4o",
        instructions="First Python agent"
    )
"""
        )

        # Create second Python agent
        agent2_dir = agents_path / "python-agent-2"
        agent2_dir.mkdir()
        (agent2_dir / "agent.py").write_text(
            """from agno.agent import Agent

def get_python_agent_2():
    return Agent(
        name="Python Agent 2",
        id="python-agent-2",
        model="openai:gpt-4o",
        instructions="Second Python agent"
    )
"""
        )

        agents = discover_agents()

        # Both should load
        assert len(agents) == 2
        agent_names = {a.name for a in agents}
        assert "Python Agent 1" in agent_names
        assert "Python Agent 2" in agent_names
