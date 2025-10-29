"""Tests for lib/database/providers/__init__.py - Provider exports."""


class TestProviderModuleExports:
    """Test that providers module exports backend implementations."""

    def test_postgresql_backend_exported(self):
        """Test that PostgreSQLBackend class is exported."""
        from lib.database.providers import PostgreSQLBackend

        assert PostgreSQLBackend is not None

    def test_sqlite_backend_exported(self):
        """Test that SQLiteBackend class is exported."""
        from lib.database.providers import SQLiteBackend

        assert SQLiteBackend is not None

    def test_all_backends_implement_base(self):
        """Test that all backend implementations inherit from base."""
        from lib.database import BaseDatabaseBackend
        from lib.database.providers import (
            PostgreSQLBackend,
            SQLiteBackend,
        )

        assert issubclass(PostgreSQLBackend, BaseDatabaseBackend)
        assert issubclass(SQLiteBackend, BaseDatabaseBackend)

    def test_module_has_all_attribute(self):
        """Test that providers module has __all__ export list."""
        import lib.database.providers

        assert hasattr(lib.database.providers, "__all__")
        assert "PostgreSQLBackend" in lib.database.providers.__all__
        assert "SQLiteBackend" in lib.database.providers.__all__


class TestProviderBackendInstantiation:
    """Test that provider backends can be instantiated."""

    def test_postgresql_backend_instantiation(self, mock_env_vars):
        """Test PostgreSQLBackend can be instantiated."""
        from lib.database.providers import PostgreSQLBackend

        # Should accept database URL
        backend = PostgreSQLBackend(db_url="postgresql://user:pass@localhost:5432/test")
        assert backend is not None

    def test_sqlite_backend_instantiation(self, mock_env_vars):
        """Test SQLiteBackend can be instantiated."""
        from lib.database.providers import SQLiteBackend

        # Should accept database URL
        backend = SQLiteBackend(db_url="sqlite:///./test.db")
        assert backend is not None

    def test_backends_accept_pool_parameters(self, mock_env_vars):
        """Test that backends accept connection pool parameters."""
        from lib.database.providers import (
            PostgreSQLBackend,
            SQLiteBackend,
        )

        # PostgreSQL
        postgres = PostgreSQLBackend(db_url="postgresql://user:pass@localhost/test", min_size=2, max_size=10)
        assert postgres is not None

        # SQLite
        sqlite = SQLiteBackend(db_url="sqlite:///./test.db", min_size=1, max_size=5)
        assert sqlite is not None


class TestProviderBackendEnvironmentDetection:
    """Test environment-based backend detection."""

    def test_detect_postgresql_from_url(self):
        """Test detection of PostgreSQL from URL scheme."""
        from lib.database.providers import PostgreSQLBackend

        # URL starting with postgresql:// should be detected
        url = "postgresql://user:pass@localhost:5432/test"
        backend = PostgreSQLBackend(db_url=url)
        assert "postgresql://" in backend.db_url

    def test_detect_sqlite_from_url(self):
        """Test detection of SQLite from URL scheme."""
        from lib.database.providers import SQLiteBackend

        # URL starting with sqlite:// should be detected
        url = "sqlite:///./test.db"
        backend = SQLiteBackend(db_url=url)
        assert backend.db_url.startswith("sqlite://")

    def test_backend_url_normalization(self):
        """Test that backends normalize URLs correctly."""
        from lib.database.providers import (
            PostgreSQLBackend,
            SQLiteBackend,
        )

        # PostgreSQL should strip +psycopg if present
        postgres = PostgreSQLBackend(db_url="postgresql+psycopg://user:pass@localhost/test")
        assert "+psycopg" not in postgres.db_url or "postgresql://" in postgres.db_url

        # SQLite should handle file paths
        sqlite = SQLiteBackend(db_url="sqlite:///./test.db")
        assert sqlite.db_url is not None
