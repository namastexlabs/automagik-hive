"""Tests for API key collection during init workflow."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.commands.service import ServiceManager


@pytest.fixture
def service_manager():
    """Create ServiceManager instance for testing."""
    return ServiceManager()


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    env_vars = {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_API_PORT": "8888",
        "HIVE_DATABASE_URL": "sqlite:///test.db",
    }
    with patch.dict("os.environ", env_vars, clear=False):
        yield env_vars


class TestAPIKeyCollection:
    """Test API key collection functionality."""

    def test_collect_openai_key_valid(self, service_manager):
        """Test collecting valid OpenAI API key."""
        with patch("builtins.input", side_effect=["1", "sk-test-openai-key-123"]):
            result = service_manager._collect_api_key_interactive()

        assert result is not None
        assert result["provider"] == "openai"
        assert result["api_key"] == "sk-test-openai-key-123"

    def test_collect_anthropic_key_valid(self, service_manager):
        """Test collecting valid Anthropic API key."""
        with patch("builtins.input", side_effect=["2", "sk-ant-test-anthropic-key-123"]):
            result = service_manager._collect_api_key_interactive()

        assert result is not None
        assert result["provider"] == "anthropic"
        assert result["api_key"] == "sk-ant-test-anthropic-key-123"

    def test_collect_key_skip(self, service_manager):
        """Test skipping API key collection."""
        with patch("builtins.input", return_value="3"):
            result = service_manager._collect_api_key_interactive()

        assert result is None

    def test_collect_key_invalid_openai_format(self, service_manager):
        """Test invalid OpenAI key format is rejected."""
        with patch("builtins.input", side_effect=["1", "invalid-key"]):
            result = service_manager._collect_api_key_interactive()

        assert result is None

    def test_collect_key_invalid_anthropic_format(self, service_manager):
        """Test invalid Anthropic key format is rejected."""
        with patch("builtins.input", side_effect=["2", "invalid-key"]):
            result = service_manager._collect_api_key_interactive()

        assert result is None

    def test_collect_key_keyboard_interrupt(self, service_manager):
        """Test keyboard interrupt during collection."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = service_manager._collect_api_key_interactive()

        assert result is None

    def test_collect_key_eof_error(self, service_manager):
        """Test EOF error during collection."""
        with patch("builtins.input", side_effect=EOFError):
            result = service_manager._collect_api_key_interactive()

        assert result is None


class TestAPIKeyConfiguration:
    """Test API key configuration in workspace."""

    def test_configure_openai_api_key(self, service_manager, tmp_path, mock_env_vars):
        """Test configuring OpenAI API key in .env and agent config."""
        # Setup
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "ai" / "agents" / "template-agent").mkdir(parents=True)

        # Create .env file
        env_file = workspace / ".env"
        env_file.write_text("OPENAI_API_KEY=your-openai-api-key-here\n")

        # Create agent config
        agent_config = workspace / "ai" / "agents" / "template-agent" / "config.yaml"
        agent_config.write_text("""
model:
  provider: anthropic
  id: claude-sonnet-4-20250514
""")

        api_key_config = {"provider": "openai", "api_key": "sk-test-openai-key"}

        # Execute
        service_manager._configure_api_keys_and_agent(workspace, api_key_config)

        # Verify .env updated
        env_content = env_file.read_text()
        assert 'OPENAI_API_KEY="sk-test-openai-key"' in env_content

        # Verify agent config updated
        import yaml

        with open(agent_config) as f:
            config = yaml.safe_load(f)

        assert config["model"]["provider"] == "openai"
        assert config["model"]["id"] == "gpt-4.1-mini"

    def test_configure_anthropic_api_key(self, service_manager, tmp_path, mock_env_vars):
        """Test configuring Anthropic API key in .env and agent config."""
        # Setup
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "ai" / "agents" / "template-agent").mkdir(parents=True)

        # Create .env file
        env_file = workspace / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=your-anthropic-api-key-here\n")

        # Create agent config
        agent_config = workspace / "ai" / "agents" / "template-agent" / "config.yaml"
        agent_config.write_text("""
model:
  provider: openai
  id: gpt-4.1-mini
""")

        api_key_config = {"provider": "anthropic", "api_key": "sk-ant-test-key"}

        # Execute
        service_manager._configure_api_keys_and_agent(workspace, api_key_config)

        # Verify .env updated
        env_content = env_file.read_text()
        assert 'ANTHROPIC_API_KEY="sk-ant-test-key"' in env_content

        # Verify agent config updated
        import yaml

        with open(agent_config) as f:
            config = yaml.safe_load(f)

        assert config["model"]["provider"] == "anthropic"
        assert config["model"]["id"] == "claude-sonnet-4-20250514"

    def test_configure_api_key_env_not_exists(self, service_manager, tmp_path):
        """Test configuration handles missing .env file gracefully."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        api_key_config = {"provider": "openai", "api_key": "sk-test-key"}

        # Should not raise exception
        service_manager._configure_api_keys_and_agent(workspace, api_key_config)

    def test_configure_api_key_agent_config_not_exists(self, service_manager, tmp_path):
        """Test configuration handles missing agent config gracefully."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        env_file = workspace / ".env"
        env_file.write_text("OPENAI_API_KEY=placeholder\n")

        api_key_config = {"provider": "openai", "api_key": "sk-test-key"}

        # Should not raise exception
        service_manager._configure_api_keys_and_agent(workspace, api_key_config)

        # Verify .env still updated
        env_content = env_file.read_text()
        assert 'OPENAI_API_KEY="sk-test-key"' in env_content
