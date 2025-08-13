"""
Comprehensive tests for FastAPI message validation dependencies.

Tests all message validation functions with various content types,
edge cases, and error conditions for TDD development workflow.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Form, HTTPException, Request, status
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestValidateMessageDependency:
    """Test suite for validate_message_dependency function."""

    @pytest.mark.asyncio
    async def test_valid_message_success(self):
        """Test valid message passes validation successfully."""
        from api.dependencies.message_validation import validate_message_dependency
        
        valid_message = "This is a valid test message"
        result = await validate_message_dependency(valid_message)
        
        assert result == valid_message

    @pytest.mark.asyncio
    async def test_empty_message_raises_http_exception(self):
        """Test empty message raises HTTPException with proper error structure."""
        from api.dependencies.message_validation import validate_message_dependency
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_message_dependency("")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error"]["code"] == "EMPTY_MESSAGE"
        assert "required" in exc_info.value.detail["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_whitespace_only_message_raises_exception(self):
        """Test whitespace-only message is treated as empty."""
        from api.dependencies.message_validation import validate_message_dependency
        
        whitespace_messages = ["   ", "\t\t", "\n\n", "  \t  \n  "]
        
        for whitespace_msg in whitespace_messages:
            with pytest.raises(HTTPException) as exc_info:
                await validate_message_dependency(whitespace_msg)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail["error"]["code"] == "EMPTY_MESSAGE"

    @pytest.mark.asyncio
    async def test_message_length_limit_enforcement(self):
        """Test message exceeding 10KB limit raises HTTPException."""
        from api.dependencies.message_validation import validate_message_dependency
        
        # Create message over 10KB (10,000 characters)
        long_message = "x" * 10001
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_message_dependency(long_message)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error"]["code"] == "MESSAGE_TOO_LONG"
        assert "10,000" in exc_info.value.detail["error"]["details"]

    @pytest.mark.asyncio
    async def test_message_exactly_at_limit_passes(self):
        """Test message exactly at 10KB limit passes validation."""
        from api.dependencies.message_validation import validate_message_dependency
        
        # Create message exactly 10,000 characters
        limit_message = "x" * 10000
        
        result = await validate_message_dependency(limit_message)
        assert result == limit_message

    @pytest.mark.asyncio
    async def test_unicode_message_validation(self):
        """Test Unicode characters in message content."""
        from api.dependencies.message_validation import validate_message_dependency
        
        unicode_messages = [
            "Hello 世界",
            "Test with émojis 🚀🧪",
            "Русский текст",
            "العربية",
        ]
        
        for unicode_msg in unicode_messages:
            result = await validate_message_dependency(unicode_msg)
            assert result == unicode_msg

    @pytest.mark.asyncio
    async def test_special_characters_and_newlines(self):
        """Test messages with special characters and formatting."""
        from api.dependencies.message_validation import validate_message_dependency
        
        special_messages = [
            "Line 1\nLine 2\nLine 3",
            "Tab\tseparated\tvalues",
            "Quotes: 'single' and \"double\"",
            "Symbols: !@#$%^&*()[]{}|;:,.<>?",
        ]
        
        for special_msg in special_messages:
            result = await validate_message_dependency(special_msg)
            assert result == special_msg

    @pytest.mark.asyncio  
    async def test_error_response_structure(self):
        """Test error response contains required structure."""
        from api.dependencies.message_validation import validate_message_dependency
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_message_dependency("")
        
        error_detail = exc_info.value.detail
        
        # Validate error structure
        assert "error" in error_detail
        assert "data" in error_detail
        assert error_detail["data"] is None
        
        error_obj = error_detail["error"]
        assert "code" in error_obj
        assert "message" in error_obj
        assert "details" in error_obj

    @pytest.mark.asyncio
    async def test_logging_integration(self):
        """Test that validation errors trigger appropriate logging."""
        from api.dependencies.message_validation import validate_message_dependency
        
        with patch("api.dependencies.message_validation.logger") as mock_logger:
            with pytest.raises(HTTPException):
                await validate_message_dependency("")
            
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Empty message detected" in warning_call


class TestValidateOptionalMessageDependency:
    """Test suite for validate_optional_message_dependency function."""

    @pytest.mark.asyncio
    async def test_none_message_returns_none(self):
        """Test None message input returns None."""
        from api.dependencies.message_validation import validate_optional_message_dependency
        
        result = await validate_optional_message_dependency(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_message_calls_main_validator(self):
        """Test valid message calls main validation function."""
        from api.dependencies.message_validation import validate_optional_message_dependency
        
        valid_message = "Valid optional message"
        result = await validate_optional_message_dependency(valid_message)
        
        assert result == valid_message

    @pytest.mark.asyncio
    async def test_invalid_message_propagates_exception(self):
        """Test invalid message propagates HTTPException from main validator."""
        from api.dependencies.message_validation import validate_optional_message_dependency
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_optional_message_dependency("")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error"]["code"] == "EMPTY_MESSAGE"

    @pytest.mark.asyncio
    async def test_long_message_propagates_exception(self):
        """Test overly long message propagates length exception."""
        from api.dependencies.message_validation import validate_optional_message_dependency
        
        long_message = "x" * 10001
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_optional_message_dependency(long_message)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error"]["code"] == "MESSAGE_TOO_LONG"


class TestValidateRunsRequest:
    """Test suite for validate_runs_request function."""

    @pytest.mark.asyncio
    async def test_multipart_form_data_valid_message(self):
        """Test multipart/form-data content type with valid message."""
        from api.dependencies.message_validation import validate_runs_request
        
        # Mock request with form data
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "multipart/form-data; boundary=test"}
        
        # Mock form data
        mock_form = Mock()
        mock_form.get.return_value = "Valid form message"
        mock_request.form = AsyncMock(return_value=mock_form)
        
        # Should not raise exception
        await validate_runs_request(mock_request)

    @pytest.mark.asyncio
    async def test_application_json_valid_message(self):
        """Test application/json content type with valid message."""
        from api.dependencies.message_validation import validate_runs_request
        
        # Mock request with JSON data
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body.return_value = json.dumps({"message": "Valid JSON message"}).encode()
        
        # Should not raise exception
        await validate_runs_request(mock_request)

    @pytest.mark.asyncio
    async def test_empty_json_body_raises_exception(self):
        """Test empty JSON body raises HTTPException."""
        from api.dependencies.message_validation import validate_runs_request
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body.return_value = b""
        mock_request.url.path = "/test/endpoint"
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_runs_request(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error"]["code"] == "EMPTY_MESSAGE"

    @pytest.mark.asyncio
    async def test_json_without_message_field_raises_exception(self):
        """Test JSON without message field raises HTTPException."""
        from api.dependencies.message_validation import validate_runs_request
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body.return_value = json.dumps({"other_field": "value"}).encode()
        mock_request.url.path = "/test/endpoint"
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_runs_request(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_form_data_empty_message_raises_exception(self):
        """Test form data with empty message raises HTTPException."""
        from api.dependencies.message_validation import validate_runs_request
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "multipart/form-data"}
        mock_request.url.path = "/test/endpoint"
        
        mock_form = Mock()
        mock_form.get.return_value = ""
        mock_request.form = AsyncMock(return_value=mock_form)
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_runs_request(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_unsupported_content_type_skips_validation(self):
        """Test unsupported content type skips validation."""
        from api.dependencies.message_validation import validate_runs_request
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "text/plain"}
        
        # Should not raise exception
        result = await validate_runs_request(mock_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_malformed_json_graceful_handling(self):
        """Test malformed JSON is handled gracefully."""
        from api.dependencies.message_validation import validate_runs_request
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body.return_value = b"{invalid json"
        mock_request.url.path = "/test/endpoint"
        
        # Should not raise exception (graceful degradation)
        result = await validate_runs_request(mock_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_long_message_json_raises_exception(self):
        """Test overly long message in JSON raises HTTPException."""
        from api.dependencies.message_validation import validate_runs_request
        
        long_message = "x" * 10001
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body.return_value = json.dumps({"message": long_message}).encode()
        mock_request.url.path = "/test/endpoint"
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_runs_request(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail["error"]["code"] == "MESSAGE_TOO_LONG"

    @pytest.mark.asyncio
    async def test_error_logging_integration(self):
        """Test error logging during request validation."""
        from api.dependencies.message_validation import validate_runs_request
        
        mock_request = Mock(spec=Request)
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body.return_value = b"{invalid json"
        mock_request.url.path = "/test/endpoint"
        
        with patch("api.dependencies.message_validation.logger") as mock_logger:
            await validate_runs_request(mock_request)
            mock_logger.error.assert_called_once()


class TestMessageValidationIntegration:
    """Integration tests for message validation with FastAPI."""

    def test_message_validation_as_fastapi_dependency(self, test_client):
        """Test message validation used as FastAPI dependency."""
        from fastapi import Depends, FastAPI
        from api.dependencies.message_validation import validate_message_dependency
        
        # Create test app with dependency
        app = FastAPI()
        
        @app.post("/test-validation")
        async def test_endpoint(message: str = Depends(validate_message_dependency)):
            return {"received_message": message}
        
        client = TestClient(app)
        
        # Test valid message
        response = client.post("/test-validation", data={"message": "Valid test message"})
        assert response.status_code == 200
        assert response.json()["received_message"] == "Valid test message"
        
        # Test empty message
        response = client.post("/test-validation", data={"message": ""})
        assert response.status_code == 400
        assert response.json()["detail"]["error"]["code"] == "EMPTY_MESSAGE"

    @pytest.mark.asyncio
    async def test_async_client_integration(self, async_client: AsyncClient):
        """Test message validation with async client."""
        from fastapi import Depends, FastAPI
        from httpx import ASGITransport, AsyncClient as HTTPXAsyncClient
        from api.dependencies.message_validation import validate_optional_message_dependency
        
        app = FastAPI()
        
        @app.post("/test-optional")
        async def test_optional_endpoint(
            message: str | None = Depends(validate_optional_message_dependency)
        ):
            return {"message": message}
        
        # Test None message using correct AsyncClient syntax
        async with HTTPXAsyncClient(
            transport=ASGITransport(app=app), 
            base_url="http://test"
        ) as client:
            response = await client.post("/test-optional")
            assert response.status_code == 200
            assert response.json()["message"] is None

    def test_concurrent_validation_requests(self, test_client):
        """Test concurrent validation requests handle properly."""
        import concurrent.futures
        from fastapi import Depends, FastAPI
        from api.dependencies.message_validation import validate_message_dependency
        
        app = FastAPI()
        
        @app.post("/test-concurrent")
        async def test_endpoint(message: str = Depends(validate_message_dependency)):
            return {"message": message}
        
        client = TestClient(app)
        
        def make_request(msg_num):
            return client.post("/test-concurrent", data={"message": f"Message {msg_num}"})
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200
            assert response.json()["message"] == f"Message {i}"

    def test_request_validation_middleware_integration(self):
        """Test validate_runs_request integration with middleware."""
        from fastapi import FastAPI, Request, HTTPException
        from fastapi.responses import JSONResponse
        from api.dependencies.message_validation import validate_runs_request
        
        app = FastAPI()
        
        @app.middleware("http")
        async def validation_middleware(request: Request, call_next):
            if request.url.path.startswith("/api/"):
                try:
                    await validate_runs_request(request)
                except HTTPException as e:
                    # Convert HTTPException to proper response in middleware
                    return JSONResponse(
                        status_code=e.status_code,
                        content=e.detail
                    )
            response = await call_next(request)
            return response
        
        @app.post("/api/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        
        # Test valid JSON request
        response = client.post(
            "/api/test",
            json={"message": "Valid API message"},
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        
        # Test invalid request (empty message)
        response = client.post(
            "/api/test",
            json={"message": ""},
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "EMPTY_MESSAGE"
