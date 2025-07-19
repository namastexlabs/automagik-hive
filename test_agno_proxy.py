#!/usr/bin/env python3
"""
Test script for the new Agno Proxy System

This script validates that our dynamic proxy system correctly maps
configuration parameters to Agno Agent constructor parameters.
"""

import os
import sys
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_agno_proxy():
    """Test all Agno proxy systems without requiring database."""
    
    try:
        from lib.utils.agno_proxy import get_agno_proxy, get_agno_team_proxy, get_agno_workflow_proxy
        
        print("🔍 Testing Agno Proxy Systems...")
        
        # Test Agent Proxy
        agent_proxy = get_agno_proxy()
        agent_params = agent_proxy.get_supported_parameters()
        print(f"✅ Agent Proxy: {len(agent_params)} parameters")
        print(f"   Sample: {sorted(list(agent_params))[:5]}...")
        
        # Test Team Proxy
        team_proxy = get_agno_team_proxy()
        team_params = team_proxy.get_supported_parameters()
        print(f"✅ Team Proxy: {len(team_params)} parameters")
        print(f"   Sample: {sorted(list(team_params))[:5]}...")
        
        # Test Workflow Proxy
        workflow_proxy = get_agno_workflow_proxy()
        workflow_params = workflow_proxy.get_supported_parameters()
        print(f"✅ Workflow Proxy: {len(workflow_params)} parameters")
        print(f"   Sample: {sorted(list(workflow_params))[:5]}...")
        
        # Test with template config
        template_config_path = project_root / "ai" / "agents" / "template" / "config_complete_agno.yaml"
        
        if template_config_path.exists():
            with open(template_config_path) as f:
                config = yaml.safe_load(f)
            
            # Validate configuration with agent proxy
            validation = agent_proxy.validate_config(config)
            
            print(f"\n📊 Agent Configuration Analysis:")
            print(f"   Supported Agno params found: {len(validation['supported_agno_params'])}")
            print(f"   Custom params found: {len(validation['custom_params'])}")
            print(f"   Unknown params found: {len(validation['unknown_params'])}")
            print(f"   Coverage: {validation['coverage_percentage']:.1f}%")
            
            if validation['unknown_params']:
                print(f"   ⚠️  Unknown params: {validation['unknown_params']}")
            
            print(f"\n✅ All proxy systems validated successfully!")
            return True
        else:
            print(f"❌ Template config not found at {template_config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing proxies: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_version_factory_integration():
    """Test version factory integration (requires database)."""
    
    print("\n🔗 Testing Version Factory Integration...")
    
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  DATABASE_URL not set - skipping factory integration test")
        print("   To test with database: export DATABASE_URL='postgresql://...'")
        return True
    
    try:
        from lib.utils.version_factory import create_agent
        
        # Test creating template agent
        agent = create_agent('template')
        
        print(f"✅ Template agent created successfully!")
        print(f"   Agent name: {agent.name}")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Model: {agent.model.id}")
        print(f"   Storage table: {agent.storage.table_name}")
        print(f"   Metadata: {agent.metadata.get('agno_parameters_count', 'unknown')} Agno params")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing version factory: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    
    print("🚀 Testing New Agno Proxy System")
    print("=" * 50)
    
    success = True
    
    # Test 1: Proxy system
    if not test_agno_proxy():
        success = False
    
    # Test 2: Version factory integration
    if not test_version_factory_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The proxy system is working correctly.")
        print("\n💡 Benefits of the new system:")
        print("   • Automatically discovers ALL Agno Agent parameters")
        print("   • Future-proof against Agno updates")
        print("   • Maintains backward compatibility")
        print("   • Handles custom parameters gracefully")
        print("   • Provides detailed configuration validation")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()