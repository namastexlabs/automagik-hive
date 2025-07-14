from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.settings import api_settings
from api.routes.v1_router import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        # Start monitoring system
        from api.monitoring.startup import start_monitoring
        await start_monitoring()
        print("✅ Monitoring system started")
    except Exception as e:
        print(f"⚠️  Warning: Could not start monitoring system: {e}")
    
    yield
    
    # Shutdown
    try:
        # Stop monitoring system
        from api.monitoring.startup import stop_monitoring
        await stop_monitoring()
        print("✅ Monitoring system stopped")
    except Exception as e:
        print(f"⚠️  Warning: Could not stop monitoring system: {e}")


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
        description="Sistema multi-agente de atendimento ao cliente PagBank",
        lifespan=lifespan
    )

    # Add v1 router
    app.include_router(v1_router)

    # Add Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list if api_settings.cors_origin_list else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# Create FastAPI app
app = create_app()
