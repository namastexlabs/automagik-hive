#!/usr/bin/env python3
"""
Test memory integration with team
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from teams.ana.team import get_ana_team
from dotenv import load_dotenv
import os

load_dotenv()

# Test the team with memory integration
team = get_ana_team(
    session_id="test_memory_integration", 
    debug_mode=True,
    user_id="test_user"
)

print("=== Testing Memory Integration ===")
print(f"Team Name: {team.name}")
print(f"Team Mode: {team.mode}")
print(f"Team Members: {len(team.members)}")

# Check if team has memory
print(f"Team Memory: {team.memory}")

# Check if members have memory
for i, member in enumerate(team.members):
    print(f"Member {i+1} ({member.agent_id}): Memory={member.memory}")

# Test with conversation to check memory persistence
print("\n=== Testing Memory Persistence ===")
print("First message:")
try:
    response1 = team.run("Meu nome é João e perdi meu cartão.")
    print(f"Response 1: {response1.content}")
except Exception as e:
    print(f"Error 1: {e}")

print("\nSecond message (should remember name):")
try:
    response2 = team.run("Qual é o meu nome?")
    print(f"Response 2: {response2.content}")
except Exception as e:
    print(f"Error 2: {e}")

print("\nThird message (follow-up):")
try:
    response3 = team.run("Como faço para bloquear?")
    print(f"Response 3: {response3.content}")
except Exception as e:
    print(f"Error 3: {e}")