"""
Clean Version Router using Agno Storage

Modern versioning endpoints using Agno storage abstractions.
No backward compatibility - clean implementation only.
"""

import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from lib.versioning import AgnoVersionService
from lib.versioning.bidirectional_sync import BidirectionalSync
from lib.versioning.dev_mode import DevMode

router = APIRouter(prefix="/version", tags=["versioning"])


class VersionedExecutionRequest(BaseModel):
    """Request model for versioned component execution."""

    message: str
    component_id: str
    version: int
    session_id: str | None = None
    debug_mode: bool = False
    user_id: str | None = None
    user_name: str | None = None
    phone_number: str | None = None
    cpf: str | None = None


class VersionedExecutionResponse(BaseModel):
    """Response model for versioned component execution."""

    response: str
    component_id: str
    component_type: str
    version: int
    session_id: str | None
    metadata: dict[str, Any]


class VersionCreateRequest(BaseModel):
    """Request model for creating a new version."""

    component_type: str
    version: int
    config: dict[str, Any]
    description: str | None = None
    is_active: bool = False


class VersionUpdateRequest(BaseModel):
    """Request model for updating a version."""

    config: dict[str, Any]
    reason: str | None = None


def get_version_service() -> AgnoVersionService:
    """Get version service instance."""
    db_url = os.getenv("HIVE_DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="HIVE_DATABASE_URL not configured")
    return AgnoVersionService(db_url)


@router.post("/execute", response_model=VersionedExecutionResponse)
async def execute_versioned_component(
    request: VersionedExecutionRequest, background_tasks: BackgroundTasks
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
    version_record = await service.get_version(request.component_id, request.version)

    if not version_record:
        raise HTTPException(
            status_code=404,
            detail=f"Version {request.version} not found for component {request.component_id}",
        )

    # Determine component type
    component_type = version_record.component_type

    # Create versioned component using factory
    from lib.utils.version_factory import VersionFactory

    factory = VersionFactory()

    component = await factory.create_versioned_component(
        component_id=request.component_id,
        component_type=component_type,
        version=request.version,
        session_id=request.session_id,
        debug_mode=request.debug_mode,
        user_id=request.user_id,
        user_name=request.user_name,
        phone_number=request.phone_number,
        cpf=request.cpf,
    )

    # Execute component with validation
    from lib.utils.message_validation import safe_agent_run

    response = safe_agent_run(
        component, request.message, f"versioned {component_type} {request.component_id}"
    )

    # Create response
    return VersionedExecutionResponse(
        response=response.content if hasattr(response, "content") else str(response),
        component_id=request.component_id,
        component_type=component_type,
        version=request.version,
        session_id=request.session_id,
        metadata=getattr(component, "metadata", {}),
    )


@router.post("/components/{component_id}/versions")
async def create_component_version(component_id: str, request: VersionCreateRequest):
    """Create a new component version."""

    service = get_version_service()

    try:
        # Create the version
        await service.create_version(
            component_id=component_id,
            component_type=request.component_type,
            version=request.version,
            config=request.config,
            created_by="api",
            description=request.description,
        )

        # Set as active if requested
        if request.is_active:
            await service.set_active_version(component_id, request.version, "api")

        # Get the created version info
        version_info = await service.get_version(component_id, request.version)

        return {
            "component_id": version_info.component_id,
            "version": version_info.version,
            "component_type": version_info.component_type,
            "created_at": version_info.created_at,
            "is_active": version_info.is_active,
            "description": version_info.description,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/components/{component_id}/versions")
async def list_component_versions(component_id: str):
    """List all versions for a component."""

    service = get_version_service()
    versions = await service.list_versions(component_id)

    return {
        "component_id": component_id,
        "versions": [
            {
                "version": v.version,
                "component_type": v.component_type,
                "created_at": v.created_at,
                "is_active": v.is_active,
                "description": v.description,
            }
            for v in versions
        ],
    }


@router.get("/components/{component_id}/versions/{version}")
async def get_component_version(component_id: str, version: int):
    """Get details for a specific component version."""

    service = get_version_service()
    version_record = await service.get_version(component_id, version)

    if not version_record:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found for component {component_id}",
        )

    return {
        "component_id": version_record.component_id,
        "version": version_record.version,
        "component_type": version_record.component_type,
        "config": version_record.config,
        "created_at": version_record.created_at,
        "is_active": version_record.is_active,
        "description": version_record.description,
    }


@router.put("/components/{component_id}/versions/{version}")
async def update_component_version(
    component_id: str, version: int, request: VersionUpdateRequest
):
    """Update configuration for a specific version."""

    service = get_version_service()

    try:
        # Check if version exists first
        existing_version = await service.get_version(component_id, version)
        if not existing_version:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for component {component_id}",
            )

        # Use the underlying component service directly for update
        import json

        db_service = service.component_service
        db = await db_service._get_db_service()

        # Update the config directly
        update_query = """
        UPDATE hive.component_versions
        SET config = %(config)s
        WHERE component_id = %(component_id)s AND version = %(version)s
        """

        await db.execute(
            update_query,
            {
                "component_id": component_id,
                "version": version,
                "config": json.dumps(request.config),
            },
        )

        # Record history
        history_query = """
        INSERT INTO hive.version_history
        (component_id, to_version, action, description, changed_by)
        VALUES (%(component_id)s, %(version)s, 'config_updated', %(description)s, 'api')
        """

        await db.execute(
            history_query,
            {
                "component_id": component_id,
                "version": version,
                "description": request.reason or "Configuration updated via API",
            },
        )

        # Trigger YAML write-back (production only)
        if not DevMode.is_enabled():
            try:
                db_url = os.getenv("HIVE_DATABASE_URL")
                if db_url:
                    sync_engine = BidirectionalSync(db_url)
                    await sync_engine.write_back_to_yaml(
                        component_id=component_id,
                        component_type=existing_version.component_type,
                        config=request.config,
                        version=version,
                    )
            except Exception as e:
                # Log but don't fail the API call - database update succeeded
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to write back to YAML for {component_id}: {e}")

        # Return updated version info
        updated_version = await service.get_version(component_id, version)
        return {
            "component_id": updated_version.component_id,
            "version": updated_version.version,
            "component_type": updated_version.component_type,
            "config": updated_version.config,
            "is_active": updated_version.is_active,
            "description": updated_version.description,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/components/{component_id}/versions/{version}/activate")
async def activate_component_version(
    component_id: str, version: int, reason: str | None = None
):
    """Activate a specific version."""

    service = get_version_service()

    try:
        await service.set_active_version(component_id, version, "api")
        version_info = await service.get_version(component_id, version)

        return {
            "component_id": version_info.component_id,
            "version": version_info.version,
            "component_type": version_info.component_type,
            "is_active": version_info.is_active,
            "message": f"Version {version} activated successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/components/{component_id}/versions/{version}")
async def delete_component_version(component_id: str, version: int):
    """Delete a specific version."""

    service = get_version_service()

    try:
        # Check if version exists first
        existing_version = await service.get_version(component_id, version)
        if not existing_version:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found for component {component_id}",
            )

        # Use the underlying component service directly for deletion
        db_service = service.component_service
        db = await db_service._get_db_service()

        # If this is the active version, deactivate it first
        if existing_version.is_active:
            # Deactivate all versions for this component first
            await db.execute(
                "UPDATE hive.component_versions SET is_active = false WHERE component_id = %(component_id)s",
                {"component_id": component_id},
            )

        # Delete the version
        delete_query = "DELETE FROM hive.component_versions WHERE component_id = %(component_id)s AND version = %(version)s"
        await db.execute(
            delete_query, {"component_id": component_id, "version": version}
        )

        # Record history
        history_query = """
        INSERT INTO hive.version_history
        (component_id, from_version, to_version, action, description, changed_by)
        VALUES (%(component_id)s, %(version)s, NULL, 'deleted', 'Version deleted via API', 'api')
        """

        await db.execute(
            history_query,
            {
                "component_id": component_id,
                "version": version,
            },
        )

        return {
            "component_id": component_id,
            "version": version,
            "message": f"Version {version} deleted successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/components/{component_id}/history")
async def get_component_history(component_id: str, limit: int = 50):
    """Get version history for a component."""

    service = get_version_service()
    history = await service.get_version_history(component_id)

    return {
        "component_id": component_id,
        "history": [
            {
                "version": h.version,
                "action": h.action,
                "timestamp": h.timestamp,
                "changed_by": h.changed_by,
                "reason": h.reason,
            }
            for h in history
        ],
    }


@router.get("/components")
async def list_all_components():
    """List all components with versions."""

    service = get_version_service()
    components = await service.get_all_components()

    result = []
    for component_id in components:
        active_version = await service.get_active_version(component_id)
        if active_version:
            result.append(
                {
                    "component_id": component_id,
                    "component_type": active_version.component_type,
                    "active_version": active_version.version,
                    "description": active_version.description,
                }
            )

    return {"components": result}


@router.get("/components/by-type/{component_type}")
async def list_components_by_type(component_type: str):
    """List components by type."""

    service = get_version_service()
    components = await service.get_components_by_type(component_type)

    result = []
    for component_id in components:
        active_version = await service.get_active_version(component_id)
        if active_version:
            result.append(
                {
                    "component_id": component_id,
                    "active_version": active_version.version,
                    "description": active_version.description,
                }
            )

    return {"component_type": component_type, "components": result}


# Export router for inclusion in main app
version_router = router
