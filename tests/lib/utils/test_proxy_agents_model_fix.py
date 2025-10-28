"""
Test Model Configuration Bug Fix in AgnoAgentProxy

Verifies that _handle_model_config() returns Model instance (not dict)
after the bug fix in lib/utils/proxy_agents.py
"""

import pytest
from unittest.mock import patch

from lib.utils.proxy_agents import AgnoAgentProxy


class TestModelConfigFix:
    """Test suite for model configuration bug fix"""

    def test_handle_model_config_returns_model_instance(self):
        """Verify _handle_model_config returns Model instance, not dict."""
        proxy = AgnoAgentProxy()

        model_config = {"id": "gpt-4o-mini", "temperature": 0.7, "provider": "openai"}

        result = proxy._handle_model_config(
            model_config=model_config, config={}, component_id="test-agent", db_url=None, model_id="gpt-4o-mini"
        )

        # Critical assertions
        assert not isinstance(result, dict), "Should return Model instance, not dict"
        assert hasattr(result, "id"), "Model should have id attribute"
        assert result.id == "gpt-4o-mini", f"Model ID should be 'gpt-4o-mini', got {result.id}"
        assert hasattr(result, "temperature"), "Model should have temperature"

    def test_handle_model_config_with_none_model_id(self):
        """Verify default model resolution works with None model_id."""
        proxy = AgnoAgentProxy()

        model_config = {"temperature": 0.7, "provider": "openai"}

        with patch.dict("os.environ", {"HIVE_DEFAULT_MODEL": "gpt-4o-mini"}, clear=False):
            result = proxy._handle_model_config(
                model_config=model_config, config={}, component_id="test-agent", db_url=None, model_id=None
            )

        # Should still return Model instance
        assert not isinstance(result, dict), "Should return Model instance even with None model_id"
        assert hasattr(result, "id"), "Model should have id attribute"

    def test_handle_model_config_preserves_temperature(self):
        """Verify temperature and other config values are preserved."""
        proxy = AgnoAgentProxy()

        model_config = {"id": "gpt-4o-mini", "temperature": 0.9, "provider": "openai"}

        result = proxy._handle_model_config(
            model_config=model_config, config={}, component_id="test-agent", db_url=None, model_id="gpt-4o-mini"
        )

        assert not isinstance(result, dict), "Should return Model instance, not dict"
        assert result.temperature == 0.9, f"Temperature should be 0.9, got {result.temperature}"

    def test_handle_model_config_uses_config_id(self):
        """Verify model_config['id'] is used when present."""
        proxy = AgnoAgentProxy()

        model_config = {
            "id": "gpt-4o",  # Config specifies gpt-4o
            "temperature": 0.7,
            "provider": "openai",
        }

        result = proxy._handle_model_config(
            model_config=model_config,
            config={},
            component_id="test-agent",
            db_url=None,
            model_id="gpt-4o-mini",  # model_id kwarg present but config['id'] takes precedence
        )

        assert not isinstance(result, dict), "Should return Model instance, not dict"
        assert result.id == "gpt-4o", f"Model ID should be 'gpt-4o' from config, got {result.id}"

    def test_handle_model_config_type_consistency(self):
        """Verify the return type is always Model, never dict."""
        proxy = AgnoAgentProxy()

        test_cases = [
            {"id": "gpt-4o-mini", "temperature": 0.7},
            {"id": "claude-sonnet-4-20250514", "temperature": 0.5},
            {"id": "gpt-4o", "temperature": 0.3},
        ]

        for model_config in test_cases:
            result = proxy._handle_model_config(
                model_config=model_config,
                config={},
                component_id="test-agent",
                db_url=None,
                model_id=model_config["id"],
            )

            assert not isinstance(result, dict), (
                f"Should return Model instance (not dict) for {model_config['id']}, got {type(result)}"
            )
