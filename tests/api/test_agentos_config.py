"""High-level tests for AgentOS configuration endpoints."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def agentos_client() -> TestClient:
    """Return TestClient bound to the full FastAPI app with auth enabled."""
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


class TestAgentOSConfigEndpoints:
    """Validate authentication and payload parity for AgentOS routes."""

    def test_requires_api_key_for_both_routes(self, agentos_client: TestClient):
        """Versioned and legacy endpoints should reject anonymous requests."""
        versioned = agentos_client.get("/api/v1/agentos/config")
        legacy = agentos_client.get("/config")

        assert versioned.status_code == status.HTTP_401_UNAUTHORIZED
        assert legacy.status_code == status.HTTP_401_UNAUTHORIZED

    def test_alias_matches_versioned_payload(self, agentos_client: TestClient):
        """Legacy alias should mirror versioned route response content."""
        headers = {"x-api-key": os.environ["HIVE_API_KEY"]}

        versioned = agentos_client.get("/api/v1/agentos/config", headers=headers)
        legacy = agentos_client.get("/config", headers=headers)

        assert versioned.status_code == status.HTTP_200_OK
        assert legacy.status_code == status.HTTP_200_OK

        versioned_payload = versioned.json()
        legacy_payload = legacy.json()

        assert versioned_payload == legacy_payload

        quick_prompts = versioned_payload.get("chat", {}).get("quick_prompts", {})
        assert quick_prompts
        assert all(len(entries) <= 3 for entries in quick_prompts.values())

        raw_host = os.environ.get("HIVE_API_HOST", "0.0.0.0")  # noqa: S104
        host = "localhost" if raw_host in {"0.0.0.0", "::"} else raw_host  # noqa: S104
        expected_base = f"http://{host}:{os.environ['HIVE_API_PORT']}"
        routes = {entry["type"]: entry["route"] for entry in versioned_payload["interfaces"]}

        assert routes["agentos-config"] == f"{expected_base}/api/v1/agentos/config"
        assert routes["wish-catalog"] == f"{expected_base}/api/v1/wishes"
        assert routes["control-pane"] == expected_base

        embed_playground = os.environ.get("HIVE_EMBED_PLAYGROUND", "1").lower() not in {
            "0",
            "false",
        }
        if embed_playground:
            mount_path = os.environ.get("HIVE_PLAYGROUND_MOUNT_PATH", "/playground")
            assert routes["playground"] == f"{expected_base}{mount_path}"
