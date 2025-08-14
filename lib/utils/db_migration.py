"""
Database Migration Utilities

Conditional Alembic migration support for startup initialization.
Only runs migrations if database schema is missing or outdated.
"""

import asyncio
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from lib.logging import logger


def _find_alembic_config() -> Path:
    """
    Find alembic.ini with UVX-aware path resolution.

    In UVX environments, __file__ points to the installed package
    location, not the workspace directory. This function implements multiple
    strategies to locate alembic.ini in the correct location.

    Returns:
        Path: Path to alembic.ini file

    Raises:
        FileNotFoundError: If alembic.ini cannot be found
    """
    # Strategy 1: Try current working directory (UVX workspace context)
    cwd_config = Path.cwd() / "alembic.ini"
    if cwd_config.exists():
        logger.debug(f"Found alembic.ini in workspace: {cwd_config}")
        return cwd_config

    # Strategy 2: Try relative to this file (development context)
    dev_config = Path(__file__).parent.parent.parent / "alembic.ini"
    if dev_config.exists():
        logger.debug(f"Found alembic.ini in development: {dev_config}")
        return dev_config

    # Strategy 3: Search upward from current directory
    current_path = Path.cwd()
    while current_path != current_path.parent:
        alembic_ini = current_path / "alembic.ini"
        if alembic_ini.exists():
            logger.debug(f"Found alembic.ini via upward search: {alembic_ini}")
            return alembic_ini
        current_path = current_path.parent

    # Strategy 4: Search common locations where workspace might be
    common_locations = [
        Path.home() / "workspace",
        Path("/tmp"),
        Path("/workspace"),  # Docker context
    ]

    for base_path in common_locations:
        if base_path.exists():
            for potential_workspace in base_path.glob("*/alembic.ini"):
                if potential_workspace.exists():
                    logger.debug(
                        f"Found alembic.ini in common location: {potential_workspace}"
                    )
                    return potential_workspace

    # If all strategies fail, provide helpful error message
    raise FileNotFoundError(
        "Could not locate alembic.ini file. This is required for database migrations.\n"
        f"Searched locations:\n"
        f"  - Current directory: {Path.cwd() / 'alembic.ini'}\n"
        f"  - Development path: {Path(__file__).parent.parent.parent / 'alembic.ini'}\n"
        f"  - Upward search from: {Path.cwd()}\n"
        "For UVX workspaces, ensure you're running from a directory that contains alembic.ini"
    )


def _ensure_environment_loaded():
    """
    Ensure environment variables are loaded consistently across all environments.

    This function handles UVX environments where working directory
    differs from development, preventing .env file loading issues.
    """
    try:
        from dotenv import load_dotenv

        # Try to find and load environment files using multiple strategies
        current_dir = Path(__file__).parent

        # Strategy 1: Look in project root (go up to find project root)
        project_root = current_dir
        while project_root.parent != project_root:
            env_file = project_root / ".env"

            if env_file.exists():
                load_dotenv(dotenv_path=env_file)
                logger.debug(f"Loaded environment from {env_file}")
                return

            # Look for pyproject.toml as project root indicator
            if (project_root / "pyproject.toml").exists():
                break

            project_root = project_root.parent

        # Strategy 2: Try loading from current working directory (fallback)
        load_dotenv()
        logger.debug("Using default dotenv loading (CWD-based)")

    except ImportError:
        logger.debug("python-dotenv not available, using system environment variables")
    except Exception as e:
        logger.warning(f"Environment loading failed: {e}")


async def check_and_run_migrations() -> bool:
    """
    Check if database migrations are needed and run them if necessary.

    Ensures consistent environment loading across all environments.

    Returns:
        bool: True if migrations were run, False if not needed
    """
    try:
        # Ensure environment variables are loaded before migration check
        # This handles UVX environments where .env may not be auto-loaded
        _ensure_environment_loaded()

        # Get database URL
        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            logger.warning(
                "HIVE_DATABASE_URL not set, skipping migration check. "
                "This may indicate environment loading issues in UVX environments."
            )
            return False

        # Use the same URL format - SQLAlchemy will handle the driver
        sync_db_url = db_url

        # Check if database is accessible
        engine = create_engine(sync_db_url)

        try:
            with engine.connect() as conn:
                # Check if hive schema exists
                result = conn.execute(
                    text(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'hive'"
                    )
                )
                schema_exists = result.fetchone() is not None

                if not schema_exists:
                    logger.info("Database schema missing, running migrations...")
                    return await _run_migrations()

                # Check if component_versions table exists
                result = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'hive' AND table_name = 'component_versions'"
                    )
                )
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
            error_str = str(e)
            logger.error("🚨 Database connection failed", error=error_str)

            # Provide specific guidance based on error type
            if "password authentication failed" in error_str:
                logger.error("❌ CRITICAL: Database authentication failed!")
                logger.error(
                    "📝 ACTION REQUIRED: Check your database credentials in .env files"
                )
                logger.error("🔧 Steps to fix:")
                logger.error("   1. Verify HIVE_DATABASE_URL in .env file")
                logger.error("   2. Ensure PostgreSQL is running on the specified port")
                logger.error("   3. Confirm username/password are correct")
                logger.error("   4. Test connection: psql 'your-database-url-here'")
            elif (
                "Connection refused" in error_str
                or "could not connect to server" in error_str
            ):
                logger.error("❌ CRITICAL: Database server is not accessible!")
                logger.error("📝 ACTION REQUIRED: Start your PostgreSQL database")
                logger.error("🔧 Steps to fix:")
                logger.error(
                    "   1. Start PostgreSQL: 'make agent' should start postgres automatically"
                )
                logger.error("   2. Check if postgres is running: 'make agent-status'")
                logger.error(
                    "   3. Verify DATABASE_URL port matches your postgres instance"
                )
            else:
                logger.error("❌ CRITICAL: Database connection error!")
                logger.error("📝 ACTION REQUIRED: Fix database configuration")
                logger.error("🔧 Check your HIVE_DATABASE_URL in .env files")

            logger.error("🛑 Startup cannot continue without database access")
            return False

    except Exception as e:
        logger.error("Migration check failed", error=str(e))
        return False


def _check_migration_status(conn) -> bool:
    """Check if database schema needs migration updates."""
    try:
        # Get Alembic configuration with UVX-aware path resolution
        alembic_cfg_path = _find_alembic_config()
        alembic_cfg = Config(str(alembic_cfg_path))

        # Get current database revision (configure with hive schema)
        context = MigrationContext.configure(
            conn, opts={"version_table_schema": "hive"}
        )
        current_rev = context.get_current_revision()

        # Get script directory and head revision
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()

        # Migration needed if current != head
        migration_needed = current_rev != head_rev

        if migration_needed:
            logger.info(
                "Migration status",
                current_revision=current_rev or "None",
                head_revision=head_rev,
            )

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
                # Get Alembic configuration with UVX-aware path resolution
                alembic_cfg_path = _find_alembic_config()
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
