"""
Agent Version Management API Endpoints

This module provides REST API endpoints for managing agent versions,
including creation, activation, A/B testing, and metrics tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from db.session import get_db
from db.services.agent_version_service import AgentVersionService
from agents.version_factory import agent_factory, create_versioned_agent


# Pydantic models for request/response
class AgentVersionCreate(BaseModel):
    """Request model for creating a new agent version."""
    agent_id: str = Field(..., description="Agent identifier (e.g., 'pagbank-specialist')")
    version: int = Field(..., description="Version number (e.g., 27, 28, 29)", ge=1)
    config: Dict[str, Any] = Field(..., description="Full agent configuration")
    description: Optional[str] = Field(None, description="Description of changes in this version")
    is_active: bool = Field(False, description="Whether to make this version active immediately")
    created_by: str = Field("api", description="User who created this version")


class AgentVersionResponse(BaseModel):
    """Response model for agent version information."""
    id: int
    agent_id: str
    version: int
    created_at: Optional[datetime]
    created_by: Optional[str]
    is_active: bool
    is_deprecated: bool
    description: Optional[str]
    config: Dict[str, Any]


class AgentVersionUpdate(BaseModel):
    """Request model for updating agent version configuration."""
    config: Dict[str, Any] = Field(..., description="Updated configuration")
    description: Optional[str] = Field(None, description="Reason for the update")
    changed_by: str = Field("api", description="User making the change")


class AgentVersionActivate(BaseModel):
    """Request model for activating an agent version."""
    reason: Optional[str] = Field(None, description="Reason for activation")
    changed_by: str = Field("api", description="User making the change")


class AgentRunRequest(BaseModel):
    """Request model for running an agent with specific version."""
    message: str = Field(..., description="Message to send to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    debug_mode: bool = Field(False, description="Enable debug mode")


class AgentRunResponse(BaseModel):
    """Response model for agent run results."""
    response: str
    agent_id: str
    version: int
    session_id: Optional[str]
    metadata: Dict[str, Any]


class AgentMetricsResponse(BaseModel):
    """Response model for agent metrics."""
    agent_id: str
    version: int
    metric_date: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: Optional[int]
    escalation_rate: Optional[int]
    user_satisfaction: Optional[int]


# Create router
router = APIRouter(prefix="/agents", tags=["agent-versions"])


@router.post("/", response_model=AgentVersionResponse)
def create_agent_version(
    request: AgentVersionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new agent version.
    
    This endpoint allows creating new versions of agents with different
    configurations, prompts, or behaviors.
    """
    try:
        service = AgentVersionService(db)
        
        version = service.create_version(
            agent_id=request.agent_id,
            version=request.version,
            config=request.config,
            created_by=request.created_by,
            description=request.description,
            is_active=request.is_active
        )
        
        return AgentVersionResponse(
            id=version.id,
            agent_id=version.agent_id,
            version=version.version,
            created_at=version.created_at,
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


@router.get("/{agent_id}/versions", response_model=List[AgentVersionResponse])
def list_agent_versions(
    agent_id: str,
    include_deprecated: bool = Query(False, description="Include deprecated versions"),
    db: Session = Depends(get_db)
):
    """
    List all versions for a specific agent.
    
    Returns all versions for the specified agent, optionally including
    deprecated versions.
    """
    try:
        service = AgentVersionService(db)
        versions = service.list_versions(agent_id, include_deprecated)
        
        return [
            AgentVersionResponse(
                id=v.id,
                agent_id=v.agent_id,
                version=v.version,
                created_at=v.created_at,
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


@router.get("/{agent_id}/versions/active", response_model=AgentVersionResponse)
def get_active_agent_version(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the currently active version for an agent.
    
    Returns the version that is currently marked as active for the specified agent.
    """
    try:
        service = AgentVersionService(db)
        active_version = service.get_active_version(agent_id)
        
        if not active_version:
            raise HTTPException(status_code=404, detail=f"No active version found for agent {agent_id}")
        
        return AgentVersionResponse(
            id=active_version.id,
            agent_id=active_version.agent_id,
            version=active_version.version,
            created_at=active_version.created_at,
            created_by=active_version.created_by,
            is_active=active_version.is_active,
            is_deprecated=active_version.is_deprecated,
            description=active_version.description,
            config=active_version.config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{agent_id}/versions/{version}", response_model=AgentVersionResponse)
def get_agent_version(
    agent_id: str,
    version: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific agent version.
    
    Returns detailed information about a specific version of an agent.
    """
    try:
        service = AgentVersionService(db)
        agent_version = service.get_version(agent_id, version)
        
        if not agent_version:
            raise HTTPException(status_code=404, detail=f"Version {version} not found for agent {agent_id}")
        
        return AgentVersionResponse(
            id=agent_version.id,
            agent_id=agent_version.agent_id,
            version=agent_version.version,
            created_at=agent_version.created_at,
            created_by=agent_version.created_by,
            is_active=agent_version.is_active,
            is_deprecated=agent_version.is_deprecated,
            description=agent_version.description,
            config=agent_version.config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{agent_id}/versions/{version}/activate", response_model=AgentVersionResponse)
def activate_agent_version(
    agent_id: str,
    version: int,
    request: AgentVersionActivate,
    db: Session = Depends(get_db)
):
    """
    Activate a specific agent version.
    
    Makes the specified version active and deactivates all other versions
    for the same agent.
    """
    try:
        service = AgentVersionService(db)
        activated_version = service.activate_version(
            agent_id=agent_id,
            version=version,
            changed_by=request.changed_by,
            reason=request.reason
        )
        
        return AgentVersionResponse(
            id=activated_version.id,
            agent_id=activated_version.agent_id,
            version=activated_version.version,
            created_at=activated_version.created_at,
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


@router.put("/{agent_id}/versions/{version}/deprecate", response_model=AgentVersionResponse)
def deprecate_agent_version(
    agent_id: str,
    version: int,
    request: AgentVersionActivate,  # Reuse the same model
    db: Session = Depends(get_db)
):
    """
    Deprecate a specific agent version.
    
    Marks the specified version as deprecated. Cannot deprecate the
    currently active version.
    """
    try:
        service = AgentVersionService(db)
        deprecated_version = service.deprecate_version(
            agent_id=agent_id,
            version=version,
            changed_by=request.changed_by,
            reason=request.reason
        )
        
        return AgentVersionResponse(
            id=deprecated_version.id,
            agent_id=deprecated_version.agent_id,
            version=deprecated_version.version,
            created_at=deprecated_version.created_at,
            created_by=deprecated_version.created_by,
            is_active=deprecated_version.is_active,
            is_deprecated=deprecated_version.is_deprecated,
            description=deprecated_version.description,
            config=deprecated_version.config
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{agent_id}/versions/{version}/config", response_model=AgentVersionResponse)
def update_agent_version_config(
    agent_id: str,
    version: int,
    request: AgentVersionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update configuration for a specific agent version.
    
    Updates the configuration for the specified version. This allows
    modifying prompts, tools, or other settings.
    """
    try:
        service = AgentVersionService(db)
        updated_version = service.update_config(
            agent_id=agent_id,
            version=version,
            config=request.config,
            changed_by=request.changed_by,
            reason=request.description
        )
        
        return AgentVersionResponse(
            id=updated_version.id,
            agent_id=updated_version.agent_id,
            version=updated_version.version,
            created_at=updated_version.created_at,
            created_by=updated_version.created_by,
            is_active=updated_version.is_active,
            is_deprecated=updated_version.is_deprecated,
            description=updated_version.description,
            config=updated_version.config
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{agent_id}/run", response_model=AgentRunResponse)
def run_agent(
    agent_id: str,
    request: AgentRunRequest,
    version: Optional[int] = Query(None, description="Specific version to run, or None for active version"),
    db: Session = Depends(get_db)
):
    """
    Run an agent with a specific version.
    
    Executes the agent with the specified version (or active version if not specified)
    and returns the response.
    """
    try:
        # Create agent instance
        agent = create_versioned_agent(
            agent_id=agent_id,
            version=version,
            session_id=request.session_id,
            debug_mode=request.debug_mode
        )
        
        # Run the agent
        response = agent.run(request.message)
        
        # Get version info from agent metadata
        agent_version = agent.metadata.get("version", "unknown")
        
        return AgentRunResponse(
            response=response.content,
            agent_id=agent_id,
            version=agent_version,
            session_id=request.session_id,
            metadata=agent.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{agent_id}/versions/{version}/run", response_model=AgentRunResponse)
def run_agent_version(
    agent_id: str,
    version: int,
    request: AgentRunRequest,
    db: Session = Depends(get_db)
):
    """
    Run a specific agent version.
    
    Executes the agent with the specified version and returns the response.
    """
    try:
        # Create agent instance with specific version
        agent = create_versioned_agent(
            agent_id=agent_id,
            version=version,
            session_id=request.session_id,
            debug_mode=request.debug_mode
        )
        
        # Run the agent
        response = agent.run(request.message)
        
        return AgentRunResponse(
            response=response.content,
            agent_id=agent_id,
            version=version,
            session_id=request.session_id,
            metadata=agent.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{agent_id}/versions/{version}/metrics", response_model=List[AgentMetricsResponse])
def get_agent_version_metrics(
    agent_id: str,
    version: int,
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get metrics for a specific agent version.
    
    Returns performance metrics for the specified version over the
    specified time period.
    """
    try:
        service = AgentVersionService(db)
        metrics = service.get_metrics(agent_id, version, days)
        
        return [
            AgentMetricsResponse(
                agent_id=m.agent_id,
                version=m.version,
                metric_date=m.metric_date,
                total_requests=m.total_requests,
                successful_requests=m.successful_requests,
                failed_requests=m.failed_requests,
                average_response_time=m.average_response_time,
                escalation_rate=m.escalation_rate,
                user_satisfaction=m.user_satisfaction
            )
            for m in metrics
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
def list_all_agents():
    """
    List all available agents and their versions.
    
    Returns information about all agents in the system, including
    their versions and status.
    """
    try:
        return agent_factory.list_available_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{agent_id}/migrate", response_model=Dict[str, Any])
def migrate_agent_to_database(
    agent_id: str,
    version: int = Query(..., description="Version number to assign"),
    created_by: str = Query("api", description="User performing migration"),
    db: Session = Depends(get_db)
):
    """
    Migrate file-based agent configuration to database.
    
    This endpoint migrates an agent's file-based configuration to the
    database versioning system.
    """
    try:
        success = agent_factory.migrate_file_to_database(
            agent_id=agent_id,
            version=version,
            created_by=created_by
        )
        
        if success:
            return {
                "message": f"Successfully migrated {agent_id} to database version {version}",
                "agent_id": agent_id,
                "version": version
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to migrate {agent_id}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{agent_id}/versions/{source_version}/clone", response_model=AgentVersionResponse)
def clone_agent_version(
    agent_id: str,
    source_version: int,
    target_version: int = Query(..., description="New version number"),
    created_by: str = Query("api", description="User creating the clone"),
    description: Optional[str] = Query(None, description="Description for the new version"),
    db: Session = Depends(get_db)
):
    """
    Clone an existing agent version.
    
    Creates a new version by copying the configuration from an existing version.
    This is useful for creating variations or starting from a known good state.
    """
    try:
        service = AgentVersionService(db)
        cloned_version = service.clone_version(
            agent_id=agent_id,
            source_version=source_version,
            target_version=target_version,
            created_by=created_by,
            description=description
        )
        
        return AgentVersionResponse(
            id=cloned_version.id,
            agent_id=cloned_version.agent_id,
            version=cloned_version.version,
            created_at=cloned_version.created_at,
            created_by=cloned_version.created_by,
            is_active=cloned_version.is_active,
            is_deprecated=cloned_version.is_deprecated,
            description=cloned_version.description,
            config=cloned_version.config
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Export the router
agent_versions_router = router