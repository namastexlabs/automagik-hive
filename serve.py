"""
FastAPI server for PagBank Multi-Agent System
Production-ready API endpoint for the orchestrator
"""

from agno.app.fastapi.app import FastAPIApp
from agno.models.anthropic import Claude

from agents.orchestrator.main_orchestrator import create_main_orchestrator


def create_pagbank_api():
    """Create FastAPI app for PagBank orchestrator"""
    
    # Create the main orchestrator
    orchestrator = create_main_orchestrator()
    
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