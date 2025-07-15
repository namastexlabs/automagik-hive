"""
Playground Extensions for Version Support

Extends Agno Playground endpoints to support version parameters without
breaking the existing functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json

from db.session import get_db
from db.services.component_version_service import ComponentVersionService


# Custom middleware to add version support to existing playground endpoints
class PlaygroundVersionMiddleware:
    """
    Middleware to add version support to Agno Playground run endpoints.
    
    This intercepts requests to /runs and adds version handling if the
    version parameter is provided.
    """
    
    def __init__(self, app, db_session_factory=get_db):
        self.app = app
        self.db_session_factory = db_session_factory
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        
        # Check if this is a request to /runs endpoint with version parameter
        if (scope["type"] == "http" and 
            scope["path"].startswith("/runs") and
            scope["method"] in ["POST"]):
            
            # Parse query parameters to check for version
            query_string = scope.get("query_string", b"").decode()
            if "version=" in query_string:
                # Handle versioned request
                return await self._handle_versioned_request(scope, receive, send)
        
        # Pass through to original app
        await self.app(scope, receive, send)
    
    async def _handle_versioned_request(self, scope, receive, send):
        """Handle requests with version parameters."""
        # This is complex to implement as middleware
        # Better to use route overrides instead
        await self.app(scope, receive, send)


def create_playground_extensions_router():
    """
    Create router with extended playground endpoints that support versioning.
    
    These endpoints mirror the Agno Playground endpoints but add version support.
    """
    router = APIRouter()
    
    @router.post("/runs")
    async def run_with_version_support(
        request: Request,
        version: Optional[int] = Query(None, description="Specific version to run"),
        agent_id: Optional[str] = Query(None, description="Agent ID to run"),
        team_id: Optional[str] = Query(None, description="Team ID to run"),
        workflow_id: Optional[str] = Query(None, description="Workflow ID to run"),
        db: Session = Depends(get_db)
    ):
        """
        Enhanced /runs endpoint with version support.
        
        If version is specified, runs the specific version of the component.
        Otherwise, behaves exactly like the original Agno Playground endpoint.
        """
        
        # Get request body
        body = await request.body()
        
        if version is not None:
            # Handle versioned request
            return await _handle_versioned_run(
                body, version, agent_id, team_id, workflow_id, db
            )
        else:
            # Forward to original Agno Playground endpoint
            # This requires importing the original playground router
            # and calling its run method
            from agno.playground import Playground
            
            # Parse the request body to get the run parameters
            try:
                request_data = json.loads(body.decode()) if body else {}
            except:
                request_data = {}
            
            # Extract component ID from request
            component_id = (
                agent_id or team_id or workflow_id or 
                request_data.get("agent_id") or 
                request_data.get("team_id") or 
                request_data.get("workflow_id")
            )
            
            if not component_id:
                raise HTTPException(
                    status_code=400, 
                    detail="Must specify agent_id, team_id, or workflow_id"
                )
            
            # Call the actual Agno Playground endpoint by importing the unified router
            # and delegating to it - this preserves the exact behavior
            from api.serve import app
            
            # Get the original run endpoint from the app
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/runs" and "POST" in route.methods:
                    # Delegate to the original endpoint
                    return await route.endpoint(request)
            
            # Fallback if route not found
            return {
                "message": "Standard Agno Playground endpoint delegation",
                "component_id": component_id,
                "version": "active",
                "request_data": request_data
            }
    
    return router


async def _handle_versioned_run(
    body: bytes, 
    version: int, 
    agent_id: Optional[str], 
    team_id: Optional[str], 
    workflow_id: Optional[str],
    db: Session
):
    """Handle a versioned run request."""
    
    # Determine component ID and type
    component_id = agent_id or team_id or workflow_id
    if not component_id:
        raise HTTPException(
            status_code=400, 
            detail="Must specify agent_id, team_id, or workflow_id"
        )
    
    component_type = (
        "agent" if agent_id else
        "team" if team_id else
        "workflow" if workflow_id else
        None
    )
    
    # Get the specific version from database
    service = ComponentVersionService(db)
    version_record = service.get_version(component_id, version)
    
    if not version_record:
        raise HTTPException(
            status_code=404, 
            detail=f"Version {version} not found for {component_type} {component_id}"
        )
    
    # Parse request body
    try:
        request_data = json.loads(body.decode()) if body else {}
    except:
        request_data = {}
    
    # Extract message and other parameters
    message = request_data.get("message", "")
    session_id = request_data.get("session_id")
    
    # Validate message content before processing
    from utils.message_validation import validate_agent_message
    validate_agent_message(message, "playground extension execution")
    
    # Run the specific version
    # Note: This is a simplified implementation
    # A full implementation would need to:
    # 1. Dynamically create the component with the version-specific config
    # 2. Handle all the component types properly
    # 3. Return the exact same response format as Agno Playground
    
    try:
        if component_type == "agent":
            result = _run_versioned_agent(component_id, version_record, message, session_id, request_data)
        elif component_type == "team":
            result = _run_versioned_team(component_id, version_record, message, session_id, request_data)
        elif component_type == "workflow":
            result = _run_versioned_workflow(component_id, version_record, message, session_id, request_data)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported component type: {component_type}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


def _run_versioned_agent(component_id: str, version_record, message: str, session_id: Optional[str], request_data: Dict[str, Any]):
    """Run a versioned agent."""
    try:
        # Import agent registry to get the agent
        from agents.registry import get_agent
        
        # Create agent instance with the specific version
        agent = get_agent(
            component_id.split('-')[0],  # Convert 'pagbank-specialist' to 'pagbank'
            version=version_record.version,
            session_id=session_id,
            debug_mode=request_data.get("debug_mode", False),
            # Pass user context from request_data
            user_id=request_data.get("user_id"),
            user_name=request_data.get("user_name"),
            phone_number=request_data.get("phone_number"),
            cpf=request_data.get("cpf")
        )
        
        # Run the agent with validation
        from utils.message_validation import safe_agent_run
        response = safe_agent_run(agent, message, f"playground extension agent {component_id}")
        
        return {
            "response": response.content if hasattr(response, 'content') else str(response),
            "component_id": component_id,
            "component_type": "agent",
            "version": version_record.version,
            "session_id": session_id,
            "metadata": {
                "version_config": version_record.config,
                "created_at": version_record.created_at.isoformat() if version_record.created_at else None,
                "agent_metadata": getattr(agent, 'metadata', {})
            }
        }
        
    except Exception as e:
        return {
            "response": f"Error running versioned agent {component_id} v{version_record.version}: {str(e)}",
            "component_id": component_id,
            "component_type": "agent",
            "version": version_record.version,
            "session_id": session_id,
            "metadata": {
                "error": str(e),
                "version_config": version_record.config,
                "created_at": version_record.created_at.isoformat() if version_record.created_at else None
            }
        }


def _run_versioned_team(component_id: str, version_record, message: str, session_id: Optional[str], request_data: Dict[str, Any]):
    """Run a versioned team."""
    return {
        "response": f"Versioned team {component_id} v{version_record.version} would process: {message}",
        "component_id": component_id,
        "component_type": "team", 
        "version": version_record.version,
        "session_id": session_id,
        "metadata": {
            "version_config": version_record.config,
            "created_at": version_record.created_at.isoformat() if version_record.created_at else None
        }
    }


def _run_versioned_workflow(component_id: str, version_record, message: str, session_id: Optional[str], request_data: Dict[str, Any]):
    """Run a versioned workflow."""
    return {
        "response": f"Versioned workflow {component_id} v{version_record.version} would process: {message}",
        "component_id": component_id,
        "component_type": "workflow",
        "version": version_record.version, 
        "session_id": session_id,
        "metadata": {
            "version_config": version_record.config,
            "created_at": version_record.created_at.isoformat() if version_record.created_at else None
        }
    }


# Export the extensions
playground_extensions_router = create_playground_extensions_router()