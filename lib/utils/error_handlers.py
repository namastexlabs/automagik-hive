"""
Error handlers for graceful API error management.

Provides centralized error handling for model provider errors,
particularly API key issues and rate limits.
"""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

from lib.logging import logger


class APIKeyError(Exception):
    """Raised when API key is invalid, expired, or missing."""

    pass


class ModelProviderErrorHandler:
    """Handles model provider errors gracefully."""

    @staticmethod
    def handle_api_error(error: Exception, agent_id: str = "unknown") -> dict[str, Any]:
        """
        Handle API errors and return a user-friendly response.

        Args:
            error: The exception that occurred
            agent_id: The agent that encountered the error

        Returns:
            Dictionary with error details for user response
        """
        error_str = str(error).lower()

        # Check for API key issues
        if any(
            phrase in error_str
            for phrase in [
                "api key expired",
                "api_key_invalid",
                "invalid api key",
                "api key not found",
                "unauthorized",
                "authentication failed",
            ]
        ):
            logger.error(
                f"🔑 API Key Error for agent {agent_id}",
                error_type="api_key_error",
                agent=agent_id,
                details="API key is invalid or expired. Please check your environment variables.",
            )
            return {
                "error": "authentication_error",
                "message": "⚠️ API key issue detected. Please check your API credentials in the .env file.",
                "details": "The API key for this model provider is either expired, invalid, or missing.",
                "agent": agent_id,
                "suggestion": "Update your API key in the .env file and restart the server.",
            }

        # Check for quota/rate limit issues
        elif any(phrase in error_str for phrase in ["rate limit", "quota exceeded", "too many requests", "429"]):
            logger.warning(f"⏱️ Rate limit hit for agent {agent_id}", error_type="rate_limit", agent=agent_id)
            return {
                "error": "rate_limit",
                "message": "⏱️ Rate limit reached. Please try again in a moment.",
                "agent": agent_id,
                "suggestion": "Wait a few seconds before retrying.",
            }

        # Check for model availability issues
        elif any(phrase in error_str for phrase in ["model not found", "invalid model", "unsupported model"]):
            logger.error(f"🤖 Model not available for agent {agent_id}", error_type="model_not_found", agent=agent_id)
            return {
                "error": "model_not_found",
                "message": "🤖 The requested model is not available.",
                "agent": agent_id,
                "suggestion": "Check if the model name is correct and you have access to it.",
            }

        # Generic model provider error
        else:
            logger.error(
                f"❌ Model provider error for agent {agent_id}",
                error_type="model_provider_error",
                agent=agent_id,
                error=str(error),
            )
            return {
                "error": "model_provider_error",
                "message": "❌ An error occurred with the AI model provider.",
                "agent": agent_id,
                "details": str(error)[:200],  # Truncate long error messages
                "suggestion": "Check the logs for more details or try again later.",
            }


def handle_model_errors(agent_id: str | None = None):
    """
    Decorator to handle model provider errors gracefully.

    Args:
        agent_id: Optional agent identifier for better error tracking

    Usage:
        @handle_model_errors(agent_id="atena")
        async def run_agent():
            # Agent code that might fail
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Check if it's a model provider error (expanded list)
                if any(
                    error_type in str(type(e))
                    for error_type in [
                        "ModelProviderError",
                        "ClientError",
                        "ServerError",
                        "APIError",
                        "AuthenticationError",
                        "PermissionError",
                        "google.genai.errors",
                        "GoogleAIError",
                        "GenerativeAIError",
                    ]
                ):
                    handler = ModelProviderErrorHandler()
                    error_response = handler.handle_api_error(e, agent_id or "unknown")

                    # Return error response instead of raising
                    return {"success": False, **error_response}
                else:
                    # Re-raise non-model provider errors
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if it's a model provider error (expanded list)
                if any(
                    error_type in str(type(e))
                    for error_type in [
                        "ModelProviderError",
                        "ClientError",
                        "ServerError",
                        "APIError",
                        "AuthenticationError",
                        "PermissionError",
                        "google.genai.errors",
                        "GoogleAIError",
                        "GenerativeAIError",
                    ]
                ):
                    handler = ModelProviderErrorHandler()
                    error_response = handler.handle_api_error(e, agent_id or "unknown")

                    # Return error response instead of raising
                    return {"success": False, **error_response}
                else:
                    # Re-raise non-model provider errors
                    raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Export main components
__all__ = ["APIKeyError", "ModelProviderErrorHandler", "handle_model_errors"]
