"""
Agno Playground Message Validation Middleware

Validates messages for Agno Playground endpoints before they reach
the agent execution handlers.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
import logging

logger = logging.getLogger(__name__)


class AgnoValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate messages for Agno Playground endpoints.
    
    This middleware specifically targets Agno's standard endpoints like
    /runs, /agents/{id}/runs, /teams/{id}/runs, etc.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and validate message content for Agno endpoints."""
        
        # Check if this is an Agno execution endpoint
        if self._is_agno_execution_endpoint(request):
            validation_error = await self._validate_agno_message(request)
            if validation_error:
                return JSONResponse(
                    status_code=400,
                    content=validation_error
                )
        
        # Continue with normal processing
        response = await call_next(request)
        return response
    
    def _is_agno_execution_endpoint(self, request: Request) -> bool:
        """Check if this is an Agno Playground execution endpoint."""
        path = request.url.path
        method = request.method
        
        # Only validate POST requests
        if method != "POST":
            return False
        
        # Target Agno Playground execution endpoints
        agno_endpoints = [
            "/runs",  # Main execution endpoint
            # Agent execution patterns
            lambda p: p.startswith("/agents/") and p.endswith("/runs"),
            lambda p: p.startswith("/agents/") and "/runs/" in p,
            # Team execution patterns
            lambda p: p.startswith("/teams/") and p.endswith("/runs"),
            lambda p: p.startswith("/teams/") and "/runs/" in p,
            # Workflow execution patterns
            lambda p: p.startswith("/workflows/") and p.endswith("/runs"),
            lambda p: p.startswith("/workflows/") and "/runs/" in p,
        ]
        
        for endpoint in agno_endpoints:
            if callable(endpoint):
                if endpoint(path):
                    return True
            elif path == endpoint:
                return True
        
        return False
    
    async def _validate_agno_message(self, request: Request) -> dict | None:
        """
        Validate message content for Agno endpoints.
        
        Returns:
            Error dict if validation fails, None if validation passes
        """
        try:
            content_type = request.headers.get("content-type", "")
            message = ""
            
            if content_type.startswith("multipart/form-data"):
                # For multipart data (Agno's standard format)
                form = await request.form()
                message = form.get("message", "")
            elif content_type.startswith("application/json"):
                # For JSON data
                body = await request.body()
                if body:
                    try:
                        data = json.loads(body.decode())
                        message = data.get("message", "")
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
                # For other content types, check query params
                message = request.query_params.get("message", "")
            
            # Validate message content
            if not message or not message.strip():
                logger.warning(f"Empty message detected in Agno endpoint: {request.url.path}")
                return {
                    "error": {
                        "code": "EMPTY_MESSAGE",
                        "message": "Message content is required",
                        "details": "The 'message' parameter cannot be empty. Please provide a message for the agent to process."
                    },
                    "data": None
                }
            
            # Check for overly long messages
            if len(message) > 10000:  # 10KB limit
                logger.warning(f"Message too long in Agno endpoint {request.url.path}: {len(message)} characters")
                return {
                    "error": {
                        "code": "MESSAGE_TOO_LONG",
                        "message": "Message content is too long",
                        "details": f"Message length ({len(message)} characters) exceeds the maximum allowed length of 10,000 characters."
                    },
                    "data": None
                }
            
            # Validation passed
            return None
            
        except Exception as e:
            logger.error(f"Error during Agno message validation: {e}")
            # Don't fail the request for validation errors
            return None