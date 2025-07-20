"""
FastAPI server for Automagik Hive Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

import os
import sys
import logging
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

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")


# Initialize execution tracing system
# Execution tracing removed - was unused bloat that duplicated metrics system

# Configure logging levels based on environment
def setup_demo_logging():
    """Setup logging for demo presentation"""
    debug_mode = os.getenv("HIVE_DEBUG_MODE", "false").lower() == "true"
    demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
    
    # Configure logging for demo mode
    if demo_mode:
        # Keep INFO level for demo logging but suppress noisy framework loggers
        logging.getLogger().setLevel(logging.INFO)
        
        # Suppress specific noisy loggers only
        logging.getLogger("uvicorn").setLevel(logging.ERROR)
        logging.getLogger("fastapi").setLevel(logging.ERROR)
        logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
        logging.getLogger("alembic").setLevel(logging.ERROR)
        
        # Force all known noisy loggers to ERROR level
        for logger_name in ["openai", "httpx", "httpcore", "urllib3"]:
            logging.getLogger(logger_name).setLevel(logging.ERROR)
        
        # Enable demo logging specifically
        logging.getLogger("teams.ana.demo_logging").setLevel(logging.INFO)
        logging.getLogger("teams.ana.team").setLevel(logging.INFO)
        
        # Set console handler to INFO level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to root logger if not already present
        root_logger = logging.getLogger()
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            root_logger.addHandler(console_handler)
    
    agno_log_level = os.getenv("AGNO_LOG_LEVEL", "warning").upper()
    
    # Set Agno framework logging level - be more aggressive
    agno_level = getattr(logging, agno_log_level, logging.WARNING)
    
    # Set multiple possible Agno logger names
    for logger_name in ["agno", "agno.agent", "agno.team", "agno.utils", "agno.utils.log"]:
        logging.getLogger(logger_name).setLevel(agno_level)
    
    # Also set the root logger if we're not in debug mode and agno level is higher than debug
    if agno_level > logging.DEBUG and not debug_mode:
        logging.getLogger().setLevel(logging.INFO)
    
    print(f"🎯 Demo mode: {'ON' if demo_mode else 'OFF'} | Debug: {'ON' if debug_mode else 'OFF'} | Agno: {agno_log_level}")

# Setup logging immediately
setup_demo_logging()


# Import V2 Ana team
from ai.teams.ana.team import get_ana_team

# Import workflow registry for dynamic loading
from ai.workflows.registry import list_available_workflows, get_workflow

# Import team registry for dynamic loading
from ai.teams.registry import list_available_teams, get_team

# Import CSV hot reload manager
from lib.knowledge.csv_hot_reload import CSVHotReloadManager


def create_lifespan(startup_display=None):
    """Create lifespan context manager with startup_display access"""
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager"""
        # Startup
        try:
            # Initialize MCP catalog
            from lib.mcp import MCPCatalog
            catalog = MCPCatalog()
            servers = catalog.list_servers()
            print(f"✅ MCP system initialized with {len(servers)} servers")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize MCP Connection Manager: {e}")
        
        # Send startup notification with rich component information (production only)
        environment = os.getenv("HIVE_ENVIRONMENT", "development").lower()
        if environment == "production":
            async def _send_startup_notification():
                try:
                    await asyncio.sleep(2)  # Give MCP manager time to fully initialize
                    from common.startup_notifications import send_startup_notification
                    # Pass startup_display for rich notification content
                    await send_startup_notification(startup_display)
                    print("✅ Startup notification sent")
                except Exception as e:
                    print(f"⚠️  Warning: Could not send startup notification: {e}")
            
            try:
                asyncio.create_task(_send_startup_notification())
                print("✅ Startup notification scheduled")
            except Exception as e:
                print(f"⚠️  Warning: Could not schedule startup notification: {e}")
        else:
            print("ℹ️  Startup notifications disabled in development mode")
        
        yield
        
        # Shutdown
        async def _send_shutdown_notification():
            try:
                from common.startup_notifications import send_shutdown_notification
                await send_shutdown_notification()
                print("✅ Shutdown notification sent")
            except Exception as e:
                print(f"⚠️  Warning: Could not send shutdown notification: {e}")
        
        try:
            asyncio.create_task(_send_shutdown_notification())
            print("✅ Shutdown notification scheduled")
        except Exception as e:
            print(f"⚠️  Warning: Could not schedule shutdown notification: {e}")
        
        # MCP system has no resources to cleanup in simplified implementation
        print("✅ MCP system cleanup completed")
    
    return lifespan
    
    


def create_automagik_api():
    """Create unified FastAPI app with environment-based features"""
    
    # Get environment settings
    environment = os.getenv("HIVE_ENVIRONMENT", "production")
    is_development = environment == "development"
    demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
    
    # Check if we're in uvicorn reload process to prevent duplicate output
    import sys
    
    # More precise reloader detection - only block for actual reloader processes
    # Check if this is the reloader master process (not the worker process)
    is_reloader = (
        any("reloader" in str(arg) for arg in sys.argv) and 
        os.getenv("RUN_MAIN") != "true"  # This is the key - worker processes have RUN_MAIN=true
    )
    
    # Debug logging for reloader detection in demo/development mode
    if (demo_mode or is_development):
        print(f"🔍 Reloader detection: is_reloader={is_reloader}")
        if is_reloader:
            print(f"   - sys.argv: {sys.argv}")
            uvicorn_module = sys.modules.get("uvicorn")
            if uvicorn_module:
                print(f"   - uvicorn module: {str(uvicorn_module)}")
    
    # Initialize authentication system
    auth_service = get_auth_service()
    
    # Show environment info in demo/development mode
    if (demo_mode or is_development) and not is_reloader:
        print(f"🌍 Environment: {environment}")
        print(f"🔐 Authentication: {'Enabled' if auth_service.is_auth_enabled() else 'Disabled (Development Mode)'}")
        print(f"📖 Public Docs: http://localhost:9888/docs (no auth required)")
        if auth_service.is_auth_enabled():
            print(f"🔑 API Key: {auth_service.get_current_key()}")
            print(f"📝 Usage: curl -H \"x-api-key: {auth_service.get_current_key()}\" http://localhost:9888/playground/status")
        print(f"🔧 Development features: {'ENABLED' if is_development else 'DISABLED'}")
    
    # Database initialization is now handled by Agno storage automatically
    if (demo_mode or is_development) and not is_reloader:
        print("✅ Database: Using Agno storage abstractions (auto-initialized)")
    
    # Initialize CSV hot reload manager using global knowledge configuration
    # Get CSV path from global knowledge config
    try:
        import yaml
        global_config_path = Path(__file__).parent.parent / "lib/knowledge/config.yaml"
        with open(global_config_path) as f:
            global_config = yaml.safe_load(f)
        csv_path = global_config.get("knowledge", {}).get("csv_file_path", "knowledge_rag.csv")
        # Convert to absolute path (relative to config file location)
        config_dir = Path(__file__).parent.parent / "lib/knowledge"
        csv_path = config_dir / csv_path
        print(f"📋 Using global knowledge configuration: {csv_path}")
    except Exception as e:
        # Fallback to default if config reading fails
        csv_path = Path(__file__).parent.parent / "lib/knowledge/knowledge_rag.csv"
        print(f"⚠️ Could not read global knowledge config, using default: {e}")
    if (demo_mode or is_development) and not is_reloader:
        print(f"🔍 CSV hot reload manager configured: {csv_path}")
        
        # Start CSV hot reload manager immediately in demo/development mode
        try:
            from lib.knowledge.csv_hot_reload import CSVHotReloadManager
            csv_manager = CSVHotReloadManager(str(csv_path))
            csv_manager.start_watching()
            print("📄 CSV hot reload manager: ACTIVE (watching for changes)")
        except Exception as e:
            print(f"⚠️ Could not start CSV hot reload manager: {e}")
            print("📄 CSV hot reload manager: CONFIGURED (will start on first use)")
    
    # V2 Architecture: Agno framework handles memory internally
    # No need for global memory manager - removed legacy memory system
    if (demo_mode or is_development) and not is_reloader:
        print("✅ Memory system: CONFIGURED (agno handles memory internally)")
    
    # Create the Ana routing team
    try:
        ana_team = get_ana_team(
            debug_mode=bool(os.getenv("HIVE_DEBUG_MODE", "false").lower() == "true"),
            session_id=None  # Will be set per request
        )
        
        # Get all agents for comprehensive endpoint generation
        from ai.agents.registry import AgentRegistry
        agent_registry = AgentRegistry()
        available_agents = agent_registry.get_all_agents(
            debug_mode=bool(os.getenv("HIVE_DEBUG_MODE", "false").lower() == "true")
        )
    except Exception as e:
        if (demo_mode or is_development) and not is_reloader:
            print(f"⚠️ Agent/Team loading error: {e}")
        # Fallback: create minimal setup
        ana_team = None
        available_agents = {}
    
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
            
            def sync_on_startup(self):
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
                        results = self.sync_component_type(component_type)
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
        sync_results = sync_service.sync_on_startup()
        startup_display.set_sync_results(sync_results)
        
    except Exception as e:
        startup_display.add_error("Version Sync", f"Component version sync failed: {e}")
    
    # Collect component information for display (remove redundant debug logs)
    if ana_team and available_agents:
        # Extract version from team metadata if available
        team_version = None
        if hasattr(ana_team, 'metadata') and ana_team.metadata:
            team_version = ana_team.metadata.get('version')
        
        startup_display.add_team(
            ana_team.team_id, 
            ana_team.name, 
            len(available_agents),
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
    elif not ana_team or not available_agents:
        startup_display.add_error("System", "No team or agents loaded - running with minimal configuration")
    
    # Create FastAPI app with both teams AND agents for full endpoint generation
    teams_list = [ana_team] if ana_team else []
    agents_list = list(available_agents.values()) if available_agents else []
    
    # Ensure we have at least something to create app
    if not teams_list and not agents_list:
        # Create a minimal dummy agent for testing
        from agno.agent import Agent
        from agno.models.anthropic import Claude
        dummy_agent = Agent(name="Test Agent", model=Claude(id="claude-sonnet-4-20250514"))
        agents_list = [dummy_agent]
    
    # Create workflow instances dynamically
    try:
        workflows_list = []
        available_workflows = list_available_workflows()
        
        for workflow_id in available_workflows:
            try:
                workflow = get_workflow(workflow_id, debug_mode=is_development)
                workflows_list.append(workflow)
            except Exception as e:
                print(f"⚠️ Failed to load workflow {workflow_id}: {e}")
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
    except Exception as e:
        startup_display.add_error("Workflows", f"Could not load workflows: {e}")
        workflows_list = []
    
    # Discover and add additional teams to startup display dynamically
    try:
        available_teams = list_available_teams()
        
        for team_id in available_teams:
            team_name = team_id.replace('-', ' ').title()
            
            # Try to get version and member count from the team instance if available
            team_version = None
            member_count = 0
            try:
                team = get_team(team_id, debug_mode=is_development)
                if hasattr(team, 'metadata') and team.metadata:
                    team_version = team.metadata.get('version')
                if hasattr(team, 'members') and team.members:
                    member_count = len(team.members)
            except Exception as e:
                print(f"⚠️ Failed to load team {team_id} for metadata: {e}")
                continue
            
            startup_display.add_team(team_id, team_name, member_count, version=team_version, status="✅")
    except Exception as e:
        startup_display.add_error("Teams", f"Could not load additional teams: {e}")
    
    # Create base FastAPI app for configuration
    
    # Create base FastAPI app that will be configured by Playground
    app = FastAPI(
        title="PagBank Multi-Agent System",
        description="Sistema multi-agente de atendimento ao cliente PagBank com Ana como assistente unificada",
        version="1.0.0"
    )
    
    # ✅ CONFIGURE APP WITH UNIFIED SETTINGS
    # Apply settings from api/settings.py
    from api.settings import api_settings
    app.title = api_settings.title
    app.version = api_settings.version
    app.description = "Sistema multi-agente de atendimento ao cliente PagBank com Ana como assistente unificada"
    
    # Set lifespan for monitoring
    app.router.lifespan_context = create_lifespan(startup_display)
    
    # ✅ UNIFIED API - Single set of endpoints for both production and playground
    # Use Playground as the primary router since it provides comprehensive CRUD operations
    try:
        # Try to import workflow trigger handler safely
        external_handler = None
        try:
            from ai.agents.tools.finishing_tools import trigger_conversation_typification_workflow
            external_handler = trigger_conversation_typification_workflow
        except ImportError as e:
            startup_display.add_error("Workflow Handler", f"Could not load handler: {e}")
        
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
            
    except Exception as e:
        startup_display.add_error("API Endpoints", f"Could not register unified API endpoints: {e}")
        # Fallback: create minimal endpoints if Playground fails
        
        @app.get("/status")
        async def status():
            return {"status": "ok", "message": "PagBank Multi-Agent System"}
        
        @app.post("/runs")
        async def minimal_runs():
            return {"error": "Playground initialization failed - limited functionality"}
    
    # Configure docs based on settings and environment
    if is_development or api_settings.docs_enabled:
        app.docs_url = "/docs"
        app.redoc_url = "/redoc"
        app.openapi_url = "/openapi.json"
        if (demo_mode or is_development) and not is_reloader:
            pass  # Removed verbose API documentation logging
    else:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None
    
    # Always display startup summary with component table (core feature) - moved outside try-catch
    if not is_reloader:
        try:
            startup_display.display_summary()
        except Exception as e:
            print(f"⚠️ Warning: Could not display startup summary table: {e}")
            # Try fallback simple display
            try:
                from lib.utils.startup_display import display_simple_status
                display_simple_status("Ana Team", "ana", len(available_agents) if available_agents else 0)
            except Exception:
                print("📊 System components loaded successfully (table display unavailable)")
    
    # Add custom business endpoints
    try:
        from api.routes.v1_router import v1_router
        app.include_router(v1_router)
        
        # Add version router
        from api.routes.version_router import version_router
        app.include_router(version_router)
        
        if (demo_mode or is_development) and not is_reloader:
            # Add development URLs
            port = get_server_config().port
            from rich.console import Console
            from rich.table import Table
            
            console = Console()
            table = Table(title="🌐 Development URLs", show_header=False, box=None)
            table.add_column("", style="cyan", width=20)
            table.add_column("", style="green")
            
            table.add_row("📖 API Docs:", f"http://localhost:{port}/docs")
            table.add_row("🚀 Main API:", f"http://localhost:{port}")
            table.add_row("💗 Health:", f"http://localhost:{port}/api/v1/health")
            
            console.print("\n")
            console.print(table)
            
            # Add MCP Integration Config
            print(f"\n🔧 MCP Integration Config (for playground testing of agents, teams, and workflows):")
            print(f'"automagik-hive": {{')
            print(f'  "command": "uvx",')
            print(f'  "args": ["automagik-tools", "tool", "automagik-hive"],')
            print(f'  "env": {{')
            print(f'    "AUTOMAGIK_HIVE_API_BASE_URL": "http://localhost:{port}",')
            print(f'    "AUTOMAGIK_HIVE_TIMEOUT": "300"')
            print(f'  }}')
            print(f'}}')
    except Exception as e:
        startup_display.add_error("Business Endpoints", f"Could not register custom business endpoints: {e}")
    
    # Add Agno message validation middleware (optional, removed in v2 cleanup)
    # Note: Agno validation middleware was removed in v2 architecture cleanup
    # Validation is now handled by Agno's built-in request validation
    
    # Version support handled via router endpoints
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list if api_settings.cors_origin_list else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


# Lazy app creation - only create when imported by uvicorn, not when running as script
app = None

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
    
    # Show startup info in demo/development mode
    demo_mode = os.getenv("HIVE_DEMO_MODE", "false").lower() == "true"
    is_development = environment == "development"
    if demo_mode or is_development:
        print(f"🌐 Using host: {host}")
        print(f"🔧 Using port: {port}")
        print(f"🔄 Auto-reload: {reload} ({'development' if reload else 'production'} mode)")
        print("🚀 Starting PagBank API...")
    
    # Use uvicorn directly with import string for reload/workers support
    uvicorn.run(
        "api.serve:app",
        host=host,
        port=port,
        reload=reload
    )