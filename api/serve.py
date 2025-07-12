"""
FastAPI server for PagBank Multi-Agent System
Production-ready API endpoint for the orchestrator
"""

import os
from dotenv import load_dotenv
from agno.app.fastapi.app import FastAPIApp

# Import storage configuration
from config.postgres_config import get_postgres_storage

# Import main orchestrator
from agents.orchestrator.main_orchestrator import create_main_orchestrator

# Load environment variables
load_dotenv()


def create_pagbank_api():
    """Create FastAPI app for PagBank orchestrator"""
    
    # Create the main orchestrator
    orchestrator = create_main_orchestrator()
    
    # Get PostgreSQL storage if available (Agno handles everything)
    postgres_storage = get_postgres_storage(mode="team")
    
    # Configure storage for the orchestrator's routing team
    if postgres_storage:
        orchestrator.routing_team.storage = postgres_storage
        print("✅ Using PostgreSQL storage")
    else:
        print("ℹ️  Using default SQLite storage (set DATABASE_URL for PostgreSQL)")
    
    # Extract the routing team which is the main entry point
    routing_team = orchestrator.routing_team
    
    # Debug: Print team information
    print(f"📋 Team Name: {routing_team.name}")
    print(f"🆔 Team ID: {routing_team.team_id}")
    print("💡 Use this team_id in API calls: /runs?team_id=" + routing_team.team_id)
    
    # Create FastAPI app with the team
    fastapi_app = FastAPIApp(
        teams=[routing_team],
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