"""Tests for the AgentOS service facade."""

from __future__ import annotations

from agno.os.schema import ConfigResponse

from lib.config.settings import HiveSettings


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

    def test_service_serialization_matches_response_model(self):
        """Serialized payload should mirror ConfigResponse data."""
        from lib.services.agentos_service import AgentOSService

        service = AgentOSService(settings=HiveSettings())
        response = service.get_config_response()
        payload = service.serialize()

        assert payload == response.model_dump(mode="json")
