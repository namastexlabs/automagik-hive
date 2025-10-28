"""
Simplified regression tests for model configuration bug fix.

This suite ensures that agents respect their YAML-configured models
and never fall back to Agno's default gpt-4o.

Bug Context:
- Original issue: Agents returned dict instead of Model instance
- Impact: All agents ignored YAML config and used default gpt-4o
- Fix: Use resolve_model() to create Model instances
- Fix Location: lib/utils/proxy_agents.py, lib/config/models.py

REGRESSION PROTECTION:
- Agent models must NEVER be dict instances
- Agents must use YAML-configured models, not defaults
- resolve_model() must ALWAYS return Model instances
"""

import sys
from pathlib import Path
import pytest
import os
from unittest.mock import patch, MagicMock

# Set test database URL BEFORE loading any modules
os.environ["HIVE_DATABASE_URL"] = "sqlite:///test.db"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["HIVE_DEFAULT_MODEL"] = "gpt-4.1-mini"

# Test is in tests/integration/, so need to go up 2 levels to reach project root
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestCriticalModelRegressions:
    """Critical regression tests to prevent model config bug from recurring."""

    @patch("lib.knowledge.get_agentos_knowledge_base")
    def test_CRITICAL_agent_model_never_dict(self, mock_knowledge):
        """CRITICAL: Agent models must NEVER be dict instances."""
        # Mock knowledge base to avoid database connections
        mock_knowledge.return_value = None

        # Direct import using importlib to handle hyphenated directory
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "template_agent", project_root / "ai" / "agents" / "template-agent" / "agent.py"
        )
        template_agent_module = importlib.util.module_from_spec(spec)
        sys.modules["template_agent"] = template_agent_module
        spec.loader.exec_module(template_agent_module)

        get_template_agent = template_agent_module.get_template_agent
        agent = get_template_agent()

        # CRITICAL CHECK: Model must not be dict
        assert not isinstance(agent.model, dict), f"REGRESSION: Agent model is dict: {agent.model} - BUG HAS RETURNED!"

        # Must be proper Model instance
        assert hasattr(agent.model, "id"), "Model missing id attribute"
        assert hasattr(agent.model, "provider"), "Model missing provider attribute"

    @patch("lib.knowledge.get_agentos_knowledge_base")
    def test_CRITICAL_yaml_config_respected(self, mock_knowledge):
        """CRITICAL: Agents must use YAML-configured models, not defaults."""
        # Mock knowledge base to avoid database connections
        mock_knowledge.return_value = None

        # Direct import using importlib to handle hyphenated directory
        import importlib.util
        import sys
        import yaml

        spec = importlib.util.spec_from_file_location(
            "template_agent", project_root / "ai" / "agents" / "template-agent" / "agent.py"
        )
        template_agent_module = importlib.util.module_from_spec(spec)
        sys.modules["template_agent"] = template_agent_module
        spec.loader.exec_module(template_agent_module)

        get_template_agent = template_agent_module.get_template_agent

        # Load expected config
        config_path = project_root / "ai" / "agents" / "template-agent" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        expected_model_id = config["model"]["id"]
        agent = get_template_agent()

        # CRITICAL CHECK: Uses configured model, not default
        assert agent.model.id == expected_model_id, (
            f"REGRESSION: Agent using {agent.model.id} instead of configured {expected_model_id}!"
        )

        # CRITICAL CHECK: NOT using Agno's default
        assert agent.model.id != "gpt-4o", "REGRESSION: Agent fell back to default gpt-4o - BUG HAS RETURNED!"

    def test_CRITICAL_resolve_model_returns_instances(self):
        """CRITICAL: resolve_model must ALWAYS return Model instances."""
        from lib.config.models import resolve_model

        # Test with different model IDs
        test_models = ["gpt-4o-mini", "gpt-4o"]

        for model_id in test_models:
            result = resolve_model(model_id=model_id, temperature=0.7)

            # CRITICAL CHECK: Must never be dict
            assert not isinstance(result, dict), (
                f"REGRESSION: resolve_model returned dict for {model_id} - BUG HAS RETURNED!"
            )

            # Must be Model instance with id
            assert hasattr(result, "id"), f"Model missing id for {model_id}"
            assert result.id == model_id, f"ID mismatch for {model_id}"

    @pytest.mark.asyncio
    async def test_agent_registry_creates_model_instances(self):
        """Verify AgentRegistry creates agents with Model instances."""
        from ai.agents.registry import AgentRegistry

        agent = await AgentRegistry.get_agent("template-agent")

        # Must have model attribute
        assert hasattr(agent, "model"), "Agent missing model attribute"

        # Model must not be None or dict
        assert agent.model is not None, "Agent model is None"
        assert not isinstance(agent.model, dict), "REGRESSION: Agent model is dict!"

        # Model must have id attribute
        assert hasattr(agent.model, "id"), "Model missing id attribute"

    @patch("lib.knowledge.get_agentos_knowledge_base")
    def test_factory_never_passes_agent_id_to_constructor(self, mock_knowledge):
        """Verify factory doesn't pass agent_id to Agent() constructor."""
        # Mock knowledge base to avoid database connections
        mock_knowledge.return_value = None

        # Direct import using importlib to handle hyphenated directory
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "template_agent", project_root / "ai" / "agents" / "template-agent" / "agent.py"
        )
        template_agent_module = importlib.util.module_from_spec(spec)
        sys.modules["template_agent"] = template_agent_module
        spec.loader.exec_module(template_agent_module)

        get_template_agent = template_agent_module.get_template_agent

        # This should NOT raise TypeError about agent_id
        try:
            agent = get_template_agent(session_id="test")
            success = True
        except TypeError as e:
            if "agent_id" in str(e):
                pytest.fail(f"Factory passing agent_id to Agent() constructor: {e}")
            raise

        assert success, "Agent creation failed"

    @patch("lib.knowledge.get_agentos_knowledge_base")
    def test_factory_sets_agent_id_as_attribute(self, mock_knowledge):
        """Verify factory sets agent_id as instance attribute."""
        # Mock knowledge base to avoid database connections
        mock_knowledge.return_value = None

        # Direct import using importlib to handle hyphenated directory
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "template_agent", project_root / "ai" / "agents" / "template-agent" / "agent.py"
        )
        template_agent_module = importlib.util.module_from_spec(spec)
        sys.modules["template_agent"] = template_agent_module
        spec.loader.exec_module(template_agent_module)

        get_template_agent = template_agent_module.get_template_agent
        agent = get_template_agent()

        # Should have agent_id as attribute
        assert hasattr(agent, "agent_id"), "Agent missing agent_id attribute"
        assert agent.agent_id == "template-agent"

    def test_resolve_model_preserves_temperature(self):
        """Verify resolve_model preserves temperature parameter."""
        from lib.config.models import resolve_model

        result = resolve_model(model_id="gpt-4o-mini", temperature=0.123)

        assert hasattr(result, "temperature")
        assert result.temperature == 0.123


# REGRESSION TEST SUCCESS CRITERIA:
# ✅ Agent models are NEVER dict instances
# ✅ YAML configs are respected (not default gpt-4o)
# ✅ resolve_model creates instances correctly
# ✅ Factory pattern doesn't pass agent_id to constructor
# ✅ Temperature and other params preserved
