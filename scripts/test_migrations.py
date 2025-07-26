#!/usr/bin/env python3
"""Test script for the migration service.
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
        from lib.services.migration_service import (
            check_migration_status_async,
            ensure_database_ready_async,
        )

        # Check if database URL is configured
        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            return False

        # Check migration status
        await check_migration_status_async()

        # Test ensure database ready
        result = await ensure_database_ready_async()

        return bool(result["success"])

    except ImportError:
        return False
    except Exception:
        return False


if __name__ == "__main__":
    success = asyncio.run(test_migration_service())
    sys.exit(0 if success else 1)
