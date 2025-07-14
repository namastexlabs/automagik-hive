"""
FastAPI server for PagBank Multi-Agent System
Production-ready API endpoint using V2 Ana Team architecture
"""

import os
from dotenv import load_dotenv
from agno.app.fastapi.app import FastAPIApp

# Import V2 Ana team (replaces orchestrator)
from teams.ana.team import get_ana_team

# Load environment variables
load_dotenv()


def create_pagbank_api():
    """Create FastAPI app using V2 Ana team architecture"""
    
    # Create the Ana routing team (V2 architecture)
    ana_team = get_ana_team(
        debug_mode=bool(os.getenv("DEBUG_MODE", "false").lower() == "true"),
        session_id=None  # Will be set per request
    )
    
    # Debug: Print team information
    print(f"📋 Team Name: {ana_team.name}")
    print(f"🆔 Team ID: {ana_team.team_id}")
    print("💡 Use this team_id in API calls: /runs?team_id=" + ana_team.team_id)
    print("✅ Using V2 Ana Team architecture with Agno routing")
    
    # Create FastAPI app with the Ana team
    fastapi_app = FastAPIApp(
        teams=[ana_team],
        name="PagBank Multi-Agent System",
        app_id="pagbank_multiagent",
        description="Sistema multi-agente de atendimento ao cliente PagBank com Ana como assistente unificada",
        version="1.0.0",
        monitoring=True
    )
    
    return fastapi_app


# Create the app instance
fastapi_app = create_pagbank_api()
app = fastapi_app.get_app()


if __name__ == "__main__":
    # Get host and port from environment variables
    host = os.getenv("PB_AGENTS_HOST")
    port = os.getenv("PB_AGENTS_PORT")
    
    # Build kwargs for serve() - only include if env vars are set
    serve_kwargs = {
        "app": "serve:app",
        "reload": True
    }
    
    if host:
        serve_kwargs["host"] = host
        print(f"🌐 Using custom host: {host}")
    
    if port:
        serve_kwargs["port"] = int(port)
        print(f"🔧 Using custom port: {port}")
    
    # Serve the app with Agno's defaults unless overridden
    print("🚀 Starting PagBank API...")
    fastapi_app.serve(**serve_kwargs)