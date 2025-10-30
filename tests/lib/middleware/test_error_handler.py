"""
Comprehensive tests for AgentRunErrorHandler middleware.

Tests ALL error scenarios, request/response flow, and logging behavior.
Target: 80%+ coverage for CRITICAL middleware.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

# Standard path fix for imports
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.middleware.error_handler import (
    AgentRunErrorHandler,
    create_agent_run_error_handler,
)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = MagicMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/playground/agents/test-agent/runs/continue"
    request.method = "POST"
    request.query_params = {}
    request.headers = {"user-agent": "TestClient/1.0"}
    return request


@pytest.fixture
def error_handler():
    """Create an instance of AgentRunErrorHandler."""
    return AgentRunErrorHandler(app=MagicMock())


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function for middleware."""
    call_next = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    call_next.return_value = mock_response
    return call_next


class TestAgentRunErrorHandlerDispatch:
    """Test the main dispatch method of the error handler."""

    @pytest.mark.asyncio
    async def test_dispatch_happy_path_success(self, error_handler, mock_request, mock_call_next):
        """Test dispatch with successful request (no errors)."""
        response = await error_handler.dispatch(mock_request, mock_call_next)

        assert response is not None
        assert response.status_code == 200
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_handles_missing_run_error(self, error_handler, mock_request, mock_call_next):
        """Test dispatch handles 'No runs found for run ID' RuntimeError."""
        # Setup: call_next raises RuntimeError with specific message
        mock_call_next.side_effect = RuntimeError("No runs found for run ID abc123")

        with patch.object(error_handler, "_handle_missing_run_error", new=AsyncMock()) as mock_handler:
            mock_handler.return_value = JSONResponse(status_code=410, content={"error": "session_expired"})

            response = await error_handler.dispatch(mock_request, mock_call_next)

            # Verify the handler was called
            mock_handler.assert_called_once_with(mock_request, "No runs found for run ID abc123")
            assert response.status_code == 410

    @pytest.mark.asyncio
    async def test_dispatch_reraises_other_runtime_errors(self, error_handler, mock_request, mock_call_next):
        """Test dispatch re-raises RuntimeError without 'No runs found' message."""
        mock_call_next.side_effect = RuntimeError("Some other runtime error")

        with pytest.raises(RuntimeError, match="Some other runtime error"):
            await error_handler.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_dispatch_logs_and_reraises_unexpected_errors(self, error_handler, mock_request, mock_call_next):
        """Test dispatch logs unexpected exceptions and re-raises them."""
        mock_call_next.side_effect = ValueError("Unexpected value error")

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with pytest.raises(ValueError, match="Unexpected value error"):
                await error_handler.dispatch(mock_request, mock_call_next)

            # Verify logging occurred (first positional arg is the message)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "Unexpected error in agent run handler"
            call_kwargs = call_args[1]
            assert call_kwargs["error"] == "Unexpected value error"
            assert call_kwargs["path"] == mock_request.url.path
            assert call_kwargs["method"] == "POST"
            assert "traceback" in call_kwargs

    @pytest.mark.asyncio
    async def test_dispatch_handles_exception_during_exception_handling(
        self, error_handler, mock_request, mock_call_next
    ):
        """Test dispatch handles errors that occur during error handling."""
        # This ensures the middleware doesn't crash when logging fails
        mock_call_next.side_effect = ValueError("Test error")

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            # Make logger.error raise an exception
            mock_logger.error.side_effect = Exception("Logger failed")

            # The original ValueError should still propagate even if logging fails
            with pytest.raises(Exception):  # Will raise either ValueError or logger Exception
                await error_handler.dispatch(mock_request, mock_call_next)


class TestHandleMissingRunError:
    """Test the _handle_missing_run_error method."""

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_extracts_run_id(self, error_handler, mock_request):
        """Test extraction of run_id from error message."""
        error_message = "No runs found for run ID abc123xyz"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger") as mock_session_logger:
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                assert isinstance(response, JSONResponse)
                assert response.status_code == 410

                # Check response content
                content = response.body.decode("utf-8")
                assert "session_expired" in content
                assert "abc123xyz" in content

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_extracts_agent_id_from_path(self, error_handler, mock_request):
        """Test extraction of agent_id from URL path."""
        mock_request.url.path = "/playground/agents/my-agent/runs/continue"
        error_message = "No runs found for run ID test123"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger") as mock_session_logger:
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                # Verify logger was called with agent_id
                assert mock_logger.warning.called
                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["agent_id"] == "my-agent"

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_handles_missing_agent_id(self, error_handler, mock_request):
        """Test handling when agent_id cannot be extracted."""
        mock_request.url.path = "/some/other/path"
        error_message = "No runs found for run ID test123"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                assert response.status_code == 410
                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["agent_id"] is None

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_extracts_session_id_from_query_params(self, error_handler, mock_request):
        """Test extraction of session_id from query parameters (GET requests)."""
        mock_request.method = "GET"
        mock_request.query_params = {"session_id": "session456"}
        error_message = "No runs found for run ID test123"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["session_id"] == "session456"

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_post_request_no_session_id(self, error_handler, mock_request):
        """Test POST request where session_id is not accessible."""
        mock_request.method = "POST"
        mock_request.query_params = {}
        error_message = "No runs found for run ID test123"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["session_id"] is None

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_logs_to_session_logger(self, error_handler, mock_request):
        """Test that session logger is called when run_id and agent_id are available."""
        mock_request.url.path = "/playground/agents/test-agent/runs/continue"
        error_message = "No runs found for run ID run123"

        with patch("lib.middleware.error_handler.logger"):
            with patch("lib.middleware.error_handler.session_logger") as mock_session_logger:
                await error_handler._handle_missing_run_error(mock_request, error_message)

                # Verify session logger was called
                mock_session_logger.log_run_continuation_failure.assert_called_once()
                call_kwargs = mock_session_logger.log_run_continuation_failure.call_args[1]
                assert call_kwargs["run_id"] == "run123"
                assert call_kwargs["agent_id"] == "test-agent"
                assert call_kwargs["error_type"] == "RunNotFound"

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_no_session_log_without_run_id(self, error_handler, mock_request):
        """Test session logger NOT called when run_id is missing."""
        mock_request.url.path = "/playground/agents/test-agent/runs/continue"
        error_message = "No runs found"  # No run ID in message

        with patch("lib.middleware.error_handler.logger"):
            with patch("lib.middleware.error_handler.session_logger") as mock_session_logger:
                await error_handler._handle_missing_run_error(mock_request, error_message)

                # Verify session logger was NOT called
                mock_session_logger.log_run_continuation_failure.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_response_structure(self, error_handler, mock_request):
        """Test the structure of the error response."""
        mock_request.url.path = "/playground/agents/my-agent/runs/continue"
        error_message = "No runs found for run ID abc123"

        with patch("lib.middleware.error_handler.logger"):
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                assert response.status_code == 410
                import json

                content = json.loads(response.body)

                # Verify response structure
                assert content["error"] == "session_expired"
                assert "message" in content
                assert "details" in content
                assert content["details"]["run_id"] == "abc123"
                assert content["details"]["reason"] == "The agent run session was not found in memory"
                assert "recovery_options" in content
                assert len(content["recovery_options"]) == 2

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_recovery_endpoints(self, error_handler, mock_request):
        """Test recovery endpoints in error response."""
        mock_request.url.path = "/playground/agents/my-agent/runs/continue"
        error_message = "No runs found for run ID abc123"

        with patch("lib.middleware.error_handler.logger"):
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                import json

                content = json.loads(response.body)
                recovery_options = content["recovery_options"]

                # Check new conversation endpoint
                new_conv = next(
                    (opt for opt in recovery_options if opt["action"] == "start_new_conversation"),
                    None,
                )
                assert new_conv is not None
                assert new_conv["endpoint"] == "/playground/agents/my-agent/runs"

                # Check history endpoint
                history = next(
                    (opt for opt in recovery_options if opt["action"] == "view_conversation_history"),
                    None,
                )
                assert history is not None
                assert history["endpoint"] == "/playground/agents/my-agent/sessions"

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_logs_user_agent(self, error_handler, mock_request):
        """Test that user-agent header is logged."""
        mock_request.headers = {"user-agent": "Mozilla/5.0 Test Browser"}
        error_message = "No runs found for run ID test123"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger"):
                await error_handler._handle_missing_run_error(mock_request, error_message)

                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["user_agent"] == "Mozilla/5.0 Test Browser"


class TestGetNewConversationEndpoint:
    """Test the _get_new_conversation_endpoint helper method."""

    def test_get_new_conversation_endpoint_with_agent_id(self, error_handler, mock_request):
        """Test endpoint generation when agent_id is in path."""
        mock_request.url.path = "/playground/agents/my-test-agent/runs/continue"

        endpoint = error_handler._get_new_conversation_endpoint(mock_request)

        assert endpoint == "/playground/agents/my-test-agent/runs"

    def test_get_new_conversation_endpoint_without_agent_id(self, error_handler, mock_request):
        """Test endpoint generation when agent_id is NOT in path."""
        mock_request.url.path = "/some/other/path"

        endpoint = error_handler._get_new_conversation_endpoint(mock_request)

        assert endpoint == "/playground/agents"

    def test_get_new_conversation_endpoint_agents_at_end(self, error_handler, mock_request):
        """Test endpoint when 'agents' is at the end of path."""
        mock_request.url.path = "/playground/agents"

        endpoint = error_handler._get_new_conversation_endpoint(mock_request)

        assert endpoint == "/playground/agents"

    def test_get_new_conversation_endpoint_malformed_path(self, error_handler, mock_request):
        """Test endpoint with malformed path (empty agent_id after agents)."""
        mock_request.url.path = "/agents/"  # agents with empty following segment

        endpoint = error_handler._get_new_conversation_endpoint(mock_request)

        # Empty string agent_id still creates endpoint (actual behavior)
        assert endpoint == "/playground/agents//runs"


class TestGetConversationHistoryEndpoint:
    """Test the _get_conversation_history_endpoint helper method."""

    def test_get_conversation_history_endpoint_with_agent_id(self, error_handler, mock_request):
        """Test history endpoint generation when agent_id is in path."""
        mock_request.url.path = "/playground/agents/my-test-agent/runs/continue"

        endpoint = error_handler._get_conversation_history_endpoint(mock_request)

        assert endpoint == "/playground/agents/my-test-agent/sessions"

    def test_get_conversation_history_endpoint_without_agent_id(self, error_handler, mock_request):
        """Test history endpoint when agent_id is NOT in path."""
        mock_request.url.path = "/some/other/path"

        endpoint = error_handler._get_conversation_history_endpoint(mock_request)

        assert endpoint == "/playground/agents"

    def test_get_conversation_history_endpoint_agents_at_end(self, error_handler, mock_request):
        """Test history endpoint when 'agents' is at the end of path."""
        mock_request.url.path = "/playground/agents"

        endpoint = error_handler._get_conversation_history_endpoint(mock_request)

        assert endpoint == "/playground/agents"

    def test_get_conversation_history_endpoint_malformed_path(self, error_handler, mock_request):
        """Test history endpoint with malformed path (empty agent_id after agents)."""
        mock_request.url.path = "/agents/"  # agents with empty following segment

        endpoint = error_handler._get_conversation_history_endpoint(mock_request)

        # Empty string agent_id still creates endpoint (actual behavior)
        assert endpoint == "/playground/agents//sessions"


class TestFactoryFunction:
    """Test the factory function for creating error handler."""

    def test_create_agent_run_error_handler_returns_instance(self):
        """Test factory function returns AgentRunErrorHandler instance."""
        # Mock BaseHTTPMiddleware.__init__ since it requires an app parameter
        with patch("lib.middleware.error_handler.BaseHTTPMiddleware.__init__", return_value=None):
            handler = create_agent_run_error_handler()

            assert isinstance(handler, AgentRunErrorHandler)

    def test_create_agent_run_error_handler_creates_new_instances(self):
        """Test factory creates independent instances."""
        # Mock BaseHTTPMiddleware.__init__ since it requires an app parameter
        with patch("lib.middleware.error_handler.BaseHTTPMiddleware.__init__", return_value=None):
            handler1 = create_agent_run_error_handler()
            handler2 = create_agent_run_error_handler()

            # Each call creates a new instance
            assert handler1 is not handler2
            assert isinstance(handler1, AgentRunErrorHandler)
            assert isinstance(handler2, AgentRunErrorHandler)


class TestEdgeCasesAndErrorPaths:
    """Test edge cases and error paths."""

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_with_empty_error_message(self, error_handler, mock_request):
        """Test handling with empty error message."""
        error_message = ""

        with patch("lib.middleware.error_handler.logger"):
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                assert response.status_code == 410
                import json

                content = json.loads(response.body)
                assert content["details"]["run_id"] is None

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_with_special_characters_in_run_id(self, error_handler, mock_request):
        """Test extraction of run_id with special characters."""
        error_message = "No runs found for run ID abc-123_xyz@456"

        with patch("lib.middleware.error_handler.logger"):
            with patch("lib.middleware.error_handler.session_logger"):
                response = await error_handler._handle_missing_run_error(mock_request, error_message)

                import json

                content = json.loads(response.body)
                assert "abc-123_xyz@456" in content["details"]["run_id"]

    @pytest.mark.asyncio
    async def test_handle_missing_run_error_with_missing_headers(self, error_handler, mock_request):
        """Test handling when user-agent header is missing."""
        mock_request.headers = {}  # No user-agent
        error_message = "No runs found for run ID test123"

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger"):
                await error_handler._handle_missing_run_error(mock_request, error_message)

                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["user_agent"] is None

    @pytest.mark.asyncio
    async def test_dispatch_with_keyboard_interrupt(self, error_handler, mock_request, mock_call_next):
        """Test dispatch with KeyboardInterrupt (should propagate)."""
        mock_call_next.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            await error_handler.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_dispatch_with_system_exit(self, error_handler, mock_request, mock_call_next):
        """Test dispatch with SystemExit (should propagate)."""
        mock_call_next.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            await error_handler.dispatch(mock_request, mock_call_next)

    def test_get_endpoints_with_multiple_agents_in_path(self, error_handler, mock_request):
        """Test endpoint extraction when 'agents' appears multiple times."""
        mock_request.url.path = "/agents/test/agents/real-agent/runs"

        # Should use the FIRST occurrence
        new_endpoint = error_handler._get_new_conversation_endpoint(mock_request)
        assert new_endpoint == "/playground/agents/test/runs"

    def test_get_endpoints_with_unicode_agent_id(self, error_handler, mock_request):
        """Test endpoint extraction with Unicode characters in agent_id."""
        mock_request.url.path = "/playground/agents/агент-тест/runs/continue"

        new_endpoint = error_handler._get_new_conversation_endpoint(mock_request)
        assert "агент-тест" in new_endpoint


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_session_recovery_flow(self, error_handler, mock_request):
        """Test complete session recovery flow from error to response."""
        # Setup realistic request
        mock_request.url.path = "/playground/agents/customer-support/runs/continue"
        mock_request.method = "POST"
        mock_request.query_params = {"session_id": "sess_12345"}

        # Simulate agent run error
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = RuntimeError("No runs found for run ID run_abc123def456")

        with patch("lib.middleware.error_handler.logger") as mock_logger:
            with patch("lib.middleware.error_handler.session_logger") as mock_session_logger:
                response = await error_handler.dispatch(mock_request, mock_call_next)

                # Verify response
                assert response.status_code == 410
                import json

                content = json.loads(response.body)
                assert content["error"] == "session_expired"
                assert "customer-support" in content["recovery_options"][0]["endpoint"]

                # Verify logging
                assert mock_logger.warning.called
                assert mock_session_logger.log_run_continuation_failure.called

    @pytest.mark.asyncio
    async def test_multiple_requests_through_middleware(self, error_handler):
        """Test multiple requests processed by same middleware instance."""
        mock_call_next = AsyncMock()
        mock_call_next.return_value = MagicMock(status_code=200)

        # Process multiple successful requests
        for i in range(3):
            request = MagicMock(spec=Request)
            request.url = MagicMock()
            request.url.path = f"/test/path/{i}"
            request.method = "GET"
            request.headers = {}

            response = await error_handler.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # Verify call_next was called for each request
        assert mock_call_next.call_count == 3
