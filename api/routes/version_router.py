"""
Lightweight Version Router for API Architecture Cleanup

This router provides version-handling endpoints that replace the heavy operations
currently performed in the middleware layer. This is part of the architectural
cleanup to move blocking operations out of middleware and into proper FastAPI
router endpoints.

Part of Epic: api-architecture-cleanup, Task T-005
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
from pydantic import BaseModel

from db.session import get_db
from db.services.component_version_service import ComponentVersionService


router = APIRouter(prefix="/api/v1/version", tags=["versioning"])


class VersionedExecutionRequest(BaseModel):
    """Request model for versioned component execution."""
    message: str
    component_id: str
    version: int
    session_id: Optional[str] = None
    debug_mode: bool = False
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    cpf: Optional[str] = None


class VersionedExecutionResponse(BaseModel):
    """Response model for versioned component execution."""
    response: str
    component_id: str
    component_type: str
    version: int
    session_id: Optional[str]
    metadata: Dict[str, Any]


@router.post("/execute", response_model=VersionedExecutionResponse)
async def execute_versioned_component(
    request: VersionedExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute a versioned component with proper async handling.
    
    This endpoint replaces the heavy operations currently performed in middleware,
    providing better performance by moving blocking operations to router level.
    """
    
    # Validate message content before processing
    from utils.message_validation import validate_agent_message
    validate_agent_message(request.message, "versioned component execution")
    
    # Get the specific version from database
    service = ComponentVersionService(db)
    version_record = service.get_version(request.component_id, request.version)
    
    if not version_record:
        raise HTTPException(
            status_code=404,
            detail=f"Version {request.version} not found for component {request.component_id}"
        )
    
    # Determine component type
    component_type = version_record.component_type
    
    # Create versioned component using factory
    from common.version_factory import VersionFactory
    factory = VersionFactory()
    
    component = factory.create_versioned_component(
        component_id=request.component_id,
        component_type=component_type,
        version=request.version,
        session_id=request.session_id,
        debug_mode=request.debug_mode,
        user_id=request.user_id,
        user_name=request.user_name,
        phone_number=request.phone_number,
        cpf=request.cpf
    )
    
    # Execute component with validation
    from utils.message_validation import safe_agent_run
    response = safe_agent_run(
        component, 
        request.message, 
        f"versioned {component_type} {request.component_id}"
    )
    
    # Create response
    result = VersionedExecutionResponse(
        response=response.content if hasattr(response, 'content') else str(response),
        component_id=request.component_id,
        component_type=component_type,
        version=request.version,
        session_id=request.session_id,
        metadata=getattr(component, 'metadata', {})
    )
    
    return result


@router.get("/components/{component_id}/versions")
async def list_component_versions(
    component_id: str,
    db: Session = Depends(get_db)
):
    """List all versions for a component."""
    
    service = ComponentVersionService(db)
    versions = service.list_versions(component_id)
    
    return {
        "component_id": component_id,
        "versions": [
            {
                "version": v.version,
                "component_type": v.component_type,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "is_active": v.is_active
            }
            for v in versions
        ]
    }


@router.get("/components/{component_id}/versions/{version}")
async def get_component_version(
    component_id: str,
    version: int,
    db: Session = Depends(get_db)
):
    """Get details for a specific component version."""
    
    service = ComponentVersionService(db)
    version_record = service.get_version(component_id, version)
    
    if not version_record:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for component {component_id}"
        )
    
    return {
        "component_id": component_id,
        "version": version_record.version,
        "component_type": version_record.component_type,
        "config": version_record.config,
        "created_at": version_record.created_at.isoformat() if version_record.created_at else None,
        "is_active": version_record.is_active
    }


# SimplifiedVersionMiddleware removed - using pure router approach instead


# Export router for inclusion in main app
version_router = router