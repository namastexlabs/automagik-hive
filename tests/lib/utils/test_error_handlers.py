"""Comprehensive tests for error handler utilities.

Tests all error handling functions including ModelProviderErrorHandler
and handle_model_errors decorator with various error types and edge cases.
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

from lib.utils.error_handlers import (
    APIKeyError,
    ModelProviderErrorHandler,
    handle_model_errors,
)


class TestModelProviderErrorHandler:
    """Test suite for ModelProviderErrorHandler.handle_api_error() method."""

    def test_api_key_expired_error(self):
        """Test API key expired error detection."""
        handler = ModelProviderErrorHandler()
        error = Exception("API key expired")
        
        result = handler.handle_api_error(error, "test_agent")
        
        assert result["error"] == "authentication_error"
        assert "API key" in result["message"]
        assert result["agent"] == "test_agent"
        assert "suggestion" in result

    def test_api_key_invalid_error(self):
        """Test invalid API key error detection."""
        handler = ModelProviderErrorHandler()
        error_cases = [
            "api_key_invalid",
            "invalid api key",
            "api key not found",
        ]
        
        for error_str in error_cases:
            error = Exception(error_str)
            result = handler.handle_api_error(error, "test_agent")
            assert result["error"] == "authentication_error"

    def test_unauthorized_error(self):
        """Test unauthorized and authentication failed errors."""
        handler = ModelProviderErrorHandler()
        error_cases = [
            "unauthorized",
            "authentication failed",
        ]
        
        for error_str in error_cases:
            error = Exception(error_str)
            result = handler.handle_api_error(error, "test_agent")
            assert result["error"] == "authentication_error"
            assert "API key" in result["message"]

    def test_rate_limit_errors(self):
        """Test rate limit error detection and response formatting."""
        handler = ModelProviderErrorHandler()
        error_cases = [
            "rate limit",
            "quota exceeded",
            "too many requests",
            "429",
        ]
        
        for error_str in error_cases:
            error = Exception(error_str)
            result = handler.handle_api_error(error, "test_agent")
            assert result["error"] == "rate_limit"
            assert "rate limit" in result["message"].lower()
            assert result["agent"] == "test_agent"

    def test_model_not_found_errors(self):
        """Test model not found/invalid error detection."""
        handler = ModelProviderErrorHandler()
        error_cases = [
            "model not found",
            "invalid model",
            "unsupported model",
        ]
        
        for error_str in error_cases:
            error = Exception(error_str)
            result = handler.handle_api_error(error, "test_agent")
            assert result["error"] == "model_not_found"
            assert "model" in result["message"].lower()

    def test_generic_model_provider_error(self):
        """Test generic model provider error handling fallback."""
        handler = ModelProviderErrorHandler()
        error = Exception("An unexpected error occurred")
        
        result = handler.handle_api_error(error, "test_agent")
        
        assert result["error"] == "model_provider_error"
        assert "error occurred" in result["message"].lower()
        assert result["agent"] == "test_agent"
        assert "details" in result

    def test_case_insensitive_error_matching(self):
        """Test that error matching is case-insensitive."""
        handler = ModelProviderErrorHandler()
        error_cases = [
            "API KEY EXPIRED",
            "Rate Limit Exceeded",
            "Model Not Found",
        ]
        
        results = [
            handler.handle_api_error(Exception(e), "test_agent") for e in error_cases
        ]
        
        assert results[0]["error"] == "authentication_error"
        assert results[1]["error"] == "rate_limit"
        assert results[2]["error"] == "model_not_found"

    def test_default_agent_id(self):
        """Test handling with default agent_id."""
        handler = ModelProviderErrorHandler()
        error = Exception("Some error")
        
        result = handler.handle_api_error(error)
        
        assert result["agent"] == "unknown"

    def test_error_details_truncation(self):
        """Test that long error messages are truncated in details."""
        handler = ModelProviderErrorHandler()
        long_error_message = "x" * 300
        error = Exception(long_error_message)
        
        result = handler.handle_api_error(error, "test_agent")
        
        assert "details" in result
        assert len(result["details"]) <= 200

    @patch("lib.utils.error_handlers.logger")
    def test_logging_for_api_key_error(self, mock_logger):
        """Test that API key errors trigger appropriate logging."""
        handler = ModelProviderErrorHandler()
        error = Exception("api key expired")
        
        handler.handle_api_error(error, "test_agent")
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "API Key Error" in call_args[0][0]

    @patch("lib.utils.error_handlers.logger")
    def test_logging_for_rate_limit(self, mock_logger):
        """Test that rate limit errors trigger warning logging."""
        handler = ModelProviderErrorHandler()
        error = Exception("rate limit")
        
        handler.handle_api_error(error, "test_agent")
        
        mock_logger.warning.assert_called_once()


class TestHandleModelErrorsDecorator:
    """Test suite for handle_model_errors decorator function."""

    @pytest.mark.asyncio
    async def test_async_function_model_provider_error_handling(self):
        """Test async function error handling with model provider errors."""
        
        @handle_model_errors(agent_id="test_agent")
        async def async_func_with_error():
            raise Exception("ModelProviderError: api key expired")
        
        result = await async_func_with_error()
        
        assert result["success"] is False
        assert "error" in result
        assert result["agent"] == "test_agent"

    @pytest.mark.asyncio
    async def test_async_function_success_case(self):
        """Test async function returns normal result when no error."""
        
        @handle_model_errors(agent_id="test_agent")
        async def async_func_success():
            return {"result": "success"}
        
        result = await async_func_success()
        
        assert result["result"] == "success"

    def test_sync_function_model_provider_error_handling(self):
        """Test sync function error handling with model provider errors."""
        
        @handle_model_errors(agent_id="test_agent")
        def sync_func_with_error():
            raise Exception("ClientError: rate limit")
        
        result = sync_func_with_error()
        
        assert result["success"] is False
        assert "error" in result
        assert result["agent"] == "test_agent"

    def test_sync_function_success_case(self):
        """Test sync function returns normal result when no error."""
        
        @handle_model_errors(agent_id="test_agent")
        def sync_func_success():
            return {"result": "success"}
        
        result = sync_func_success()
        
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_async_non_model_error_reraises(self):
        """Test that non-model-provider errors are re-raised in async."""
        
        @handle_model_errors(agent_id="test_agent")
        async def async_func_with_non_model_error():
            raise ValueError("This is not a model provider error")
        
        with pytest.raises(ValueError) as exc_info:
            await async_func_with_non_model_error()
        
        assert "not a model provider error" in str(exc_info.value)

    def test_sync_non_model_error_reraises(self):
        """Test that non-model-provider errors are re-raised in sync."""
        
        @handle_model_errors(agent_id="test_agent")
        def sync_func_with_non_model_error():
            raise ValueError("This is not a model provider error")
        
        with pytest.raises(ValueError) as exc_info:
            sync_func_with_non_model_error()
        
        assert "not a model provider error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_decorator_without_agent_id(self):
        """Test decorator works without explicit agent_id."""
        
        @handle_model_errors()
        async def async_func_with_error():
            raise Exception("APIError: something went wrong")
        
        result = await async_func_with_error()
        
        assert result["success"] is False
        assert result["agent"] == "unknown"

    @pytest.mark.asyncio
    async def test_various_error_types_detection(self):
        """Test detection of various model provider error types."""
        error_types = [
            "ModelProviderError",
            "ClientError",
            "ServerError",
            "APIError",
            "AuthenticationError",
            "google.genai.errors",
            "GoogleAIError",
            "GenerativeAIError",
        ]
        
        for error_type in error_types:
            @handle_model_errors(agent_id="test_agent")
            async def async_func():
                raise Exception(f"{error_type}: test error")
            
            result = await async_func()
            assert result["success"] is False, f"Failed for {error_type}"

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        
        @handle_model_errors(agent_id="test_agent")
        def test_function():
            """Test docstring."""
            return "result"
        
        assert test_function.__name__ == "test_function"
        assert "Test docstring" in test_function.__doc__

    @pytest.mark.asyncio
    async def test_decorator_with_function_arguments(self):
        """Test decorator works with functions that have arguments."""
        
        @handle_model_errors(agent_id="test_agent")
        async def async_func_with_args(arg1, arg2, kwarg1=None):
            return {"arg1": arg1, "arg2": arg2, "kwarg1": kwarg1}
        
        result = await async_func_with_args("value1", "value2", kwarg1="value3")
        
        assert result["arg1"] == "value1"
        assert result["arg2"] == "value2"
        assert result["kwarg1"] == "value3"

    def test_decorator_with_sync_function_arguments(self):
        """Test decorator works with sync functions that have arguments."""
        
        @handle_model_errors(agent_id="test_agent")
        def sync_func_with_args(arg1, arg2, kwarg1=None):
            if kwarg1 == "error":
                raise Exception("APIError: test error")
            return {"arg1": arg1, "arg2": arg2}
        
        result = sync_func_with_args("value1", "value2")
        assert result["arg1"] == "value1"
        
        error_result = sync_func_with_args("value1", "value2", kwarg1="error")
        assert error_result["success"] is False


class TestAPIKeyError:
    """Test suite for APIKeyError exception class."""

    def test_api_key_error_is_exception(self):
        """Test that APIKeyError is an Exception subclass."""
        assert issubclass(APIKeyError, Exception)

    def test_api_key_error_can_be_raised(self):
        """Test that APIKeyError can be raised and caught."""
        with pytest.raises(APIKeyError) as exc_info:
            raise APIKeyError("Test API key error")
        
        assert "Test API key error" in str(exc_info.value)

    def test_api_key_error_message(self):
        """Test APIKeyError with custom message."""
        error = APIKeyError("Custom error message")
        assert str(error) == "Custom error message"
