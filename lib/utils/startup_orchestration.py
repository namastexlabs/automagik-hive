"""
Startup orchestration infrastructure for Performance-Optimized Sequential Startup
Eliminates scattered logging and implements dependency-aware initialization order
"""

import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from agno.team import Team
from agno.workflow import Workflow

from lib.logging import logger


@dataclass
class ComponentRegistries:
    """Container for all component registries with batch discovery results"""

    workflows: dict[str, Callable[..., Workflow]]
    teams: dict[str, Callable[..., Team]]
    agents: dict[str, Any]  # Agent registry type from agents/registry.py
    summary: str

    @property
    def total_components(self) -> int:
        """Total number of components discovered"""
        return len(self.workflows) + len(self.teams) + len(self.agents)


@dataclass
class StartupServices:
    """Container for initialized services"""

    auth_service: Any
    mcp_system: Any | None = None
    csv_manager: Any | None = None
    metrics_service: Any | None = None


@dataclass
class StartupResults:
    """Complete startup orchestration results"""

    registries: ComponentRegistries
    services: StartupServices
    sync_results: dict[str, Any] | None = None
    startup_display: Any | None = None


async def batch_component_discovery() -> ComponentRegistries:
    """
    Single-pass discovery of all component types to eliminate redundant I/O.

    This replaces the scattered import-time discovery with a coordinated
    batch operation that happens at the right time in the startup sequence.

    Returns:
        ComponentRegistries: All discovered components with summary
    """
    logger.debug("Starting batch component discovery")
    start_time = datetime.now()

    # Import registry functions (triggers lazy initialization)
    from ai.agents.registry import AgentRegistry
    from ai.teams.registry import get_team_registry
    from ai.workflows.registry import get_workflow_registry

    # Batch discovery - single filesystem scan per type
    try:
        # Initialize registries in parallel where possible
        workflow_registry = get_workflow_registry()
        team_registry = get_team_registry()

        # Agent registry requires async initialization
        agent_registry_instance = AgentRegistry()
        agents = await agent_registry_instance.get_all_agents()

        discovery_time = (datetime.now() - start_time).total_seconds()

        registries = ComponentRegistries(
            workflows=workflow_registry,
            teams=team_registry,
            agents=agents,
            summary=f"{len(workflow_registry)} workflows, {len(team_registry)} teams, {len(agents)} agents",
        )

        logger.info(
            "🔍 Component discovery completed",
            components=registries.summary,
            discovery_time_seconds=f"{discovery_time:.2f}",
        )

        return registries

    except Exception as e:
        logger.error(
            "Component discovery failed", error=str(e), error_type=type(e).__name__
        )
        # Return minimal registries to allow startup to continue
        return ComponentRegistries(
            workflows={}, teams={}, agents={}, summary="0 components (discovery failed)"
        )


async def initialize_knowledge_base() -> Any | None:
    """
    Initialize CSV hot reload manager for knowledge base watching.

    The shared knowledge base will be initialized lazily when first accessed by agents,
    preventing duplicate loading and race conditions.

    Returns:
        CSV manager instance or None if initialization failed
    """

    csv_manager = None
    try:
        from pathlib import Path

        from lib.knowledge.csv_hot_reload import CSVHotReloadManager
        from lib.utils.version_factory import load_global_knowledge_config

        # Load centralized knowledge configuration
        global_config = load_global_knowledge_config()
        csv_filename = global_config.get("csv_file_path", "knowledge_rag.csv")

        # Convert to absolute path
        config_dir = Path(__file__).parent.parent.parent / "lib/knowledge"
        csv_path = config_dir / csv_filename

        # Initialize CSV hot reload manager (this will handle knowledge base creation internally)
        csv_manager = CSVHotReloadManager(str(csv_path))
        csv_manager.start_watching()

        logger.info(
            "Knowledge base CSV watching initialized",
            csv_path=str(csv_path),
            status="watching_for_changes",
            timing="early_initialization",
            note="shared_kb_will_be_initialized_lazily",
        )
    except Exception as e:
        logger.warning(
            "Knowledge base CSV watching initialization failed", error=str(e)
        )
        logger.info(
            "Knowledge base will use fallback initialization when first accessed"
        )

    return csv_manager


async def initialize_other_services(
    csv_manager: Any | None = None,
) -> StartupServices:
    """
    Initialize remaining core services (auth, MCP, metrics).
    Knowledge base is already initialized earlier in the startup sequence.

    Args:
        csv_manager: Already initialized CSV manager from early initialization

    Returns:
        StartupServices: Container with all initialized services
    """
    logger.info("⚙️ Initializing remaining services (auth, MCP, metrics)")

    # Initialize authentication system
    from lib.auth.dependencies import get_auth_service

    auth_service = get_auth_service()
    logger.debug(
        "Authentication service ready", auth_enabled=auth_service.is_auth_enabled()
    )

    # Initialize MCP system
    mcp_system = None
    try:
        from lib.mcp import MCPCatalog

        catalog = MCPCatalog()
        servers = catalog.list_servers()
        mcp_system = catalog
        logger.debug("MCP system ready", server_count=len(servers))
    except Exception as e:
        # Provide more specific error guidance for common MCP issues
        error_msg = str(e)
        if "MCP configuration file not found" in error_msg:
            logger.warning(
                "MCP system initialization failed - configuration file missing",
                error=error_msg,
                suggestion="Ensure .mcp.json exists in working directory or set HIVE_MCP_CONFIG_PATH"
            )
        elif "Invalid JSON" in error_msg:
            logger.warning(
                "MCP system initialization failed - invalid configuration",
                error=error_msg,
                suggestion="Check .mcp.json file for valid JSON syntax"
            )
        else:
            logger.warning("MCP system initialization failed", error=error_msg)

    # Initialize metrics service
    metrics_service = None
    try:
        from lib.config.settings import settings

        if settings.enable_metrics:
            from lib.metrics import (
                AgnoMetricsBridge,
                initialize_dual_path_metrics,
            )
            from lib.metrics.async_metrics_service import initialize_metrics_service

            # Create config with validated environment variables
            metrics_config = {
                "batch_size": settings.metrics_batch_size,
                "flush_interval": settings.metrics_flush_interval,
                "queue_size": settings.metrics_queue_size,
            }

            # Initialize async metrics service
            async_metrics_service = initialize_metrics_service(metrics_config)
            await async_metrics_service.initialize()

            # Check if LangWatch should be enabled
            langwatch_enabled = getattr(settings, "enable_langwatch", False)
            langwatch_config = getattr(settings, "langwatch_config", {})

            # Launch LangWatch global setup as background task (async, non-blocking)
            if langwatch_enabled and langwatch_config:
                from lib.metrics.langwatch_integration import setup_langwatch_global

                asyncio.create_task(setup_langwatch_global(langwatch_config))
                logger.debug("🚀 LangWatch async setup task launched")

            # Initialize dual-path metrics coordinator with LangWatch integration
            metrics_bridge = AgnoMetricsBridge()
            metrics_coordinator = initialize_dual_path_metrics(
                agno_bridge=metrics_bridge,
                langwatch_enabled=langwatch_enabled,
                langwatch_config=langwatch_config,
                async_metrics_service=async_metrics_service,
            )

            # Initialize the coordinator (this actually initializes LangWatch)
            await metrics_coordinator.initialize()

            # Use coordinator as the metrics service (it wraps async service)
            metrics_service = metrics_coordinator

            logger.debug(
                "Dual-path metrics service ready",
                batch_size=settings.metrics_batch_size,
                flush_interval=settings.metrics_flush_interval,
                queue_size=settings.metrics_queue_size,
                langwatch_enabled=langwatch_enabled,
            )
        else:
            logger.debug("Metrics service disabled via HIVE_ENABLE_METRICS")
    except Exception as e:
        logger.warning("Metrics service initialization failed", error=str(e))

    services = StartupServices(
        auth_service=auth_service,
        mcp_system=mcp_system,
        csv_manager=csv_manager,
        metrics_service=metrics_service,
    )

    logger.info("⚙️ Remaining services initialization completed")
    return services


async def run_version_synchronization(
    registries: ComponentRegistries, db_url: str | None
) -> dict[str, Any] | None:
    """
    Run component version synchronization with enhanced reporting and proper cleanup.
    Now uses actual registries data for more accurate synchronization.

    Args:
        registries: Component registries from batch discovery (now actually used)
        db_url: Database URL for version sync service

    Returns:
        Version sync results or None if skipped
    """
    # Check if dev mode is enabled (single feature flag)
    from lib.versioning.dev_mode import DevMode

    if DevMode.is_enabled():
        logger.info(
            "🔄 Version synchronization skipped - DEV MODE enabled",
            mode=DevMode.get_mode_description(),
            discovered_components=registries.summary,
            note="Using YAML-only configuration",
        )
        return None

    if not db_url:
        logger.warning(
            "Version synchronization skipped - HIVE_DATABASE_URL not configured"
        )
        return None

    # Log actual component counts from registries
    logger.info(
        "🔄 Synchronizing component versions", discovered_components=registries.summary
    )

    sync_service = None
    try:
        from lib.services.version_sync_service import AgnoVersionSyncService

        sync_service = AgnoVersionSyncService(db_url=db_url)

        # Run comprehensive sync using actual registry data
        total_synced = 0
        sync_results = {}

        # Sync each component type with registry-aware logging
        component_mapping = {
            "agent": (registries.agents, "agents"),
            "team": (registries.teams, "teams"),
            "workflow": (registries.workflows, "workflows"),
        }

        for component_type, (registry_dict, plural_name) in component_mapping.items():
            try:
                results = await sync_service.sync_component_type(component_type)
                sync_results[plural_name] = results
                synced_count = len(results) if results else 0
                total_synced += synced_count

                # Log comparison between discovered and synced
                discovered_count = len(registry_dict)
                logger.debug(
                    f"🔧 {component_type.title()} sync: {synced_count} synced vs {discovered_count} discovered"
                )

            except Exception as e:
                logger.error(f"🚨 {component_type} sync failed", error=str(e))
                sync_results[plural_name] = {"error": str(e)}

        # Create more informative summary with registry comparison
        sync_summary = []
        for comp_type, results in sync_results.items():
            if isinstance(results, list):
                sync_summary.append(f"{len(results)} {comp_type}")
            elif isinstance(results, dict) and results.get("error"):
                sync_summary.append(f"0 {comp_type} (error)")

        logger.info(
            "🔄 Version synchronization completed",
            summary=", ".join(sync_summary) if sync_summary else "no components",
            total_synced=total_synced,
            total_discovered=registries.total_components,
        )

        return sync_results

    except Exception as e:
        logger.error("Version synchronization failed", error=str(e))
        return None
    finally:
        # Ensure proper cleanup of database connections
        if sync_service:
            try:
                # Clean up the underlying component service and version service
                if hasattr(sync_service, "component_service"):
                    component_service = sync_service.component_service
                    if hasattr(component_service, "close"):
                        await component_service.close()
                if hasattr(sync_service, "version_service"):
                    version_service = sync_service.version_service
                    if hasattr(version_service, "component_service"):
                        component_service = version_service.component_service
                        if hasattr(component_service, "close"):
                            await component_service.close()
                logger.debug("Database connections cleaned up")
            except Exception as cleanup_error:
                logger.debug("Database cleanup attempted", error=str(cleanup_error))


async def orchestrated_startup(quiet_mode: bool = False) -> StartupResults:
    """
    Performance-Optimized Sequential Startup Implementation

    This function eliminates scattered logging and implements the optimal
    startup sequence with proper dependency ordering and performance optimization.

    Startup Sequence:
    1. Database Migration (user requirement)
    2. Logging System Ready
    3. Knowledge Base CSV Watching Init (lazy shared KB initialization)
    4. Component Discovery (BATCH - single filesystem scan)
    5. Version Synchronization (uses actual discovered components)
    6. Configuration Resolution
    7. Other Service Initialization (auth, MCP, metrics)
    8. API Wiring preparation

    Returns:
        StartupResults: Complete startup state for API wiring
    """
    startup_start = datetime.now()
    if not quiet_mode:
        logger.info("🚀 Starting Performance-Optimized Sequential Startup")
    else:
        logger.debug(
            "🚀 Starting Performance-Optimized Sequential Startup (quiet mode)"
        )

    services = None
    registries = None
    sync_results = None

    try:
        # 1. Database Migration (User requirement - first priority)
        if not quiet_mode:
            logger.info("🗄️ Database migration check")
        try:
            from lib.utils.db_migration import check_and_run_migrations

            migrations_run = await check_and_run_migrations()
            if migrations_run:
                logger.info("Database schema initialized via Alembic migrations")
            else:
                logger.debug("Database schema already up to date")
        except Exception as e:
            logger.error("🚨 Database migration check failed", error=str(e))
            logger.error("⚠️ System will continue with limited functionality")
            logger.error(
                "💡 Some features requiring database access will be unavailable"
            )
            logger.warning(
                "🔄 Fix database connection and restart for full functionality"
            )

        # 2. Logging System Ready (implicit - already configured)
        if not quiet_mode:
            logger.info("📝 Logging system ready")

        # 3. Knowledge Base Init (CSV watching setup - shared KB initialized lazily)
        if not quiet_mode:
            logger.info("Initializing knowledge base CSV watching")
        csv_manager = await initialize_knowledge_base()

        # 4. Component Discovery (Single batch operation - MOVED BEFORE version sync)
        if not quiet_mode:
            logger.info("🔍 Discovering components")
        registries = await batch_component_discovery()

        # 5. Version Synchronization (NOW uses actual discovered registries)
        db_url = os.getenv("HIVE_DATABASE_URL")
        sync_results = await run_version_synchronization(registries, db_url)

        # 6. Configuration Resolution (implicit via registry lazy loading)
        if not quiet_mode:
            logger.info("⚙️ Configuration resolution completed")

        # 7. Other Service Initialization (auth, MCP, metrics)
        services = await initialize_other_services(csv_manager)

        # 8. Startup Summary
        startup_time = (datetime.now() - startup_start).total_seconds()
        if not quiet_mode:
            logger.info(
                "🚀 Sequential startup completed",
                total_components=registries.total_components,
                startup_time_seconds=f"{startup_time:.2f}",
                sequence="optimized",
            )
        else:
            logger.debug(
                "Sequential startup completed (quiet mode)",
                total_components=registries.total_components,
                startup_time_seconds=f"{startup_time:.2f}",
            )

        return StartupResults(
            registries=registries, services=services, sync_results=sync_results
        )

    except Exception as e:
        logger.error(
            "Sequential startup failed", error=str(e), error_type=type(e).__name__
        )
        # Return minimal results to allow server to continue
        return StartupResults(
            registries=registries
            or ComponentRegistries(
                workflows={}, teams={}, agents={}, summary="startup failed"
            ),
            services=services or StartupServices(auth_service=None),
            sync_results=sync_results,
        )


def get_startup_display_with_results(startup_results: StartupResults) -> Any:
    """
    Create and populate startup display with orchestrated results.

    Args:
        startup_results: Results from orchestrated_startup()

    Returns:
        Configured startup display ready for presentation
    """
    from lib.utils.startup_display import create_startup_display

    startup_display = create_startup_display()

    # Add teams from registries
    for team_id in startup_results.registries.teams:
        team_name = team_id.replace("-", " ").title()
        startup_display.add_team(team_id, team_name, 0, version=1, status="✅")

    # Add agents from registries
    for agent_id, agent in startup_results.registries.agents.items():
        agent_name = getattr(agent, "name", agent_id)
        version = getattr(agent, "version", None)
        if hasattr(agent, "metadata") and agent.metadata:
            version = agent.metadata.get("version", version)
        startup_display.add_agent(agent_id, agent_name, version=version, status="✅")

    # Add workflows from registries
    for workflow_id in startup_results.registries.workflows:
        workflow_name = workflow_id.replace("-", " ").title()
        startup_display.add_workflow(workflow_id, workflow_name, version=1, status="✅")

    # Store sync results
    startup_display.set_sync_results(startup_results.sync_results)

    return startup_display
