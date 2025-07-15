#!/usr/bin/env python3
"""
Debug script to test team knowledge integration issue.
Compares agent behavior when instantiated directly vs through team registry.
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from agents.pagbank.agent import get_pagbank_agent
from agents.registry import get_agent
from teams.ana.team import get_ana_team
from dotenv import load_dotenv

load_dotenv()

async def test_direct_agent():
    """Test pagbank agent instantiated directly"""
    print("=== Testing Direct Agent Instantiation ===")
    
    try:
        agent = get_pagbank_agent(
            session_id="test_direct",
            debug_mode=True,
            db_url=os.getenv("DATABASE_URL")
        )
        
        print(f"Agent ID: {agent.agent_id}")
        print(f"Agent Name: {agent.name}")
        print(f"Agent Tools: {[tool.name for tool in agent.tools] if agent.tools else 'No tools'}")
        
        # Check agent attributes
        print(f"Search Knowledge: {getattr(agent, 'search_knowledge', 'Not set')}")
        print(f"Enable Agentic Knowledge Filters: {getattr(agent, 'enable_agentic_knowledge_filters', 'Not set')}")
        print(f"Knowledge Filters: {getattr(agent, 'knowledge_filters', 'Not set')}")
        print(f"Knowledge Base: {type(getattr(agent, 'knowledge', 'Not set'))}")
        
        # Check for knowledge search tools
        has_knowledge_search = any(
            "knowledge" in tool.name.lower() or "search" in tool.name.lower()
            for tool in (agent.tools or [])
        )
        print(f"Has Knowledge Search: {has_knowledge_search}")
        
        if agent.tools:
            for tool in agent.tools:
                print(f"  - Tool: {tool.name}")
        else:
            print("No tools found")
            
        # Check if the agent has tool_functions
        if hasattr(agent, 'tool_functions') and agent.tool_functions:
            print(f"Tool Functions: {len(agent.tool_functions)}")
            for func in agent.tool_functions:
                print(f"  - Function: {func.name}")
        else:
            print("No tool functions found")
        
        return agent
        
    except Exception as e:
        print(f"Error creating direct agent: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_registry_agent():
    """Test pagbank agent instantiated through registry"""
    print("\n=== Testing Registry Agent Instantiation ===")
    
    try:
        agent = get_agent(
            name="pagbank",
            session_id="test_registry",
            debug_mode=True,
            db_url=os.getenv("DATABASE_URL")
        )
        
        print(f"Agent ID: {agent.agent_id}")
        print(f"Agent Name: {agent.name}")
        print(f"Agent Tools: {[tool.name for tool in agent.tools] if agent.tools else 'No tools'}")
        
        # Check for knowledge search tools
        has_knowledge_search = any(
            "knowledge" in tool.name.lower() or "search" in tool.name.lower()
            for tool in (agent.tools or [])
        )
        print(f"Has Knowledge Search: {has_knowledge_search}")
        
        if agent.tools:
            for tool in agent.tools:
                print(f"  - Tool: {tool.name}")
        
        return agent
        
    except Exception as e:
        print(f"Error creating registry agent: {e}")
        return None

async def test_team_agents():
    """Test agents loaded through Ana team"""
    print("\n=== Testing Team Agent Loading ===")
    
    try:
        team = get_ana_team(
            session_id="test_team",
            debug_mode=True
        )
        
        print(f"Team Name: {team.name}")
        print(f"Team Mode: {team.mode}")
        print(f"Team Members: {len(team.members)}")
        
        for i, member in enumerate(team.members):
            print(f"\nMember {i+1}:")
            print(f"  Agent ID: {member.agent_id}")
            print(f"  Agent Name: {member.name}")
            print(f"  Agent Tools: {[tool.name for tool in member.tools] if member.tools else 'No tools'}")
            
            # Check for knowledge search tools
            has_knowledge_search = any(
                "knowledge" in tool.name.lower() or "search" in tool.name.lower()
                for tool in (member.tools or [])
            )
            print(f"  Has Knowledge Search: {has_knowledge_search}")
            
            if member.tools:
                for tool in member.tools:
                    print(f"    - Tool: {tool.name}")
        
        return team
        
    except Exception as e:
        print(f"Error creating team: {e}")
        return None

async def main():
    """Main test function"""
    print("PagBank Team Knowledge Integration Debug")
    print("=" * 50)
    
    # Test direct instantiation
    direct_agent = await test_direct_agent()
    
    # Test registry instantiation
    registry_agent = await test_registry_agent()
    
    # Test team loading
    team = await test_team_agents()
    
    # Compare results
    print("\n=== Comparison Results ===")
    
    if direct_agent and registry_agent:
        direct_tools = [tool.name for tool in direct_agent.tools] if direct_agent.tools else []
        registry_tools = [tool.name for tool in registry_agent.tools] if registry_agent.tools else []
        
        print(f"Direct Agent Tools: {direct_tools}")
        print(f"Registry Agent Tools: {registry_tools}")
        print(f"Tools Match: {direct_tools == registry_tools}")
        
        if direct_tools != registry_tools:
            print("⚠️  DIFFERENCE FOUND!")
            print(f"Direct only: {set(direct_tools) - set(registry_tools)}")
            print(f"Registry only: {set(registry_tools) - set(direct_tools)}")
    
    if team:
        print(f"\nTeam has {len(team.members)} members")
        for i, member in enumerate(team.members):
            member_tools = [tool.name for tool in member.tools] if member.tools else []
            has_knowledge = any("knowledge" in tool.lower() or "search" in tool.lower() for tool in member_tools)
            print(f"Member {i+1} ({member.agent_id}): Knowledge={has_knowledge}, Tools={len(member_tools)}")

if __name__ == "__main__":
    asyncio.run(main())