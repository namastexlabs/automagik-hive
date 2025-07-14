from fastapi import APIRouter

from api.routes.playground import playground_router
from api.routes.health import health_check_router
from api.routes.agent_versions import agent_versions_router
from api.routes.monitoring import monitoring_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(playground_router)
v1_router.include_router(health_check_router)
v1_router.include_router(agent_versions_router)
v1_router.include_router(monitoring_router)