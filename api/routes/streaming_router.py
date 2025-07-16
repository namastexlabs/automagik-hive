"""
Custom streaming router to override Agno's default stream=False behavior.
This router wraps the playground endpoints to enable streaming by default.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Form, File, Query, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from agno.agent.agent import Agent
from agno.team.team import Team
from agno.workflow.workflow import Workflow
from agno.app.fastapi.async_router import (
    agent_chat_response_streamer,
    team_chat_response_streamer,
    get_async_router as get_agno_router
)
from uuid import uuid4
import json
from dataclasses import asdict
from agno.utils.log import logger


def get_streaming_router(
    agents: Optional[List[Agent]] = None, 
    teams: Optional[List[Team]] = None, 
    workflows: Optional[List[Workflow]] = None
) -> APIRouter:
    """
    Create a custom router that defaults to streaming=True instead of False.
    
    This overrides the Agno framework's default behavior where stream=False.
    """
    router = APIRouter()
    
    # Get the default streaming mode from environment
    default_stream_mode = os.getenv("DEFAULT_STREAM_MODE", "true").lower() == "true"
    
    if agents is None and teams is None and workflows is None:
        raise ValueError("Either agents, teams or workflows must be provided.")
    
    @router.get("/status")
    async def status():
        return {"status": "available"}
    
    @router.post("/runs")
    async def run_with_streaming_default(
        message: str = Form(None),
        stream: Optional[bool] = Form(None),  # Allow None to detect when not provided
        monitor: bool = Form(False),
        session_id: Optional[str] = Form(None),
        user_id: Optional[str] = Form(None),
        files: Optional[List[UploadFile]] = File(None),
        agent_id: Optional[str] = Query(None),
        team_id: Optional[str] = Query(None),
        workflow_id: Optional[str] = Query(None),
        workflow_input: Optional[str] = Form(None),
    ):
        """
        Enhanced endpoint that defaults to streaming=True instead of False.
        """
        
        # If stream parameter is not provided, use the default from environment
        if stream is None:
            stream = default_stream_mode
            logger.info(f"Stream parameter not provided, using default: {stream}")
        
        # Use the original Agno router but with our stream parameter
        agno_router = get_agno_router(agents=agents, teams=teams, workflows=workflows)
        
        # Get the original endpoint function
        original_endpoint = None
        for route in agno_router.routes:
            if hasattr(route, 'path') and route.path == "/runs" and route.methods == {"POST"}:
                original_endpoint = route.endpoint
                break
        
        if original_endpoint is None:
            raise HTTPException(status_code=500, detail="Could not find original endpoint")
        
        # Call the original endpoint with our stream parameter
        return await original_endpoint(
            message=message,
            stream=stream,
            monitor=monitor,
            session_id=session_id,
            user_id=user_id,
            files=files,
            agent_id=agent_id,
            team_id=team_id,
            workflow_id=workflow_id,
            workflow_input=workflow_input,
        )
    
    # Include all other routes from the original router
    original_router = get_agno_router(agents=agents, teams=teams, workflows=workflows)
    for route in original_router.routes:
        if hasattr(route, 'path') and route.path != "/runs":
            router.routes.append(route)
    
    return router


def get_playground_router_with_default_streaming(
    agents: Optional[List[Agent]] = None, 
    teams: Optional[List[Team]] = None, 
    workflows: Optional[List[Workflow]] = None
) -> APIRouter:
    """
    Convenience function to get a playground router with default streaming enabled.
    """
    return get_streaming_router(agents=agents, teams=teams, workflows=workflows)