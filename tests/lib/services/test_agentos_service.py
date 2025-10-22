"""Tests for the AgentOS service facade and loader."""

from __future__ import annotations

import pytest
import yaml
from agno.os.schema import ConfigResponse

from lib.agentos import load_agentos_config
from lib.agentos.exceptions import AgentOSConfigError
from lib.config.settings import HiveSettings


class TestLoadAgentOSConfig:
    """Ensure AgentOS loader behaviour matches expectations."""

    def test_loader_prefers_explicit_config_path(self, tmp_path):
        """Custom YAML payload should override defaults when provided."""
        config_path = tmp_path / "custom_agentos.yaml"

        baseline = load_agentos_config()
        payload = baseline.model_dump(mode="python")
        payload["available_models"] = ["unit-test-model"]

        with config_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle)

        settings = HiveSettings().model_copy(
            update={
                "hive_agentos_config_path": config_path,
                "hive_agentos_enable_defaults": False,
            }
        )

        config = load_agentos_config(config_path=config_path, settings=settings)

        assert config.available_models == ["unit-test-model"]

    def test_loader_respects_defaults_disabled_flag(self, tmp_path):
        """Missing config should raise when defaults are disabled."""
        missing_path = tmp_path / "missing.yaml"
        settings = HiveSettings().model_copy(
            update={
                "hive_agentos_config_path": missing_path,
                "hive_agentos_enable_defaults": False,
            }
        )

        with pytest.raises(AgentOSConfigError):
            load_agentos_config(config_path=missing_path, settings=settings)

    def test_loader_applies_overrides(self):
        """Overrides should be merged into loaded configuration."""
        config = load_agentos_config(overrides={"available_models": ["override-model"]})

        assert config.available_models == ["override-model"]


class TestAgentOSService:
    """Validate AgentOS service behaviour."""

    def test_service_returns_schema_compliant_payload(self):
        """Service should build ConfigResponse with expected metadata."""
        from lib.services.agentos_service import AgentOSService

        settings = HiveSettings()
        service = AgentOSService(settings=settings)

        response = service.get_config_response()

        assert isinstance(response, ConfigResponse)
        assert response.os_id == "automagik-hive"
        assert {"hive_sessions", "hive_memories", "hive_metrics", "hive_knowledge", "hive_evals"}.issubset(
            set(response.databases)
        )

        assert response.chat is not None
        assert all(len(prompts) <= 3 for prompts in response.chat.quick_prompts.values())

        interfaces = {entry.type: entry.route for entry in response.interfaces}
        host = "localhost" if settings.hive_api_host in {"0.0.0.0", "::"} else settings.hive_api_host  # noqa: S104
        expected_base = f"http://{host}:{settings.hive_api_port}"

        assert interfaces["agentos-config"].endswith("/api/v1/agentos/config")
        assert interfaces["wish-catalog"] == f"{expected_base}/api/v1/wishes"
        assert interfaces["control-pane"] == expected_base

        if settings.hive_embed_playground:
            assert interfaces["playground"] == f"{expected_base}{settings.hive_playground_mount_path}"

    def test_service_serialization_matches_response_model(self):
        """Serialized payload should mirror ConfigResponse data."""
        from lib.services.agentos_service import AgentOSService

        service = AgentOSService(settings=HiveSettings())
        response = service.get_config_response()
        payload = service.serialize()

        assert payload == response.model_dump(mode="json")

    def test_interfaces_follow_control_pane_settings(self):
        """Interface routes should reflect control pane overrides."""
        from lib.services.agentos_service import AgentOSService

        settings = HiveSettings().model_copy(
            update={
                "hive_control_pane_base_url": "https://hive.example.com",
                "hive_playground_mount_path": "/surfaces/playground",
            }
        )
        service = AgentOSService(settings=settings)

        response = service.get_config_response(force_reload=True)

        interfaces = {entry.type: entry.route for entry in response.interfaces}

        assert interfaces["agentos-config"] == "https://hive.example.com/api/v1/agentos/config"
        assert interfaces["wish-catalog"] == "https://hive.example.com/api/v1/wishes"
        assert interfaces["control-pane"] == "https://hive.example.com"
        assert interfaces["playground"] == "https://hive.example.com/surfaces/playground"

    def test_config_response_reuses_cached_instance(self):
        """Subsequent calls should return cached response object."""
        from lib.services.agentos_service import AgentOSService

        service = AgentOSService(settings=HiveSettings())

        first = service.get_config_response()
        second = service.get_config_response()

        assert second is first

        reloaded = service.get_config_response(force_reload=True)

        assert reloaded is not first

    def test_refresh_invalidates_cache(self):
        """Manual refresh should drop cached response state."""
        from lib.services.agentos_service import AgentOSService

        service = AgentOSService(settings=HiveSettings())

        initial = service.get_config_response()
        service.refresh()
        refreshed = service.get_config_response()

        assert refreshed is not initial
