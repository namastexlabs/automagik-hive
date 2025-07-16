"""
FastAPI server for PagBank Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

import os
import sys
import logging
from pathlib import Path
from agno.playground import Playground
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Add project root to path to import common module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from common.startup_display import create_startup_display, display_simple_status

# Load environment variables first (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# Add current directory to Python path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Apply global demo patches immediately after loading environment variables
# This must be done before any other imports that might use agno.Team
from teams.ana.demo_logging import apply_team_demo_patches
apply_team_demo_patches()

# Configure logging levels based on environment
def setup_demo_logging():
    """Setup logging for demo presentation"""
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    agno_log_level = os.getenv("AGNO_LOG_LEVEL", "warning").upper()
    
    # Set Agno framework logging level
    agno_level = getattr(logging, agno_log_level, logging.WARNING)
    logging.getLogger("agno").setLevel(agno_level)
    
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
    
    print(f"🎯 Demo mode: {'ON' if demo_mode else 'OFF'} | Debug: {'ON' if debug_mode else 'OFF'} | Agno: {agno_log_level}")

# Setup logging immediately
setup_demo_logging()

# Add current directory to Python path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import V2 Ana team (replaces orchestrator)
from teams.ana.team import get_ana_team

# Import workflows
from workflows.conversation_typification import get_conversation_typification_workflow
from workflows.human_handoff.workflow import get_human_handoff_workflow

# Import CSV hot reload manager
from context.knowledge.csv_hot_reload import CSVHotReloadManager


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
    
    # No cleanup needed anymore


def create_pagbank_api():
    """Create unified FastAPI app with environment-based features"""
    
    # Get environment settings
    environment = os.getenv("ENVIRONMENT", "production")
    is_development = environment == "development"
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # Check if we're in uvicorn reload process to prevent duplicate output
    import sys
    is_reloader = any("reloader" in str(arg) for arg in sys.argv) or "StatReload" in str(sys.modules.get("uvicorn", ""))
    
    # Show environment info in demo/development mode (but not in reloader)
    if (demo_mode or is_development) and not is_reloader:
        print(f"🌍 Environment: {environment}")
        print(f"🔧 Development features: {'ENABLED' if is_development else 'DISABLED'}")
    
    # Initialize database automatically
    try:
        from db.session import init_database
        init_database()
        if (demo_mode or is_development) and not is_reloader:
            print("✅ Database initialized successfully")
    except Exception as e:
        if (demo_mode or is_development) and not is_reloader:
            print(f"⚠️ Database initialization warning: {e}")
            print("📝 Note: Some features may be limited without database tables")
    
    # Initialize CSV hot reload manager for lazy loading
    csv_path = Path(__file__).parent.parent / "context/knowledge/knowledge_rag.csv"
    if (demo_mode or is_development) and not is_reloader:
        print(f"🔍 CSV hot reload manager configured: {csv_path}")
        
        # Start CSV hot reload manager immediately in demo/development mode
        try:
            from context.knowledge.csv_hot_reload import CSVHotReloadManager
            csv_manager = CSVHotReloadManager(str(csv_path))
            csv_manager.start_watching()
            print("📄 CSV hot reload manager: ACTIVE (watching for changes)")
        except Exception as e:
            print(f"⚠️ Could not start CSV hot reload manager: {e}")
            print("📄 CSV hot reload manager: CONFIGURED (will start on first use)")
    
    # Initialize global memory manager for consistent memory across all components
    global_memory = None
    try:
        from context.memory.memory_manager import create_memory_manager
        memory_manager = create_memory_manager()
        global_memory = memory_manager.memory
        if (demo_mode or is_development) and not is_reloader:
            print("✅ Global memory manager initialized successfully")
    except Exception as e:
        if (demo_mode or is_development) and not is_reloader:
            print(f"⚠️ Memory manager initialization warning: {e}")
            print("📝 Note: Teams/agents will create fallback memory instances")
    
    # Create the Ana routing team (V2 architecture) - simplified for debugging
    try:
        ana_team = get_ana_team(
            debug_mode=bool(os.getenv("DEBUG_MODE", "false").lower() == "true"),
            session_id=None,  # Will be set per request
            memory=global_memory  # Pass initialized memory to prevent fallback warnings
        )
        
        # Get all agents for comprehensive endpoint generation
        from agents.registry import AgentRegistry
        agent_registry = AgentRegistry()
        available_agents = agent_registry.get_all_agents(
            debug_mode=bool(os.getenv("DEBUG_MODE", "false").lower() == "true"),
            memory=global_memory  # Pass global memory to agents too
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
        from services.version_sync_service import VersionSyncService
        
        # Create custom sync service to capture logs
        class StartupVersionSync(VersionSyncService):
            def __init__(self, startup_display):
                super().__init__()
                self.startup_display = startup_display
            
            def sync_on_startup(self):
                """Override to capture logs for startup display."""
                self.startup_display.add_version_sync_log("🔄 Starting component version sync...")
                
                total_synced = 0
                yaml_to_db_count = 0
                db_to_yaml_count = 0
                
                for component_type in ['agent', 'team', 'workflow']:
                    try:
                        results = self.sync_component_type(component_type)
                        self.sync_results[component_type + 's'] = results
                        total_synced += len(results)
                        
                        if results:
                            # Count different sync directions
                            type_yaml_to_db = 0
                            type_db_to_yaml = 0
                            for result in results:
                                if isinstance(result, dict):
                                    action = result.get("action", "")
                                    if action in ["db_updated", "created"]:
                                        type_yaml_to_db += 1
                                        yaml_to_db_count += 1
                                    elif action in ["yaml_updated", "yaml_corrected"]:
                                        type_db_to_yaml += 1
                                        db_to_yaml_count += 1
                            
                            # Show sync direction summary
                            sync_summary = f"✅ Synced {len(results)} {component_type}(s)"
                            if type_yaml_to_db > 0 or type_db_to_yaml > 0:
                                directions = []
                                if type_yaml_to_db > 0:
                                    directions.append(f"{type_yaml_to_db} YAML→DB")
                                if type_db_to_yaml > 0:
                                    directions.append(f"{type_db_to_yaml} DB→YAML")
                                sync_summary += f" ({', '.join(directions)})"
                            
                            self.startup_display.add_version_sync_log(sync_summary)
                    except Exception as e:
                        self.startup_display.add_version_sync_log(f"❌ Error syncing {component_type}s: {e}")
                        self.sync_results[component_type + 's'] = {"error": str(e)}
                
                # Final summary with direction totals
                summary_parts = [f"🎉 Version sync completed: {total_synced} components processed"]
                if yaml_to_db_count > 0 or db_to_yaml_count > 0:
                    direction_parts = []
                    if yaml_to_db_count > 0:
                        direction_parts.append(f"{yaml_to_db_count} YAML→DB")
                    if db_to_yaml_count > 0:
                        direction_parts.append(f"{db_to_yaml_count} DB→YAML")
                    summary_parts.append(f"({', '.join(direction_parts)})")
                
                self.startup_display.add_version_sync_log(" ".join(summary_parts))
                return self.sync_results
        
        sync_service = StartupVersionSync(startup_display)
        sync_results = sync_service.sync_on_startup()
        startup_display.set_sync_results(sync_results)
        
    except Exception as e:
        startup_display.add_error("Version Sync", f"Component version sync failed: {e}")
    
    # Collect component information
    if ana_team and available_agents:
        startup_display.add_team(
            ana_team.team_id, 
            ana_team.name, 
            len(available_agents), 
            "✅"
        )
        
        # Add individual agents
        for agent_id, agent in available_agents.items():
            # Use the actual agent component ID (with hyphens) instead of registry key (with underscores)
            actual_component_id = getattr(agent, 'agent_id', agent_id)
            startup_display.add_agent(actual_component_id, agent.name or agent_id, status="✅")
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
    
    # Create workflow instances
    try:
        workflows_list = [
            get_conversation_typification_workflow(debug_mode=is_development),
            get_human_handoff_workflow()
        ]
        # Add workflows to startup display
        startup_display.add_workflow("conversation-typification", "Conversation Typification", "✅")
        startup_display.add_workflow("human-handoff", "Human Handoff", "✅")
    except Exception as e:
        startup_display.add_error("Workflows", f"Could not load workflows: {e}")
        workflows_list = []
    
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
    app.router.lifespan_context = lifespan
    
    # ✅ UNIFIED API - Single set of endpoints for both production and playground
    # Use Playground as the primary router since it provides comprehensive CRUD operations
    try:
        # Try to import workflow trigger handler safely
        external_handler = None
        try:
            from agents.tools.workflow_tools import handle_workflow_trigger_external
            external_handler = handle_workflow_trigger_external
        except ImportError as e:
            startup_display.add_error("Workflow Handler", f"Could not load handler: {e}")
        
        # Create playground (external_execution_handler not supported in current Agno version)
        playground = Playground(
            agents=agents_list,
            teams=teams_list,
            workflows=workflows_list,
            name="PagBank Multi-Agent System",
            app_id="pagbank_multiagent"
        )
        
        # Get the unified router - this provides all endpoints including workflows
        unified_router = playground.get_async_router()
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
    
    # ✅ ADD CUSTOM BUSINESS ENDPOINTS (both environments)
    # This includes health, monitoring, agent versioning, etc.
    try:
        from api.routes.v1_router import v1_router
        app.include_router(v1_router)
        
        # ✅ ADD VERSION ROUTER (API Architecture Cleanup - T-005)
        # Provides lightweight version handling endpoints to replace heavy middleware operations
        from api.routes.version_router import version_router
        app.include_router(version_router)
        if (demo_mode or is_development) and not is_reloader:
            # Display startup summary
            startup_display.display_summary()
            
            # Add development URLs
            port = int(os.getenv("PB_AGENTS_PORT", "9888"))
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
            print(f'"genie-agents": {{')
            print(f'  "command": "uvx",')
            print(f'  "args": ["automagik-tools", "tool", "genie-agents"],')
            print(f'  "env": {{')
            print(f'    "GENIE_AGENTS_API_BASE_URL": "http://localhost:{port}",')
            print(f'    "GENIE_AGENTS_TIMEOUT": "300"')
            print(f'  }}')
            print(f'}}')
    except Exception as e:
        startup_display.add_error("Business Endpoints", f"Could not register custom business endpoints: {e}")
    
    # ✅ ADD AGNO MESSAGE VALIDATION MIDDLEWARE
    # Validates messages for Agno Playground endpoints (before version middleware)
    try:
        from api.middleware.agno_validation_middleware import AgnoValidationMiddleware
        app.add_middleware(AgnoValidationMiddleware)
    except Exception as e:
        startup_display.add_error("Middleware", f"Could not add Agno validation middleware: {e}")
    
    # ✅ VERSION SUPPORT VIA ROUTER (T-006: Single Extension Mechanism)
    # Version support is now handled via /api/v1/version/* endpoints in version_router
    # This follows pure Agno patterns using FastAPI routers instead of blocking middleware
    
    # ✅ ADD CORS MIDDLEWARE (unified from main.py)
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

# Only create app if being imported (not run as script)
if __name__ != "__main__":
    app = create_pagbank_api()


if __name__ == "__main__":
    import uvicorn
    
    # No cleanup needed anymore
    
    # Get server configuration from environment variables
    host = os.getenv("PB_AGENTS_HOST", "0.0.0.0")
    port = int(os.getenv("PB_AGENTS_PORT", "7777"))
    environment = os.getenv("ENVIRONMENT", "production")
    
    # Auto-reload based on environment: enabled for development, disabled for production
    reload = environment == "development"
    
    # Show startup info in demo/development mode
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
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