#!/usr/bin/env python3
"""
Test knowledge search functionality directly
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from agents.pagbank.agent import get_pagbank_agent
from dotenv import load_dotenv
import os

load_dotenv()

# Test the agent with a real message
agent = get_pagbank_agent(
    session_id="test_knowledge",
    debug_mode=True,
    db_url=os.getenv("DATABASE_URL")
)

print("=== Testing Agent Knowledge Search ===")
print(f"Agent ID: {agent.agent_id}")
print(f"Search Knowledge: {agent.search_knowledge}")
print(f"Enable Agentic Knowledge Filters: {agent.enable_agentic_knowledge_filters}")
print(f"Knowledge Filters: {agent.knowledge_filters}")
print(f"Knowledge Base: {agent.knowledge}")

# Test run with a simple query
print("\n=== Testing Agent Run ===")
try:
    response = agent.run("Perdi meu cartão, como faço para bloquear?")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Error during run: {e}")
    import traceback
    traceback.print_exc()