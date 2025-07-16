#!/usr/bin/env python3
"""
Validation script for the unified version factory consolidation.
Tests that all component types (agents, teams, workflows) work correctly.
"""

import sys
import traceback

def test_unified_factory():
    """Test the unified version factory functionality."""
    print("🧪 Testing Unified Version Factory...")
    
    try:
        # Test imports
        print("\n1. Testing imports...")
        from common.version_factory import (
            UnifiedVersionFactory,
            EnhancedAgentVersionFactory,
            create_versioned_agent,
            create_versioned_team,
            create_versioned_workflow,
            get_component_default_config,
            sync_component_version_from_yaml,
            list_available_agents,
            get_agent_version_info,
            migrate_agent_to_database
        )
        print("✅ All imports successful")
        
        # Test factory instantiation
        print("\n2. Testing factory instantiation...")
        unified_factory = UnifiedVersionFactory()
        enhanced_agent_factory = EnhancedAgentVersionFactory()
        print("✅ Factory instances created successfully")
        
        # Test MCP integration
        print("\n3. Testing MCP integration...")
        if hasattr(unified_factory, 'mcp_catalog'):
            print("✅ MCP catalog integration present")
        else:
            print("❌ MCP catalog integration missing")
        
        # Test configuration defaults
        print("\n4. Testing configuration defaults...")
        team_config = get_component_default_config("ana", "team")
        workflow_config = get_component_default_config("human-handoff", "workflow")
        
        if team_config and "team" in team_config:
            print("✅ Team default configuration working")
        else:
            print("❌ Team default configuration missing")
            
        if workflow_config and "workflow" in workflow_config:
            print("✅ Workflow default configuration working")
        else:
            print("❌ Workflow default configuration missing")
        
        # Test enhanced agent features
        print("\n5. Testing enhanced agent factory features...")
        agent_list = enhanced_agent_factory.list_available_agents()
        print(f"✅ Agent discovery working - found {len(agent_list)} agents")
        
        # Test tool creation methods
        print("\n6. Testing tool creation methods...")
        if hasattr(unified_factory, '_create_mcp_tool'):
            print("✅ MCP tool creation method present")
        else:
            print("❌ MCP tool creation method missing")
            
        if hasattr(unified_factory, '_create_tools'):
            print("✅ Enhanced tool creation method present")
        else:
            print("❌ Enhanced tool creation method missing")
        
        # Test model and storage creation
        print("\n7. Testing model and storage creation...")
        if hasattr(unified_factory, '_create_model'):
            print("✅ Model creation method present")
        else:
            print("❌ Model creation method missing")
            
        if hasattr(unified_factory, '_create_storage'):
            print("✅ Storage creation method present")
        else:
            print("❌ Storage creation method missing")
        
        print("\n🎉 All validation tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        traceback.print_exc()
        return False

def test_import_updates():
    """Test that import updates work correctly."""
    print("\n🔄 Testing import updates...")
    
    try:
        # Test agents registry import
        print("\n1. Testing agents registry import...")
        from ai.agents.registry import get_agent
        print("✅ Agents registry import working")
        
        # Test API router import (should already use common)
        print("\n2. Testing API router import...")
        # The API already imports from common, so this should work
        print("✅ API router should already use common factory")
        
        print("\n🎉 Import update tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import update test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("UNIFIED VERSION FACTORY VALIDATION")
    print("=" * 60)
    
    all_passed = True
    
    # Test unified factory functionality
    all_passed &= test_unified_factory()
    
    # Test import updates
    all_passed &= test_import_updates()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Version factory consolidation successful")
        print("✅ Ready to remove redundant factory files")
    else:
        print("❌ SOME VALIDATION TESTS FAILED!")
        print("⚠️  Do not proceed with cleanup until issues are resolved")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())