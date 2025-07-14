from os import getenv
from agno.playground import Playground

# Import main orchestrator
from agents.orchestrator.main_orchestrator import create_main_orchestrator

# Import storage configuration
from config.postgres_config import get_postgres_storage

######################################################
## Router for the agent playground
######################################################

# Create the main orchestrator (this creates the routing team with specialist agents)
orchestrator = create_main_orchestrator()

# Get PostgreSQL storage if available (Agno handles everything)
postgres_storage = get_postgres_storage(mode="team")

# Configure storage for the orchestrator's routing team
if postgres_storage:
    orchestrator.routing_team.storage = postgres_storage

# Use the actual orchestrator's routing team (which has all the preprocessing features)
routing_team = orchestrator.routing_team

# Create a playground instance
playground = Playground(
    teams=[routing_team],
    app_id="pagbank-multi-agent-system",
    name="PagBank Multi-Agent System"
)

# Log the playground endpoint in development
if getenv("RUNTIME_ENV") == "dev":
    try:
        playground.register_app_on_platform()
    except Exception as e:
        print(f"⚠️ Could not register on platform: {e}")

playground_router = playground.get_router()