from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.routes.health import health_check_router
from api.routes.mcp_router import router as mcp_router
from api.routes.version_router import version_router
from api.settings import api_settings
from lib.auth.dependencies import get_auth_service, require_api_key
from lib.logging import logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager"""
    # Startup - initialize authentication
    auth_service = get_auth_service()
    auth_status = auth_service.get_auth_status()

    logger.info("Authentication initialized", **auth_status)

    # Log security warnings for production
    if auth_status["production_override_active"]:
        logger.warning(
            "Production Security Override: Authentication ENABLED despite HIVE_AUTH_DISABLED=true"
        )

    yield

    # Shutdown - monitoring removed


def create_app() -> FastAPI:
    """Create a FastAPI App

    Returns:
        FastAPI: FastAPI App
    """

    # Create FastAPI App
    app: FastAPI = FastAPI(
        title=api_settings.title,
        version=api_settings.version,
        docs_url="/docs" if api_settings.docs_enabled else None,
        redoc_url="/redoc" if api_settings.docs_enabled else None,
        openapi_url="/openapi.json" if api_settings.docs_enabled else None,
        description="Enterprise Multi-Agent AI Framework",
        lifespan=lifespan,
    )

    # Add health check router (public, no auth required)
    app.include_router(health_check_router)

    # Create protected router for all other endpoints
    protected_router = APIRouter(dependencies=[Depends(require_api_key)])

    # Add v1 router to protected routes (excluding health which is already added above)
    # We need to create a new router without the health endpoint
    protected_v1_router = APIRouter(prefix="/api/v1")
    protected_v1_router.include_router(version_router)
    protected_v1_router.include_router(mcp_router)

    protected_router.include_router(protected_v1_router)
    app.include_router(protected_router)

    # Add Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list
        if api_settings.cors_origin_list
        else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# Create FastAPI app
app = create_app()
