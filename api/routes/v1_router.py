from fastapi import APIRouter

from api.routes.health import health_check_router
from api.routes.versions import versions_router
from api.routes.monitoring import monitoring_router
from api.routes.mcp_router import router as mcp_router

v1_router = APIRouter(prefix="/api/v1")

# Core business endpoints only
v1_router.include_router(health_check_router)
v1_router.include_router(versions_router) 
v1_router.include_router(monitoring_router)
v1_router.include_router(mcp_router)