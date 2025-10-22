"""Tests for AgentOS API routing."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def agentos_client() -> TestClient:
    """Return TestClient bound to full FastAPI app with auth enabled."""
    # Enable authentication for these tests by setting HIVE_AUTH_DISABLED=false
    with patch.dict(os.environ, {"HIVE_AUTH_DISABLED": "false", "HIVE_ENVIRONMENT": "development"}, clear=False):
        # Force reload of global auth_service singleton to pick up new environment
        import lib.auth.dependencies
        from lib.auth.service import AuthService

        # Create a new auth service instance with the patched environment
        lib.auth.dependencies.auth_service = AuthService()

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
        raw_host = os.environ.get("HIVE_API_HOST", "0.0.0.0")  # noqa: S104
        host = "localhost" if raw_host in {"0.0.0.0", "::"} else raw_host  # noqa: S104
        expected_base = f"http://{host}:{os.environ['HIVE_API_PORT']}"

        routes = {entry["type"]: entry["route"] for entry in payload["interfaces"]}
        assert routes["agentos-config"] == f"{expected_base}/api/v1/agentos/config"
        assert routes["wish-catalog"] == f"{expected_base}/api/v1/wishes"
        assert routes["control-pane"] == expected_base
        if os.environ.get("HIVE_EMBED_PLAYGROUND", "1") not in {"0", "false", "False"}:
            assert (
                routes["playground"] == f"{expected_base}{os.environ.get('HIVE_PLAYGROUND_MOUNT_PATH', '/playground')}"
            )

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
        raw_host = os.environ.get("HIVE_API_HOST", "0.0.0.0")  # noqa: S104
        host = "localhost" if raw_host in {"0.0.0.0", "::"} else raw_host  # noqa: S104
        expected_base = f"http://{host}:{os.environ['HIVE_API_PORT']}"
        routes = {entry["type"]: entry["route"] for entry in payload["interfaces"]}

        assert routes["agentos-config"] == f"{expected_base}/api/v1/agentos/config"
        assert routes["wish-catalog"] == f"{expected_base}/api/v1/wishes"
        assert routes["control-pane"] == expected_base
        if os.environ.get("HIVE_EMBED_PLAYGROUND", "1") not in {"0", "false", "False"}:
            assert (
                routes["playground"] == f"{expected_base}{os.environ.get('HIVE_PLAYGROUND_MOUNT_PATH', '/playground')}"
            )
