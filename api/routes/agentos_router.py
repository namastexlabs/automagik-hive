"""AgentOS configuration routes."""

from __future__ import annotations

from agno.os.schema import ConfigResponse
from fastapi import APIRouter, Depends

from api.dependencies.agentos import get_agentos_service
from lib.services.agentos_service import AgentOSService

agentos_router = APIRouter(prefix="/agentos", tags=["agentos"])
legacy_agentos_router = APIRouter(tags=["agentos"])


@agentos_router.get(
    "/config",
    response_model=ConfigResponse,
    response_model_exclude_none=True,
    summary="Retrieve AgentOS configuration",
)
async def get_agentos_config(
    service: AgentOSService = Depends(get_agentos_service),
) -> ConfigResponse:
    """Return AgentOS configuration payload."""

    return service.get_config_response()


# Register legacy alias while reusing the same handler.
legacy_agentos_router.add_api_route(
    "/agentos/config",
    get_agentos_config,
    methods=["GET"],
    response_model=ConfigResponse,
    response_model_exclude_none=True,
    summary="Retrieve AgentOS configuration (legacy alias)",
)

legacy_agentos_router.add_api_route(
    "/config",
    get_agentos_config,
    methods=["GET"],
    response_model=ConfigResponse,
    response_model_exclude_none=True,
    summary="Retrieve AgentOS configuration (legacy control pane alias)",
)
