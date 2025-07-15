#!/usr/bin/env python3
"""
Simple test of memory integration without database
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
import os

load_dotenv()

# Test individual agent factory functions
from agents.pagbank.agent import get_pagbank_agent
from agents.adquirencia.agent import get_adquirencia_agent
from agents.emissao.agent import get_emissao_agent
from agents.human_handoff.agent import get_human_handoff_agent

# Mock memory object
class MockMemory:
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"MockMemory(name='{self.name}')"

# Test with mock memory
mock_memory = MockMemory("test_memory")

print("=== Testing Individual Agent Memory Integration ===")
print("Testing without database connection (will fail on storage but memory should work)\n")

# Test PagBank agent
print("1. Testing PagBank agent...")
try:
    agent = get_pagbank_agent(
        session_id="test_session",
        debug_mode=True,
        memory=mock_memory
    )
    print(f"   ✅ PagBank agent created with memory: {agent.memory}")
except Exception as e:
    print(f"   ❌ PagBank agent failed: {e}")

# Test Adquirencia agent
print("\n2. Testing Adquirencia agent...")
try:
    agent = get_adquirencia_agent(
        session_id="test_session",
        debug_mode=True,
        memory=mock_memory
    )
    print(f"   ✅ Adquirencia agent created with memory: {agent.memory}")
except Exception as e:
    print(f"   ❌ Adquirencia agent failed: {e}")

# Test Emissao agent  
print("\n3. Testing Emissao agent...")
try:
    agent = get_emissao_agent(
        session_id="test_session",
        debug_mode=True,
        memory=mock_memory
    )
    print(f"   ✅ Emissao agent created with memory: {agent.memory}")
except Exception as e:
    print(f"   ❌ Emissao agent failed: {e}")

# Test Human Handoff agent
print("\n4. Testing Human Handoff agent...")
try:
    agent = get_human_handoff_agent(
        session_id="test_session",
        debug_mode=True,
        memory=mock_memory
    )
    print(f"   ✅ Human Handoff agent created with memory: {agent.memory}")
except Exception as e:
    print(f"   ❌ Human Handoff agent failed: {e}")

print("\n=== Testing Agent Registry ===")
from agents.registry import get_agent

# Test registry with memory
print("\n5. Testing agent registry with memory...")
try:
    agent = get_agent(
        name="pagbank",
        session_id="test_session",
        debug_mode=True,
        memory=mock_memory
    )
    print(f"   ✅ Registry agent created with memory: {agent.memory}")
except Exception as e:
    print(f"   ❌ Registry agent failed: {e}")

print("\n=== Memory Integration Status ===")
print("If all tests show memory objects correctly, the memory integration is working!")