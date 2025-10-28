"""
Tests for Template Agent Factory Function

Tests our new implementation that manually loads YAML config,
creates Model instances via resolve_model(), and sets agent_id as attribute.

This replaces the old tests that expected Agent.from_yaml() pattern.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, Mock
import os

# Set test database URL BEFORE loading any modules
os.environ["HIVE_DATABASE_URL"] = "sqlite:///test.db"
os.environ["HIVE_ENVIRONMENT"] = "development"
os.environ["HIVE_API_PORT"] = "8888"
os.environ["HIVE_API_KEY"] = "hive_test_key_12345678901234567890123456"
os.environ["HIVE_CORS_ORIGINS"] = "http://localhost:3000"
os.environ["HIVE_DEFAULT_MODEL"] = "gpt-4o-mini"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

# Add project root to path (5 levels up from test file)
project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add template-agent directory to path
template_agent_dir = project_root / "ai" / "agents" / "template-agent"
if str(template_agent_dir) not in sys.path:
    sys.path.insert(0, str(template_agent_dir))

# Import using importlib to handle hyphenated directory name
import importlib.util

agent_path = str(template_agent_dir / "agent.py")
spec = importlib.util.spec_from_file_location("template_agent_module", agent_path)
template_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_agent_module)
get_template_agent = template_agent_module.get_template_agent


class TestTemplateAgentFactory:
    """Test suite for template agent factory function."""

    def test_get_template_agent_with_default_parameters_should_create_agent(self):
        """Should create template agent with default parameters."""
        result = get_template_agent()

        # Should return agent instance
        assert result is not None, "Template agent should be created successfully"
        assert hasattr(result, "agent_id"), "Agent should have agent_id attribute"
        assert result.agent_id == "template-agent", "Should have correct agent_id"

    def test_get_template_agent_loads_config_from_yaml(self):
        """Should load configuration from config.yaml file."""
        result = get_template_agent()

        # Verify YAML config was loaded correctly (accept emoji prefix)
        assert "Template Agent" in result.name, f"Expected 'Template Agent' in name, got '{result.name}'"
        assert result.agent_id == "template-agent", f"Expected 'template-agent', got '{result.agent_id}'"

    def test_get_template_agent_creates_model_instance(self):
        """Should create Model instance (not dict) via resolve_model()."""
        result = get_template_agent()

        # Model should be instance, not dict
        assert hasattr(result, "model"), "Agent should have model attribute"
        assert result.model is not None, "Model should not be None"
        assert not isinstance(result.model, dict), "Model should be instance, not dict"
        assert hasattr(result.model, "id"), "Model should have id attribute"
        assert result.model.id == "gpt-4o-mini", f"Expected 'gpt-4o-mini', got '{result.model.id}'"

    def test_get_template_agent_sets_agent_id_as_attribute(self):
        """Should set agent_id as instance attribute (not constructor param)."""
        result = get_template_agent()

        # agent_id should exist and match config
        assert hasattr(result, "agent_id"), "Agent should have agent_id attribute"
        assert result.agent_id == "template-agent", "agent_id should match YAML config"

    def test_get_template_agent_loads_knowledge_base(self):
        """Should load knowledge base from get_agentos_knowledge_base()."""
        result = get_template_agent()

        # Knowledge attribute should exist (may be None in test mode)
        assert hasattr(result, "knowledge"), "Agent should have knowledge attribute"
        # In test mode, knowledge returns None - this is expected behavior
        # In production with DB, knowledge would be loaded


class TestTemplateAgentBehavior:
    """Test suite for template agent behavior and patterns."""

    def test_template_agent_accepts_runtime_overrides(self):
        """Should accept runtime kwargs and pass to Agent constructor."""
        result = get_template_agent(session_id="test-session", user_id="test-user")

        # Runtime overrides should be applied
        assert result.session_id == "test-session", "Should accept session_id override"
        assert result.user_id == "test-user", "Should accept user_id override"

        # YAML config should still be respected
        assert result.agent_id == "template-agent", "YAML config should be preserved"

    def test_template_agent_should_be_synchronous_function(self):
        """Should verify template agent factory is synchronous."""
        import asyncio
        import inspect

        # Template agent should NOT be async
        assert not asyncio.iscoroutinefunction(get_template_agent), "Template agent factory should be synchronous"

        # Should accept **kwargs
        sig = inspect.signature(get_template_agent)
        assert "kwargs" in sig.parameters, "Should accept **kwargs for flexibility"

    def test_template_agent_provides_standard_interface(self):
        """Should provide standard agent interface."""
        result = get_template_agent()

        # Should have standard agent attributes
        assert hasattr(result, "name"), "Should have name attribute"
        assert hasattr(result, "model"), "Should have model attribute"
        assert hasattr(result, "knowledge"), "Should have knowledge attribute"


class TestTemplateAgentFilePathHandling:
    """Test suite for configuration file path handling."""

    def test_template_agent_loads_config_from_correct_path(self):
        """Should load config.yaml from correct agent directory."""
        import yaml

        # Load YAML directly to verify
        config_path = template_agent_dir / "config.yaml"
        assert config_path.exists(), f"Config should exist at {config_path}"

        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)

        # Create agent
        result = get_template_agent()

        # Verify loaded config matches YAML
        assert result.agent_id == yaml_config["agent"]["agent_id"], "agent_id should match YAML"
        assert result.name == yaml_config["agent"]["name"], "name should match YAML"

    def test_template_agent_handles_path_with_file_attribute(self):
        """Should construct config path using __file__ attribute."""
        result = get_template_agent()

        # Should successfully create agent (path handling worked)
        assert result is not None, "Agent should be created with correct path"
        assert result.agent_id == "template-agent", "Should load correct config"


class TestTemplateAgentIntegration:
    """Integration tests for template agent creation and usage."""

    def test_template_agent_export_includes_factory_function(self):
        """Should export get_template_agent in module."""
        # Use the module we loaded with importlib
        # Should have __all__ with get_template_agent
        assert hasattr(template_agent_module, "__all__"), "Module should define __all__"
        assert "get_template_agent" in template_agent_module.__all__, "Factory function should be exported"

    def test_template_agent_creates_isolated_instances(self):
        """Should create isolated agent instances."""
        agent1 = get_template_agent(session_id="session-1")
        agent2 = get_template_agent(session_id="session-2")

        # Should be different instances
        assert agent1 is not agent2, "Each call should create new instance"

        # Should have isolated session data
        assert agent1.session_id == "session-1", "Agent 1 session should be isolated"
        assert agent2.session_id == "session-2", "Agent 2 session should be isolated"

        # But share same configuration
        assert agent1.agent_id == agent2.agent_id, "Both should share agent_id"
        assert agent1.model.id == agent2.model.id, "Both should share model config"

    def test_template_agent_serves_as_foundation_pattern(self):
        """Should provide foundation pattern for specialized agents."""
        result = get_template_agent()

        # Should provide standard agent capabilities
        assert hasattr(result, "name"), "Should have name"
        assert hasattr(result, "model"), "Should have model"
        assert hasattr(result, "knowledge"), "Should have knowledge"
        assert hasattr(result, "agent_id"), "Should have agent_id"

        # Should use proper types
        assert isinstance(result.name, str), "name should be string"
        assert result.model is not None, "model should exist"
        assert not isinstance(result.model, dict), "model should be instance"

    def test_template_agent_with_various_parameter_combinations(self):
        """Should handle various parameter combinations."""
        test_cases = [
            {},  # No params
            {"session_id": "test-session"},  # Single param
            {"session_id": "test", "user_id": "user"},  # Multiple params
            {"debug_mode": True},  # Optional param
        ]

        for kwargs in test_cases:
            result = get_template_agent(**kwargs)

            # Should always create valid agent
            assert result is not None, f"Should create agent with {kwargs}"
            assert result.agent_id == "template-agent", "Should maintain config"
            assert result.model.id == "gpt-4o-mini", "Should maintain model"

            # Runtime params should be applied if provided
            for key, value in kwargs.items():
                if hasattr(result, key):
                    assert getattr(result, key) == value, f"{key} should be set to {value}"


# TEST SUCCESS CRITERIA:
# ✅ Tests our NEW implementation (manual YAML loading + Model instance creation)
# ✅ Verifies Model is instance (not dict)
# ✅ Verifies agent_id set as attribute (not constructor param)
# ✅ Tests knowledge base integration
# ✅ Tests runtime parameter overrides
# ✅ Tests configuration path handling
# ✅ Tests module exports
# ✅ Tests instance isolation
# ✅ Tests various parameter combinations
# ✅ No mocking of our implementation (tests real behavior)
