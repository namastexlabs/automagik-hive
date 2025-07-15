#!/usr/bin/env python3
"""
Test team knowledge integration with real message
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from teams.ana.team import get_ana_team
from dotenv import load_dotenv
import os

load_dotenv()

# Test the team with a real message
team = get_ana_team(
    session_id="test_team_knowledge", 
    debug_mode=True
)

print("=== Testing Ana Team Knowledge Integration ===")
print(f"Team Name: {team.name}")
print(f"Team Mode: {team.mode}")
print(f"Team Members: {len(team.members)}")

# Test with a PagBank query that should route to PagBank specialist
print("\n=== Testing Team Run with PagBank Query ===")
try:
    response = team.run("Perdi meu cartão, como faço para bloquear?")
    print(f"Team Response: {response.content}")
except Exception as e:
    print(f"Error during team run: {e}")
    import traceback
    traceback.print_exc()

# Test with another query
print("\n=== Testing Team Run with Card Query ===")
try:
    response = team.run("Qual é o limite do meu cartão?")
    print(f"Team Response: {response.content}")
except Exception as e:
    print(f"Error during team run: {e}")
    import traceback
    traceback.print_exc()