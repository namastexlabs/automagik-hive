"""
FastAPI server for PagBank Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

import os
import sys
import threading
import logging
from pathlib import Path
from dotenv import load_dotenv
from agno.app.fastapi.app import FastAPIApp
from agno.playground import Playground
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Load environment variables first
load_dotenv()

# Configure logging levels based on environment
def setup_demo_logging():
    """Setup logging for demo presentation"""
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    agno_log_level = os.getenv("AGNO_LOG_LEVEL", "warning").upper()
    
    # Set Agno framework logging level
    agno_level = getattr(logging, agno_log_level, logging.WARNING)
    logging.getLogger("agno").setLevel(agno_level)
    
    # Suppress INFO level from all loggers for clean demo
    if demo_mode and not debug_mode:
        logging.getLogger().setLevel(logging.ERROR)
        # Specifically suppress ALL noisy loggers
        logging.getLogger("uvicorn").setLevel(logging.ERROR)
        logging.getLogger("fastapi").setLevel(logging.ERROR)
        logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
        logging.getLogger("alembic").setLevel(logging.ERROR)
        
        # Force all known loggers to ERROR level
        for logger_name in ["agno", "openai", "httpx", "httpcore", "urllib3"]:
            logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    print(f"🎯 Demo mode: {'ON' if demo_mode else 'OFF'} | Debug: {'ON' if debug_mode else 'OFF'} | Agno: {agno_log_level}")

# Setup logging immediately
setup_demo_logging()

# Add current directory to Python path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import V2 Ana team (replaces orchestrator)
from teams.ana.team import get_ana_team

# Import workflows
from workflows.conversation_typification import get_conversation_typification_workflow
from workflows.human_handoff import get_human_handoff_workflow

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


def create_pagbank_api():
    """Create unified FastAPI app with environment-based features"""
    
    # Get environment settings
    environment = os.getenv("ENVIRONMENT", "production")
    is_development = environment == "development"
    
    print(f"🌍 Environment: {environment}")
    print(f"🔧 Development features: {'ENABLED' if is_development else 'DISABLED'}")
    
    # Initialize database automatically
    try:
        from db.session import init_database
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        print("📝 Note: Some features may be limited without database tables")
    
    # Start CSV hot reload manager - REAL-TIME watchdog
    csv_path = Path(__file__).parent.parent / "context/knowledge/knowledge_rag.csv"
    print(f"🔍 CSV hot reload watching: {csv_path}")
    csv_manager = CSVHotReloadManager(csv_path=str(csv_path))
    csv_thread = threading.Thread(target=csv_manager.start_watching, daemon=True)
    csv_thread.start()
    print("📄 CSV hot reload manager: ACTIVE (real-time file watching)")
    
    # Create the Ana routing team (V2 architecture) - simplified for debugging
    try:
        ana_team = get_ana_team(
            debug_mode=bool(os.getenv("DEBUG_MODE", "false").lower() == "true"),
            session_id=None  # Will be set per request
        )
        
        # Get all agents for comprehensive endpoint generation
        from agents.registry import AgentRegistry
        agent_registry = AgentRegistry()
        available_agents = agent_registry.get_all_agents(
            debug_mode=bool(os.getenv("DEBUG_MODE", "false").lower() == "true")
        )
    except Exception as e:
        print(f"⚠️ Agent/Team loading error: {e}")
        # Fallback: create minimal setup
        ana_team = None
        available_agents = {}
    
    # Debug: Print team and agents information
    if ana_team:
        print(f"📋 Team Name: {ana_team.name}")
        print(f"🆔 Team ID: {ana_team.team_id}")
        print("💡 Use this team_id in API calls: /runs?team_id=" + ana_team.team_id)
        print("✅ Using V2 Ana Team architecture with Agno routing")
    else:
        print("⚠️ No team loaded - creating minimal FastAPI app")
    
    print(f"👥 Available Agents: {list(available_agents.keys())}")
    
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
            get_human_handoff_workflow(debug_mode=is_development)
        ]
        print("✅ Workflows loaded: ConversationTypification, HumanHandoff")
    except Exception as e:
        print(f"⚠️ Could not load workflows: {e}")
        workflows_list = []
    
    # Create FastAPIApp for all environments
    print("🚀 Using FastAPIApp mode")
    app_instance = FastAPIApp(
        teams=teams_list,
        agents=agents_list,
        workflows=workflows_list,
        name="PagBank Multi-Agent System",
        app_id="pagbank_multiagent", 
        description="Sistema multi-agente de atendimento ao cliente PagBank com Ana como assistente unificada",
        version="1.0.0",
        monitoring=True
    )
    
    # Get the FastAPI app instance
    app = app_instance.get_app()
    
    # ✅ CONFIGURE APP WITH UNIFIED SETTINGS
    # Apply settings from api/settings.py
    from api.settings import api_settings
    app.title = api_settings.title
    app.version = api_settings.version
    app.description = "Sistema multi-agente de atendimento ao cliente PagBank com Ana como assistente unificada"
    
    # Set lifespan for monitoring
    app.router.lifespan_context = lifespan
    
    # ✅ ADD ENDPOINTS
    # Add async router only (sync router would create duplicate operation IDs)
    async_router = app_instance.get_async_router()
    
    app.include_router(async_router)
    print("✅ FastAPIApp endpoints registered: /runs, /sessions, /agents, /teams (async)")
    
    # ✅ ADD PLAYGROUND ROUTER FOR WORKFLOW CRUD ENDPOINTS
    # This provides the missing /workflows endpoints that FastAPIApp doesn't generate
    try:
        playground = Playground(
            agents=agents_list,
            teams=teams_list,
            workflows=workflows_list,
            name="PagBank Multi-Agent Playground",
            app_id="pagbank_playground"
        )
        playground_router = playground.get_async_router()
        app.include_router(playground_router)
        print("✅ Playground endpoints registered: /playground/workflows, /playground/agents, /playground/teams")
        print("   • Workflow CRUD: GET /playground/workflows, POST /playground/workflows/{id}/runs")
    except Exception as e:
        print(f"⚠️ Could not register playground endpoints: {e}")
    
    # Configure docs based on settings and environment
    if is_development or api_settings.docs_enabled:
        app.docs_url = "/docs"
        app.redoc_url = "/redoc"
        app.openapi_url = "/openapi.json"
        print("✅ API documentation enabled")
    else:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None
    
    # ✅ ADD CUSTOM BUSINESS ENDPOINTS (both environments)
    # This includes health, monitoring, agent versioning, etc.
    try:
        from api.routes.v1_router import v1_router
        app.include_router(v1_router)
        print("✅ Custom business endpoints registered: Health, Monitoring, Agent Versioning")
        print("   • Health checks: /api/v1/health")
        print("   • Monitoring: /api/v1/monitoring/*") 
        print("   • Agent versions: /api/v1/agents/*")
        print("   • WebSocket: /api/v1/monitoring/ws/realtime")
        print("📋 Native Agno framework endpoints (UNTOUCHED for UI):")
        print("   • FastAPIApp - Basic execution: /runs")
        print("   • Sessions: /sessions") 
        print("   • Entity lists: /agents, /teams")
        print("   • Status: /status")
        print("   • Playground - Full CRUD: /playground/workflows, /playground/agents, /playground/teams")
        print("   • Workflow execution: POST /playground/workflows/{id}/runs")
    except Exception as e:
        print(f"⚠️ Could not register custom business endpoints: {e}")
    
    # ✅ ADD CORS MIDDLEWARE (unified from main.py)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list if api_settings.cors_origin_list else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app_instance


# Create the unified app instance
app_instance = create_pagbank_api()
app = app_instance.get_app()


if __name__ == "__main__":
    import uvicorn
    
    # Get all server configuration from environment variables
    host = os.getenv("PB_AGENTS_HOST", "0.0.0.0")
    port = int(os.getenv("PB_AGENTS_PORT", "7777"))
    reload = os.getenv("PB_AGENTS_RELOAD", "true").lower() == "true"
    
    print(f"🌐 Using host: {host}")
    print(f"🔧 Using port: {port}")
    print(f"🔄 Reload: {reload}")
    print("🚀 Starting PagBank API...")
    
    # Use uvicorn directly with import string for reload/workers support
    uvicorn.run(
        "api.serve:app",
        host=host,
        port=port,
        reload=reload
    )