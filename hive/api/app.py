"""Minimal FastAPI app for Hive V2 development."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hive.config import settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = settings()

    app = FastAPI(
        title="Hive V2 API",
        description="AI-powered multi-agent framework",
        version="2.0.0",
        docs_url="/docs" if config.is_development else None,
        redoc_url="/redoc" if config.is_development else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "2.0.0",
            "environment": config.hive_environment,
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "🚀 Hive V2 API",
            "version": "2.0.0",
            "docs": "/docs" if config.is_development else None,
        }

    return app
