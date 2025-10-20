"""Unit tests for ServiceManager.agentos_config CLI helper."""

from __future__ import annotations

import json

from cli.commands.service import ServiceManager
from lib.agentos.exceptions import AgentOSConfigError


class TestServiceManagerAgentOSConfig:
    """Ensure CLI entry point surfaces AgentOS configuration cleanly."""

    def test_returns_false_when_loader_fails(self, capsys, monkeypatch):
        """Errors from the service should be surfaced with helpful messaging."""

        class FailingService:
            def __init__(self) -> None:
                raise AgentOSConfigError("boom")

        monkeypatch.setattr("lib.services.agentos_service.AgentOSService", FailingService)

        manager = ServiceManager()
        success = manager.agentos_config()
        output = capsys.readouterr().out

        assert success is False
        assert "Unable to load AgentOS configuration" in output

    def test_prints_summary_output(self, capsys, monkeypatch):
        """Default rendering should include key fields from payload."""
        payload = {
            "os_id": "unit-test-os",
            "name": "Unit Test AgentOS",
            "available_models": ["model-a", "model-b"],
            "agents": [{"id": "alpha-agent", "name": "Alpha Agent"}],
            "teams": [],
            "workflows": [],
        }

        class StubService:
            def serialize(self) -> dict[str, object]:
                return payload

        monkeypatch.setattr("lib.services.agentos_service.AgentOSService", StubService)

        manager = ServiceManager()
        success = manager.agentos_config()
        output = capsys.readouterr().out

        assert success is True
        assert "AgentOS Configuration Snapshot" in output
        assert "Unit Test AgentOS" in output
        assert "model-a" in output

    def test_json_output_serializes_payload(self, capsys, monkeypatch):
        """JSON mode should dump payload to stdout with deterministic ordering."""
        payload = {
            "os_id": "json-test-os",
            "available_models": ["model-x"],
            "agents": [],
            "teams": [],
            "workflows": [],
        }

        class StubService:
            def serialize(self) -> dict[str, object]:
                return payload

        monkeypatch.setattr("lib.services.agentos_service.AgentOSService", StubService)

        manager = ServiceManager()
        success = manager.agentos_config(json_output=True)
        output = capsys.readouterr().out

        assert success is True
        assert json.loads(output) == payload
