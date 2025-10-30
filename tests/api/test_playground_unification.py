"""Tests for playground unification and unified router integration.

Validates that playground endpoints are properly mounted under the unified router
with appropriate authentication and that the configuration surfaces are accessible.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi import status

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestPlaygroundUnification:
    """Test suite for playground router unification and mounting."""

    def test_unified_router_includes_playground(self, test_client, mock_auth_service):
        """Ensure unified router properly includes playground routes when enabled."""
        # Mock playground availability
        with patch.dict(os.environ, {"HIVE_EMBED_PLAYGROUND": "1"}):
            # The playground routes should be included in the app
            # This is validated by checking the interfaces endpoint
            mock_auth_service.validate_api_key.return_value = True

            from lib.auth.dependencies import require_api_key

            test_client.app.dependency_overrides[require_api_key] = lambda: True
            try:
                response = test_client.get(
                    "/api/v1/agentos/config",
                    headers={"x-api-key": os.environ["HIVE_API_KEY"]},
                )
            finally:
                test_client.app.dependency_overrides.pop(require_api_key, None)

            assert response.status_code == status.HTTP_200_OK

            payload = response.json()
            interfaces = payload.get("interfaces", [])

            # Find playground interface
            playground_interface = next((i for i in interfaces if i.get("type") == "playground"), None)

            if os.environ.get("HIVE_EMBED_PLAYGROUND", "1") != "0":
                assert playground_interface is not None, "Playground interface should be present"
                assert "route" in playground_interface
                assert "/playground" in playground_interface["route"]

    def test_unified_router_auth_enforcement(self, test_client, mock_auth_service):
        """Verify unified router enforces authentication when enabled."""
        # Enable authentication in environment for this test
        with patch.dict(os.environ, {"HIVE_AUTH_DISABLED": "false", "HIVE_ENVIRONMENT": "development"}, clear=False):
            # Re-create the app with auth enabled
            from starlette.testclient import TestClient

            import lib.auth.dependencies
            from api.main import create_app
            from lib.auth.service import AuthService

            # Force reload of global auth_service singleton to pick up new environment
            lib.auth.dependencies.auth_service = AuthService()

            app = create_app()
            with TestClient(app) as auth_client:
                # Attempt to access protected endpoint without auth
                response = auth_client.get("/api/v1/agentos/config")
                assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_health_endpoint_remains_public(self, test_client):
        """Ensure health check endpoint remains publicly accessible."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        assert payload["status"] == "success"

    def test_interfaces_includes_all_required_routes(self, test_client, mock_auth_service, api_headers):
        """Validate that interfaces payload includes all required route types."""
        mock_auth_service.validate_api_key.return_value = True

        from lib.auth.dependencies import require_api_key

        test_client.app.dependency_overrides[require_api_key] = lambda: True
        try:
            response = test_client.get("/api/v1/agentos/config", headers=api_headers)
        finally:
            test_client.app.dependency_overrides.pop(require_api_key, None)

        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        interfaces = payload.get("interfaces", [])
        interface_types = {i.get("type") for i in interfaces}

        # Required interface types
        required_types = {"agentos-config", "wish-catalog", "control-pane"}
        assert required_types.issubset(interface_types), (
            f"Missing required interface types. Expected: {required_types}, Got: {interface_types}"
        )

        # Playground is optional based on HIVE_EMBED_PLAYGROUND
        if os.environ.get("HIVE_EMBED_PLAYGROUND", "1") != "0":
            assert "playground" in interface_types


class TestUnifiedRouterIntegration:
    """Test integration between unified router and component endpoints."""

    def test_v1_router_aggregates_business_endpoints(self, test_client):
        """Verify v1_router properly aggregates all business endpoints."""
        # Health endpoint should be accessible
        response = test_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK

        # MCP status should be accessible (may require auth)
        response = test_client.get("/api/v1/mcp/status")
        assert response.status_code in {
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
        }

    def test_legacy_config_alias_parity(self, test_client, mock_auth_service, api_headers):
        """Ensure legacy /config alias maintains parity with versioned route."""
        mock_auth_service.validate_api_key.return_value = True

        from lib.auth.dependencies import require_api_key

        test_client.app.dependency_overrides[require_api_key] = lambda: True
        try:
            versioned_response = test_client.get("/api/v1/agentos/config", headers=api_headers)
            legacy_response = test_client.get("/config", headers=api_headers)
        finally:
            test_client.app.dependency_overrides.pop(require_api_key, None)

        assert versioned_response.status_code == status.HTTP_200_OK
        assert legacy_response.status_code == status.HTTP_200_OK

        # Payloads should be identical
        assert versioned_response.json() == legacy_response.json()

    def test_startup_orchestration_populates_interfaces(self, test_client, mock_auth_service, api_headers):
        """Verify startup orchestration properly populates interface routes."""
        mock_auth_service.validate_api_key.return_value = True

        from lib.auth.dependencies import require_api_key

        test_client.app.dependency_overrides[require_api_key] = lambda: True
        try:
            response = test_client.get("/api/v1/agentos/config", headers=api_headers)
        finally:
            test_client.app.dependency_overrides.pop(require_api_key, None)

        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        interfaces = payload.get("interfaces", [])

        # Each interface should have required fields
        for interface in interfaces:
            assert "type" in interface
            assert "route" in interface
            assert isinstance(interface["route"], str)
            assert interface["route"].startswith("http")
