#!/usr/bin/env python3
"""
Test script for the migration service.
Verifies automatic migration functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_migration_service():
    """Test the migration service functionality."""
    try:
        # Test import
        from lib.services.migration_service import ensure_database_ready_async, check_migration_status_async
        
        print("🔧 Testing migration service...")
        
        # Check if database URL is configured
        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            print("❌ HIVE_DATABASE_URL not set")
            return False
        
        print(f"✅ Database URL configured: {db_url.split('@')[0]}@***")
        
        # Check migration status
        status = await check_migration_status_async()
        print(f"🔍 Migration Status Check: {status}")
        
        # Test ensure database ready
        result = await ensure_database_ready_async()
        print(f"🚀 Ensure Database Ready: {result}")
        
        if result["success"]:
            print("✅ Migration service working correctly!")
            return True
        else:
            print(f"❌ Migration service failed: {result.get('message')}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_migration_service())
    sys.exit(0 if success else 1)