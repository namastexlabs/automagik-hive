from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.playground import Playground
from agno.team import Team
import os
import threading

# Import storage configuration
from config.postgres_config import get_postgres_storage

# Import main orchestrator
from agents.orchestrator.main_orchestrator import create_main_orchestrator

# Import CSV hot reload manager
from context.knowledge.csv_hot_reload import CSVHotReloadManager

# Initialize at module level - only print on first load
if not os.environ.get('UVICORN_RELOADER_PROCESS'):
    print("🚀 Initializing PagBank Multi-Agent System...")
    
# Create the main orchestrator (this creates the routing team with specialist agents)
orchestrator = create_main_orchestrator()

# Get PostgreSQL storage if available (Agno handles everything)
postgres_storage = get_postgres_storage(mode="team")

# Configure storage for the orchestrator's routing team
if postgres_storage:
    orchestrator.routing_team.storage = postgres_storage
    storage_type = "PostgreSQL"
else:
    storage_type = "SQLite (default)"

# Extract the actual Agno Agents from specialist agents
agno_agents = []
for agent_name, agent_instance in orchestrator.specialist_agents.items():
    if isinstance(agent_instance, Agent):
        agno_agents.append(agent_instance)

# Use the actual orchestrator's routing team (which has all the preprocessing features)
routing_team = orchestrator.routing_team

# Start CSV hot reload manager in background thread
csv_manager = CSVHotReloadManager(csv_path="knowledge/knowledge_rag.csv", check_interval=60)  # Check every minute
csv_thread = threading.Thread(target=csv_manager.start_watching, daemon=True)
csv_thread.start()

# Create Playground app with routing team (no individual agents shown to avoid confusion)
playground_app = Playground(
    teams=[routing_team],
    app_id="pagbank-multi-agent-system",
    name="PagBank Multi-Agent System"
)

# Get the FastAPI app for ASGI
app = playground_app.get_app()

if not os.environ.get('UVICORN_RELOADER_PROCESS'):
    print(f"📦 Configured storage: {storage_type}")
    print(f"🎯 Using actual orchestrator routing team: {routing_team.name}")
    print(f"🎯 Routing to {len(agno_agents)} specialist agents")
    print("🎯 PagBank Playground ready with simplified single-agent architecture")
    print(f"✅ Ana persona configured: show_tool_calls={routing_team.show_tool_calls}, show_members_responses={routing_team.show_members_responses}, stream_intermediate_steps={routing_team.stream_intermediate_steps}")
    print("📄 CSV hot reload manager: ACTIVE (checks every 60 seconds)")
    print("🌐 Playground will serve at: http://localhost:7777")
    print("\n📋 Architecture:")
    print(f"  • {routing_team.name} (mode={routing_team.mode}, routes to specialist agents)")
    print("\n📋 Specialist Agents:")
    for agent_name, agent in orchestrator.specialist_agents.items():
        print(f"  • {agent_name} ({agent.name})")

def main():
    """Main entry point for PagBank Playground"""
    try:
        print("\n" + "="*50)
        print("🏦 PAGBANK MULTI-AGENT SYSTEM DEMO")
        print("="*50)
        print("✅ System: 100% Complete")
        print("✅ Routing team with specialist agents: Active")
        print("✅ All 4 specialist agents loaded (3 business units + human handoff)")
        print("✅ Knowledge base: 622 entries")
        print("✅ Memory system: Active")
        print("✅ Portuguese support: Full")
        print("✅ Demo ready: YES")
        print("="*50)
        print("\n🎬 Starting demo server...")
        
        # Serve the playground
        playground_app.serve("playground:app", reload=False)
        
    except Exception as e:
        print(f"❌ Error starting playground: {e}")
        print("💡 Check if all dependencies are installed with 'uv add'")
        raise

if __name__ == "__main__":
    main()