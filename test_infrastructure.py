#!/usr/bin/env python3
"""
Test script to verify PagBank infrastructure modernization.
Tests API, database, agent registry, and workspace patterns.
"""

import sys
from pathlib import Path

def test_api_structure():
    """Test FastAPI structure with modern patterns."""
    print("🧪 Testing API structure...")
    try:
        from api.main import app
        from api.settings import api_settings
        from api.routes.health import get_health
        
        # Test basic app creation
        assert app is not None
        assert api_settings.title == "PagBank Multi-Agent System"
        
        # Test health endpoint
        health_response = get_health()
        assert health_response["status"] == "success"
        assert "PagBank" in health_response["service"]
        
        print("✅ API structure: PASSED")
        return True
    except Exception as e:
        print(f"❌ API structure: FAILED - {e}")
        return False

def test_database_infrastructure():
    """Test database infrastructure with modern patterns."""
    print("🧪 Testing database infrastructure...")
    try:
        from db.session import db_engine, get_db, init_database
        from db.settings import db_settings
        
        # Test settings
        assert db_settings is not None
        db_url = db_settings.get_db_url()
        assert "sqlite" in db_url or "postgresql" in db_url
        
        # Test session creation
        db_gen = get_db()
        db_session = next(db_gen)
        assert db_session is not None
        db_session.close()
        
        # Test initialization
        init_database()
        
        print("✅ Database infrastructure: PASSED")
        return True
    except Exception as e:
        print(f"❌ Database infrastructure: FAILED - {e}")
        return False

def test_agent_registry():
    """Test agent registry with generic factory pattern."""
    print("🧪 Testing agent registry...")
    try:
        from agents.registry import AgentRegistry, get_agent
        from agents.settings import agent_settings
        
        # Test settings
        assert agent_settings is not None
        assert agent_settings.default_language == "pt-BR"
        
        # Test registry methods
        available_agents = AgentRegistry.list_available_agents()
        assert len(available_agents) > 0
        
        print("✅ Agent registry: PASSED")
        return True
    except Exception as e:
        print(f"❌ Agent registry: FAILED - {e}")
        return False

def test_workspace_pattern():
    """Test workspace development patterns."""
    print("🧪 Testing workspace patterns...")
    try:
        from workspace.settings import WS_NAME, WS_ROOT, DEV_ENV
        from workspace.dev_resources import dev_db, dev_fastapi
        
        # Test workspace settings
        assert WS_NAME == "pagbank-multiagents"
        assert DEV_ENV == "dev"
        assert WS_ROOT.exists()
        
        # Test development resources
        assert dev_db.name.endswith("-dev-db")
        assert dev_fastapi.name.endswith("-dev")
        
        print("✅ Workspace patterns: PASSED")
        return True
    except Exception as e:
        print(f"❌ Workspace patterns: FAILED - {e}")
        return False

def test_utility_functions():
    """Test utility functions."""
    print("🧪 Testing utility functions...")
    try:
        from utils.log import logger
        from utils.dttm import current_utc, current_utc_str
        
        # Test logging
        assert logger.name == "pagbank-multiagents"
        
        # Test datetime utils
        utc_time = current_utc()
        utc_str = current_utc_str()
        assert utc_time is not None
        assert len(utc_str) > 10
        
        print("✅ Utility functions: PASSED")
        return True
    except Exception as e:
        print(f"❌ Utility functions: FAILED - {e}")
        return False

def test_migration_setup():
    """Test migration setup."""
    print("🧪 Testing migration setup...")
    try:
        from pathlib import Path
        
        # Check migration files exist
        db_path = Path("db")
        assert (db_path / "alembic.ini").exists()
        assert (db_path / "migrations" / "env.py").exists()
        assert (db_path / "migrations" / "script.py.mako").exists()
        
        print("✅ Migration setup: PASSED")
        return True
    except Exception as e:
        print(f"❌ Migration setup: FAILED - {e}")
        return False

def main():
    """Run all infrastructure tests."""
    print("🚀 PagBank Infrastructure Modernization Test Suite")
    print("=" * 60)
    
    tests = [
        test_api_structure,
        test_database_infrastructure,
        test_agent_registry,
        test_workspace_pattern,
        test_utility_functions,
        test_migration_setup,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: CRITICAL FAILURE - {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} PASSED, {failed} FAILED")
    
    if failed == 0:
        print("🎉 All infrastructure tests PASSED!")
        print("✅ PagBank infrastructure successfully modernized with agno-demo-app patterns")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the infrastructure setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())