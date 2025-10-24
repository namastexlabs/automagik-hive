"""Tests for SQLite warning suppression in database migrations."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_sqlite_env():
    """Mock SQLite database URL."""
    with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///./data/test.db"}, clear=False):
        yield


@pytest.fixture
def mock_postgres_env():
    """Mock PostgreSQL database URL."""
    with patch.dict(os.environ, {"HIVE_DATABASE_URL": "postgresql://user:pass@localhost:5432/db"}, clear=False):
        yield


class TestSQLiteMigrationWarnings:
    """Test SQLite-specific migration warning suppression."""

    @pytest.mark.asyncio
    async def test_unable_to_open_database_file_suppressed_for_sqlite(self, mock_sqlite_env):
        """Test that 'unable to open database file' error is suppressed for SQLite."""
        from lib.utils.db_migration import check_and_run_migrations

        with patch("lib.utils.db_migration.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Simulate SQLite database file not existing yet
            mock_engine.connect.side_effect = OperationalError(
                "unable to open database file", None, None
            )

            with patch("lib.logging.logger.error") as mock_error:
                with patch("lib.logging.logger.debug") as mock_debug:
                    result = await check_and_run_migrations()

                    # Should use debug, not error for SQLite
                    assert mock_debug.called
                    assert not mock_error.called
                    assert result is False

    @pytest.mark.asyncio
    async def test_no_such_table_suppressed_for_sqlite(self, mock_sqlite_env):
        """Test that 'no such table' error is suppressed for SQLite."""
        from lib.utils.db_migration import check_and_run_migrations

        with patch("lib.utils.db_migration.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Simulate table doesn't exist yet
            mock_engine.connect.side_effect = OperationalError("no such table: alembic_version", None, None)

            with patch("lib.logging.logger.error") as mock_error:
                with patch("lib.logging.logger.debug") as mock_debug:
                    result = await check_and_run_migrations()

                    # Should use debug, not error for SQLite
                    assert mock_debug.called
                    assert not mock_error.called
                    assert result is False

    @pytest.mark.asyncio
    async def test_postgres_errors_still_logged(self, mock_postgres_env):
        """Test that PostgreSQL errors are still logged as errors."""
        from lib.utils.db_migration import check_and_run_migrations

        with patch("lib.utils.db_migration.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Simulate PostgreSQL connection error
            mock_engine.connect.side_effect = OperationalError(
                "could not connect to server: Connection refused", None, None
            )

            with patch("lib.logging.logger.error") as mock_error:
                with patch("lib.logging.logger.debug") as mock_debug:
                    result = await check_and_run_migrations()

                    # Should use error for PostgreSQL
                    assert mock_error.called
                    assert result is False

    @pytest.mark.asyncio
    async def test_password_authentication_errors_still_logged(self, mock_postgres_env):
        """Test that password authentication errors are logged for any database."""
        from lib.utils.db_migration import check_and_run_migrations

        with patch("lib.utils.db_migration.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            # Simulate auth failure
            mock_engine.connect.side_effect = OperationalError(
                "password authentication failed for user", None, None
            )

            with patch("lib.logging.logger.error") as mock_error:
                result = await check_and_run_migrations()

                # Should always log auth errors
                assert mock_error.called
                assert result is False
