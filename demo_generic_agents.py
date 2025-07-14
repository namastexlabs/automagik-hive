#!/usr/bin/env python3
"""
Demo: Generic Agent Factory Pattern with Ana Router
Shows how to use the new generic get_agent() factory and Ana Team routing.
"""

from agents.registry import get_agent, get_team_agents, AgentRegistry
from teams.ana.team import get_ana_team, get_custom_team


def demo_generic_agent_factory():
    """Demonstrate the generic agent factory pattern"""
    print("🤖 Generic Agent Factory Demo")
    print("=" * 50)
    
    # 1. List available agents
    print("\n1. Available Agents:")
    available = AgentRegistry.list_available_agents()
    for agent_id in available:
        print(f"   - {agent_id}")
    
    # 2. Get individual agents using generic get_agent()
    print("\n2. Loading Individual Agents:")
    try:
        pagbank_agent = get_agent("pagbank", debug_mode=True)
        print(f"   ✅ PagBank Agent: {pagbank_agent.name}")
        
        adq_agent = get_agent("adquirencia", debug_mode=True)
        print(f"   ✅ Adquirência Agent: {adq_agent.name}")
        
        emissao_agent = get_agent("emissao", debug_mode=True)
        print(f"   ✅ Emissão Agent: {emissao_agent.name}")
        
        handoff_agent = get_agent("human_handoff", debug_mode=True)
        print(f"   ✅ Human Handoff Agent: {handoff_agent.name}")
        
    except Exception as e:
        print(f"   ❌ Error loading agents: {e}")
    
    # 3. Get multiple agents for team composition
    print("\n3. Loading Team Agents:")
    try:
        team_agents = get_team_agents(
            agent_names=["pagbank", "adquirencia", "emissao", "human_handoff"],
            debug_mode=True
        )
        print(f"   ✅ Loaded {len(team_agents)} agents for team:")
        for agent in team_agents:
            print(f"      - {agent.name}")
    except Exception as e:
        print(f"   ❌ Error loading team agents: {e}")


def demo_ana_router():
    """Demonstrate Ana Team as Agno router"""
    print("\n\n🎯 Ana Team Router Demo")
    print("=" * 50)
    
    # 1. Standard Ana team with default agents
    print("\n1. Standard Ana Team (PagBank agents):")
    try:
        ana_team = get_ana_team(debug_mode=True)
        print(f"   ✅ Team: {ana_team.name}")
        print(f"   ✅ Mode: {ana_team.mode}")
        print(f"   ✅ Members: {len(ana_team.members)} agents")
        for member in ana_team.members:
            print(f"      - {member.name}")
    except Exception as e:
        print(f"   ❌ Error creating Ana team: {e}")
    
    # 2. Custom Ana team with different agents
    print("\n2. Custom Ana Team (subset of agents):")
    try:
        custom_ana = get_ana_team(
            agent_names=["pagbank", "human_handoff"],
            debug_mode=True
        )
        print(f"   ✅ Team: {custom_ana.name}")
        print(f"   ✅ Members: {len(custom_ana.members)} agents")
        for member in custom_ana.members:
            print(f"      - {member.name}")
    except Exception as e:
        print(f"   ❌ Error creating custom Ana team: {e}")
    
    # 3. Fully custom team
    print("\n3. Fully Custom Team:")
    try:
        custom_team = get_custom_team(
            team_name="Test Team",
            agent_names=["pagbank", "emissao"],
            instructions="Route banking questions to pagbank, card questions to emissao",
            debug_mode=True
        )
        print(f"   ✅ Team: {custom_team.name}")
        print(f"   ✅ Mode: {custom_team.mode}")
        print(f"   ✅ Members: {len(custom_team.members)} agents")
        for member in custom_team.members:
            print(f"      - {member.name}")
    except Exception as e:
        print(f"   ❌ Error creating fully custom team: {e}")


def demo_agno_pattern():
    """Demonstrate the Agno pattern implementation"""
    print("\n\n📋 Agno Pattern Implementation")
    print("=" * 50)
    
    print("\n✅ Key Features Implemented:")
    print("   1. Generic get_agent(name) factory function")
    print("   2. Team(mode='route') with dynamic member loading")
    print("   3. Agent registry with dynamic imports")
    print("   4. Branch-flexible naming (not PagBank-specific)")
    print("   5. Ana as router with configurable members")
    
    print("\n📝 Usage Examples:")
    print("   # Get any agent")
    print("   agent = get_agent('pagbank')")
    print("   ")
    print("   # Create Ana team with default agents")
    print("   ana = get_ana_team()")
    print("   ")
    print("   # Create Ana team with custom agents")
    print("   ana = get_ana_team(agent_names=['pagbank', 'emissao'])")
    print("   ")
    print("   # Create fully custom team")
    print("   team = get_custom_team('Support', ['agent1', 'agent2'], 'instructions')")
    
    print("\n🔧 Agno Team Pattern:")
    print("   Team(")
    print("     name='Ana',")
    print("     mode='route',  # Key insight from Agno docs")
    print("     members=[get_agent(name) for name in agent_names],")
    print("     instructions='Routing logic...'")
    print("   )")


if __name__ == "__main__":
    print("🚀 Generic Agent Factory & Ana Router Demo")
    print("=" * 60)
    
    demo_generic_agent_factory()
    demo_ana_router() 
    demo_agno_pattern()
    
    print("\n\n✅ Demo Complete!")
    print("🎯 Key Achievement: Ana is now a generic Agno Team router")
    print("🔧 Generic factory pattern enables any agent system")
    print("📋 Ready for branch flexibility beyond PagBank")