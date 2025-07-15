#!/usr/bin/env python3
"""
Test script to debug agent creation differences
"""

import asyncio
from agents.registry import get_agent
from agents.pagbank.agent import get_pagbank_agent
from db.session import db_url

async def test_agent_creation():
    """Test different ways of creating agents"""
    
    print("🔍 Testing Agent Creation Methods")
    print("=" * 50)
    
    # Test 1: Direct pagbank agent factory
    print("1. Direct pagbank agent factory:")
    agent1 = get_pagbank_agent(debug_mode=False, db_url=db_url)
    print(f"   Agent ID: {agent1.agent_id}")
    print(f"   Has knowledge: {hasattr(agent1, 'knowledge') and agent1.knowledge is not None}")
    print(f"   Tools: {[tool.name for tool in agent1.tools] if agent1.tools else 'None'}")
    
    # Test 2: Registry via pagbank
    print("\n2. Registry via 'pagbank':")
    try:
        agent2 = get_agent("pagbank", debug_mode=False, db_url=db_url)
        print(f"   Agent ID: {agent2.agent_id}")
        print(f"   Has knowledge: {hasattr(agent2, 'knowledge') and agent2.knowledge is not None}")
        print(f"   Tools: {[tool.name for tool in agent2.tools] if agent2.tools else 'None'}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Registry via pagbank-specialist
    print("\n3. Registry via 'pagbank-specialist':")
    try:
        agent3 = get_agent("pagbank-specialist", debug_mode=False, db_url=db_url)
        print(f"   Agent ID: {agent3.agent_id}")
        print(f"   Has knowledge: {hasattr(agent3, 'knowledge') and agent3.knowledge is not None}")
        print(f"   Tools: {[tool.name for tool in agent3.tools] if agent3.tools else 'None'}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_creation())