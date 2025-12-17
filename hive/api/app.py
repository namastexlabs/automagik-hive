"""Hive V2 API powered by Agno AgentOS.

This is the PROPER way to build an Agno-powered API:
- AgentOS() automatically generates REST endpoints for all agents
- No manual endpoint creation needed
- Built-in session management, memory, and knowledge base handling

Serverless Mode:
- When HIVE_DATABASE_URL is not set, embedded PostgreSQL is auto-started
- Zero configuration required for development/serverless deployments
"""

import logging
import os
import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from agno.os import AgentOS

# Suppress AgentOS route conflict warnings (expected behavior when merging routes)
logging.getLogger("agno.os.app").setLevel(logging.ERROR)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hive import __version__
from hive.config import settings
from hive.discovery import discover_agents, discover_teams, discover_workflows

# Suppress AgentOS route conflict warnings (expected behavior when merging routes)
warnings.filterwarnings("ignore", message=".*Route conflict detected.*")


def _mask_database_url(url: str | None) -> str:
    """Mask credentials in database URL to avoid leaking secrets in logs.

    Transforms: postgresql://user:password@host:5432/db
    Into:       postgresql://***:***@host:5432/db
    """
    if not url:
        return "<empty>"

    try:
        # Handle postgresql:// and postgres:// schemes
        if "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                # Has credentials: user:pass@host/db
                credentials_and_host = rest.split("@", 1)
                if len(credentials_and_host) == 2:
                    host_and_db = credentials_and_host[1]
                    return f"{scheme}://***:***@{host_and_db}"
            # No credentials, safe to show
            return url
        return "<invalid-url-format>"
    except Exception:
        return "<url-parse-error>"


# Global reference to embedded postgres (for cleanup)
_embedded_postgres = None

# AGUI is optional - requires ag_ui package
try:
    from agno.os.interfaces.agui import AGUI

    AGUI_AVAILABLE = True
    AGUI_TYPE: type[AGUI] | None = AGUI
except ImportError:
    AGUI_AVAILABLE = False
    AGUI_TYPE = None


async def _initialize_embedded_postgres() -> None:
    """Initialize embedded PostgreSQL if in serverless mode."""
    global _embedded_postgres

    config = settings()

    if not config.use_embedded_postgres:
        print(f"📡 Using external PostgreSQL: {_mask_database_url(config.hive_database_url)}")
        return

    print("🚀 Serverless mode: Starting embedded PostgreSQL...")

    # Import here to avoid circular imports and allow optional usage
    from hive.database import get_embedded_postgres

    # Initialize embedded postgres
    _embedded_postgres = await get_embedded_postgres(
        port=config.hive_embedded_postgres_port,
        data_dir=config.hive_embedded_postgres_data_dir,
    )

    # Set environment variable so other components can use it
    db_url = _embedded_postgres.get_connection_url()
    os.environ["HIVE_DATABASE_URL"] = db_url

    print(f"✅ Embedded PostgreSQL ready on port {config.hive_embedded_postgres_port}")


async def _shutdown_embedded_postgres() -> None:
    """Shutdown embedded PostgreSQL if running."""
    global _embedded_postgres

    if _embedded_postgres is not None:
        print("🛑 Stopping embedded PostgreSQL...")
        from hive.database import stop_embedded_postgres

        await stop_embedded_postgres()
        _embedded_postgres = None
        print("✅ Embedded PostgreSQL stopped")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles:
    - Embedded PostgreSQL startup (serverless mode)
    - Graceful shutdown of database connections
    """
    # Startup
    await _initialize_embedded_postgres()

    yield

    # Shutdown
    await _shutdown_embedded_postgres()


def create_app() -> FastAPI:
    """Create and configure AgentOS-powered FastAPI application.

    This uses Agno's AgentOS to:
    - Auto-discover agents from hive/examples/agents/
    - Auto-generate REST API endpoints (/agents/{id}/runs, etc.)
    - Provide optional AGUI web interface
    - Handle session state, memory, and knowledge bases

    Returns:
        FastAPI: Configured application with AgentOS routes
    """
    config = settings()

    # Propagate API keys from settings to environment variables
    # This ensures Agno models can access them when instantiated
    if config.openai_api_key:
        os.environ["OPENAI_API_KEY"] = config.openai_api_key
    if config.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = config.anthropic_api_key
    if config.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = config.gemini_api_key
    if config.groq_api_key:
        os.environ["GROQ_API_KEY"] = config.groq_api_key
    if config.cohere_api_key:
        os.environ["COHERE_API_KEY"] = config.cohere_api_key

    # Discover all components from examples (auto-loads all agents, workflows, and teams)
    print("\n🔍 Discovering AI components...")
    agents = discover_agents()
    workflows = discover_workflows()
    teams = discover_teams()

    # Create base FastAPI app for custom routes
    base_app = FastAPI(
        title="Hive V2 API",
        description="AI-powered multi-agent framework powered by Agno AgentOS",
        version=__version__,
        docs_url="/docs" if config.is_development else None,
        redoc_url="/redoc" if config.is_development else None,
        lifespan=lifespan,  # Handle embedded postgres lifecycle
    )

    # CORS middleware
    base_app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Note: AgentOS provides default /health and / endpoints
    # We let AgentOS handle those to avoid route conflicts
    # (The warning about route conflicts is expected and harmless)

    # Initialize AgentOS with agents and base app
    # AgentOS will auto-generate:
    # - POST /agents/{agent_id}/runs
    # - GET /config (system configuration)
    # - AGUI interface (if enabled and available)

    # Setup interfaces (optional AGUI)
    interfaces = []
    if config.hive_enable_agui and agents and AGUI_AVAILABLE:
        interfaces.append(AGUI(agent=agents[0]))
        print("✅ AGUI interface enabled")
    elif config.hive_enable_agui and not AGUI_AVAILABLE:
        print("⚠️  AGUI requested but ag_ui package not installed. Install: uv add ag-ui")

    agent_os = AgentOS(
        description="Automagik Hive - Multi-Agent Framework",
        agents=agents if agents else None,
        workflows=workflows if workflows else None,
        teams=teams if teams else None,
        base_app=base_app,  # Merges custom routes with AgentOS routes
        interfaces=interfaces if interfaces else None,  # type: ignore[arg-type]
    )

    # Get combined app with AgentOS routes + custom routes
    app = agent_os.get_app()

    return app
