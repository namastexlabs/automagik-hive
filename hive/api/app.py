"""Hive V2 API powered by Agno AgentOS.

This is the PROPER way to build an Agno-powered API:
- AgentOS() automatically generates REST endpoints for all agents
- No manual endpoint creation needed
- Built-in session management, memory, and knowledge base handling
"""

import warnings

from agno.os import AgentOS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hive import __version__
from hive.config import settings
from hive.discovery import discover_agents

# Suppress AgentOS route conflict warnings (expected behavior when merging routes)
warnings.filterwarnings("ignore", message=".*Route conflict detected.*")

# AGUI is optional - requires ag_ui package
try:
    from agno.os.interfaces.agui import AGUI

    AGUI_AVAILABLE = True
    AGUI_TYPE: type[AGUI] | None = AGUI
except ImportError:
    AGUI_AVAILABLE = False
    AGUI_TYPE = None


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

    # Discover agents from examples (auto-loads all agents)
    agents = discover_agents()

    # Create base FastAPI app for custom routes
    base_app = FastAPI(
        title="Hive V2 API",
        description="AI-powered multi-agent framework powered by Agno AgentOS",
        version=__version__,
        docs_url="/docs" if config.is_development else None,
        redoc_url="/redoc" if config.is_development else None,
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
        agents=agents,
        base_app=base_app,  # Merges custom routes with AgentOS routes
        interfaces=interfaces if interfaces else None,  # type: ignore[arg-type]
    )

    # Get combined app with AgentOS routes + custom routes
    app = agent_os.get_app()

    return app
