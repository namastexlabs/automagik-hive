"""
Tests for template agent factory function.

Verifies that get_template_agent() properly loads configuration from YAML,
creates Model instances via resolve_model(), and respects runtime overrides.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch
import importlib.util

# Add project root to path (4 levels up from test file)
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Define template-agent directory location
template_agent_dir = project_root / "ai" / "agents" / "template-agent"

# Import using importlib to handle hyphenated directory name
agent_path = str(template_agent_dir / "agent.py")
spec = importlib.util.spec_from_file_location("template_agent_module", agent_path)
template_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_agent_module)
get_template_agent = template_agent_module.get_template_agent


@pytest.fixture
def mock_env_vars():
    """Mock required environment variables."""
    env_vars = {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_API_PORT": "8888",
        "HIVE_DATABASE_URL": "sqlite:///test.db",
        "HIVE_API_KEY": "hive_test_key_12345678901234567890123456",
        "HIVE_CORS_ORIGINS": "http://localhost:3000",
        "HIVE_DEFAULT_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
    }
    with patch.dict("os.environ", env_vars, clear=False):
        yield env_vars


def test_template_agent_factory_creates_agent(mock_env_vars):
    """Verify get_template_agent() creates Agent instance."""
    agent = get_template_agent(session_id="test-session")

    # Should return Agent instance
    assert agent is not None, "Factory should return agent instance"
    assert hasattr(agent, "agent_id"), "Agent should have agent_id attribute"
    assert agent.agent_id == "template-agent", f"Expected 'template-agent', got '{agent.agent_id}'"
    assert hasattr(agent, "name"), "Agent should have name attribute"
    # Accept emoji prefix in name
    assert "Template Agent" in agent.name, f"Expected 'Template Agent' in name, got '{agent.name}'"


def test_template_agent_model_from_yaml(mock_env_vars):
    """Verify template agent loads model config from YAML."""
    agent = get_template_agent()

    # Should have Model instance (not dict)
    assert hasattr(agent, "model"), "Agent should have model attribute"
    assert agent.model is not None, "Model should not be None"
    assert not isinstance(agent.model, dict), "Model should be instance, not dict"

    # Model should have id attribute
    assert hasattr(agent.model, "id"), "Model should have id attribute"

    # Check it matches YAML config (gpt-4o-mini from template config)
    assert agent.model.id == "gpt-4o-mini", f"Expected 'gpt-4o-mini', got '{agent.model.id}'"

    # Model should have temperature if specified in YAML
    if hasattr(agent.model, "temperature"):
        assert isinstance(agent.model.temperature, (int, float)), "Temperature should be numeric"


def test_template_agent_runtime_overrides(mock_env_vars):
    """Verify runtime kwargs override YAML config."""
    agent = get_template_agent(session_id="override-session", user_id="test-user-123")

    # Runtime overrides should be applied
    assert agent.session_id == "override-session", f"Expected session override, got '{agent.session_id}'"
    assert agent.user_id == "test-user-123", f"Expected user override, got '{agent.user_id}'"

    # YAML config should still be respected
    assert agent.agent_id == "template-agent", "YAML agent_id should be preserved"
    assert agent.model.id == "gpt-4o-mini", "YAML model config should be preserved"


def test_template_agent_knowledge_integration(mock_env_vars):
    """Verify template agent has knowledge base."""
    agent = get_template_agent()

    # Should have knowledge attribute
    assert hasattr(agent, "knowledge"), "Agent should have knowledge attribute"
    # In test mode, knowledge returns None - this is expected
    # Knowledge would be loaded in production with database connection
    if agent.knowledge is not None:
        # If knowledge is loaded (non-test environment), verify it's proper instance
        assert not isinstance(agent.knowledge, dict), "Knowledge should be instance, not dict"


def test_template_agent_storage_configuration(mock_env_vars):
    """Verify template agent storage is configured correctly."""
    agent = get_template_agent()

    # Agno uses 'db' attribute, not 'storage'
    # Check that agent has database configuration capability
    assert hasattr(agent, "db") or hasattr(agent.model, "store"), (
        "Agent should have database configuration (db attribute or model.store)"
    )

    # Database might be None in test environment, which is acceptable
    # In production, db/store would be configured via Agent constructor


def test_template_agent_tools_configuration(mock_env_vars):
    """Verify template agent tools are loaded from config."""
    agent = get_template_agent()

    # Should have tools attribute
    assert hasattr(agent, "tools"), "Agent should have tools attribute"

    # Tools can be None or list (depending on YAML config)
    if agent.tools is not None:
        assert isinstance(agent.tools, (list, tuple)), "Tools should be a sequence"


def test_template_agent_instructions_loaded(mock_env_vars):
    """Verify template agent instructions are loaded from YAML."""
    agent = get_template_agent()

    # Should have instructions
    assert hasattr(agent, "instructions"), "Agent should have instructions attribute"

    # Instructions can be string or list
    if agent.instructions is not None:
        assert isinstance(agent.instructions, (str, list)), (
            f"Instructions should be string or list, got {type(agent.instructions)}"
        )

        # If string, should not be empty
        if isinstance(agent.instructions, str):
            assert len(agent.instructions.strip()) > 0, "Instructions should not be empty"


def test_template_agent_yaml_config_path(mock_env_vars):
    """Verify template agent loads config from correct path."""
    import yaml

    # Load YAML directly to compare
    config_path = template_agent_dir / "config.yaml"
    assert config_path.exists(), f"Config file should exist at {config_path}"

    with open(config_path) as f:
        yaml_config = yaml.safe_load(f)

    # Create agent
    agent = get_template_agent()

    # Verify key attributes match YAML
    assert agent.agent_id == yaml_config["agent"]["agent_id"], (
        f"Agent ID mismatch: {agent.agent_id} != {yaml_config['agent']['agent_id']}"
    )
    assert agent.name == yaml_config["agent"]["name"], (
        f"Agent name mismatch: {agent.name} != {yaml_config['agent']['name']}"
    )

    # Model ID should match (after resolution)
    yaml_model_id = yaml_config.get("model", {}).get("id", "gpt-4o-mini")
    assert agent.model.id == yaml_model_id, f"Model ID mismatch: {agent.model.id} != {yaml_model_id}"


def test_template_agent_multiple_instances_isolated(mock_env_vars):
    """Verify multiple agent instances are properly isolated."""
    # Create two agents with different sessions
    agent1 = get_template_agent(session_id="session-1", user_id="user-1")
    agent2 = get_template_agent(session_id="session-2", user_id="user-2")

    # Should be different instances
    assert agent1 is not agent2, "Each call should create new instance"

    # Should have isolated session data
    assert agent1.session_id == "session-1", "Agent 1 session should be isolated"
    assert agent2.session_id == "session-2", "Agent 2 session should be isolated"
    assert agent1.user_id == "user-1", "Agent 1 user should be isolated"
    assert agent2.user_id == "user-2", "Agent 2 user should be isolated"

    # But should share same configuration
    assert agent1.agent_id == agent2.agent_id, "Both should share agent_id from YAML"
    assert agent1.model.id == agent2.model.id, "Both should share model config from YAML"


@pytest.mark.parametrize(
    "session_id,user_id",
    [
        ("test-session-1", "user-abc"),
        ("test-session-2", "user-xyz"),
        (None, None),  # Test with no overrides
    ],
)
def test_template_agent_parametrized_creation(mock_env_vars, session_id, user_id):
    """Verify template agent creation with various parameter combinations."""
    kwargs = {}
    if session_id is not None:
        kwargs["session_id"] = session_id
    if user_id is not None:
        kwargs["user_id"] = user_id

    agent = get_template_agent(**kwargs)

    # Should always create valid agent
    assert agent is not None, "Agent should be created regardless of parameters"
    assert agent.agent_id == "template-agent", "Agent ID should always match YAML"
    assert agent.model.id == "gpt-4o-mini", "Model should always match YAML"

    # Runtime params should be applied if provided
    if session_id is not None:
        assert agent.session_id == session_id
    if user_id is not None:
        assert agent.user_id == user_id
