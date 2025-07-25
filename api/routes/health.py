from fastapi import APIRouter
from datetime import datetime

######################################################
## Router for health checks
######################################################

health_check_router = APIRouter(tags=["Health"])


@health_check_router.get("/health")
def get_health():
    """Check the health of the Automagik Hive Multi-Agent System API"""

    return {
        "status": "success",
        "service": "Automagik Hive Multi-Agent System",
        "router": "health",
        "path": "/health",
        "utc": datetime.utcnow().isoformat(),
        "message": "System operational",
    }