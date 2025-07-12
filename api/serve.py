"""
FastAPI server for PagBank Multi-Agent System
Production-ready API endpoint for the orchestrator
"""

from agno.app.fastapi.app import FastAPIApp

# Import storage configuration
from config.postgres_config import get_postgres_storage

# Import main orchestrator
from agents.orchestrator.main_orchestrator import create_main_orchestrator


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
    # Serve the app
    fastapi_app.serve(
        app="serve:app",
        host="0.0.0.0",
        port=8880,
        reload=True
    )