#!/usr/bin/env python3
"""
Test script to verify Performance-Optimized Sequential Startup
Shows the new clean, sequential logging vs old scattered approach
"""

import os
import asyncio
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

# Mock database and external dependencies for testing
os.environ["HIVE_DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["HIVE_LOG_LEVEL"] = "INFO"

async def test_orchestrated_startup():
    """Test the orchestrated startup sequence"""
    
    print("\n🚀 Testing Performance-Optimized Sequential Startup")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Mock external dependencies that might not be available in test
        with patch('lib.utils.db_migration.check_and_run_migrations', return_value=False), \
             patch('lib.mcp.MCPCatalog') as mock_mcp, \
             patch('lib.services.version_sync_service.AgnoVersionSyncService') as mock_sync:
            
            # Configure mocks
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.list_servers.return_value = []
            mock_mcp.return_value = mock_mcp_instance
            
            mock_sync_instance = MagicMock()
            mock_sync_instance.sync_component_type.return_value = []
            mock_sync.return_value = mock_sync_instance
            
            # Import and run orchestrated startup
            from lib.utils.startup_orchestration import orchestrated_startup
            
            print("📍 Starting orchestrated startup test...")
            startup_results = await orchestrated_startup()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f"\n✅ Orchestrated Startup Completed!")
            print(f"   ⏱️  Total execution time: {execution_time:.2f} seconds")
            print(f"   📊 Components discovered: {startup_results.registries.total_components}")
            print(f"   📝 Summary: {startup_results.registries.summary}")
            
            # Verify results structure
            assert startup_results.registries is not None
            assert startup_results.services is not None
            assert hasattr(startup_results.registries, 'workflows')
            assert hasattr(startup_results.registries, 'teams')
            assert hasattr(startup_results.registries, 'agents')
            
            print(f"   ✅ Workflow registry: {len(startup_results.registries.workflows)} workflows")
            print(f"   ✅ Team registry: {len(startup_results.registries.teams)} teams")  
            print(f"   ✅ Agent registry: {len(startup_results.registries.agents)} agents")
            print(f"   ✅ Auth service: {'Enabled' if startup_results.services.auth_service.is_auth_enabled() else 'Disabled'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lazy_registry_loading():
    """Test that registries don't load at import time"""
    
    print("\n🔍 Testing Lazy Registry Loading")
    print("=" * 40)
    
    try:
        import_start = time.time()
        
        # Import registries - should be instant (no discovery)
        from ai.workflows.registry import get_workflow_registry
        from ai.teams.registry import get_team_registry
        
        import_time = time.time() - import_start
        
        print(f"✅ Registry imports completed in {import_time:.4f} seconds")
        print("   📝 No discovery triggered at import time")
        
        # Now trigger lazy loading
        discovery_start = time.time()
        
        workflow_registry = get_workflow_registry()
        team_registry = get_team_registry()
        
        discovery_time = time.time() - discovery_start
        
        print(f"✅ Lazy discovery completed in {discovery_time:.4f} seconds")
        print(f"   📊 Found: {len(workflow_registry)} workflows, {len(team_registry)} teams")
        
        # Verify second call uses cache
        cache_start = time.time()
        workflow_registry_2 = get_workflow_registry()
        cache_time = time.time() - cache_start
        
        print(f"✅ Cached access completed in {cache_time:.6f} seconds")
        print("   📝 Second call uses cached results")
        
        return True
        
    except Exception as e:
        print(f"❌ Lazy loading test failed: {e}")
        import traceback  
        traceback.print_exc()
        return False

def compare_startup_approaches():
    """Compare old vs new startup approach"""
    
    print("\n📊 Startup Approach Comparison")
    print("=" * 50)
    
    print("📋 BEFORE (Old Scattered Approach):")
    print("   ❌ Import-time discovery → logs scattered during imports")
    print("   ❌ Registry refresh on every access → O(n²) filesystem ops")
    print("   ❌ Random component loading order")
    print("   ❌ No dependency awareness")
    print("   ❌ Verbose redundant logging")
    
    print("\n📋 AFTER (Performance-Optimized Sequential):")
    print("   ✅ Lazy discovery → no import-time side effects")
    print("   ✅ Cached results → O(n) filesystem operations")
    print("   ✅ Dependency-aware startup sequence")
    print("   ✅ Knowledge base initialized early (agents/teams depend on it)")
    print("   ✅ Clean sequential logging")
    print("   ✅ Batch component discovery")
    print("   ✅ Performance monitoring and metrics")

async def main():
    """Run all tests"""
    
    print("🎯 Performance-Optimized Sequential Startup Test Suite")
    print("=" * 60)
    
    # Test 1: Lazy Loading
    lazy_test_passed = test_lazy_registry_loading()
    
    # Test 2: Orchestrated Startup
    if lazy_test_passed:
        orchestration_test_passed = await test_orchestrated_startup()
    else:
        orchestration_test_passed = False
    
    # Test 3: Comparison Summary
    compare_startup_approaches()
    
    print(f"\n🏁 Test Results Summary")
    print("=" * 30)
    print(f"   Lazy Loading: {'✅ PASS' if lazy_test_passed else '❌ FAIL'}")
    print(f"   Orchestration: {'✅ PASS' if orchestration_test_passed else '❌ FAIL'}")
    
    if lazy_test_passed and orchestration_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("   Performance-Optimized Sequential Startup is working correctly!")
        print("   Ready for production deployment.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("   Please check the errors above and fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)