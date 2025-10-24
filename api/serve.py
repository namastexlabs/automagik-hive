"""
FastAPI server for Automagik Hive Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

# import logging - replaced with unified logging
import asyncio
import os
import signal
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Agno v2 uses AgentOS instead of deprecated Playground
try:
    from agno.os.app import AgentOS
    from agno.os.settings import AgnoAPISettings
except ImportError:  # pragma: no cover - optional dependency
    AgentOS = None  # type: ignore[assignment, misc]
    AgnoAPISettings = None  # type: ignore[assignment, misc]
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# Load environment variables FIRST before any other imports
# This ensures AGNO_LOG_LEVEL is available when logging system initializes
try:
    from dotenv import load_dotenv
    from pathlib import Path as DotenvPath

    # EXPLICIT: Load from workspace .env (current working directory)
    # This ensures external workspaces (uvx usage) load their local .env
    # and prevents race conditions from multiple load_dotenv() calls
    workspace_env = DotenvPath.cwd() / ".env"
    if workspace_env.exists():
        load_dotenv(dotenv_path=workspace_env, override=False)
    else:
        # Fallback: Search upward from CWD
        load_dotenv(override=False)
except ImportError:
    pass  # Silently continue - dotenv is optional for development

# Add project root to path to import common module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.config.server_config import (  # noqa: E402 - Path setup required before import
    get_server_config,  # noqa: E402 - Logging must be initialized before importing application modules
)
from lib.config.settings import (  # noqa: E402 - Path setup required before import
    settings,  # noqa: E402 - Logging must be initialized before importing application modules
)
from lib.exceptions import (  # noqa: E402 - Path setup required before import
    ComponentLoadingError,  # noqa: E402 - Logging must be initialized before importing application modules
)

# Configure unified logging system AFTER environment variables are loaded
from lib.logging import initialize_logging, logger  # noqa: E402 - Startup orchestration after logging setup
from lib.utils.startup_display import create_startup_display  # noqa: E402 - Startup orchestration after logging setup
from lib.utils.version_reader import get_api_version  # noqa: E402 - Startup orchestration after logging setup

# Initialize execution tracing system
# Execution tracing removed - was unused bloat that duplicated metrics system

# Setup logging immediately via unified bootstrap helper
initialized_now = initialize_logging(surface="api.serve")

# Log startup message at INFO level (replaces old demo mode print)
if initialized_now:
    log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
    agno_log_level = os.getenv("AGNO_LOG_LEVEL", "WARNING").upper()
    logger.info(
        "Automagik Hive logging initialized",
        log_level=log_level,
        agno_level=agno_log_level,
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
from ai.workflows.registry import get_workflow  # noqa: E402 - Conditional import based on runtime configuration

# Import CSV hot reload manager
# Import orchestrated startup infrastructure
from lib.utils.startup_orchestration import (  # noqa: E402 - Conditional import based on runtime configuration
    get_startup_display_with_results,
    orchestrated_startup,
)

# Import team registry for dynamic loading
from lib.utils.version_factory import create_team  # noqa: E402 - Conditional import based on runtime configuration


def create_lifespan(startup_display: Any = None) -> Any:
    """Create lifespan context manager with startup_display access"""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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
                    suggestion="Ensure .mcp.json exists in working directory or set HIVE_MCP_CONFIG_PATH",
                )
            elif "Invalid JSON" in error_msg:
                logger.warning(
                    "Could not initialize MCP Connection Manager - invalid configuration",
                    error=error_msg,
                    suggestion="Check .mcp.json file for valid JSON syntax",
                )
            else:
                logger.warning("Could not initialize MCP Connection Manager", error=error_msg)

        # Send startup notification with rich component information (production only)
        environment = os.getenv("HIVE_ENVIRONMENT", "development").lower()
        if environment == "production":

            async def _send_startup_notification() -> None:
                try:
                    await asyncio.sleep(2)  # Give MCP manager time to fully initialize
                    from common.startup_notifications import send_startup_notification

                    # Pass startup_display for rich notification content
                    await send_startup_notification(startup_display)  # type: ignore[no-untyped-call]
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

        # Graceful Shutdown with Progress Display (following Langflow pattern)
        try:
            # Import our new shutdown progress utility
            from lib.utils.shutdown_progress import create_automagik_shutdown_progress

            # Create shutdown progress with verbose mode based on log level
            log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
            shutdown_progress = create_automagik_shutdown_progress(verbose=(log_level == "DEBUG"))

            # Step 0: Stopping Server
            with shutdown_progress.step(0):
                await asyncio.sleep(0.1)  # Brief pause for visual effect

            # Step 1: Cancelling Background Tasks
            with shutdown_progress.step(1):
                # Cancel all background tasks to prevent resource leaks
                current_tasks = [task for task in asyncio.all_tasks() if not task.done()]
                background_tasks = []

                for task in current_tasks:
                    task_name = getattr(task, "_name", "unnamed")
                    coro_name = getattr(task.get_coro(), "__qualname__", "") if hasattr(task, "get_coro") else ""

                    # Cancel background service tasks (metrics, notifications, etc)
                    if any(
                        keyword in task_name.lower()
                        for keyword in ["notification", "background", "processor", "metrics"]
                    ):
                        background_tasks.append(task)
                    elif any(
                        keyword in coro_name.lower()
                        for keyword in ["_background_processor", "notification", "background"]
                    ):
                        background_tasks.append(task)

                # Cancel the tasks
                for task in background_tasks:
                    task.cancel()

                # Wait for them to complete cancellation
                if background_tasks:
                    await asyncio.gather(*background_tasks, return_exceptions=True)

            # Step 2: Cleaning Up Services
            with shutdown_progress.step(2):
                # Shutdown metrics service if it exists
                try:
                    from lib.metrics.async_metrics_service import shutdown_metrics_service

                    await shutdown_metrics_service()  # type: ignore[no-untyped-call]
                except Exception as e:
                    # Don't warn about metrics shutdown - it may not have been fully initialized
                    logger.debug("Metrics service shutdown note", error=str(e))

                # Send shutdown notification
                try:
                    from common.startup_notifications import send_shutdown_notification

                    await send_shutdown_notification()  # type: ignore[no-untyped-call]
                    logger.debug("Shutdown notification sent successfully")
                except Exception as e:
                    logger.warning("Could not send shutdown notification", error=str(e))

                # MCP system cleanup
                try:
                    # Simple MCP cleanup - no complex resources in our implementation
                    logger.debug("MCP system cleanup completed")
                except Exception as e:
                    logger.warning("MCP cleanup error", error=str(e))

                # PGlite bridge cleanup
                try:
                    from lib.utils.startup_orchestration import cleanup_pglite_backend

                    await cleanup_pglite_backend()
                except Exception as e:
                    logger.debug("PGlite cleanup note", error=str(e))

            # Step 3: Clearing Temporary Files
            with shutdown_progress.step(3):
                # Database connection cleanup would go here if needed
                # Currently handled by connection pooling
                await asyncio.sleep(0.1)  # Brief pause for completion

            # Step 4: Finalizing Shutdown
            with shutdown_progress.step(4):
                logger.debug("Automagik Hive shutdown complete")

            # Print farewell message (only once)
            shutdown_progress.print_farewell_message()

        except asyncio.CancelledError:
            logger.debug("Shutdown cancelled")
        except Exception as e:
            logger.warning(f"Shutdown error: {e}")
            # Don't print farewell message again on error, just log

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
        "template-team",
        "Template Team",
        0,
        version=1,
        status="✅",
        db_label="—",
    )
    startup_display.add_agent(
        "test",
        "Test Agent",
        version=1,
        status="⚠️",
        db_label="—",
        dependencies=[],
    )
    startup_display.add_error("System", "Running in simplified mode due to async conflicts")

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
    async def root() -> dict[str, str]:
        return {
            "status": "ok",
            "mode": "simplified",
            "message": "System running in simplified mode",
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "mode": "simplified"}

    return app


async def _async_create_automagik_api() -> FastAPI:
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

    logger.debug(
        "Reloader environment snapshot",
        run_main=os.getenv("RUN_MAIN"),
        is_reloader_context=is_reloader_context,
        process_id=os.getpid(),
        working_directory=os.getcwd(),
    )

    # PERFORMANCE-OPTIMIZED SEQUENTIAL STARTUP
    # Replace scattered initialization with orchestrated startup sequence
    startup_results = await orchestrated_startup(quiet_mode=is_reloader_context)

    logger.debug(
        "Startup orchestration snapshot",
        result_type=type(startup_results).__name__,
        registries_type=type(startup_results.registries).__name__,
        agents_registry=startup_results.registries.agents,
        agent_keys=list(startup_results.registries.agents.keys()) if startup_results.registries.agents else [],
        has_agents=bool(startup_results.registries.agents),
    )

    # Extract auth service for all environments (used later for AgentOS configuration)
    auth_service = startup_results.services.auth_service

    # Show environment info in development mode
    if is_development:
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
                usage_example=f'curl -H "x-api-key: {auth_service.get_current_key()}" http://localhost:{settings().hive_api_port}/agents',
            )
        logger.debug("Development features status", enabled=is_development)

    # Extract components from orchestrated startup results
    available_agents = startup_results.registries.agents
    workflow_registry = startup_results.registries.workflows
    team_registry = startup_results.registries.teams

    try:
        logger.debug(
            "Agent registry snapshot",
            startup_type=type(startup_results).__name__,
            registries_type=type(startup_results.registries).__name__,
            has_agents_registry=hasattr(startup_results.registries, "agents"),
            available_agents_type=type(available_agents).__name__,
            has_available_agents=bool(available_agents),
            available_agents_count=len(available_agents) if available_agents else 0,
            available_agent_keys=list(available_agents.keys()) if available_agents else [],
            available_agents=available_agents,
        )
    except Exception:
        logger.exception("Agent registry introspection failed during startup")

    # Load team instances from registry
    # Create two versions: one with metrics for internal use, one without for AgentOS serialization
    loaded_teams = []
    teams_for_agentos = []

    for team_id in team_registry:
        try:
            # Team with metrics for internal use
            team = await create_team(team_id, metrics_service=startup_results.services.metrics_service)
            if team:
                loaded_teams.append(team)
                logger.debug("Team instance created", team_id=team_id)

                # Create clean team instance for AgentOS (no metrics_service)
                # This prevents Pydantic serialization errors with DualPathMetricsCoordinator
                team_for_agentos = await create_team(team_id)
                teams_for_agentos.append(team_for_agentos)
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

    # Allow skipping agent validation in test mode
    skip_agent_validation = os.getenv("PYTEST_CURRENT_TEST") is not None

    if not available_agents and not skip_agent_validation:
        logger.error("Critical: No agents loaded from registry")
        logger.error(
            "DEBUG: Agent validation failed",
            available_agents=available_agents,
            type_check=type(available_agents).__name__,
            bool_check=bool(available_agents),
        )
        raise ComponentLoadingError("At least one agent is required but none were loaded")

    # Create startup display with orchestrated results
    startup_display = get_startup_display_with_results(startup_results)

    # Version synchronization already handled by orchestrated startup
    # Results are available in startup_results.sync_results

    # Component information already populated by orchestrated startup
    # startup_display already contains all component details from get_startup_display_with_results()

    # Create FastAPI app components from orchestrated startup results
    # Use clean teams without metrics_service for AgentOS to avoid serialization errors
    teams_list = teams_for_agentos if teams_for_agentos else []

    # ORCHESTRATION FIX: Reuse agents from orchestrated startup to prevent duplicate loading
    # Agents were already loaded with proper metrics configuration during startup orchestration
    agents_list = []
    if startup_results.registries.agents:
        # Use the already-loaded agents from orchestrated startup (now with metrics integration)
        for agent_id, agent_instance in startup_results.registries.agents.items():
            try:
                agents_list.append(agent_instance)
                logger.debug(f"Agent {agent_id} loaded from orchestrated startup with metrics integration")

            except Exception as e:
                logger.warning(f"Failed to use agent {agent_id} from orchestrated startup: {e}")
                continue

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
    app.description = "Multi-Agent System with intelligent routing and dynamic team discovery"

    # Set lifespan for monitoring
    app.router.lifespan_context = create_lifespan(startup_display)

    # ✅ UNIFIED API - Single set of endpoints for both production and playground
    # Use Playground as the primary router since it provides comprehensive CRUD operations

    # Try to get workflow handler via registry (same pattern as agents/teams)
    try:
        from ai.workflows.registry import is_workflow_registered

        if is_workflow_registered("conversation-typification"):
            # Note: This workflow is currently not implemented but system handles gracefully
            logger.debug("🤖 Conversation typification workflow registered but not implemented")
        else:
            logger.debug("🤖 Conversation typification workflow not available - system operating normally")
    except Exception as e:
        logger.debug("🔧 Workflow registry check completed", error=str(e))

    # ============================================================================
    # AGNO V2 AGENTOS INTEGRATION
    # ============================================================================
    # AgentOS replaces the deprecated Playground and provides all agent/team/workflow endpoints
    # Automatically creates: /agents, /teams, /workflows, /knowledge, /sessions, /memories, etc.

    agent_os_enabled = False
    if not settings().hive_embed_playground:
        logger.info("Agno AgentOS embedding disabled by configuration")
    elif AgentOS is None or AgnoAPISettings is None:
        logger.warning("Agno AgentOS not available in current Agno distribution; starting API without AgentOS routes.")
        startup_display.add_version_sync_log("⚠️ Agno AgentOS not installed — running API without agent management UI")
    else:
        try:
            # Configure AgentOS settings
            agentos_settings = AgnoAPISettings(
                env=environment,
                docs_enabled=is_development or api_settings.docs_enabled,
                os_security_key=auth_service.get_current_key() if auth_service.is_auth_enabled() else None,
                cors_origin_list=api_settings.cors_origin_list,
            )

            # Initialize AgentOS with our agents, teams, and workflows
            agent_os = AgentOS(
                os_id="automagik_hive",
                name="Automagik Hive Multi-Agent System",
                description="Production-ready multi-agent system with dynamic agent loading",
                version=get_api_version(),
                agents=agents_list,
                teams=teams_list,
                workflows=workflows_list,
                fastapi_app=app,  # Pass our existing FastAPI app
                settings=agentos_settings,
                telemetry=False,  # Disable AgentOS telemetry - using our own metrics service
                replace_routes=False,  # Don't replace our existing routes
            )

            # CRITICAL: Call get_app() to actually register the routes
            # Even though we passed fastapi_app=app, the routes are only registered in get_app()
            _ = agent_os.get_app()

            agent_os_enabled = True
            logger.info(
                "AgentOS initialized successfully",
                agents=len(agents_list),
                teams=len(teams_list),
                workflows=len(workflows_list),
            )
            startup_display.add_version_sync_log(
                f"✅ Agno AgentOS enabled — {len(agents_list)} agents, {len(teams_list)} teams, {len(workflows_list)} workflows"
            )

        except Exception as exc:
            logger.error(f"Failed to initialize Agno AgentOS: {exc}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            startup_display.add_error(
                "Agno AgentOS",
                f"AgentOS could not start: {exc}",
            )

    # Add AGUI support if enabled
    if settings().hive_enable_agui:
        from agno.agent.agent import Agent
        from agno.app.agui.app import AGUIApp  # type: ignore[import-not-found]

        # Use the same dynamic agent loading as playground
        from ai.agents.registry import AgentRegistry
        from lib.config.models import resolve_model

        # Get agent ID from environment or default to first available
        agui_agent_id = os.getenv("HIVE_AGUI_AGENT", None)
        available_agent_list = AgentRegistry.list_available_agents()
        logger.info(f"AGUI: Found {len(available_agent_list)} available agents: {available_agent_list}")

        selected_agent_id: str | None = None
        if agui_agent_id and agui_agent_id in available_agent_list:
            selected_agent_id = agui_agent_id
            logger.info(f"AGUI: Using specified agent: {agui_agent_id}")
        elif available_agent_list:
            selected_agent_id = available_agent_list[0]
            logger.info(f"AGUI: Using first available agent: {selected_agent_id}")

        if selected_agent_id:
            # Load the selected agent asynchronously
            try:
                selected_agent = await AgentRegistry.get_agent(agent_id=selected_agent_id)
                logger.info(f"AGUI: Successfully loaded agent: {selected_agent_id}")

                # Setup AGUI with dynamically loaded agent
                agui_app = AGUIApp(
                    agent=selected_agent,
                    name=selected_agent.name,
                    app_id=f"{selected_agent.agent_id}_agui",  # type: ignore[attr-defined]
                    description=selected_agent.description or f"AGUI interface for {selected_agent.name}",
                )
            except Exception as e:
                logger.error(f"AGUI: Failed to load agent {selected_agent_id}: {e}")
                raise RuntimeError(f"AGUI: Failed to load any agents for AGUI interface: {e}")
        else:
            logger.error("AGUI: No agents found")
            raise RuntimeError("AGUI: No agents available - check ai/agents/ directory")

        # Mount AGUI app
        agui_fastapi_app = agui_app.get_app()
        app.mount("/agui", agui_fastapi_app)

    # AgentOS handles authentication internally via os_security_key
    # No need to wrap routes - they're already registered in the app by AgentOS.__init__
    if agent_os_enabled:
        logger.debug("AgentOS routes registered successfully with built-in authentication")
    else:
        logger.debug("Skipping AgentOS router registration (not available)")

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
        logger.debug("Skipping startup display (reloader context - avoiding duplicate table)")

    # Add custom business endpoints
    try:
        from api.routes.v1_router import v1_router

        app.include_router(v1_router)

        # Version router already included via v1_router above

        if is_development and not is_reloader_context:
            # Add development URLs
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
        startup_display.add_error("Business Endpoints", f"Could not register custom business endpoints: {e}")

    # Add Agno message validation middleware (optional, removed in v2 cleanup)
    # Note: Agno validation middleware was removed in v2 architecture cleanup
    # Validation is now handled by Agno's built-in request validation

    # Version support handled via router endpoints

    # Add custom agent run error handler middleware
    from lib.middleware import AgentRunErrorHandler

    app.add_middleware(AgentRunErrorHandler)

    # Add CORS middleware
    # Note: allow_credentials=True is incompatible with allow_origins=["*"]
    # Browsers reject this combination as a security measure
    cors_origins = api_settings.cors_origin_list or []
    use_credentials = "*" not in cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=use_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    if not use_credentials:
        logger.debug("CORS credentials disabled due to wildcard origin", origins=cors_origins)

    # Switch from startup to runtime logging mode
    from lib.logging import set_runtime_mode

    set_runtime_mode()  # type: ignore[no-untyped-call]

    return app


# Global app instance for lazy loading
_app_instance: FastAPI | None = None


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


def _setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown on Ctrl+C."""

    def signal_handler(signum: int, frame: Any) -> None:
        # Let the normal shutdown process handle cleanup
        sys.exit(0)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point for Automagik Hive server."""
    import uvicorn

    # Setup signal handlers for proper cleanup
    _setup_signal_handlers()

    # Get server configuration from unified config
    config = get_server_config()
    host = config.host
    port = config.port
    environment = os.getenv("HIVE_ENVIRONMENT", "production")

    # Auto-reload configuration: can be controlled via environment variable
    # Set DISABLE_RELOAD=true to disable auto-reload even in development
    reload = environment == "development" and os.getenv("DISABLE_RELOAD", "false").lower() != "true"

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
