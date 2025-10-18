"""
Fallback model for handling API errors gracefully.

This module provides a mock model that returns user-friendly error messages
instead of crashing when API keys are invalid or expired.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

from lib.logging import logger


class FallbackModel:
    """
    A fallback model that returns user-friendly error messages instead of crashing.

    This model is used when API keys are invalid, expired, or other provider errors occur.
    Instead of throwing exceptions, it returns structured error responses.
    """

    def __init__(self, error_response: dict[str, Any], component_id: str):
        """
        Initialize fallback model with error details.

        Args:
            error_response: The error response from ModelProviderErrorHandler
            component_id: The component that had the error
        """
        self.error_response = error_response
        self.component_id = component_id
        self.id = f"fallback-{component_id}"
        self.provider = "fallback"

        logger.info(f"🔄 FallbackModel created for {component_id}: {error_response.get('message', 'Unknown error')}")

    def invoke(self, messages: str | list[dict[str, str]] | Any, **kwargs: Any) -> str:
        """
        Return error message instead of making API call.

        Args:
            messages: The input messages (ignored)
            **kwargs: Additional arguments (ignored)

        Returns:
            User-friendly error message
        """
        return self._format_error_message()

    async def ainvoke(self, messages: str | list[dict[str, str]] | Any, **kwargs: Any) -> str:
        """
        Async version of invoke - return error message instead of making API call.

        Args:
            messages: The input messages (ignored)
            **kwargs: Additional arguments (ignored)

        Returns:
            User-friendly error message
        """
        return self._format_error_message()

    def stream(self, messages: str | list[dict[str, str]] | Any, **kwargs: Any) -> Iterator[str]:
        """
        Stream error message instead of making API call.

        Args:
            messages: The input messages (ignored)
            **kwargs: Additional arguments (ignored)

        Yields:
            Error message chunks
        """
        message = self._format_error_message()
        # Simulate streaming by yielding chunks
        chunk_size = 20
        for i in range(0, len(message), chunk_size):
            yield message[i : i + chunk_size]

    async def astream(self, messages: str | list[dict[str, str]] | Any, **kwargs: Any) -> AsyncIterator[str]:
        """
        Async stream error message instead of making API call.

        Args:
            messages: The input messages (ignored)
            **kwargs: Additional arguments (ignored)

        Yields:
            Error message chunks
        """
        message = self._format_error_message()
        # Simulate streaming by yielding chunks with small delays
        chunk_size = 20
        for i in range(0, len(message), chunk_size):
            yield message[i : i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay to simulate streaming

    def _format_error_message(self) -> str:
        """
        Format a user-friendly error message.

        Returns:
            Formatted error message for display
        """
        error_type = self.error_response.get("error", "unknown_error")
        message = self.error_response.get("message", "An unknown error occurred")
        suggestion = self.error_response.get("suggestion", "")

        formatted_message = f"❌ **{error_type.replace('_', ' ').title()}**\n\n"
        formatted_message += f"{message}\n"

        if suggestion:
            formatted_message += f"\n💡 **Suggestion**: {suggestion}\n"

        formatted_message += f"\n🤖 **Component**: {self.component_id}\n"
        formatted_message += "🔧 **Status**: Using fallback mode to prevent crashes\n"

        return formatted_message

    # Additional streaming methods that might be called during async operations
    async def ainvoke_stream(self, messages: str | list[dict[str, str]] | Any, **kwargs: Any) -> AsyncIterator[str]:
        """
        Handle ainvoke_stream calls that trigger the original error.
        This is the method where the Gemini API error occurs in line 376.

        Args:
            messages: The input messages (ignored)
            **kwargs: Additional arguments (ignored)

        Yields:
            Error message chunks
        """
        async for chunk in self.astream(messages, **kwargs):
            yield chunk

    def invoke_stream(self, messages: str | list[dict[str, str]] | Any, **kwargs: Any) -> Iterator[str]:
        """
        Handle invoke_stream calls for synchronous streaming.

        Args:
            messages: The input messages (ignored)
            **kwargs: Additional arguments (ignored)

        Yields:
            Error message chunks
        """
        yield from self.stream(messages, **kwargs)

    # Mock required properties/methods that Agno models might expect
    @property
    def model_name(self) -> str:
        return f"fallback-{self.component_id}"

    @property
    def model_id(self) -> str:
        return self.id

    @property
    def name(self) -> str:
        """Some Agno models expect a 'name' property."""
        return self.model_name

    @property
    def client(self) -> None:
        """Mock client property to prevent AttributeError."""
        return None

    def _get_client(self) -> None:
        """Mock client getter method."""
        return None

    def __str__(self) -> str:
        return f"FallbackModel({self.component_id})"

    def __repr__(self) -> str:
        return (
            f"FallbackModel(component_id='{self.component_id}', error='{self.error_response.get('error', 'unknown')}')"
        )


# Export main class
__all__ = ["FallbackModel"]
