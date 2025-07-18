"""
Clean Version Router using Agno Storage

Modern versioning endpoints using Agno storage abstractions.
No backward compatibility - clean implementation only.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any, List
import json
from pydantic import BaseModel
import os

from lib.versioning import AgnoVersionService, VersionInfo, VersionHistory


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


class VersionCreateRequest(BaseModel):
    """Request model for creating a new version."""
    component_type: str
    version: int
    config: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = False


class VersionUpdateRequest(BaseModel):
    """Request model for updating a version."""
    config: Dict[str, Any]
    reason: Optional[str] = None


def get_version_service() -> AgnoVersionService:
    """Get version service instance."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL not configured"
        )
    return AgnoVersionService(db_url)


@router.post("/execute", response_model=VersionedExecutionResponse)
async def execute_versioned_component(
    request: VersionedExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a versioned component using Agno storage.
    
    This endpoint uses the new AgnoVersionService for clean execution.
    """
    
    # Validate message content before processing
    from lib.utils.message_validation import validate_agent_message
    validate_agent_message(request.message, "versioned component execution")
    
    # Get the specific version from Agno storage
    service = get_version_service()
    version_record = service.get_version(request.component_id, request.version)
    
    if not version_record:
        raise HTTPException(
            status_code=404,
            detail=f"Version {request.version} not found for component {request.component_id}"
        )
    
    # Determine component type
    component_type = version_record.component_type
    
    # Create versioned component using factory
    from lib.utils.version_factory import VersionFactory
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
    from lib.utils.message_validation import safe_agent_run
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


@router.post("/components/{component_id}/versions")
async def create_component_version(
    component_id: str,
    request: VersionCreateRequest
):
    """Create a new component version."""
    
    service = get_version_service()
    
    try:
        version_info = service.create_version(
            component_id=component_id,
            component_type=request.component_type,
            version=request.version,
            config=request.config,
            created_by="api",
            description=request.description,
            is_active=request.is_active
        )
        
        return {
            "component_id": version_info.component_id,
            "version": version_info.version,
            "component_type": version_info.component_type,
            "created_at": version_info.created_at,
            "is_active": version_info.is_active,
            "description": version_info.description
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/components/{component_id}/versions")
async def list_component_versions(component_id: str):
    """List all versions for a component."""
    
    service = get_version_service()
    versions = service.list_versions(component_id)
    
    return {
        "component_id": component_id,
        "versions": [
            {
                "version": v.version,
                "component_type": v.component_type,
                "created_at": v.created_at,
                "is_active": v.is_active,
                "description": v.description
            }
            for v in versions
        ]
    }


@router.get("/components/{component_id}/versions/{version}")
async def get_component_version(
    component_id: str,
    version: int
):
    """Get details for a specific component version."""
    
    service = get_version_service()
    version_record = service.get_version(component_id, version)
    
    if not version_record:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for component {component_id}"
        )
    
    return {
        "component_id": version_record.component_id,
        "version": version_record.version,
        "component_type": version_record.component_type,
        "config": version_record.config,
        "created_at": version_record.created_at,
        "is_active": version_record.is_active,
        "description": version_record.description
    }


@router.put("/components/{component_id}/versions/{version}")
async def update_component_version(
    component_id: str,
    version: int,
    request: VersionUpdateRequest
):
    """Update configuration for a specific version."""
    
    service = get_version_service()
    
    try:
        version_info = service.update_config(
            component_id=component_id,
            version=version,
            config=request.config,
            changed_by="api",
            reason=request.reason
        )
        
        return {
            "component_id": version_info.component_id,
            "version": version_info.version,
            "component_type": version_info.component_type,
            "config": version_info.config,
            "created_at": version_info.created_at,
            "is_active": version_info.is_active
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/components/{component_id}/versions/{version}/activate")
async def activate_component_version(
    component_id: str,
    version: int,
    reason: Optional[str] = None
):
    """Activate a specific version."""
    
    service = get_version_service()
    
    try:
        version_info = service.activate_version(
            component_id=component_id,
            version=version,
            changed_by="api",
            reason=reason
        )
        
        return {
            "component_id": version_info.component_id,
            "version": version_info.version,
            "component_type": version_info.component_type,
            "is_active": version_info.is_active,
            "message": f"Version {version} activated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/components/{component_id}/versions/{version}")
async def delete_component_version(
    component_id: str,
    version: int
):
    """Delete a specific version."""
    
    service = get_version_service()
    
    try:
        success = service.delete_version(
            component_id=component_id,
            version=version,
            changed_by="api"
        )
        
        if success:
            return {
                "component_id": component_id,
                "version": version,
                "message": f"Version {version} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for component {component_id}"
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/components/{component_id}/history")
async def get_component_history(
    component_id: str,
    limit: int = 50
):
    """Get version history for a component."""
    
    service = get_version_service()
    history = service.get_history(component_id, limit)
    
    return {
        "component_id": component_id,
        "history": [
            {
                "version": h.version,
                "action": h.action,
                "timestamp": h.timestamp,
                "changed_by": h.changed_by,
                "reason": h.reason
            }
            for h in history
        ]
    }


@router.get("/components")
async def list_all_components():
    """List all components with versions."""
    
    service = get_version_service()
    components = service.get_all_components()
    
    result = []
    for component_id in components:
        active_version = service.get_active_version(component_id)
        if active_version:
            result.append({
                "component_id": component_id,
                "component_type": active_version.component_type,
                "active_version": active_version.version,
                "description": active_version.description
            })
    
    return {"components": result}


@router.get("/components/by-type/{component_type}")
async def list_components_by_type(component_type: str):
    """List components by type."""
    
    service = get_version_service()
    components = service.get_components_by_type(component_type)
    
    result = []
    for component_id in components:
        active_version = service.get_active_version(component_id)
        if active_version:
            result.append({
                "component_id": component_id,
                "active_version": active_version.version,
                "description": active_version.description
            })
    
    return {
        "component_type": component_type,
        "components": result
    }


# Export router for inclusion in main app
version_router = router