"""
FastAPI server for Automagik Hive Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

# import logging - replaced with unified logging
import asyncio
import os
import sys
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from agno.playground import Playground
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# Load environment variables FIRST before any other imports
# This ensures AGNO_LOG_LEVEL is available when logging system initializes
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # Silently continue - dotenv is optional for development

# Add project root to path to import common module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.config.server_config import get_server_config
from lib.config.settings import settings
from lib.exceptions import ComponentLoadingError

# Configure unified logging system AFTER environment variables are loaded
from lib.logging import logger, setup_logging
from lib.utils.startup_display import create_startup_display
from lib.utils.version_reader import get_api_version

# Initialize execution tracing system
# Execution tracing removed - was unused bloat that duplicated metrics system

# Setup logging immediately
setup_logging()

# Log startup message at INFO level (replaces old demo mode print)
log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
agno_log_level = os.getenv("AGNO_LOG_LEVEL", "WARNING").upper()
logger.info(
    "Automagik Hive logging initialized", log_level=log_level, agno_level=agno_log_level
)

# CRITICAL: Run database migrations FIRST before any imports that trigger component loading
# This ensures the database schema is ready before agents/teams are registered
try:
    from lib.utils.db_migration import check_and_run_migrations

    # Run migrations synchronously at startup
    try:
        # Try to get current event loop (Python 3.10+ recommended approach)
        loop = asyncio.get_running_loop()
        logger.debug("Event loop detected, scheduling migration check")
    except RuntimeError:
        # No event loop running, safe to run directly
        try:
            migrations_run = asyncio.run(check_and_run_migrations())
            if migrations_run:
                logger.info("Database schema initialized via Alembic migrations")
            else:
                logger.debug("Database schema already up to date")
        except Exception as migration_error:
            logger.warning("Database migration error", error=str(migration_error))
except Exception as e:
    logger.warning("Database migration check failed during startup", error=str(e))
    logger.info("Continuing startup - system may use fallback initialization")


# Import teams via dynamic registry (removed hardcoded ana import)

# Import workflow registry for dynamic loading
from ai.workflows.registry import get_workflow

# Import CSV hot reload manager
# Import orchestrated startup infrastructure
from lib.utils.startup_orchestration import (
    get_startup_display_with_results,
    orchestrated_startup,
)

# Import team registry for dynamic loading
from lib.utils.version_factory import create_team


def create_lifespan(startup_display: Any = None) -> Callable:
    """Create lifespan context manager with startup_display access"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager"""
        # Startup - Database migrations are now handled in main startup function
        # This lifespan function handles other FastAPI startup tasks

        # Initialize MCP catalog
        try:
            from lib.mcp import MCPCatalog

            catalog = MCPCatalog()
            servers = catalog.list_servers()
            logger.debug("MCP system initialized", server_count=len(servers))
        except Exception as e:
            # Provide more specific error guidance for common MCP issues
            error_msg = str(e)
            if "MCP configuration file not found" in error_msg:
                logger.warning(
                    "Could not initialize MCP Connection Manager - configuration file missing",
                    error=error_msg,
                    suggestion="Ensure .mcp.json exists in working directory or set HIVE_MCP_CONFIG_PATH"
                )
            elif "Invalid JSON" in error_msg:
                logger.warning(
                    "Could not initialize MCP Connection Manager - invalid configuration",
                    error=error_msg,
                    suggestion="Check .mcp.json file for valid JSON syntax"
                )
            else:
                logger.warning("Could not initialize MCP Connection Manager", error=error_msg)

        # Send startup notification with rich component information (production only)
        environment = os.getenv("HIVE_ENVIRONMENT", "development").lower()
        if environment == "production":

            async def _send_startup_notification():
                try:
                    await asyncio.sleep(2)  # Give MCP manager time to fully initialize
                    from common.startup_notifications import send_startup_notification

                    # Pass startup_display for rich notification content
                    await send_startup_notification(startup_display)
                    logger.debug("Startup notification sent successfully")
                except Exception as e:
                    logger.warning("Could not send startup notification", error=str(e))

            try:
                asyncio.create_task(_send_startup_notification())
                logger.debug("Startup notification scheduled")
            except Exception as e:
                logger.warning("Could not schedule startup notification", error=str(e))
        else:
            logger.debug("Startup notifications disabled in development mode")

        yield

        # Shutdown
        async def _send_shutdown_notification():
            try:
                from common.startup_notifications import send_shutdown_notification

                await send_shutdown_notification()
                logger.debug("Shutdown notification sent successfully")
            except Exception as e:
                logger.warning("Could not send shutdown notification", error=str(e))

        try:
            asyncio.create_task(_send_shutdown_notification())
            logger.debug("Shutdown notification scheduled")
        except Exception as e:
            logger.warning("Could not schedule shutdown notification", error=str(e))

        # MCP system has no resources to cleanup in simplified implementation
        logger.debug("MCP system cleanup completed")

    return lifespan


def _create_simple_sync_api() -> FastAPI:
    """Simple synchronous API creation for event loop conflict scenarios."""
    from fastapi import FastAPI

    # Get environment settings
    os.getenv("HIVE_ENVIRONMENT", "production")

    # Initialize startup display
    startup_display = create_startup_display()

    # Add some basic components to show the table works
    startup_display.add_team(
        "template-team", "Template Team", 0, version=1, status="✅"
    )
    startup_display.add_agent("test", "Test Agent", version=1, status="⚠️")
    startup_display.add_error(
        "System", "Running in simplified mode due to async conflicts"
    )

    # Display the table
    try:
        startup_display.display_summary()
        logger.debug("Simplified startup display completed")
    except Exception as e:
        logger.error("Could not display even simplified table", error=str(e))

    # Create minimal FastAPI app
    app = FastAPI(
        title="Automagik Hive Multi-Agent System",
        description="Multi-Agent System (Simplified Mode)",
        version=get_api_version(),
    )

    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "mode": "simplified",
            "message": "System running in simplified mode",
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy", "mode": "simplified"}

    return app


async def _async_create_automagik_api():
    """Create unified FastAPI app with Performance-Optimized Sequential Startup"""

    # Get environment settings
    environment = os.getenv("HIVE_ENVIRONMENT", "production")
    is_development = environment == "development"
    os.getenv("HIVE_LOG_LEVEL", "INFO").upper()

    # Check if we're in uvicorn reload process to prevent duplicate output

    # Detect if we're in the reloader context to reduce duplicate logs
    # In development with reload, uvicorn creates multiple processes
    is_reloader_context = os.getenv("RUN_MAIN") == "true"

    # Skip verbose logging for reloader context to reduce duplicate output
    if is_reloader_context and is_development:
        logger.debug("Reloader worker process - reducing log verbosity")

    # PERFORMANCE-OPTIMIZED SEQUENTIAL STARTUP
    # Replace scattered initialization with orchestrated startup sequence
    startup_results = await orchestrated_startup(quiet_mode=is_reloader_context)

    # Show environment info in development mode
    if is_development:
        auth_service = startup_results.services.auth_service
        logger.debug(
            "Environment configuration",
            environment=environment,
            auth_enabled=auth_service.is_auth_enabled(),
            docs_url=f"http://localhost:{settings().hive_api_port}/docs",
        )
        if auth_service.is_auth_enabled():
            logger.debug(
                "API authentication details",
                api_key=auth_service.get_current_key(),
                usage_example=f'curl -H "x-api-key: {auth_service.get_current_key()}" http://localhost:{settings().hive_api_port}/playground/status',
            )
        logger.debug("Development features status", enabled=is_development)

    # Extract components from orchestrated startup results
    available_agents = startup_results.registries.agents
    workflow_registry = startup_results.registries.workflows
    team_registry = startup_results.registries.teams

    # Load team instances from registry
    loaded_teams = []
    for team_id in team_registry:
        try:
            team = await create_team(
                team_id, metrics_service=startup_results.services.metrics_service
            )
            if team:
                loaded_teams.append(team)
                logger.debug("Team instance created", team_id=team_id)
        except Exception as e:
            logger.warning(
                "Team instance creation failed",
                team_id=team_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            continue

    # Validate critical components loaded successfully
    if not loaded_teams:
        logger.warning("Warning: No teams loaded - server will start with agents only")

    if not available_agents:
        logger.error("Critical: No agents loaded from registry")
        raise ComponentLoadingError(
            "At least one agent is required but none were loaded"
        )

    # Create startup display with orchestrated results
    startup_display = get_startup_display_with_results(startup_results)

    # Version synchronization already handled by orchestrated startup
    # Results are available in startup_results.sync_results

    # Component information already populated by orchestrated startup
    # startup_display already contains all component details from get_startup_display_with_results()

    # Create FastAPI app components from orchestrated startup results
    teams_list = loaded_teams if loaded_teams else []

    # ORCHESTRATION FIX: Reuse agents from orchestrated startup to prevent duplicate loading
    # Agents were already loaded with proper configuration during batch_component_discovery()
    agents_list = []
    if startup_results.registries.agents:
        # Use the already-loaded agents from orchestrated startup
        for agent_id, agent_instance in startup_results.registries.agents.items():
            try:
                # Add metrics service to existing agent if available
                if (
                    hasattr(agent_instance, "metrics_service")
                    and startup_results.services.metrics_service
                ):
                    agent_instance.metrics_service = (
                        startup_results.services.metrics_service
                    )

                agents_list.append(agent_instance)
                logger.debug(f"Agent {agent_id} reused from orchestrated startup")

            except Exception as e:
                logger.warning(
                    f"Failed to configure agent {agent_id} from orchestrated startup: {e}"
                )
                # Agent instance is still usable, add it anyway
                agents_list.append(agent_instance)
                logger.debug(f"Using agent {agent_id} without metrics enhancement")

    logger.debug(f"Created {len(agents_list)} agents for Playground")

    # Create workflow instances from registry
    workflows_list = []
    for workflow_id in workflow_registry:
        try:
            workflow = get_workflow(workflow_id, debug_mode=is_development)
            workflows_list.append(workflow)
            logger.debug("Workflow instance created", workflow_id=workflow_id)
        except Exception as e:
            logger.warning(
                "Workflow instance creation failed",
                workflow_id=workflow_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            continue

    # Ensure we have at least something to create app
    if not teams_list and not agents_list:
        from agno.agent import Agent

        from lib.config.models import resolve_model

        dummy_agent = Agent(name="Test Agent", model=resolve_model())
        agents_list = [dummy_agent]
        logger.warning("Using dummy agent - no components loaded successfully")

    # Create base FastAPI app for configuration

    # Create base FastAPI app that will be configured by Playground
    app = FastAPI(
        title="Automagik Hive Multi-Agent System",
        description="Multi-Agent System with intelligent routing and dynamic team discovery",
        version=get_api_version(),
    )

    # ✅ CONFIGURE APP WITH UNIFIED SETTINGS
    # Apply settings from api/settings.py
    from api.settings import api_settings

    app.title = api_settings.title
    app.version = api_settings.version
    app.description = (
        "Multi-Agent System with intelligent routing and dynamic team discovery"
    )

    # Set lifespan for monitoring
    app.router.lifespan_context = create_lifespan(startup_display)

    # ✅ UNIFIED API - Single set of endpoints for both production and playground
    # Use Playground as the primary router since it provides comprehensive CRUD operations

    # Try to get workflow handler via registry (same pattern as agents/teams)
    try:
        from ai.workflows.registry import is_workflow_registered

        if is_workflow_registered("conversation-typification"):
            # Note: This workflow is currently not implemented but system handles gracefully
            logger.debug(
                "🤖 Conversation typification workflow registered but not implemented"
            )
        else:
            logger.debug(
                "🤖 Conversation typification workflow not available - system operating normally"
            )
    except Exception as e:
        logger.debug("🔧 Workflow registry check completed", error=str(e))

    # Create playground
    playground = Playground(
        agents=agents_list,
        teams=teams_list,
        workflows=workflows_list,
        name="Automagik Hive Multi-Agent System",
        app_id="automagik_hive",
    )

    # Get the unified router - this provides all endpoints including workflows
    unified_router = playground.get_async_router()

    # Add authentication protection to playground routes if auth is enabled
    auth_service = startup_results.services.auth_service
    if auth_service.is_auth_enabled():
        from fastapi import APIRouter, Depends

        from lib.auth.dependencies import require_api_key

        # Create protected wrapper for playground routes
        protected_router = APIRouter(dependencies=[Depends(require_api_key)])
        protected_router.include_router(unified_router)
        app.include_router(protected_router)
    else:
        # Development mode - no auth protection
        app.include_router(unified_router)

    logger.debug("Unified API endpoints registered successfully")

    # Configure docs based on settings and environment
    if is_development or api_settings.docs_enabled:
        app.docs_url = "/docs"
        app.redoc_url = "/redoc"
        app.openapi_url = "/openapi.json"
    else:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None

    # Display startup summary with component table (skip in quiet mode to avoid duplicates)
    if not is_reloader_context:
        logger.debug(
            "About to display startup summary",
            teams=len(startup_display.teams),
            agents=len(startup_display.agents),
            workflows=len(startup_display.workflows),
        )
        try:
            startup_display.display_summary()
            logger.debug("Startup display completed successfully")
        except Exception as e:
            import traceback

            logger.error(
                "Could not display startup summary table",
                error=str(e),
                traceback=traceback.format_exc(),
            )
            # Try fallback simple display
            try:
                from lib.utils.startup_display import display_simple_status

                team_name = "Multi-Agent System"
                team_count = len(loaded_teams) if loaded_teams else 0
                display_simple_status(
                    team_name,
                    f"{team_count}_teams",
                    len(available_agents) if available_agents else 0,
                )
            except Exception:
                logger.debug(
                    "System components loaded successfully",
                    display_status="table_unavailable",
                )
    else:
        logger.debug(
            "Skipping startup display (reloader context - avoiding duplicate table)"
        )

    # Add custom business endpoints
    try:
        from api.routes.v1_router import v1_router

        app.include_router(v1_router)

        # Version router already included via v1_router above

        if is_development and not is_reloader_context:
            # Add development URLs
            get_server_config().port
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="🌐 Development URLs", show_header=False, box=None)
            table.add_column("", style="cyan", width=20)
            table.add_column("", style="green")

            # Import here to avoid circular imports
            from lib.config.server_config import get_server_config

            base_url = get_server_config().get_base_url()

            table.add_row("📖 API Docs:", f"{base_url}/docs")
            table.add_row("🚀 Main API:", f"{base_url}")
            table.add_row("💗 Health:", f"{base_url}/api/v1/health")

            console.print("\n")
            console.print(table)

            # Add MCP Integration Config
            logger.debug(
                "MCP Integration Config for playground testing",
                config={
                    "automagik-hive": {
                        "command": "uvx",
                        "args": ["automagik-tools", "tool", "automagik-hive"],
                        "env": {
                            "AUTOMAGIK_HIVE_API_BASE_URL": f"{base_url}",
                            "AUTOMAGIK_HIVE_TIMEOUT": "300",
                        },
                    }
                },
            )
    except Exception as e:
        startup_display.add_error(
            "Business Endpoints", f"Could not register custom business endpoints: {e}"
        )

    # Add Agno message validation middleware (optional, removed in v2 cleanup)
    # Note: Agno validation middleware was removed in v2 architecture cleanup
    # Validation is now handled by Agno's built-in request validation

    # Version support handled via router endpoints

    # Add custom agent run error handler middleware
    from lib.middleware import AgentRunErrorHandler

    app.add_middleware(AgentRunErrorHandler)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list,  # No ["*"] fallback
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Switch from startup to runtime logging mode
    from lib.logging import set_runtime_mode

    set_runtime_mode()

    return app


# Lazy app creation to prevent import-time execution
app = None


def create_automagik_api() -> FastAPI:
    """Create unified FastAPI app with environment-based features"""

    try:
        # Try to get the running event loop
        asyncio.get_running_loop()
        # We're in an event loop, need to handle this properly
        logger.debug("Event loop detected, using thread-based async initialization")

        import concurrent.futures

        def run_async_in_thread() -> FastAPI:
            # Create a fresh event loop in a separate thread
            event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(event_loop)
            try:
                return event_loop.run_until_complete(_async_create_automagik_api())
            finally:
                # Simplified cleanup - just close the loop
                event_loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_in_thread)
            return future.result()

    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        logger.debug("No event loop detected, using direct async initialization")
        return asyncio.run(_async_create_automagik_api())


# Global app instance for lazy loading
_app_instance = None


def get_app() -> FastAPI:
    """Get or create the FastAPI application lazily."""
    global _app_instance
    if _app_instance is None:
        _app_instance = create_automagik_api()
    return _app_instance


# For uvicorn - use factory function to avoid import-time app creation
def app() -> FastAPI:
    """Factory function for uvicorn to create app on demand."""
    return get_app()


def main():
    """Main entry point for Automagik Hive server."""
    import uvicorn

    # Get server configuration from unified config
    config = get_server_config()
    host = config.host
    port = config.port
    environment = os.getenv("HIVE_ENVIRONMENT", "production")

    # Auto-reload configuration: can be controlled via environment variable
    # Set DISABLE_RELOAD=true to disable auto-reload even in development
    reload = (
        environment == "development"
        and os.getenv("DISABLE_RELOAD", "false").lower() != "true"
    )

    # Show startup info in development mode
    is_development = environment == "development"
    if is_development:
        logger.debug(
            "Starting Automagik Hive API",
            host=host,
            port=port,
            reload=reload,
            mode="development" if reload else "production",
        )

    # Use uvicorn with factory function to support reload
    uvicorn.run("api.serve:app", host=host, port=port, reload=reload, factory=True)


if __name__ == "__main__":
    main()
