#!/usr/bin/env python3
"""
Agent Versioning System Demo

This script demonstrates the complete agent versioning system including:
- Creating versions from configurations
- Version activation and management
- A/B testing capabilities
- Performance metrics tracking
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from db.session import init_database
from db.services.agent_version_service import AgentVersionService
from agents.version_factory import agent_factory
from agents.ab_testing import ABTestManager, create_ab_test


def create_sample_configs() -> Dict[str, Dict[str, Any]]:
    """Create sample agent configurations for demonstration."""
    
    base_config = {
        "agent": {
            "agent_id": "demo-specialist",
            "name": "Demo Specialist Agent",
            "role": "Demo Specialist",
            "description": "Demo agent for versioning system"
        },
        "model": {
            "provider": "anthropic",
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "storage": {
            "type": "postgres",
            "table_name": "demo_specialist",
            "auto_upgrade_schema": True
        },
        "memory": {
            "add_history_to_messages": True,
            "num_history_runs": 5
        },
        "markdown": False,
        "show_tool_calls": True
    }
    
    # Version 1: Basic configuration
    v1_config = {
        **base_config,
        "agent": {
            **base_config["agent"],
            "version": 1
        },
        "instructions": "You are a helpful demo agent. Provide basic assistance.",
        "tools": ["basic_tool"],
        "escalation_triggers": {
            "keywords": ["help", "problem"]
        }
    }
    
    # Version 2: Enhanced with better prompts
    v2_config = {
        **base_config,
        "agent": {
            **base_config["agent"],
            "version": 2
        },
        "instructions": """You are an advanced demo agent with enhanced capabilities.
        
        Your role is to provide comprehensive assistance with:
        - Detailed explanations
        - Step-by-step guidance
        - Proactive suggestions
        
        Always maintain a helpful and professional tone.""",
        "tools": ["basic_tool", "advanced_tool"],
        "escalation_triggers": {
            "keywords": ["help", "problem", "urgent", "escalate"],
            "confidence_threshold": 0.8
        }
    }
    
    # Version 3: Experimental with new features
    v3_config = {
        **base_config,
        "agent": {
            **base_config["agent"],
            "version": 3
        },
        "model": {
            **base_config["model"],
            "temperature": 0.5,  # More conservative
            "max_tokens": 3000   # More detailed responses
        },
        "instructions": """You are an experimental demo agent with cutting-edge capabilities.
        
        Features:
        - Advanced reasoning and analysis
        - Multi-step problem solving
        - Contextual awareness
        - Personalized responses
        
        Provide thoughtful, comprehensive assistance while being concise.""",
        "tools": ["basic_tool", "advanced_tool", "experimental_tool"],
        "escalation_triggers": {
            "keywords": ["help", "problem", "urgent", "escalate", "complex"],
            "confidence_threshold": 0.9,
            "response_time_threshold": 5000
        }
    }
    
    return {
        1: v1_config,
        2: v2_config,
        3: v3_config
    }


async def demo_basic_versioning():
    """Demonstrate basic versioning functionality."""
    print("=" * 60)
    print("DEMO: Basic Agent Versioning")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    # Create version service
    version_service = AgentVersionService()
    
    # Create sample configurations
    configs = create_sample_configs()
    
    print("\n1. Creating agent versions...")
    
    # Create versions
    for version, config in configs.items():
        try:
            created_version = version_service.create_version(
                agent_id="demo-specialist",
                version=version,
                config=config,
                created_by="demo_script",
                description=f"Demo version {version} with enhanced features"
            )
            print(f"   ✅ Created version {version}")
        except Exception as e:
            print(f"   ⚠️  Version {version} already exists: {e}")
    
    print("\n2. Listing all versions...")
    versions = version_service.list_versions("demo-specialist")
    for v in versions:
        status = "🟢 ACTIVE" if v.is_active else "⚪ INACTIVE"
        print(f"   {status} v{v.version}: {v.description}")
    
    print("\n3. Activating version 2...")
    version_service.activate_version(
        agent_id="demo-specialist",
        version=2,
        changed_by="demo_script",
        reason="Demo activation"
    )
    
    print("\n4. Checking active version...")
    active_version = version_service.get_active_version("demo-specialist")
    if active_version:
        print(f"   🟢 Active version: {active_version.version}")
    
    print("\n5. Creating agents from different versions...")
    
    # Test creating agents from different versions
    for version in [1, 2, 3]:
        try:
            agent = agent_factory.create_agent(
                agent_id="demo-specialist",
                version=version,
                session_id=f"demo-session-{version}",
                debug_mode=True
            )
            print(f"   ✅ Created agent with version {version}")
            print(f"      Agent name: {agent.name}")
            print(f"      Version metadata: {agent.metadata.get('version', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Failed to create agent with version {version}: {e}")
    
    print("\n6. Version history...")
    history = version_service.get_version_history("demo-specialist")
    for record in history[:3]:  # Show last 3 changes
        print(f"   📅 {record.changed_at}: {record.action} (by {record.changed_by})")
        if record.reason:
            print(f"      Reason: {record.reason}")


async def demo_ab_testing():
    """Demonstrate A/B testing functionality."""
    print("\n" + "=" * 60)
    print("DEMO: A/B Testing")
    print("=" * 60)
    
    # Create A/B test manager
    ab_manager = ABTestManager()
    
    print("\n1. Creating A/B test...")
    
    # Create test configuration
    test_config = create_ab_test(
        test_id="demo-test-v2-vs-v3",
        name="Version 2 vs Version 3 Performance Test",
        description="Testing improved prompts and features in version 3",
        agent_id="demo-specialist",
        control_version=2,
        test_versions=[3],
        traffic_distribution={2: 70, 3: 30},  # 70% control, 30% test
        duration_days=7,
        min_sample_size=50,
        primary_metric="success_rate",
        secondary_metrics=["response_time", "satisfaction"]
    )
    
    print(f"   ✅ Created test: {test_config.name}")
    print(f"      Control version: {test_config.control_version}")
    print(f"      Test versions: {test_config.test_versions}")
    print(f"      Traffic distribution: {test_config.traffic_distribution}")
    
    print("\n2. Starting A/B test...")
    ab_manager.start_test(test_config)
    print(f"   🟢 Test started at {test_config.start_date}")
    
    print("\n3. Simulating user interactions...")
    
    # Simulate user interactions
    users = [f"user_{i}" for i in range(1, 21)]  # 20 test users
    
    for user_id in users:
        # Get version for user
        version = ab_manager.get_version_for_user(test_config.test_id, user_id)
        
        # Create agent for user
        agent = ab_manager.create_agent_for_test(
            test_id=test_config.test_id,
            user_id=user_id,
            session_id=f"session-{user_id}",
            debug_mode=False
        )
        
        print(f"   👤 {user_id} -> version {version} ({agent.metadata.get('ab_test_variant', 'unknown')})")
        
        # Simulate interaction metrics
        import random
        success = random.choice([True, True, True, False])  # 75% success rate
        response_time = random.randint(800, 2500)  # 800-2500ms
        satisfaction = random.randint(6, 10) if success else random.randint(3, 7)
        
        # Record interaction
        ab_manager.record_interaction(
            test_id=test_config.test_id,
            user_id=user_id,
            version=version,
            success=success,
            response_time_ms=response_time,
            satisfaction_score=satisfaction,
            escalated=not success and random.random() < 0.3
        )
    
    print("\n4. Analyzing test results...")
    
    # Wait a moment to simulate test running
    await asyncio.sleep(1)
    
    # Analyze results
    analysis = ab_manager.analyze_test_results(test_config.test_id)
    
    print(f"   📊 Test Analysis: {analysis['test_name']}")
    print(f"      Status: {analysis['status']}")
    print(f"      Sufficient data: {analysis['sufficient_data']}")
    
    if analysis['results_by_version']:
        print("\n   📈 Results by version:")
        for version, results in analysis['results_by_version'].items():
            variant = results['variant_type']
            print(f"      Version {version} ({variant}):")
            print(f"         Sample size: {results['sample_size']}")
            print(f"         Success rate: {results['success_rate']:.1%}")
            print(f"         Avg response time: {results['avg_response_time']:.0f}ms")
            print(f"         Avg satisfaction: {results['avg_satisfaction']:.1f}/10")
    
    if analysis['recommendations']:
        print("\n   💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"      Version {rec['version']}: {rec['recommendation']}")
            print(f"         Improvement: {rec['improvement_percent']:.1f}%")
            print(f"         Significant: {rec['is_significant']}")
    
    print("\n5. Stopping test...")
    ab_manager.stop_test(test_config.test_id, "Demo completed")
    print("   ⏹️  Test stopped")


async def demo_api_integration():
    """Demonstrate API integration."""
    print("\n" + "=" * 60)
    print("DEMO: API Integration")
    print("=" * 60)
    
    print("\n1. Available agents:")
    agents_info = agent_factory.list_available_agents()
    for agent_id, info in agents_info.items():
        source_icon = "💾" if info["source"] == "database" else "📁"
        print(f"   {source_icon} {agent_id}")
        if info["source"] == "database":
            print(f"      Versions: {info['versions']}")
            print(f"      Active: v{info['active_version']}")
    
    print("\n2. Testing agent execution...")
    
    # Test messages
    test_messages = [
        "Hello, how can you help me?",
        "I need help with a problem",
        "What are your capabilities?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Test {i}: '{message}'")
        
        try:
            # Create agent with active version
            agent = agent_factory.create_agent(
                agent_id="demo-specialist",
                session_id=f"demo-api-session-{i}",
                debug_mode=True
            )
            
            # Simulate running the agent (would actually call agent.run(message) in real usage)
            print(f"      ✅ Agent created (version {agent.metadata.get('version', 'unknown')})")
            print(f"      📝 Would process: {message}")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print("\n3. Version management operations...")
    
    version_service = AgentVersionService()
    
    # Clone a version
    try:
        cloned_version = version_service.clone_version(
            agent_id="demo-specialist",
            source_version=2,
            target_version=4,
            created_by="demo_script",
            description="Cloned from v2 for experimentation"
        )
        print(f"   ✅ Cloned version 2 -> 4")
    except Exception as e:
        print(f"   ⚠️  Clone failed: {e}")
    
    # Update configuration
    try:
        config = version_service.get_config("demo-specialist", 1)
        if config:
            config["instructions"] = "Updated instructions for demo purposes"
            version_service.update_config(
                agent_id="demo-specialist",
                version=1,
                config=config,
                changed_by="demo_script",
                reason="Demo configuration update"
            )
            print(f"   ✅ Updated version 1 configuration")
    except Exception as e:
        print(f"   ⚠️  Update failed: {e}")


async def main():
    """Run all demonstrations."""
    print("🤖 Agent Versioning System Demo")
    print("=" * 60)
    
    try:
        await demo_basic_versioning()
        await demo_ab_testing()
        await demo_api_integration()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60)
        
        print("\n📚 What was demonstrated:")
        print("• Database-driven agent versioning")
        print("• Version creation, activation, and management")
        print("• A/B testing with traffic distribution")
        print("• Performance metrics tracking")
        print("• API integration capabilities")
        print("• Version cloning and configuration updates")
        
        print("\n🚀 Next steps:")
        print("• Run the API server: uv run python api/playground.py")
        print("• Test API endpoints: curl http://localhost:7777/v1/agents/")
        print("• Use CLI tool: python scripts/agent_version_manager.py --help")
        print("• Explore A/B testing: python -c 'from agents.ab_testing import *'")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())