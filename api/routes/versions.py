"""
Simplified Component Version Management API

Unified endpoints for managing versions of agents, teams, and workflows.
Supports bilateral sync between YAML configurations and database storage.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from db.session import get_db
from db.services.component_version_service import ComponentVersionService
from services.version_sync_service import VersionSyncService


# Pydantic models for request/response
class ComponentVersionCreate(BaseModel):
    """Request model for creating a new component version."""
    version: int = Field(..., description="Version number (e.g., 28, 29, 30)", ge=1)
    config: Dict[str, Any] = Field(..., description="Full component configuration (complete YAML content)")
    component_type: str = Field("agent", description="Component type: 'agent', 'team', 'workflow'")
    description: Optional[str] = Field(None, description="Description of changes in this version")
    is_active: bool = Field(True, description="Whether to make this version active immediately")
    update_yaml: bool = Field(True, description="Whether to update the YAML file")
    created_by: str = Field("api", description="User who created this version")


class ComponentVersionResponse(BaseModel):
    """Response model for component version information."""
    id: int
    component_id: str
    component_type: str
    version: int
    created_at: Optional[str]
    created_by: Optional[str]
    is_active: bool
    is_deprecated: bool
    description: Optional[str]
    config: Dict[str, Any]


# Create router
router = APIRouter(prefix="/versions", tags=["component-versions"])


@router.get("/{component_id}")
def list_component_versions(
    component_id: str,
    include_deprecated: bool = Query(False, description="Include deprecated versions"),
    db: Session = Depends(get_db)
):
    """
    List all versions for a component.
    
    Returns all versions for the specified component (agent, team, or workflow),
    optionally including deprecated versions.
    """
    try:
        service = ComponentVersionService(db)
        versions = service.list_versions(component_id, include_deprecated)
        
        return [
            ComponentVersionResponse(
                id=v.id,
                component_id=v.component_id,
                component_type=v.component_type,
                version=v.version,
                created_at=v.created_at.isoformat() if v.created_at else None,
                created_by=v.created_by,
                is_active=v.is_active,
                is_deprecated=v.is_deprecated,
                description=v.description,
                config=v.config
            )
            for v in versions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{component_id}")
def create_component_version(
    component_id: str,
    request: ComponentVersionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new component version.
    
    Creates a new version with the provided configuration and optionally
    updates the corresponding YAML file.
    """
    try:
        service = ComponentVersionService(db)
        sync_service = VersionSyncService(db)
        
        # Create the version in database
        version = service.create_version(
            component_id=component_id,
            component_type=request.component_type,
            version=request.version,
            config=request.config,
            created_by=request.created_by,
            description=request.description,
            is_active=request.is_active,
            sync_source="api"
        )
        
        # Update YAML file if requested
        if request.update_yaml:
            try:
                yaml_file = service.get_yaml_file_path(component_id, request.component_type)
                if yaml_file:
                    sync_service.update_yaml_from_db(yaml_file, component_id, request.component_type)
                else:
                    print(f"⚠️ Could not find YAML file for {request.component_type} {component_id}")
            except Exception as yaml_error:
                print(f"⚠️ Could not update YAML file: {yaml_error}")
                # Don't fail the API call if YAML update fails
        
        return ComponentVersionResponse(
            id=version.id,
            component_id=version.component_id,
            component_type=version.component_type,
            version=version.version,
            created_at=version.created_at.isoformat() if version.created_at else None,
            created_by=version.created_by,
            is_active=version.is_active,
            is_deprecated=version.is_deprecated,
            description=version.description,
            config=version.config
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{component_id}/{version}/activate")
def activate_component_version(
    component_id: str,
    version: int,
    update_yaml: bool = Query(True, description="Whether to update YAML file"),
    reason: Optional[str] = Query(None, description="Reason for activation"),
    changed_by: str = Query("api", description="User making the change"),
    db: Session = Depends(get_db)
):
    """
    Activate a specific component version.
    
    Makes the specified version active and optionally updates the YAML file
    with the new active configuration.
    """
    try:
        service = ComponentVersionService(db)
        sync_service = VersionSyncService(db)
        
        # Activate the version
        activated_version = service.activate_version(
            component_id=component_id,
            version=version,
            changed_by=changed_by,
            reason=reason,
            sync_source="api"
        )
        
        # Update YAML file if requested
        if update_yaml:
            try:
                yaml_file = service.get_yaml_file_path(component_id, activated_version.component_type)
                if yaml_file:
                    sync_service.update_yaml_from_db(yaml_file, component_id, activated_version.component_type)
                else:
                    print(f"⚠️ Could not find YAML file for {activated_version.component_type} {component_id}")
            except Exception as yaml_error:
                print(f"⚠️ Could not update YAML file: {yaml_error}")
                # Don't fail the API call if YAML update fails
        
        return ComponentVersionResponse(
            id=activated_version.id,
            component_id=activated_version.component_id,
            component_type=activated_version.component_type,
            version=activated_version.version,
            created_at=activated_version.created_at.isoformat() if activated_version.created_at else None,
            created_by=activated_version.created_by,
            is_active=activated_version.is_active,
            is_deprecated=activated_version.is_deprecated,
            description=activated_version.description,
            config=activated_version.config
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{component_id}/{version}")
def delete_component_version(
    component_id: str,
    version: int,
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    changed_by: str = Query("api", description="User making the change"),
    db: Session = Depends(get_db)
):
    """
    Delete (deprecate) a specific component version.
    
    Marks the specified version as deprecated. Cannot delete the
    currently active version.
    """
    try:
        service = ComponentVersionService(db)
        
        # Deprecate the version (soft delete)
        deprecated_version = service.deprecate_version(
            component_id=component_id,
            version=version,
            changed_by=changed_by,
            reason=reason
        )
        
        return {
            "message": f"Version {version} of {deprecated_version.component_type} {component_id} has been deprecated",
            "component_id": component_id,
            "component_type": deprecated_version.component_type,
            "version": version,
            "deprecated": True
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Sync management endpoints
@router.post("/sync/startup")
def trigger_startup_sync(db: Session = Depends(get_db)):
    """Manually trigger the startup sync process."""
    try:
        from services.version_sync_service import sync_all_components
        results = sync_all_components()
        return {"message": "Startup sync completed", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/sync/{component_id}")
def force_sync_component(
    component_id: str,
    component_type: str = Query(..., description="Component type: 'agent', 'team', 'workflow'"),
    direction: str = Query("auto", description="Sync direction: 'auto', 'yaml_to_db', 'db_to_yaml'"),
    db: Session = Depends(get_db)
):
    """Force sync a specific component."""
    try:
        sync_service = VersionSyncService(db)
        result = sync_service.force_sync_component(component_id, component_type, direction)
        return {"message": f"Sync completed for {component_type} {component_id}", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


# Export the router
versions_router = router