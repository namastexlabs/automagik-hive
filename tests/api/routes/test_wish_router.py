"""Tests for the wish catalog API router."""

from __future__ import annotations

from fastapi import status


class TestWishRouter:
    """Validate authentication and response contract for /api/v1/wishes."""

    def test_wish_catalog_requires_auth(self, test_client, mock_auth_service):
        """Ensure requests without a valid API key are rejected."""

        mock_auth_service.validate_api_key.return_value = False

        response = test_client.get("/api/v1/wishes")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_wish_catalog_returns_entries(
        self, test_client, mock_auth_service, api_headers
    ):
        """Ensure the wish catalog lists available wish metadata."""

        mock_auth_service.validate_api_key.return_value = True

        from lib.auth.dependencies import require_api_key

        test_client.app.dependency_overrides[require_api_key] = lambda: True
        try:
            response = test_client.get("/api/v1/wishes", headers=api_headers)
        finally:
            test_client.app.dependency_overrides.pop(require_api_key, None)

        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        assert "wishes" in payload
        assert isinstance(payload["wishes"], list)
        assert payload["wishes"], "Expected at least one wish entry"

        first_entry = payload["wishes"][0]
        assert {"id", "title", "status", "path"} <= set(first_entry.keys())
