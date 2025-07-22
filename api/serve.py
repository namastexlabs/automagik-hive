"""
FastAPI server for Automagik Hive Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

import os
import sys
# import logging - replaced with unified logging
import asyncio
from pathlib import Path
from agno.playground import Playground
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI


# Add project root to path to import common module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.utils.startup_display import create_startup_display, display_simple_status
from lib.config.server_config import get_server_config
from lib.auth.dependencies import get_auth_service
from lib.exceptions import ComponentLoadingError

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("🌐 python-dotenv not installed, using system environment variables")


# Initialize execution tracing system
# Execution tracing removed - was unused bloat that duplicated metrics system

# Configure unified logging system
from lib.logging import setup_logging, logger

# Setup logging immediately
setup_logging()

# Log startup message at INFO level (replaces old demo mode print)
log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
agno_log_level = os.getenv("AGNO_LOG_LEVEL", "WARNING").upper()
logger.info("🌐 Automagik Hive logging initialized", 
           log_level=log_level, agno_level=agno_log_level)

# CRITICAL: Run database migrations FIRST before any imports that trigger component loading
# This ensures the database schema is ready before agents/teams are registered
try:
    from lib.utils.db_migration import check_and_run_migrations
    
    # Run migrations synchronously at startup
    if asyncio.get_event_loop().is_running():
        # If event loop is running, schedule the migration check
        logger.debug("🔧 Event loop detected, scheduling migration check")
    else:
        # No event loop, safe to run directly
        migrations_run = asyncio.run(check_and_run_migrations())
        if migrations_run:
            logger.info("🔧 Database schema initialized via Alembic migrations")
        else:
            logger.debug("🔧 Database schema already up to date")
except Exception as e:
    logger.warning("🔧 Database migration check failed during startup", error=str(e))
    logger.info("🔧 Continuing startup - system may use fallback initialization")


# Import teams via dynamic registry (removed hardcoded ana import)

# Import workflow registry for dynamic loading
from ai.workflows.registry import list_available_workflows, get_workflow

# Import team registry for dynamic loading
from ai.teams.registry import list_available_teams, get_team
from lib.utils.version_factory import create_team

# Import CSV hot reload manager
from lib.knowledge.csv_hot_reload import CSVHotReloadManager


def create_lifespan(startup_display=None):
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
            logger.info("🌐 MCP system initialized", server_count=len(servers))
        except Exception as e:
            logger.warning("🌐 Could not initialize MCP Connection Manager", error=str(e))
        
        # Send startup notification with rich component information (production only)
        environment = os.getenv("HIVE_ENVIRONMENT", "development").lower()
        if environment == "production":
            async def _send_startup_notification():
                try:
                    await asyncio.sleep(2)  # Give MCP manager time to fully initialize
                    from common.startup_notifications import send_startup_notification
                    # Pass startup_display for rich notification content
                    await send_startup_notification(startup_display)
                    logger.info("🌐 Startup notification sent successfully")
                except Exception as e:
                    logger.warning("🌐 Could not send startup notification", error=str(e))
            
            try:
                asyncio.create_task(_send_startup_notification())
                logger.info("🌐 Startup notification scheduled")
            except Exception as e:
                logger.warning("🌐 Could not schedule startup notification", error=str(e))
        else:
            logger.info("🌐 Startup notifications disabled in development mode")
        
        yield
        
        # Shutdown
        async def _send_shutdown_notification():
            try:
                from common.startup_notifications import send_shutdown_notification
                await send_shutdown_notification()
                logger.info("🌐 Shutdown notification sent successfully")
            except Exception as e:
                logger.warning("🌐 Could not send shutdown notification", error=str(e))
        
        try:
            asyncio.create_task(_send_shutdown_notification())
            logger.info("🌐 Shutdown notification scheduled")
        except Exception as e:
            logger.warning("🌐 Could not schedule shutdown notification", error=str(e))
        
        # MCP system has no resources to cleanup in simplified implementation
        logger.info("🌐 MCP system cleanup completed")
    
    return lifespan
    
    


def _create_simple_sync_api():
    """Simple synchronous API creation for event loop conflict scenarios."""
    from fastapi import FastAPI
    
    # Get environment settings
    environment = os.getenv("HIVE_ENVIRONMENT", "production")
    is_development = environment == "development"
    
    # Initialize startup display
    startup_display = create_startup_display()
    
    # Add some basic components to show the table works
    startup_display.add_team("template-team", "Template Team", 0, version=1, status="✅")
    startup_display.add_agent("test", "Test Agent", version=1, status="⚠️")
    startup_display.add_error("System", "Running in simplified mode due to async conflicts")
    
    # Display the table
    try:
        startup_display.display_summary()
        logger.info("🌐 Simplified startup display completed")
    except Exception as e:
        logger.error("🌐 Could not display even simplified table", error=str(e))
    
    # Create minimal FastAPI app
    app = FastAPI(
        title="Automagik Hive Multi-Agent System",
        description="Multi-Agent System (Simplified Mode)",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        return {"status": "ok", "mode": "simplified", "message": "System running in simplified mode"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "mode": "simplified"}
    
    return app


async def _async_create_automagik_api():
    """Create unified FastAPI app with environment-based features"""
    
    # Get environment settings
    environment = os.getenv("HIVE_ENVIRONMENT", "production")
    is_development = environment == "development"
    log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
    
    # Check if we're in uvicorn reload process to prevent duplicate output
    import sys
    
    # More precise reloader detection - only block for actual reloader processes
    # Check if this is the reloader master process (not the worker process)
    is_reloader = (
        any("reloader" in str(arg) for arg in sys.argv) and 
        os.getenv("RUN_MAIN") != "true"  # This is the key - worker processes have RUN_MAIN=true
    )
    
    # Debug logging for reloader detection in development mode
    if is_development:
        logger.debug("🌐 Reloader detection", is_reloader=is_reloader)
        if is_reloader:
            logger.debug("🌐 Reloader details", sys_argv=str(sys.argv))
            uvicorn_module = sys.modules.get("uvicorn")
            if uvicorn_module:
                logger.debug("🌐 Uvicorn module info", module=str(uvicorn_module))
    
    # Database migrations now happen at module import time for proper startup order
    
    # Initialize authentication system
    auth_service = get_auth_service()
    
    # Show environment info in development mode
    if is_development and not is_reloader:
        logger.info("🌐 Environment configuration", 
                   environment=environment,
                   auth_enabled=auth_service.is_auth_enabled(),
                   docs_url="http://localhost:9888/docs")
        if auth_service.is_auth_enabled():
            logger.info("🌐 API authentication details",
                       api_key=auth_service.get_current_key(),
                       usage_example=f'curl -H "x-api-key: {auth_service.get_current_key()}" http://localhost:9888/playground/status')
        logger.info("🌐 Development features status", enabled=is_development)
    
    # Database initialization is now handled by Agno storage automatically
    if is_development and not is_reloader:
        logger.info("🌐 Database initialization", method="agno_storage_abstractions", status="auto_initialized")
    
    # Initialize CSV hot reload manager using centralized global knowledge configuration
    # Use the same global config loading function as agents
    try:
        from lib.utils.version_factory import load_global_knowledge_config
        global_config = load_global_knowledge_config()
        csv_filename = global_config.get("csv_file_path", "knowledge_rag.csv")
        # Convert to absolute path (relative to knowledge directory)
        config_dir = Path(__file__).parent.parent / "lib/knowledge"
        csv_path = config_dir / csv_filename
        logger.info("🌐 Centralized knowledge configuration loaded", csv_path=str(csv_path))
    except Exception as e:
        # This should not happen in production - enforce proper configuration
        csv_path = Path(__file__).parent.parent / "lib/knowledge/knowledge_rag.csv"
        logger.error("🌐 Failed to load centralized knowledge config - using hardcoded fallback", 
                    error=str(e), fallback_path=str(csv_path))
    if is_development and not is_reloader:
        logger.info("🌐 CSV hot reload manager configured", csv_path=str(csv_path))
        
        # Start CSV hot reload manager immediately in demo/development mode
        try:
            from lib.knowledge.csv_hot_reload import CSVHotReloadManager
            csv_manager = CSVHotReloadManager(str(csv_path))
            csv_manager.start_watching()
            logger.info("🌐 CSV hot reload manager activated", status="watching_for_changes")
        except Exception as e:
            logger.warning("🌐 Could not start CSV hot reload manager", error=str(e))
            logger.info("🌐 CSV hot reload manager configured", status="will_start_on_first_use")
    
    # V2 Architecture: Agno framework handles memory internally
    # No need for global memory manager - removed legacy memory system
    if is_development and not is_reloader:
        logger.info("🌐 Memory system configured", method="agno_internal_handling")
    
    # Dynamic team loading function
    async def _load_all_discovered_teams():
        """Load all teams discovered by the registry system."""
        teams_list = []
        available_teams = list_available_teams()
        
        for team_id in available_teams:
            try:
                team = await create_team(team_id)
                if team:
                    teams_list.append(team)
                    logger.info("🌐 Team loaded successfully", team_id=team_id)
            except Exception as e:
                error_msg = str(e)
                if "HIVE_DATABASE_URL" in error_msg:
                    logger.warning("🌐 Team loading skipped - database not configured", 
                                 team_id=team_id, reason="missing_database_url")
                elif "No active version found" in error_msg:
                    logger.warning("🌐 Team loading skipped - no version in database", 
                                 team_id=team_id, reason="missing_version")
                else:
                    logger.error("🌐 Team loading failed", 
                                team_id=team_id, error=str(e), error_type=type(e).__name__)
                # Continue loading other teams even if one fails
                continue
        
        return teams_list
    
    # Get all agents for comprehensive endpoint generation
    from ai.agents.registry import AgentRegistry
    agent_registry = AgentRegistry()
    available_agents = await agent_registry.get_all_agents()
    
    # Load all teams dynamically
    loaded_teams = await _load_all_discovered_teams()
    
    # Validate critical components loaded successfully
    if not loaded_teams:
        logger.warning("🌐 Warning: No teams loaded from registry - server will start with agents only")
        # Continue without teams - Playground can handle empty teams list
    
    if not available_agents:
        logger.error("🌐 Critical: No agents loaded from registry")
        raise ComponentLoadingError("At least one agent is required but none were loaded")
    
    # Initialize startup display
    startup_display = create_startup_display()
    
    # Initialize component version sync and capture results for startup display
    sync_results = None
    try:
        from lib.services.version_sync_service import AgnoVersionSyncService
        
        # Create custom sync service to capture logs
        class StartupVersionSync(AgnoVersionSyncService):
            def __init__(self, startup_display):
                super().__init__()
                self.startup_display = startup_display
            
            async def sync_on_startup(self):
                """Enhanced version sync with detailed status reporting."""
                # Get actual component counts from filesystem
                import glob
                agent_files = glob.glob('ai/agents/*/config.yaml')
                team_files = glob.glob('ai/teams/*/config.yaml')
                workflow_files = glob.glob('ai/workflows/*/config.yaml')
                
                total_components = len(agent_files) + len(team_files) + len(workflow_files)
                
                self.startup_display.add_version_sync_log(f"🔍 Scanning {total_components} components ({len(agent_files)} agents, {len(team_files)} teams, {len(workflow_files)} workflows)")
                
                total_synced = 0
                yaml_to_db_count = 0
                db_to_yaml_count = 0
                no_change_count = 0
                updated_components = []
                
                for component_type in ['agent', 'team', 'workflow']:
                    try:
                        results = await self.sync_component_type(component_type)
                        self.sync_results[component_type + 's'] = results
                        total_synced += len(results)
                        
                        if results:
                            for result in results:
                                if isinstance(result, dict):
                                    component_id = result.get("component_id", "unknown")
                                    action = result.get("action", "")
                                    yaml_version = result.get("yaml_version")
                                    agno_version = result.get("agno_version")
                                    
                                    if action in ["created", "updated"]:
                                        yaml_to_db_count += 1
                                        updated_components.append(f"{component_id} v{yaml_version}")
                                    elif action in ["yaml_updated", "yaml_corrected"]:
                                        db_to_yaml_count += 1
                                        updated_components.append(f"{component_id} v{agno_version}")
                                    else:  # no_change or other stable states
                                        no_change_count += 1
                                        
                    except Exception as e:
                        self.startup_display.add_version_sync_log(f"❌ Error syncing {component_type}s: {e}")
                        self.sync_results[component_type + 's'] = {"error": str(e)}
                
                # Generate enhanced summary
                if yaml_to_db_count == 0 and db_to_yaml_count == 0:
                    self.startup_display.add_version_sync_log(f"✅ All {total_synced} components in sync (no changes needed)")
                    self.startup_display.add_version_sync_log("🎉 All components up-to-date")
                else:
                    if yaml_to_db_count > 0:
                        self.startup_display.add_version_sync_log(f"⬆️ {yaml_to_db_count} components updated: YAML→DB")
                    if db_to_yaml_count > 0:
                        self.startup_display.add_version_sync_log(f"⬇️ {db_to_yaml_count} components updated: DB→YAML")
                    if no_change_count > 0:
                        self.startup_display.add_version_sync_log(f"✅ {no_change_count} components in sync")
                    
                    total_updates = yaml_to_db_count + db_to_yaml_count
                    self.startup_display.add_version_sync_log(f"🎉 Sync completed: {total_updates} updates applied")
                
                return self.sync_results
        
        sync_service = StartupVersionSync(startup_display)
        
        # Run sync in the current async context (we're in _async_create_automagik_api)
        sync_results = await sync_service.sync_on_startup()
        startup_display.set_sync_results(sync_results)
        
    except Exception as e:
        startup_display.add_error("Version Sync", f"Component version sync failed: {e}")
    
    # Collect component information for display (remove redundant debug logs)
    if loaded_teams and available_agents:
        # Add all loaded teams to startup display
        for team in loaded_teams:
            # Extract version from team metadata if available
            team_version = None
            if hasattr(team, 'metadata') and team.metadata:
                team_version = team.metadata.get('version')
            
            # Count agents as team members (rough estimate)
            member_count = len(available_agents) if available_agents else 0
            
            startup_display.add_team(
                team.team_id, 
                team.name, 
                member_count,
                version=team_version,
                status="✅"
            )
        
        # Add individual agents with version information (no redundant logging)
        for agent_id, agent in available_agents.items():
            # Use the actual agent component ID
            actual_component_id = getattr(agent, 'agent_id', agent_id)
            
            # Extract version from agent metadata if available
            version = None
            if hasattr(agent, 'metadata') and agent.metadata:
                version = agent.metadata.get('version')
            
            startup_display.add_agent(actual_component_id, agent.name or agent_id, version=version, status="✅")
    elif not loaded_teams or not available_agents:
        startup_display.add_error("System", "No teams or agents loaded - running with minimal configuration")
    
    # Create FastAPI app with both teams AND agents for full endpoint generation
    teams_list = loaded_teams if loaded_teams else []
    agents_list = list(available_agents.values()) if available_agents else []
    
    # Ensure we have at least something to create app
    if not teams_list and not agents_list:
        # Create a minimal dummy agent for testing
        from agno.agent import Agent
        from lib.config.models import resolve_model
        dummy_agent = Agent(name="Test Agent", model=resolve_model())
        agents_list = [dummy_agent]
    
    # Create workflow instances dynamically
    workflows_list = []
    available_workflows = list_available_workflows()
    
    for workflow_id in available_workflows:
        try:
            workflow = get_workflow(workflow_id, debug_mode=is_development)
            workflows_list.append(workflow)
            logger.info("🌐 Workflow loaded successfully", workflow_id=workflow_id)
        except Exception as e:
            logger.error("🌐 Workflow loading failed", 
                        workflow_id=workflow_id, error=str(e), error_type=type(e).__name__)
            # Don't fail server startup for workflow loading issues
            continue
        # Add workflows to startup display dynamically with version information
        for workflow_id in available_workflows:
            workflow_name = workflow_id.replace('-', ' ').title()
            
            # Try to get version from the workflow instance if available
            workflow_version = None
            for workflow in workflows_list:
                if hasattr(workflow, 'workflow_id') and workflow.workflow_id == workflow_id:
                    if hasattr(workflow, 'metadata') and workflow.metadata:
                        workflow_version = workflow.metadata.get('version')
                    break
            
            startup_display.add_workflow(workflow_id, workflow_name, version=workflow_version, status="✅")
    
    # Discover and add additional teams to startup display dynamically
    available_teams = list_available_teams()
    
    for team_id in available_teams:
        team_name = team_id.replace('-', ' ').title()
        
        # Try to get version and member count from the team instance if available
        team_version = None
        member_count = 0
        try:
            team = await get_team(team_id, debug_mode=is_development)
            if hasattr(team, 'metadata') and team.metadata:
                team_version = team.metadata.get('version')
            if hasattr(team, 'members') and team.members:
                member_count = len(team.members)
            logger.info("🌐 Team loaded successfully", team_id=team_id)
        except Exception as e:
            import traceback
            logger.error("🌐 Team loading failed", 
                        team_id=team_id, error=str(e), error_type=type(e).__name__,
                        traceback=traceback.format_exc())
            # Don't fail server startup for additional teams
            continue
        
        startup_display.add_team(team_id, team_name, member_count, version=team_version, status="✅")
    
    # Create base FastAPI app for configuration
    
    # Create base FastAPI app that will be configured by Playground
    app = FastAPI(
        title="Automagik Hive Multi-Agent System",
        description="Multi-Agent System with intelligent routing and dynamic team discovery",
        version="1.0.0"
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
    
    # Try to import workflow trigger handler safely
    external_handler = None
    try:
        from ai.agents.tools.finishing_tools import trigger_conversation_typification_workflow
        external_handler = trigger_conversation_typification_workflow
        logger.info("🌐 Workflow handler loaded successfully")
    except ImportError as e:
        logger.warning("🌐 Workflow handler not available", error=str(e))
    
    # Create playground
    playground = Playground(
        agents=agents_list,
        teams=teams_list,
        workflows=workflows_list,
        name="Automagik Hive Multi-Agent System",
        app_id="automagik_hive"
    )
    
    # Get the unified router - this provides all endpoints including workflows
    unified_router = playground.get_async_router()
    
    # Add authentication protection to playground routes if auth is enabled
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
        
    logger.info("🌐 Unified API endpoints registered successfully")
    
    # Configure docs based on settings and environment
    if is_development or api_settings.docs_enabled:
        app.docs_url = "/docs"
        app.redoc_url = "/redoc"
        app.openapi_url = "/openapi.json"
    else:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None
    
    # Always display startup summary with component table (core feature) - moved outside try-catch
    # Force display for debugging (temporarily ignore reloader check)
    logger.info("🌐 About to display startup summary", 
                teams=len(startup_display.teams),
                agents=len(startup_display.agents), 
                workflows=len(startup_display.workflows))
    try:
        startup_display.display_summary()
        logger.info("🌐 Startup display completed successfully")
    except Exception as e:
        import traceback
        logger.error("🌐 Could not display startup summary table", error=str(e), traceback=traceback.format_exc())
        # Try fallback simple display
        try:
            from lib.utils.startup_display import display_simple_status
            team_name = "Multi-Agent System"
            team_count = len(loaded_teams) if loaded_teams else 0
            display_simple_status(team_name, f"{team_count}_teams", len(available_agents) if available_agents else 0)
        except Exception:
            logger.info("🌐 System components loaded successfully", display_status="table_unavailable")
    
    # Add custom business endpoints
    try:
        from api.routes.v1_router import v1_router
        app.include_router(v1_router)
        
        # Add version router
        from api.routes.version_router import version_router
        app.include_router(version_router)
        
        if is_development and not is_reloader:
            # Add development URLs
            port = get_server_config().port
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
            logger.info("🌐 MCP Integration Config for playground testing",
                       config={
                           "automagik-hive": {
                               "command": "uvx",
                               "args": ["automagik-tools", "tool", "automagik-hive"],
                               "env": {
                                   "AUTOMAGIK_HIVE_API_BASE_URL": f"{base_url}",
                                   "AUTOMAGIK_HIVE_TIMEOUT": "300"
                               }
                           }
                       })
    except Exception as e:
        startup_display.add_error("Business Endpoints", f"Could not register custom business endpoints: {e}")
    
    # Add Agno message validation middleware (optional, removed in v2 cleanup)
    # Note: Agno validation middleware was removed in v2 architecture cleanup
    # Validation is now handled by Agno's built-in request validation
    
    # Version support handled via router endpoints
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list,  # No ["*"] fallback
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    return app


# Lazy app creation - only create when imported by uvicorn, not when running as script
app = None

def create_automagik_api():
    """Create unified FastAPI app with environment-based features"""
    
    try:
        # Try to get the running event loop
        loop = asyncio.get_running_loop()
        # We're in an event loop, need to handle this properly
        logger.info("🌐 Event loop detected, using thread-based async initialization")
        
        import threading
        import concurrent.futures
        
        def run_async_in_thread():
            # Create a new event loop in a separate thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result = new_loop.run_until_complete(_async_create_automagik_api())
                return result
            finally:
                # Simplified cleanup - just close the loop
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        logger.info("🌐 No event loop detected, using direct async initialization")
        return asyncio.run(_async_create_automagik_api())


# Only create app when imported
if __name__ != "__main__":
    app = create_automagik_api()


if __name__ == "__main__":
    import uvicorn
    
    
    # Get server configuration from unified config
    config = get_server_config()
    host = config.host
    port = config.port
    environment = os.getenv("HIVE_ENVIRONMENT", "production")
    
    # Auto-reload configuration: can be controlled via environment variable
    # Set DISABLE_RELOAD=true to disable auto-reload even in development
    reload = (
        environment == "development" and 
        os.getenv("DISABLE_RELOAD", "false").lower() != "true"
    )
    
    # Show startup info in development mode
    is_development = environment == "development"
    if is_development:
        logger.info("🌐 Starting Automagik Hive API", 
                   host=host, port=port, reload=reload, mode="development" if reload else "production")
    
    # Use uvicorn directly with import string for reload/workers support
    uvicorn.run(
        "api.serve:app",
        host=host,
        port=port,
        reload=reload
    )