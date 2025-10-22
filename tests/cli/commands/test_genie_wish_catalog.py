"""Tests for the genie wish catalog CLI command.

Validates that the CLI can successfully retrieve and display wish metadata
from the API endpoint with proper authentication and error handling.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.commands.genie import GenieCommands  # noqa: E402


class TestGenieWishCatalog:
    """Test suite for genie wish catalog command."""

    @pytest.fixture
    def genie_cmd(self):
        """Create GenieCommands instance."""
        return GenieCommands()

    @pytest.fixture
    def mock_httpx_response(self):
        """Mock httpx response for wish catalog."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "wishes": [
                {
                    "id": "agno-agentos-unification",
                    "title": "Agno AgentOS Unification WISH",
                    "status": "APPROVED",
                    "path": "genie/wishes/agno-agentos-unification-wish.md",
                },
                {
                    "id": "api-configuration",
                    "title": "AgentOS API Configuration",
                    "status": "COMPLETED",
                    "path": "genie/wishes/api-configuration-wish.md",
                },
            ]
        }
        return mock_response

    def test_list_wishes_success(self, genie_cmd, mock_httpx_response):
        """Test successful wish catalog retrieval and display."""
        with patch("httpx.get", return_value=mock_httpx_response):
            result = genie_cmd.list_wishes(
                api_base="http://localhost:8886",
                api_key="hive_test_key_12345678901234567890123456789012",
            )

            assert result is True
            mock_httpx_response.raise_for_status.assert_called_once()

    def test_list_wishes_with_auth_header(self, genie_cmd, mock_httpx_response):
        """Test that API key is properly included in request headers."""
        api_key = "hive_test_key_12345678901234567890123456789012"

        with patch("httpx.get", return_value=mock_httpx_response) as mock_get:
            genie_cmd.list_wishes(api_base="http://localhost:8886", api_key=api_key)

            # Verify httpx.get was called with correct headers
            call_args = mock_get.call_args
            assert call_args is not None
            headers = call_args.kwargs.get("headers", {})
            assert headers.get("X-API-Key") == api_key

    def test_list_wishes_without_auth_header(self, genie_cmd, mock_httpx_response):
        """Test wish catalog request without authentication."""
        with patch("httpx.get", return_value=mock_httpx_response) as mock_get:
            genie_cmd.list_wishes(api_base="http://localhost:8886", api_key=None)

            # Verify httpx.get was called with empty or no auth header
            call_args = mock_get.call_args
            assert call_args is not None
            headers = call_args.kwargs.get("headers", {})
            assert "X-API-Key" not in headers or headers.get("X-API-Key") is None

    def test_list_wishes_default_api_base(self, genie_cmd, mock_httpx_response):
        """Test that default API base URL is used when not specified."""
        with patch("httpx.get", return_value=mock_httpx_response) as mock_get:
            genie_cmd.list_wishes()

            # Verify default URL is used
            call_args = mock_get.call_args
            assert "http://localhost:8886/api/v1/wishes" in str(call_args)

    def test_list_wishes_connection_error(self, genie_cmd, capsys):
        """Test handling of connection errors."""
        import httpx

        with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            result = genie_cmd.list_wishes(api_base="http://localhost:8886")

            assert result is False
            captured = capsys.readouterr()
            assert "Could not connect to API" in captured.err
            assert "Is the server running?" in captured.err

    def test_list_wishes_http_error(self, genie_cmd, capsys):
        """Test handling of HTTP errors (401, 403, 500, etc.)."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason_phrase = "Unauthorized"

        http_error = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = http_error

            result = genie_cmd.list_wishes(api_base="http://localhost:8886")

            assert result is False
            captured = capsys.readouterr()
            assert "API request failed" in captured.err
            assert "401" in captured.err

    def test_list_wishes_empty_catalog(self, genie_cmd):
        """Test display when wish catalog is empty."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"wishes": []}

        with patch("httpx.get", return_value=mock_response):
            result = genie_cmd.list_wishes(api_base="http://localhost:8886")

            # Should still succeed but show no wishes
            assert result is True

    def test_list_wishes_malformed_response(self, genie_cmd, capsys):
        """Test handling of malformed JSON response."""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("httpx.get", return_value=mock_response):
            result = genie_cmd.list_wishes(api_base="http://localhost:8886")

            assert result is False
            captured = capsys.readouterr()
            assert "Failed to list wishes" in captured.err

    def test_list_wishes_missing_rich_dependency(self, genie_cmd, capsys, monkeypatch):
        """Test graceful handling when httpx/rich dependencies are missing."""
        # Simulate missing dependencies by setting RICH_AVAILABLE to False
        monkeypatch.setattr("cli.commands.genie.RICH_AVAILABLE", False)

        result = genie_cmd.list_wishes()

        assert result is False
        captured = capsys.readouterr()
        assert "requires httpx and rich" in captured.err

    def test_list_wishes_timeout(self, genie_cmd, capsys):
        """Test handling of request timeout."""
        import httpx

        with patch("httpx.get", side_effect=httpx.TimeoutException("Request timed out")):
            result = genie_cmd.list_wishes(api_base="http://localhost:8886")

            assert result is False
            captured = capsys.readouterr()
            assert "Failed to list wishes" in captured.err

    def test_list_wishes_displays_all_fields(self, genie_cmd, mock_httpx_response):
        """Verify that all wish fields are properly extracted and displayed."""
        with patch("httpx.get", return_value=mock_httpx_response):
            with patch.object(genie_cmd.console, "print") as mock_print:
                result = genie_cmd.list_wishes(api_base="http://localhost:8886")

                assert result is True

                # Verify console.print was called (table display)
                assert mock_print.called

    def test_list_wishes_api_endpoint_format(self, genie_cmd, mock_httpx_response):
        """Verify correct API endpoint URL formatting."""
        with patch("httpx.get", return_value=mock_httpx_response) as mock_get:
            genie_cmd.list_wishes(api_base="http://localhost:8886")

            # Verify full endpoint URL
            call_args = mock_get.call_args
            assert call_args[0][0] == "http://localhost:8886/api/v1/wishes"

    def test_list_wishes_custom_api_base(self, genie_cmd, mock_httpx_response):
        """Test with custom API base URL."""
        custom_base = "https://custom-api.example.com:9999"

        with patch("httpx.get", return_value=mock_httpx_response) as mock_get:
            genie_cmd.list_wishes(api_base=custom_base)

            # Verify custom base is used
            call_args = mock_get.call_args
            assert custom_base in call_args[0][0]
            assert "/api/v1/wishes" in call_args[0][0]
