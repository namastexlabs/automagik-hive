from os import getenv
from agno.playground import Playground

# Import V2 Ana team
from teams.ana.team import get_ana_team
from agents.registry import AgentRegistry

######################################################
## Router for the agent playground - V2 Architecture
######################################################

# Create the Ana team (V2 architecture)
ana_team = get_ana_team(
    debug_mode=bool(getenv("DEBUG_MODE", "false").lower() == "true")
)

# Get all agents for playground
agent_registry = AgentRegistry()
available_agents = agent_registry.get_all_agents(
    debug_mode=bool(getenv("DEBUG_MODE", "false").lower() == "true")
)

# Create a playground instance with V2 architecture
playground = Playground(
    teams=[ana_team],
    agents=list(available_agents.values()),
    app_id="pagbank-multi-agent-system-v2",
    name="PagBank Multi-Agent System V2"
)

# Log the playground endpoint in development
if getenv("RUNTIME_ENV") == "dev":
    try:
        playground.register_app_on_platform()
    except Exception as e:
        print(f"⚠️ Could not register on platform: {e}")

playground_router = playground.get_router()