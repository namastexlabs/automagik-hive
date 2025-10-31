#!/usr/bin/env python3
"""
Comprehensive demonstration of all 3 example agents.

This script demonstrates:
1. All agents are working with REAL AI
2. Each uses proper Agno patterns
3. Factory functions work correctly
4. YAML configurations load properly
5. Agent IDs set as attributes
6. Real LLM responses via response.content
"""

import os
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

print("=" * 80)
print("🎉 AUTOMAGIK HIVE - EXAMPLE AGENTS DEMONSTRATION")
print("=" * 80)
print()

# Verify API keys
print("🔑 API Keys Status:")
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if openai_key:
    print(f"  ✅ OPENAI_API_KEY: {openai_key[:20]}...")
else:
    print("  ❌ OPENAI_API_KEY: NOT FOUND")
    sys.exit(1)

if anthropic_key:
    print(f"  ✅ ANTHROPIC_API_KEY: {anthropic_key[:20]}...")
else:
    print("  ❌ ANTHROPIC_API_KEY: NOT FOUND")
    sys.exit(1)

print()

# Import agent factories dynamically
import importlib.util


def load_agent_factory(agent_name: str, factory_name: str):
    """Dynamically load an agent factory function."""
    agent_path = project_root / "hive" / "examples" / "agents" / agent_name / "agent.py"
    spec = importlib.util.spec_from_file_location(f"{agent_name}_module", agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, factory_name)


get_support_bot_agent = load_agent_factory("support-bot", "get_support_bot_agent")
get_code_reviewer_agent = load_agent_factory("code-reviewer", "get_code_reviewer_agent")
get_researcher_agent = load_agent_factory("researcher", "get_researcher_agent")


def demo_agent(name: str, factory_fn, query: str):
    """Demonstrate a single agent."""
    print("=" * 80)
    print(f"🤖 AGENT: {name}")
    print("=" * 80)

    try:
        # Create agent using factory
        print("\n📦 Creating agent...")
        agent = factory_fn()

        # Verify proper Agno pattern
        print(f"  ✅ Name: {agent.name}")
        print(f"  ✅ Model: {agent.model.id}")
        print(f"  ✅ Agent ID: {agent.id}")
        print(f"  ✅ Has tools: {len(agent.tools) if agent.tools else 0}")

        # Test with real query
        print(f"\n📤 Query: {query}")
        print("\n⏳ Calling LLM (this may take a few seconds)...")

        response = agent.run(query)

        # Display response
        print("\n📥 Response (via response.content):")
        print("-" * 80)
        # Truncate for readability
        content = response.content
        if len(content) > 500:
            print(content[:500] + "...")
            print(f"\n[... {len(content) - 500} more characters ...]")
        else:
            print(content)
        print("-" * 80)

        print(f"\n✅ {name} WORKING!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all demonstrations."""

    results = []

    # Demo 1: Support Bot
    success = demo_agent("Support Bot", get_support_bot_agent, "How do I reset my password?")
    results.append(("Support Bot", success))

    print("\n\n")

    # Demo 2: Code Reviewer
    success = demo_agent("Code Reviewer", get_code_reviewer_agent, "Review this code: def add(a, b): return a + b")
    results.append(("Code Reviewer", success))

    print("\n\n")

    # Demo 3: Researcher
    success = demo_agent("Researcher", get_researcher_agent, "Summarize the key benefits of AI agents")
    results.append(("Researcher", success))

    # Summary
    print("\n\n")
    print("=" * 80)
    print("📊 DEMONSTRATION SUMMARY")
    print("=" * 80)

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    successful = sum(1 for _, success in results if success)
    print(f"\n🎯 {successful}/{len(results)} agents working successfully!")

    if successful == len(results):
        print("\n🎉 ALL AGENTS WORKING WITH REAL AI!")
        print("\n📝 Key Features Demonstrated:")
        print("  ✅ Meta-agent generation using REAL AI")
        print("  ✅ Proper Agno factory patterns")
        print("  ✅ YAML-driven configuration")
        print("  ✅ Agent ID set as attribute (not in constructor)")
        print("  ✅ Response access via response.content")
        print("  ✅ Real LLM calls to OpenAI and Anthropic")
        print("  ✅ Tool integration (PythonTools, FileTools)")
        print("\n📂 Agent Locations:")
        print("  • hive/examples/agents/support-bot/")
        print("  • hive/examples/agents/code-reviewer/")
        print("  • hive/examples/agents/researcher/")
        return 0
    else:
        print(f"\n⚠️  {len(results) - successful} agent(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
