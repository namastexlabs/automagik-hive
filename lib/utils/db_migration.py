"""
Database Migration Utilities

Conditional Alembic migration support for startup initialization.
Only runs migrations if database schema is missing or outdated.
"""

import os
import asyncio
from pathlib import Path
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from lib.logging import logger


async def check_and_run_migrations() -> bool:
    """
    Check if database migrations are needed and run them if necessary.
    
    Returns:
        bool: True if migrations were run, False if not needed
    """
    try:
        # Get database URL
        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            logger.warning("HIVE_DATABASE_URL not set, skipping migration check")
            return False
        
        # Use the same URL format - SQLAlchemy will handle the driver
        sync_db_url = db_url
        
        # Check if database is accessible
        engine = create_engine(sync_db_url)
        
        try:
            with engine.connect() as conn:
                # Check if hive schema exists
                result = conn.execute(text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'hive'"
                ))
                schema_exists = result.fetchone() is not None
                
                if not schema_exists:
                    logger.info("Database schema missing, running migrations...")
                    return await _run_migrations()
                
                # Check if component_versions table exists
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'hive' AND table_name = 'component_versions'"
                ))
                table_exists = result.fetchone() is not None
                
                if not table_exists:
                    logger.info("Required tables missing, running migrations...")
                    return await _run_migrations()
                
                # Check if migrations are up to date
                migration_needed = _check_migration_status(conn)
                if migration_needed:
                    logger.info("Database schema outdated, running migrations...")
                    return await _run_migrations()
                
                logger.debug("Database schema up to date, skipping migrations")
                return False
                
        except OperationalError as e:
            logger.error("Database connection failed", error=str(e))
            return False
            
    except Exception as e:
        logger.error("Migration check failed", error=str(e))
        return False


def _check_migration_status(conn) -> bool:
    """Check if database schema needs migration updates."""
    try:
        # Get Alembic configuration
        alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
        alembic_cfg = Config(str(alembic_cfg_path))
        
        # Get current database revision (configure with hive schema)
        context = MigrationContext.configure(conn, opts={'version_table_schema': 'hive'})
        current_rev = context.get_current_revision()
        
        # Get script directory and head revision
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()
        
        # Migration needed if current != head
        migration_needed = current_rev != head_rev
        
        if migration_needed:
            logger.info("Migration status", 
                       current_revision=current_rev or "None", 
                       head_revision=head_rev)
        
        return migration_needed
        
    except Exception as e:
        logger.warning("Could not check migration status", error=str(e))
        # Assume migration needed if we can't determine status
        return True


async def _run_migrations() -> bool:
    """Run Alembic migrations in a separate thread."""
    try:
        # Run Alembic in a thread to avoid async conflicts
        import concurrent.futures
        
        def run_alembic():
            try:
                # Get Alembic configuration
                alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
                alembic_cfg = Config(str(alembic_cfg_path))
                
                # Run migration
                command.upgrade(alembic_cfg, "head")
                return True
            except Exception as e:
                logger.error("Alembic migration failed", error=str(e))
                return False
        
        # Run in thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_alembic)
            success = future.result(timeout=30)  # 30 second timeout
        
        if success:
            logger.info("Database migrations completed successfully")
        else:
            logger.error("Database migrations failed")
        
        return success
        
    except Exception as e:
        logger.error("Migration execution failed", error=str(e))
        return False


def run_migrations_sync() -> bool:
    """Synchronous wrapper for migration check and execution."""
    try:
        return asyncio.run(check_and_run_migrations())
    except RuntimeError:
        # Already in event loop, use thread-based execution
        import concurrent.futures
        
        def run_async():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(check_and_run_migrations())
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()