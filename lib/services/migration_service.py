"""
Database Migration Service for Hive Schema

Clean Alembic integration with psycopg3 and proper error handling.
Follows project patterns for logging, error handling, and async operations.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from lib.exceptions import ComponentLoadingError
from lib.logging import logger


class MigrationService:
    """
    Database migration service using Alembic.
    Integrates with existing psycopg3 patterns and logging.
    """

    def __init__(self, db_url: str | None = None):
        """Initialize migration service."""
        self.db_url = db_url or os.getenv("HIVE_DATABASE_URL")
        if not self.db_url:
            raise ValueError("HIVE_DATABASE_URL environment variable must be set")

        # Get project root and alembic config path
        project_root = Path(__file__).parent.parent.parent
        self.alembic_cfg_path = project_root / "alembic.ini"

        if not self.alembic_cfg_path.exists():
            raise ComponentLoadingError(
                f"Alembic config not found: {self.alembic_cfg_path}"
            )

    def _get_alembic_config(self) -> Config:
        """Get Alembic configuration with database URL."""
        cfg = Config(str(self.alembic_cfg_path))
        cfg.set_main_option("sqlalchemy.url", self.db_url)
        return cfg

    def _convert_to_sync_url(self, async_url: str) -> str:
        """Convert async psycopg URL to sync for Alembic compatibility."""
        if async_url.startswith("postgresql+psycopg://"):
            return async_url  # Keep psycopg3 dialect
        if async_url.startswith("postgresql://"):
            return async_url  # Already sync format
        # Handle other formats gracefully
        return async_url

    async def check_migration_status(self) -> dict[str, Any]:
        """Check current migration status asynchronously."""

        def _check_sync():
            try:
                cfg = self._get_alembic_config()
                script = ScriptDirectory.from_config(cfg)

                # Use synchronous connection for Alembic operations
                from sqlalchemy import create_engine

                # Convert async URL to sync for Alembic
                sync_url = self._convert_to_sync_url(self.db_url)
                engine = create_engine(sync_url)

                with engine.connect() as connection:
                    context = MigrationContext.configure(connection)

                    try:
                        current_rev = context.get_current_revision()
                    except Exception:
                        # Database is uninitialized - no alembic_version table exists
                        # This is expected for first-time setup
                        logger.info(
                            "Database uninitialized - no alembic_version table found"
                        )
                        current_rev = None

                    head_rev = script.get_current_head()

                    return {
                        "success": True,
                        "current_revision": current_rev,
                        "head_revision": head_rev,
                        "pending_upgrades": current_rev != head_rev,
                        "database_url_configured": bool(self.db_url),
                        "is_database_initialized": current_rev is not None,
                    }

            except Exception as e:
                logger.error("Migration status check failed", error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "database_url_configured": bool(self.db_url),
                }

        # Run synchronous Alembic operations in thread pool
        return await asyncio.get_event_loop().run_in_executor(None, _check_sync)

    async def run_migrations(self, target_revision: str = "head") -> dict[str, Any]:
        """Run migrations asynchronously."""

        def _migrate_sync():
            try:
                cfg = self._get_alembic_config()

                # Run migrations
                logger.info("Executing Alembic upgrade command", target=target_revision)
                command.upgrade(cfg, target_revision)

                # Get final status
                ScriptDirectory.from_config(cfg)
                from sqlalchemy import create_engine

                sync_url = self._convert_to_sync_url(self.db_url)
                engine = create_engine(sync_url)

                with engine.connect() as connection:
                    context = MigrationContext.configure(connection)
                    final_rev = context.get_current_revision()

                    return {
                        "success": True,
                        "final_revision": final_rev,
                        "target_revision": target_revision,
                        "migrations_applied": True,
                    }

            except Exception as e:
                logger.error(
                    "Migration execution failed",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "migrations_applied": False,
                }

        try:
            logger.info("Starting database migrations", target=target_revision)
            result = await asyncio.get_event_loop().run_in_executor(None, _migrate_sync)

            if result["success"]:
                logger.info(
                    "Database migrations completed successfully",
                    revision=result["final_revision"],
                )
            else:
                logger.error("Database migration failed", error=result.get("error"))

            return result

        except Exception as e:
            logger.error(
                "Migration service error", error=str(e), error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "migrations_applied": False,
            }

    async def ensure_database_ready(self) -> dict[str, Any]:
        """Ensure database is ready by checking and running migrations if needed."""
        try:
            # First check current status
            status = await self.check_migration_status()

            if not status["success"]:
                return {
                    "success": False,
                    "message": "Failed to check migration status",
                    "details": status,
                }

            # If no migrations needed, we're done
            if not status.get("pending_upgrades", True) and status.get(
                "is_database_initialized", False
            ):
                logger.info(
                    "Database schema is up-to-date",
                    revision=status.get("current_revision"),
                )
                return {
                    "success": True,
                    "message": "Database schema up-to-date",
                    "action": "none_required",
                    "current_revision": status.get("current_revision"),
                }

            # Run migrations
            migration_result = await self.run_migrations()

            return {
                "success": migration_result["success"],
                "message": "Database migrations completed"
                if migration_result["success"]
                else "Database migrations failed",
                "action": "migrations_applied"
                if migration_result["success"]
                else "migrations_failed",
                "details": migration_result,
            }

        except Exception as e:
            logger.error(
                "Database readiness check failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Database readiness check failed: {e!s}",
                "action": "error",
                "error": str(e),
            }


# Global service instance for consistency with other services
_migration_service: MigrationService | None = None


async def get_migration_service() -> MigrationService:
    """Get or create global migration service instance."""
    global _migration_service
    if _migration_service is None:
        _migration_service = MigrationService()
    return _migration_service


async def run_migrations_async(target_revision: str = "head") -> dict[str, Any]:
    """Convenience function for startup integration."""
    service = await get_migration_service()
    return await service.run_migrations(target_revision)


async def check_migration_status_async() -> dict[str, Any]:
    """Convenience function to check migration status."""
    service = await get_migration_service()
    return await service.check_migration_status()


async def ensure_database_ready_async() -> dict[str, Any]:
    """Convenience function to ensure database is ready for use."""
    service = await get_migration_service()
    return await service.ensure_database_ready()
