"""High-level tests for AgentOS configuration endpoints."""

from __future__ import annotations

import os

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def agentos_client() -> TestClient:
    """Return TestClient bound to the full FastAPI app."""

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
