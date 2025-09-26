"""Tests for AgentOS API routing."""

from __future__ import annotations

import os

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def agentos_client() -> TestClient:
    """Return TestClient bound to full FastAPI app."""

    app = create_app()
    with TestClient(app) as client:
        yield client


class TestAgentOSRouter:
    """Ensure AgentOS router wiring and auth guards behave correctly."""

    def test_agentos_config_requires_api_key(self, agentos_client: TestClient):
        """Requests without API key should be rejected."""
        response = agentos_client.get("/api/v1/agentos/config")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_agentos_config_returns_payload(self, agentos_client: TestClient):
        """Protected endpoint responds with AgentOS payload when authenticated."""
        headers = {"x-api-key": os.environ["HIVE_API_KEY"]}
        response = agentos_client.get("/api/v1/agentos/config", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        payload = response.json()

        assert payload["os_id"] == "automagik-hive"
        assert "hive_sessions" in payload["databases"]

    def test_legacy_config_alias_protected(self, agentos_client: TestClient):
        """Legacy alias should maintain API key guard."""
        response = agentos_client.get("/config")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_legacy_config_alias_returns_payload(self, agentos_client: TestClient):
        """Legacy alias should mirror versioned route output."""
        headers = {"x-api-key": os.environ["HIVE_API_KEY"]}
        response = agentos_client.get("/config", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        payload = response.json()

        assert payload["os_id"] == "automagik-hive"
        assert "hive_sessions" in payload["databases"]
