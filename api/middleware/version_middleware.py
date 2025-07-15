"""
Version Parameter Middleware for Agno Playground

This middleware intercepts requests to playground endpoints and adds
version support by modifying query parameters and request data.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional
import json
import asyncio
from urllib.parse import parse_qs, urlencode


class PlaygroundVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add version support to existing Agno Playground endpoints.
    
    This intercepts requests to /runs and other playground endpoints,
    extracts version parameters, and handles version-specific routing.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and add version support if needed."""
        
        # Check if this is a playground endpoint that supports versioning
        if self._should_handle_versioning(request):
            return await self._handle_versioned_request(request, call_next)
        
        # Pass through non-versioned requests
        response = await call_next(request)
        return response
    
    def _should_handle_versioning(self, request: Request) -> bool:
        """Check if this request should be handled with versioning."""
        path = request.url.path
        method = request.method
        
        # Handle POST requests to /runs endpoints
        if method == "POST" and ("/runs" in path or path.startswith("/agents/") or path.startswith("/teams/")):
            # Check if version parameter is present in query string
            query_params = dict(request.query_params)
            return "version" in query_params
        
        return False
    
    async def _handle_versioned_request(self, request: Request, call_next):
        """Handle a request with version parameters."""
        
        # Extract version from query parameters
        query_params = dict(request.query_params)
        version = query_params.get("version")
        
        if not version:
            # No version specified, pass through normally
            return await call_next(request)
        
        try:
            version_int = int(version)
        except ValueError:
            # Invalid version format, pass through normally
            return await call_next(request)
        
        # Read request body
        body = await request.body()
        
        # Parse the request body to extract component information
        request_data = {}
        if body:
            try:
                request_data = json.loads(body.decode())
            except:
                pass
        
        # Extract component information
        component_id = self._extract_component_id(request, request_data)
        if not component_id:
            # Cannot determine component, pass through normally
            return await call_next(request)
        
        # Handle the versioned request
        try:
            return await self._execute_versioned_component(
                request, component_id, version_int, request_data
            )
        except Exception as e:
            # If versioned execution fails, fall back to normal processing
            return await call_next(request)
    
    def _extract_component_id(self, request: Request, request_data: dict) -> Optional[str]:
        """Extract component ID from request path and data."""
        
        # Try to extract from URL path
        path_parts = request.url.path.strip("/").split("/")
        
        # Check for agent/team/workflow in path
        if "agents" in path_parts:
            agent_idx = path_parts.index("agents")
            if agent_idx + 1 < len(path_parts):
                return path_parts[agent_idx + 1]
        
        if "teams" in path_parts:
            team_idx = path_parts.index("teams")
            if team_idx + 1 < len(path_parts):
                return path_parts[team_idx + 1]
        
        # Try to extract from request data
        for key in ["agent_id", "team_id", "workflow_id"]:
            if key in request_data:
                return request_data[key]
        
        # Try to extract from query parameters
        query_params = dict(request.query_params)
        for key in ["agent_id", "team_id", "workflow_id"]:
            if key in query_params:
                return query_params[key]
        
        return None
    
    async def _execute_versioned_component(
        self, 
        request: Request, 
        component_id: str, 
        version: int, 
        request_data: dict
    ):
        """Execute a versioned component and return the response."""
        
        # Import dependencies (avoid circular imports by importing directly from services)
        from db.services.component_version_service import ComponentVersionService
        from db.session import get_db
        from pydantic import BaseModel
        from fastapi import HTTPException
        
        # Create a mock request object for the versions API
        class MockRequest(BaseModel):
            message: str = ""
            session_id: Optional[str] = None
            debug_mode: bool = False
            user_id: Optional[str] = None
            user_name: Optional[str] = None
            phone_number: Optional[str] = None
            cpf: Optional[str] = None
        
        # Extract message and other parameters from request data
        message = request_data.get("message", "")
        session_id = request_data.get("session_id")
        debug_mode = request_data.get("debug_mode", False)
        
        # Validate message content before processing
        from utils.message_validation import validate_agent_message
        validate_agent_message(message, "versioned component execution")
        
        mock_request = MockRequest(
            message=message,
            session_id=session_id,
            debug_mode=debug_mode,
            user_id=request_data.get("user_id"),
            user_name=request_data.get("user_name"),
            phone_number=request_data.get("phone_number"),
            cpf=request_data.get("cpf")
        )
        
        # Get database session
        db = next(get_db())
        service = ComponentVersionService(db)
        
        # Get the specific version
        version_record = service.get_version(component_id, version)
        if not version_record:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for component {component_id}"
            )
        
        # Determine component type and execute using factories directly
        component_type = version_record.component_type
        
        # Use unified version factory for all component types
        from common.version_factory import UnifiedVersionFactory
        factory = UnifiedVersionFactory()
        
        component = factory.create_versioned_component(
            component_id=component_id,
            component_type=component_type,
            version=version,
            session_id=mock_request.session_id,
            debug_mode=mock_request.debug_mode,
            user_id=mock_request.user_id,
            user_name=mock_request.user_name,
            phone_number=mock_request.phone_number,
            cpf=mock_request.cpf
        )
        
        from utils.message_validation import safe_agent_run
        response = safe_agent_run(component, mock_request.message, f"versioned {component_type} {component_id}")
        result = {
            "response": response.content if hasattr(response, 'content') else str(response),
            "component_id": component_id,
            "component_type": component_type,
            "version": version,
            "session_id": mock_request.session_id,
            "metadata": getattr(component, 'metadata', {})
        }
        
        # Convert result to FastAPI response
        from fastapi.responses import JSONResponse
        return JSONResponse(content=result)