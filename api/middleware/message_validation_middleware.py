"""
Message Validation Middleware

This middleware validates incoming messages to agent execution endpoints
and provides user-friendly error messages before requests reach the Claude API.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class MessageValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate messages before agent execution.
    
    Prevents empty or invalid messages from reaching the Claude API
    by providing early validation and user-friendly error messages.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and validate message content if needed."""
        
        # Check if this is an agent execution endpoint
        if self._should_validate_message(request):
            validation_result = await self._validate_message_content(request)
            if validation_result:
                # Return validation error before processing
                return JSONResponse(
                    status_code=400,
                    content=validation_result
                )
        
        # Continue with normal processing
        response = await call_next(request)
        return response
    
    def _should_validate_message(self, request: Request) -> bool:
        """Check if this request should have message validation."""
        path = request.url.path
        method = request.method
        
        # Validate POST requests to agent execution endpoints
        if method == "POST":
            # Standard Agno Playground endpoints
            if path == "/runs" or path.startswith("/runs/"):
                return True
            # Agent-specific endpoints
            if path.startswith("/agents/") and "/runs" in path:
                return True
            # Team execution endpoints
            if path.startswith("/teams/") and "/runs" in path:
                return True
            # Workflow execution endpoints
            if path.startswith("/workflows/") and "/runs" in path:
                return True
        
        return False
    
    async def _validate_message_content(self, request: Request) -> Dict[str, Any] | None:
        """
        Validate the message content in the request.
        
        Returns:
            Error response dict if validation fails, None if validation passes
        """
        try:
            # Store original receive method
            original_receive = request.receive
            body_parts = []
            
            async def receive():
                message = await original_receive()
                if message["type"] == "http.request":
                    body_parts.append(message.get("body", b""))
                return message
            
            # Replace receive method
            request._receive = receive
            
            # Get request body
            body = await request.body()
            
            # Restore original receive method with complete body
            full_body = b"".join(body_parts)
            
            async def restored_receive():
                return {"type": "http.request", "body": full_body, "more_body": False}
            
            request._receive = restored_receive
            
            # Handle multipart/form-data
            content_type = request.headers.get("content-type", "")
            
            if content_type.startswith("multipart/form-data"):
                # For multipart data, we can't easily validate without consuming the stream
                # Let the endpoint handle validation for multipart
                return None
            elif content_type.startswith("application/json"):
                # For JSON data, parse and extract message
                if body:
                    try:
                        request_data = json.loads(body.decode())
                        message = request_data.get("message", "")
                    except json.JSONDecodeError:
                        return {
                            "error": {
                                "code": "INVALID_JSON",
                                "message": "Request body must be valid JSON",
                                "details": "The request body could not be parsed as JSON"
                            },
                            "data": None
                        }
                else:
                    message = ""
            else:
                # For other content types, try to get message from query params
                message = request.query_params.get("message", "")
            
            # Validate message content
            if not message or not message.strip():
                return {
                    "error": {
                        "code": "EMPTY_MESSAGE",
                        "message": "Message content is required",
                        "details": "The 'message' parameter cannot be empty. Please provide a message for the agent to process."
                    },
                    "data": None
                }
            
            # Check for overly long messages (prevent abuse)
            if len(message) > 10000:  # 10KB limit
                return {
                    "error": {
                        "code": "MESSAGE_TOO_LONG",
                        "message": "Message content is too long",
                        "details": f"Message length ({len(message)} characters) exceeds the maximum allowed length of 10,000 characters."
                    },
                    "data": None
                }
            
            # Message validation passed
            return None
            
        except Exception as e:
            logger.error(f"Error during message validation: {e}")
            return {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Unable to validate message content",
                    "details": "An error occurred while validating the request. Please check your request format and try again."
                },
                "data": None
            }
    
    async def _restore_request_body(self, request: Request, body: bytes):
        """
        Restore request body after reading it for validation.
        
        This is needed because FastAPI/Starlette can only read the body once.
        """
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive