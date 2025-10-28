"""
Regression tests for model configuration bug fix.

This suite ensures that agents respect their YAML-configured models
and never fall back to Agno's default gpt-4o.

Bug Context:
- Original issue: _handle_model_config() returned dict instead of Model instance
- Impact: All agents ignored YAML config and used default gpt-4o
- Fix: Return resolve_model() instead of dict
- Fix Location: lib/utils/proxy_agents.py::_handle_model_config()
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, Mock
import os

# Set test database URL BEFORE loading any modules
os.environ["HIVE_DATABASE_URL"] = "sqlite:///test.db"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["HIVE_DEFAULT_MODEL"] = "gpt-4.1-mini"

project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestModelConfigRegression:
    """Regression tests for model configuration bug."""

    def test_handle_model_config_never_returns_dict(self):
        """CRITICAL: Ensure _handle_model_config never returns dict."""
        from lib.utils.proxy_agents import AgnoAgentProxy

        proxy = AgnoAgentProxy()

        # Test with various configs
        configs = [
            {"id": "gpt-4o-mini", "temperature": 0.7},
            {"id": "claude-sonnet-4-20250514", "temperature": 0.5},
            {"id": "gpt-4o", "max_tokens": 2000},
        ]

        for config in configs:
            result = proxy._handle_model_config(
                model_config=config.copy(), config={}, component_id="test-agent", model_id=config["id"]
            )

            # CRITICAL: Must never be dict
            assert not isinstance(result, dict), (
                f"_handle_model_config returned dict for {config['id']}, bug has regressed!"
            )

            # Must be Model instance
            assert hasattr(result, "id"), f"Result missing 'id' attribute for {config['id']}"

            assert result.id == config["id"], f"Model ID mismatch: expected {config['id']}, got {result.id}"

    def test_agent_registry_uses_model_instance(self):
        """Verify AgentRegistry creates agents with Model instances."""
        from ai.agents.registry import AgentRegistry

        # Get template agent via registry
        agent = AgentRegistry.get_agent("template-agent")

        # Must have model attribute
        assert hasattr(agent, "model"), "Agent missing model attribute"

        # Model must not be None or dict
        assert agent.model is not None, "Agent model is None"
        assert not isinstance(agent.model, dict), "Agent model is dict - bug has regressed!"

        # Model must have id attribute
        assert hasattr(agent.model, "id"), "Model missing id attribute"

    def test_template_agent_respects_yaml_model_config(self):
        """Verify template agent uses model from config.yaml, not default."""
        from ai.agents.template_agent.agent import get_template_agent
        import yaml
        from pathlib import Path

        # Load expected config
        config_path = project_root / "ai" / "agents" / "template-agent" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        expected_model_id = config["model"]["id"]

        # Create agent
        agent = get_template_agent()

        # Verify it uses configured model, not default
        assert agent.model.id == expected_model_id, (
            f"Agent using {agent.model.id} instead of configured {expected_model_id}"
        )

        # Specifically check it's NOT using default gpt-4o
        assert agent.model.id != "gpt-4o", "Agent fell back to default gpt-4o - bug has regressed!"

    def test_multiple_agents_use_different_models(self):
        """Verify different agents can use different models."""
        from lib.utils.proxy_agents import AgnoAgentProxy

        proxy = AgnoAgentProxy()

        # Simulate different agent configs
        agent_configs = [
            ("agent-1", "gpt-4o-mini"),
            ("agent-2", "claude-sonnet-4-20250514"),
            ("agent-3", "gpt-4o"),
        ]

        models = {}
        for agent_id, model_id in agent_configs:
            result = proxy._handle_model_config(
                model_config={"id": model_id, "temperature": 0.7}, config={}, component_id=agent_id, model_id=model_id
            )
            models[agent_id] = result

        # Verify each agent got its own model
        for agent_id, expected_model_id in agent_configs:
            actual = models[agent_id]
            assert hasattr(actual, "id"), f"{agent_id} model missing id"
            assert actual.id == expected_model_id, f"{agent_id} got {actual.id} instead of {expected_model_id}"

    def test_model_config_with_none_id_uses_default(self):
        """Verify None model_id properly resolves to default."""
        from lib.utils.proxy_agents import AgnoAgentProxy
        import os

        proxy = AgnoAgentProxy()

        # Test with None model_id (should use env default)
        result = proxy._handle_model_config(
            model_config={"temperature": 0.7}, config={}, component_id="test-agent", model_id=None
        )

        # Should still return Model instance (not dict)
        assert not isinstance(result, dict), "Returned dict for None model_id"
        assert hasattr(result, "id"), "Result missing id attribute"

        # Should use HIVE_DEFAULT_MODEL from env
        expected_default = os.getenv("HIVE_DEFAULT_MODEL", "gpt-4.1-mini")
        assert result.id == expected_default

    def test_model_config_preserves_all_parameters(self):
        """Verify model config parameters are preserved."""
        from lib.utils.proxy_agents import AgnoAgentProxy

        proxy = AgnoAgentProxy()

        config = {"id": "gpt-4o-mini", "temperature": 0.9, "max_tokens": 2000, "top_p": 0.95}

        result = proxy._handle_model_config(
            model_config=config.copy(), config={}, component_id="test-agent", model_id="gpt-4o-mini"
        )

        # Verify Model instance has expected attributes
        assert hasattr(result, "id")
        assert result.id == "gpt-4o-mini"

        # Temperature should be preserved
        assert hasattr(result, "temperature")
        assert result.temperature == 0.9


class TestAgentFactoryPatternRegression:
    """Regression tests for agent factory pattern."""

    def test_factory_never_passes_agent_id_to_constructor(self):
        """CRITICAL: Ensure factory doesn't pass agent_id to Agent()."""
        from ai.agents.template_agent.agent import get_template_agent

        # This should NOT raise TypeError about agent_id
        try:
            agent = get_template_agent(session_id="test")
            success = True
        except TypeError as e:
            if "agent_id" in str(e):
                pytest.fail(f"Factory passing agent_id to Agent() constructor: {e}")
            raise

        assert success, "Agent creation failed"

    def test_factory_sets_agent_id_as_attribute(self):
        """Verify factory sets agent_id as instance attribute."""
        from ai.agents.template_agent.agent import get_template_agent

        agent = get_template_agent()

        # Should have agent_id as attribute
        assert hasattr(agent, "agent_id"), "Agent missing agent_id attribute"
        assert agent.agent_id == "template-agent"

    def test_factory_loads_from_yaml_not_hardcoded(self):
        """Verify factory loads from YAML, not hardcoded values."""
        from ai.agents.template_agent.agent import get_template_agent
        import yaml
        from pathlib import Path

        # Load YAML to get expected values
        config_path = project_root / "ai" / "agents" / "template-agent" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        agent = get_template_agent()

        # Verify values match YAML (not hardcoded)
        assert agent.name == config["agent"]["name"]
        assert agent.model.id == config["model"]["id"]
        # Instructions should include YAML content
        if config.get("instructions"):
            assert agent.instructions is not None


class TestResolveModelUtilityRegression:
    """Regression tests for resolve_model utility function."""

    def test_resolve_model_never_returns_dict(self):
        """CRITICAL: resolve_model must never return dict."""
        from lib.config.models import resolve_model

        test_cases = [
            {"model_id": "gpt-4o-mini", "temperature": 0.7},
            {"model_id": "claude-sonnet-4-20250514", "temperature": 0.5},
            {"model_id": "gpt-4o"},
        ]

        for kwargs in test_cases:
            result = resolve_model(**kwargs)

            # CRITICAL: Must never be dict
            assert not isinstance(result, dict), f"resolve_model returned dict for {kwargs}, bug has regressed!"

            # Must be Model instance with id
            assert hasattr(result, "id"), f"Missing id for {kwargs}"

    def test_resolve_model_respects_temperature(self):
        """Verify resolve_model preserves temperature parameter."""
        from lib.config.models import resolve_model

        result = resolve_model(model_id="gpt-4o-mini", temperature=0.123)

        assert hasattr(result, "temperature")
        assert result.temperature == 0.123

    def test_resolve_model_with_existing_model_instance(self):
        """Verify resolve_model handles existing Model instances correctly."""
        from lib.config.models import resolve_model
        from agno.models.openai import OpenAIChat

        # Create existing instance
        existing = OpenAIChat(id="gpt-4o-mini")

        # Pass to resolve_model
        result = resolve_model(model=existing)

        # Should return same instance
        assert result is existing
        assert result.id == "gpt-4o-mini"


class TestRegressionWithMockAgents:
    """Test regression with mocked agent creation."""

    def test_proxy_agents_creates_model_instances(self):
        """Verify AgnoAgentProxy creates Model instances for all components."""
        from lib.utils.proxy_agents import AgnoAgentProxy

        proxy = AgnoAgentProxy()

        # Test with agent, team, workflow
        component_types = ["agent", "team", "workflow"]

        for component_type in component_types:
            result = proxy._handle_model_config(
                model_config={"id": "gpt-4o-mini", "temperature": 0.7},
                config={},
                component_id=f"test-{component_type}",
                model_id="gpt-4o-mini",
            )

            # All component types should get Model instances
            assert not isinstance(result, dict), f"{component_type} got dict instead of Model instance"
            assert hasattr(result, "id")
            assert result.id == "gpt-4o-mini"


class TestModelDefaultFallbackRegression:
    """Test default model fallback behavior."""

    def test_missing_model_config_uses_env_default(self):
        """Verify missing model config falls back to HIVE_DEFAULT_MODEL."""
        from lib.utils.proxy_agents import AgnoAgentProxy
        import os

        proxy = AgnoAgentProxy()

        # Empty model config, no model_id
        result = proxy._handle_model_config(model_config={}, config={}, component_id="test-agent", model_id=None)

        # Should use env default
        expected = os.getenv("HIVE_DEFAULT_MODEL", "gpt-4.1-mini")
        assert result.id == expected

    def test_explicit_model_overrides_default(self):
        """Verify explicit model_id overrides default."""
        from lib.utils.proxy_agents import AgnoAgentProxy

        proxy = AgnoAgentProxy()

        # Explicit model should override default
        result = proxy._handle_model_config(
            model_config={"id": "claude-sonnet-4-20250514"},
            config={},
            component_id="test-agent",
            model_id="claude-sonnet-4-20250514",
        )

        # Should NOT be default
        assert result.id == "claude-sonnet-4-20250514"
        assert result.id != "gpt-4o"  # Not Agno default
        assert result.id != os.getenv("HIVE_DEFAULT_MODEL")  # Not env default


# REGRESSION TEST SUCCESS CRITERIA:
# ✅ _handle_model_config never returns dict
# ✅ All agents use Model instances
# ✅ YAML configs respected (not default gpt-4o)
# ✅ resolve_model creates instances correctly
# ✅ Factory pattern doesn't pass agent_id to constructor
# ✅ Multiple agents can use different models
# ✅ Temperature and other params preserved
# ✅ Default fallback works correctly
