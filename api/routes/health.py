from datetime import UTC, datetime

from fastapi import APIRouter

######################################################
## Router for health checks
######################################################

health_check_router = APIRouter(tags=["Health"])


@health_check_router.get("/health")
def get_health() -> dict[str, str]:
    """Check the health of the Automagik Hive Multi-Agent System API"""

    return {
        "status": "success",
        "service": "Automagik Hive Multi-Agent System",
        "router": "health",
        "path": "/health",
        "utc": datetime.now(tz=UTC).isoformat(),
        "message": "System operational",
    }
