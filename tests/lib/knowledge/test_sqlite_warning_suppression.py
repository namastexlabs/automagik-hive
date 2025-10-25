"""Tests for SQLite warning suppression in knowledge base."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader


@pytest.fixture
def mock_sqlite_env():
    """Mock SQLite database URL."""
    with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///./data/test.db"}, clear=False):
        yield


@pytest.fixture
def mock_postgres_env():
    """Mock PostgreSQL database URL."""
    with patch.dict(os.environ, {"HIVE_DATABASE_URL": "postgresql://user:pass@localhost/db"}, clear=False):
        yield


class TestSQLiteDetection:
    """Test SQLite database detection."""

    def test_is_sqlite_with_sqlite_url(self, mock_sqlite_env):
        """Test _is_sqlite() returns True for SQLite URL."""
        with patch("lib.knowledge.smart_incremental_loader._load_config", return_value={}):
            loader = SmartIncrementalLoader()
            assert loader._is_sqlite() is True

    def test_is_sqlite_with_postgres_url(self, mock_postgres_env):
        """Test _is_sqlite() returns False for PostgreSQL URL."""
        with patch("lib.knowledge.smart_incremental_loader._load_config", return_value={}):
            loader = SmartIncrementalLoader()
            assert loader._is_sqlite() is False


class TestSQLiteWarningLevels:
    """Test warning level adjustment for SQLite."""

    def test_check_existing_hashes_uses_debug_for_sqlite(self, mock_sqlite_env):
        """Test that hash check errors use debug level for SQLite."""
        with patch("lib.knowledge.smart_incremental_loader._load_config", return_value={}):
            loader = SmartIncrementalLoader()

            with patch.object(loader, "_engine") as mock_engine:
                # Simulate database error
                mock_engine.return_value.connect.side_effect = Exception("Table does not exist")

                with patch("lib.knowledge.smart_incremental_loader.app_log.logger.debug") as mock_debug:
                    with patch("lib.knowledge.smart_incremental_loader.app_log.logger.warning") as mock_warning:
                        result = loader._check_existing_hashes()

                        # Should use debug, not warning for SQLite
                        assert mock_debug.called
                        assert not mock_warning.called
                        assert result == set()

    def test_check_existing_hashes_uses_warning_for_postgres(self, mock_postgres_env):
        """Test that hash check errors use warning level for PostgreSQL."""
        with patch("lib.knowledge.smart_incremental_loader._load_config", return_value={}):
            loader = SmartIncrementalLoader()

            with patch.object(loader, "_engine") as mock_engine:
                # Simulate database error
                mock_engine.return_value.connect.side_effect = Exception("Connection failed")

                with patch("lib.knowledge.smart_incremental_loader.app_log.logger.debug"):
                    with patch("lib.knowledge.smart_incremental_loader.app_log.logger.warning") as mock_warning:
                        result = loader._check_existing_hashes()

                        # Should use warning for PostgreSQL
                        assert mock_warning.called
                        assert result == set()

    def test_add_hash_column_uses_debug_for_sqlite(self, mock_sqlite_env):
        """Test that add hash column errors use debug level for SQLite."""
        with patch("lib.knowledge.smart_incremental_loader._load_config", return_value={}):
            loader = SmartIncrementalLoader()

            with patch.object(loader, "_engine") as mock_engine:
                # Simulate database error
                mock_engine.return_value.connect.side_effect = Exception("Schema error")

                with patch("lib.knowledge.smart_incremental_loader.app_log.logger.debug") as mock_debug:
                    with patch("lib.knowledge.smart_incremental_loader.app_log.logger.warning") as mock_warning:
                        result = loader._add_hash_column_to_table()

                        # Should use debug, not warning for SQLite
                        assert mock_debug.called
                        assert not mock_warning.called
                        assert result is False

    def test_update_row_hash_uses_debug_for_sqlite(self, mock_sqlite_env):
        """Test that update row hash errors use debug level for SQLite."""
        with patch("lib.knowledge.smart_incremental_loader._load_config", return_value={}):
            loader = SmartIncrementalLoader()
            loader.kb = MagicMock()

            with patch.object(loader, "_engine") as mock_engine:
                # Simulate database error
                mock_engine.return_value.connect.side_effect = Exception("Update failed")

                with patch("lib.knowledge.smart_incremental_loader.app_log.logger.debug") as mock_debug:
                    with patch("lib.knowledge.smart_incremental_loader.app_log.logger.warning") as mock_warning:
                        result = loader._update_row_hash_in_db("test_hash", "test_prefix")

                        # Should use debug, not warning for SQLite
                        assert mock_debug.called
                        assert not mock_warning.called
                        assert result is False


class TestRowBasedCSVWarnings:
    """Test warning suppression in row-based CSV knowledge."""

    def test_no_vector_db_uses_debug_for_sqlite(self, mock_sqlite_env):
        """Test that no vector db warning uses debug level for SQLite."""
        from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase

        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv", vector_db=None)

        with patch("lib.logging.logger.debug") as mock_debug:
            with patch("lib.logging.logger.warning") as mock_warning:
                kb.load(recreate=False)

                # Should use debug, not warning for SQLite
                assert mock_debug.called
                assert not mock_warning.called

    def test_no_vector_db_uses_warning_for_postgres(self, mock_postgres_env):
        """Test that no vector db warning uses warning level for PostgreSQL."""
        from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase

        kb = RowBasedCSVKnowledgeBase(csv_path="test.csv", vector_db=None)

        with patch("lib.logging.logger.debug"):
            with patch("lib.logging.logger.warning") as mock_warning:
                kb.load(recreate=False)

                # Should use warning for PostgreSQL
                assert mock_warning.called
