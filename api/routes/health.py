from fastapi import APIRouter
from datetime import datetime

######################################################
## Router for health checks
######################################################

health_check_router = APIRouter(tags=["Health"])


@health_check_router.get("/health")
def get_health():
    """Verificar a saúde da API do PagBank Multi-Agent System"""

    return {
        "status": "success",
        "service": "PagBank Multi-Agent System",
        "router": "health",
        "path": "/health",
        "utc": datetime.utcnow().isoformat(),
        "message": "Sistema operacional",
    }