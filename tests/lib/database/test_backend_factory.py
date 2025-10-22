"""Tests for lib/database/backend_factory.py - Backend factory logic."""

import os
from unittest.mock import patch

import pytest


class TestBackendFactoryDetection:
    """Test automatic backend detection from database URLs."""

    def test_detect_pglite_from_url(self):
        """Test PgLite backend detection from URL scheme."""
        from lib.database.backend_factory import detect_backend_from_url

        url = "pglite://./data/test.db"
        backend_type = detect_backend_from_url(url)

        from lib.database import DatabaseBackendType

        assert backend_type == DatabaseBackendType.PGLITE

    def test_detect_postgresql_from_url(self):
        """Test PostgreSQL backend detection from URL scheme."""
        from lib.database.backend_factory import detect_backend_from_url

        url = "postgresql://user:pass@localhost:5432/test"
        backend_type = detect_backend_from_url(url)

        from lib.database import DatabaseBackendType

        assert backend_type == DatabaseBackendType.POSTGRESQL

    def test_detect_postgresql_with_psycopg(self):
        """Test PostgreSQL detection with +psycopg dialect."""
        from lib.database.backend_factory import detect_backend_from_url

        url = "postgresql+psycopg://user:pass@localhost:5432/test"
        backend_type = detect_backend_from_url(url)

        from lib.database import DatabaseBackendType

        assert backend_type == DatabaseBackendType.POSTGRESQL

    def test_detect_sqlite_from_url(self):
        """Test SQLite backend detection from URL scheme."""
        from lib.database.backend_factory import detect_backend_from_url

        url = "sqlite:///./test.db"
        backend_type = detect_backend_from_url(url)

        from lib.database import DatabaseBackendType

        assert backend_type == DatabaseBackendType.SQLITE

    def test_detect_invalid_url_raises_error(self):
        """Test that invalid URL raises appropriate error."""
        from lib.database.backend_factory import detect_backend_from_url

        with pytest.raises(ValueError, match="Unsupported database URL"):
            detect_backend_from_url("invalid://test")

    def test_detect_empty_url_raises_error(self):
        """Test that empty URL raises appropriate error."""
        from lib.database.backend_factory import detect_backend_from_url

        with pytest.raises((ValueError, TypeError)):
            detect_backend_from_url("")

    def test_detect_none_url_raises_error(self):
        """Test that None URL raises appropriate error."""
        from lib.database.backend_factory import detect_backend_from_url

        with pytest.raises((ValueError, TypeError)):
            detect_backend_from_url(None)


class TestBackendFactoryCreation:
    """Test backend instance creation via factory."""

    def test_create_pglite_backend(self, mock_env_vars):
        """Test creating PgLite backend instance."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import create_backend

        backend = create_backend(backend_type=DatabaseBackendType.PGLITE, db_url="pglite://./test.db")

        from lib.database.providers import PGliteBackend

        assert isinstance(backend, PGliteBackend)

    def test_create_postgresql_backend(self, mock_env_vars):
        """Test creating PostgreSQL backend instance."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import create_backend

        backend = create_backend(
            backend_type=DatabaseBackendType.POSTGRESQL,
            db_url="postgresql://user:pass@localhost/test",
        )

        from lib.database.providers import PostgreSQLBackend

        assert isinstance(backend, PostgreSQLBackend)

    def test_create_sqlite_backend(self, mock_env_vars):
        """Test creating SQLite backend instance."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import create_backend

        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///./test.db")

        from lib.database.providers import SQLiteBackend

        assert isinstance(backend, SQLiteBackend)

    def test_create_backend_with_pool_params(self, mock_env_vars):
        """Test creating backend with custom pool parameters."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import create_backend

        backend = create_backend(
            backend_type=DatabaseBackendType.SQLITE,
            db_url="sqlite:///./test.db",
            min_size=5,
            max_size=20,
        )

        assert backend.min_size == 5
        assert backend.max_size == 20

    def test_create_backend_invalid_type_raises_error(self, mock_env_vars):
        """Test that invalid backend type raises error."""
        from lib.database.backend_factory import create_backend

        with pytest.raises((ValueError, TypeError)):
            create_backend(backend_type="invalid", db_url="test://test")

    def test_create_backend_without_url_raises_error(self):
        """Test that missing URL raises error when no environment variable is set."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import create_backend

        # Ensure HIVE_DATABASE_URL is not in environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="HIVE_DATABASE_URL environment variable must be set"):
                create_backend(backend_type=DatabaseBackendType.SQLITE, db_url=None)


class TestGetDatabaseBackend:
    """Test get_database_backend main factory function."""

    def test_get_backend_from_settings_pglite(self):
        """Test getting PgLite backend from settings."""
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "pglite://./data/test.db",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import get_database_backend
            from lib.database.providers import PGliteBackend

            backend = get_database_backend()
            assert isinstance(backend, PGliteBackend)

    def test_get_backend_from_settings_postgresql(self):
        """Test getting PostgreSQL backend from settings."""
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import get_database_backend
            from lib.database.providers import PostgreSQLBackend

            backend = get_database_backend()
            assert isinstance(backend, PostgreSQLBackend)

    def test_get_backend_from_settings_sqlite(self):
        """Test getting SQLite backend from settings."""
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "sqlite:///./test.db",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import get_database_backend
            from lib.database.providers import SQLiteBackend

            backend = get_database_backend()
            assert isinstance(backend, SQLiteBackend)

    def test_get_backend_with_explicit_type_override(self):
        """Test get_database_backend with explicit type overrides settings."""
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import DatabaseBackendType, get_database_backend
            from lib.database.providers import SQLiteBackend

            # Override to SQLite despite settings having PostgreSQL
            backend = get_database_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///./test.db")
            assert isinstance(backend, SQLiteBackend)

    def test_get_backend_with_custom_pool_params(self):
        """Test get_database_backend with custom pool parameters."""
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "sqlite:///./test.db",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import get_database_backend

            backend = get_database_backend(min_size=3, max_size=15)
            assert backend.min_size == 3
            assert backend.max_size == 15

    def test_get_backend_returns_same_interface(self):
        """Test that all backends return same interface."""
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "sqlite:///./test.db",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import BaseDatabaseBackend, get_database_backend

            backend = get_database_backend()
            assert isinstance(backend, BaseDatabaseBackend)

            # Verify all required methods exist
            assert hasattr(backend, "initialize")
            assert hasattr(backend, "close")
            assert hasattr(backend, "get_connection")
            assert hasattr(backend, "execute")
            assert hasattr(backend, "fetch_one")
            assert hasattr(backend, "fetch_all")
            assert hasattr(backend, "execute_transaction")


class TestBackendFactoryEdgeCases:
    """Test edge cases and error handling in factory."""

    def test_backend_type_case_insensitive(self):
        """Test that backend type detection is case-insensitive."""
        from lib.database.backend_factory import detect_backend_from_url

        urls = [
            "PGLITE://./test.db",
            "PgLite://./test.db",
            "POSTGRESQL://localhost/test",
            "PostgreSQL://localhost/test",
            "SQLITE:///./test.db",
            "SQLite:///./test.db",
        ]

        for url in urls:
            # Should not raise error
            backend_type = detect_backend_from_url(url)
            assert backend_type is not None

    def test_url_with_query_parameters(self):
        """Test URL detection with query parameters."""
        from lib.database.backend_factory import detect_backend_from_url

        url = "postgresql://localhost/test?sslmode=require&connect_timeout=10"
        backend_type = detect_backend_from_url(url)

        from lib.database import DatabaseBackendType

        assert backend_type == DatabaseBackendType.POSTGRESQL

    def test_pglite_url_variations(self):
        """Test various PgLite URL formats."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import detect_backend_from_url

        urls = [
            "pglite://./test.db",
            "pglite:///absolute/path/test.db",
            "pglite://relative/path/test.db",
        ]

        for url in urls:
            backend_type = detect_backend_from_url(url)
            assert backend_type == DatabaseBackendType.PGLITE

    def test_postgresql_url_variations(self):
        """Test various PostgreSQL URL formats."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import detect_backend_from_url

        urls = [
            "postgresql://localhost/test",
            "postgresql://user@localhost/test",
            "postgresql://user:pass@localhost/test",
            "postgresql://user:pass@localhost:5432/test",
            "postgresql+psycopg://user:pass@localhost/test",
        ]

        for url in urls:
            backend_type = detect_backend_from_url(url)
            assert backend_type == DatabaseBackendType.POSTGRESQL

    def test_sqlite_url_variations(self):
        """Test various SQLite URL formats."""
        from lib.database import DatabaseBackendType
        from lib.database.backend_factory import detect_backend_from_url

        urls = [
            "sqlite:///./test.db",
            "sqlite:////absolute/path/test.db",
            "sqlite:///relative/path/test.db",
        ]

        for url in urls:
            backend_type = detect_backend_from_url(url)
            assert backend_type == DatabaseBackendType.SQLITE


class TestBackendFactoryIntegration:
    """Integration tests for backend factory."""

    @pytest.mark.asyncio
    async def test_created_backend_lifecycle(self, mock_env_vars):
        """Test full lifecycle of created backend."""
        from lib.database import DatabaseBackendType, get_database_backend

        # Use in-memory SQLite to avoid filesystem operations
        backend = get_database_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")

        # Should be able to initialize
        await backend.initialize()
        assert backend._initialized is True

        # Should be able to close
        await backend.close()
        assert backend._initialized is False

    @pytest.mark.asyncio
    async def test_backend_switching(self, mock_env_vars):
        """Test switching between different backend types."""
        from lib.database import DatabaseBackendType, get_database_backend

        # Create SQLite backend with in-memory database
        sqlite_backend = get_database_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await sqlite_backend.initialize()
        # SQLite doesn't have a pool attribute, check _initialized instead
        assert sqlite_backend._initialized is True
        await sqlite_backend.close()

        # Create another backend (simulating switch)
        sqlite_backend2 = get_database_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await sqlite_backend2.initialize()
        assert sqlite_backend2._initialized is True
        await sqlite_backend2.close()

    def test_multiple_backend_instances(self, mock_env_vars):
        """Test creating multiple backend instances."""
        from lib.database import DatabaseBackendType, get_database_backend

        # Create multiple backends
        backend1 = get_database_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///./test1.db")
        backend2 = get_database_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///./test2.db")

        # Should be different instances
        assert backend1 is not backend2
        assert backend1.db_url != backend2.db_url

    def test_backend_factory_respects_settings_changes(self):
        """Test that factory respects environment changes."""
        # First environment
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "sqlite:///./test1.db",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            from lib.database import get_database_backend

            backend1 = get_database_backend()
            assert "test1.db" in backend1.db_url

        # Second environment (simulating change)
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_URL": "sqlite:///./test2.db",
                "HIVE_ENVIRONMENT": "development",
                "HIVE_API_PORT": "8888",
                "HIVE_API_KEY": "hive_test_key_1234567890abcdef1234567890",
                "HIVE_CORS_ORIGINS": "http://localhost:3000",
            },
        ):
            # Force settings reload by calling get_settings with reload=True
            from lib.config.settings import get_settings

            get_settings(reload=True)

            from lib.database import get_database_backend

            backend2 = get_database_backend()
            assert "test2.db" in backend2.db_url
