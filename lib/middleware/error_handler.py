"""
Error Handler Middleware for Agent Run Session Management

This middleware provides graceful error handling for agent run session failures,
specifically addressing the issue where RuntimeError is raised when agent runs
are not found in memory (typically after server restarts).
"""

import contextlib
import traceback

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from lib.logging import logger, session_logger


class AgentRunErrorHandler(BaseHTTPMiddleware):
    """
    Custom middleware to handle agent run session management errors gracefully.

    This middleware catches RuntimeError exceptions related to missing agent runs
    and provides user-friendly error responses instead of 500 Internal Server Errors.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and handle agent run-related errors.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            Response: Either the normal response or a graceful error response
        """
        try:
            return await call_next(request)

        except RuntimeError as e:
            # Check if this is the specific agent run error we're handling
            error_message = str(e)
            if "No runs found for run ID" in error_message:
                return await self._handle_missing_run_error(request, error_message)
            # Re-raise other RuntimeErrors
            raise

        except Exception as e:
            # Handle other unexpected errors gracefully
            logger.error(
                "Unexpected error in agent run handler",
                error=str(e),
                path=request.url.path,
                method=request.method,
                traceback=traceback.format_exc(),
            )
            # Let other errors propagate normally
            raise

    async def _handle_missing_run_error(
        self, request: Request, error_message: str
    ) -> JSONResponse:
        """
        Handle missing agent run errors with user-friendly responses.

        Args:
            request: The HTTP request that caused the error
            error_message: The original error message

        Returns:
            JSONResponse: User-friendly error response
        """
        # Extract run_id from error message if possible
        run_id = None
        if "run ID " in error_message:
            with contextlib.suppress(IndexError, AttributeError):
                run_id = error_message.split("run ID ")[1].strip()

        # Extract session and agent info from URL
        session_id = None
        agent_id = None
        path_parts = request.url.path.split("/")

        if "agents" in path_parts:
            try:
                agent_index = path_parts.index("agents")
                if agent_index + 1 < len(path_parts):
                    agent_id = path_parts[agent_index + 1]
            except (ValueError, IndexError):
                pass

        # Try to get session_id from query params or form data
        if request.method == "POST":
            # Session ID might be in form data, but we can't easily access it here
            # without reading the body (which might have been consumed)
            pass
        else:
            session_id = request.query_params.get("session_id")

        # Log the error using both general and session-specific loggers
        logger.warning(
            "Agent run session not found - likely due to server restart",
            run_id=run_id,
            session_id=session_id,
            agent_id=agent_id,
            path=request.url.path,
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            original_error=error_message,
        )

        # Log using session lifecycle logger if we have the required info
        if run_id and agent_id:
            session_logger.log_run_continuation_failure(
                run_id=run_id,
                session_id=session_id or "unknown",
                agent_id=agent_id,
                error=error_message,
                error_type="RunNotFound",
            )

        # Create user-friendly error response
        error_response = {
            "error": "session_expired",
            "message": "The conversation session has expired or is no longer available",
            "details": {
                "reason": "The agent run session was not found in memory",
                "likely_cause": "Server restart or session cleanup",
                "run_id": run_id,
                "suggested_action": "Please start a new conversation",
            },
            "recovery_options": [
                {
                    "action": "start_new_conversation",
                    "description": "Begin a fresh conversation with the agent",
                    "endpoint": self._get_new_conversation_endpoint(request),
                },
                {
                    "action": "view_conversation_history",
                    "description": "View your previous conversations with this agent",
                    "endpoint": self._get_conversation_history_endpoint(request),
                },
            ],
        }

        return JSONResponse(
            status_code=410,  # 410 Gone - resource no longer available
            content=error_response,
        )

    def _get_new_conversation_endpoint(self, request: Request) -> str:
        """Get the endpoint to start a new conversation."""
        # Extract agent_id from the URL path
        path_parts = request.url.path.split("/")
        if "agents" in path_parts:
            try:
                agent_index = path_parts.index("agents")
                if agent_index + 1 < len(path_parts):
                    agent_id = path_parts[agent_index + 1]
                    return f"/playground/agents/{agent_id}/runs"
            except (ValueError, IndexError):
                pass

        return "/playground/agents"

    def _get_conversation_history_endpoint(self, request: Request) -> str:
        """Get the endpoint to view conversation history."""
        # Extract agent_id from the URL path
        path_parts = request.url.path.split("/")
        if "agents" in path_parts:
            try:
                agent_index = path_parts.index("agents")
                if agent_index + 1 < len(path_parts):
                    agent_id = path_parts[agent_index + 1]
                    return f"/playground/agents/{agent_id}/sessions"
            except (ValueError, IndexError):
                pass

        return "/playground/agents"


def create_agent_run_error_handler() -> AgentRunErrorHandler:
    """
    Factory function to create the agent run error handler middleware.

    Returns:
        AgentRunErrorHandler: Configured middleware instance
    """
    return AgentRunErrorHandler()
