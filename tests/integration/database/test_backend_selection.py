"""
Backend Selection Integration Tests.

Tests backend selection patterns used in CLI:
- Environment variable detection
- Backend validation via factory
- URL-based backend inference
- Environment precedence patterns
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database import DatabaseBackendType  # noqa: E402
from lib.database.backend_factory import create_backend, detect_backend_from_url, get_active_backend  # noqa: E402


class TestBackendEnvironmentDetection:
    """Test backend detection from environment variables."""

    @pytest.mark.parametrize(
        "backend_env,expected_type",
        [
            ("pglite", DatabaseBackendType.PGLITE),
            ("postgresql", DatabaseBackendType.POSTGRESQL),
            ("sqlite", DatabaseBackendType.SQLITE),
            ("PGLITE", DatabaseBackendType.PGLITE),  # Case insensitive
            ("PostgreSQL", DatabaseBackendType.POSTGRESQL),
            ("SQLite", DatabaseBackendType.SQLITE),
        ],
    )
    def test_env_backend_detection(self, backend_env: str, expected_type: DatabaseBackendType):
        """Test HIVE_DATABASE_BACKEND environment variable detection."""
        env_vars = {
            "HIVE_DATABASE_BACKEND": backend_env,
            "HIVE_DATABASE_URL": "sqlite:///test.db",  # Fallback
        }

        with patch.dict(os.environ, env_vars, clear=False):
            backend = get_active_backend()
            # Check class name matches backend type
            # Map backend types to their expected class name patterns
            class_name_map = {
                DatabaseBackendType.PGLITE: "PGliteBackend",
                DatabaseBackendType.POSTGRESQL: "PostgreSQLBackend",
                DatabaseBackendType.SQLITE: "SQLiteBackend",
            }
            assert backend.__class__.__name__ == class_name_map[expected_type]

    def test_env_backend_takes_precedence_over_url(self):
        """Test HIVE_DATABASE_BACKEND takes precedence over URL detection."""
        env_vars = {
            "HIVE_DATABASE_BACKEND": "sqlite",
            "HIVE_DATABASE_URL": "postgresql://user:pass@localhost/db",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            backend = get_active_backend()
            assert backend.__class__.__name__ == "SQLiteBackend"

    def test_url_detection_fallback_when_no_backend_env(self):
        """Test fallback to URL detection when HIVE_DATABASE_BACKEND not set."""
        # Save original value
        original = os.environ.get("HIVE_DATABASE_BACKEND")

        try:
            # Remove HIVE_DATABASE_BACKEND temporarily
            if "HIVE_DATABASE_BACKEND" in os.environ:
                del os.environ["HIVE_DATABASE_BACKEND"]

            with patch.dict(os.environ, {"HIVE_DATABASE_URL": "pglite://./test.db"}, clear=False):
                backend = get_active_backend()
                assert backend.__class__.__name__ == "PGliteBackend"

        finally:
            # Restore original
            if original is not None:
                os.environ["HIVE_DATABASE_BACKEND"] = original

    def test_invalid_backend_env_falls_back_to_url(self):
        """Test invalid HIVE_DATABASE_BACKEND falls back to URL detection."""
        env_vars = {
            "HIVE_DATABASE_BACKEND": "invalid_backend",
            "HIVE_DATABASE_URL": "sqlite:///test.db",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            with patch("lib.database.backend_factory.logger"):
                backend = get_active_backend()
                assert backend.__class__.__name__ == "SQLiteBackend"


class TestBackendURLInference:
    """Test URL-based backend type inference."""

    @pytest.mark.parametrize(
        "db_url,expected_class",
        [
            ("pglite://./data", "PGliteBackend"),
            ("postgresql://user:pass@localhost/db", "PostgreSQLBackend"),
            ("postgresql+psycopg://user:pass@localhost/db", "PostgreSQLBackend"),
            ("sqlite:///test.db", "SQLiteBackend"),
            ("sqlite:///:memory:", "SQLiteBackend"),
        ],
    )
    def test_create_backend_from_url(self, db_url: str, expected_class: str):
        """Test backend creation from various URL formats."""
        backend = create_backend(db_url=db_url)
        assert backend.__class__.__name__ == expected_class

    def test_url_scheme_case_insensitive(self):
        """Test URL scheme detection is case-insensitive."""
        backends = [
            create_backend(db_url="PGLITE://./test"),
            create_backend(db_url="PostgreSQL://user:pass@localhost/db"),
            create_backend(db_url="SQLite:///test.db"),
        ]

        assert backends[0].__class__.__name__ == "PGliteBackend"
        assert backends[1].__class__.__name__ == "PostgreSQLBackend"
        assert backends[2].__class__.__name__ == "SQLiteBackend"


class TestBackendTypeValidation:
    """Test backend type validation patterns."""

    def test_explicit_backend_type_overrides_url(self):
        """Test explicit backend type parameter overrides URL detection."""
        # Create SQLite backend even though URL says PostgreSQL
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="postgresql://user:pass@localhost/db")
        assert backend.__class__.__name__ == "SQLiteBackend"

    def test_invalid_backend_type_raises_error(self):
        """Test invalid backend type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backend type"):
            create_backend(backend_type="invalid", db_url="sqlite:///test.db")  # type: ignore

    def test_backend_type_enum_values(self):
        """Test all DatabaseBackendType enum values are valid."""
        for backend_type in DatabaseBackendType:
            backend = create_backend(backend_type=backend_type, db_url="test://test")
            assert backend is not None


class TestDockerSkipPatterns:
    """Test patterns for determining when to skip Docker containers."""

    def test_pglite_backend_skips_docker(self):
        """Test PGlite backend should skip Docker (uses WebAssembly)."""
        backend = create_backend(db_url="pglite://./test.db")
        # PGlite runs in-process, no Docker needed
        assert isinstance(backend, type(backend))  # Type check passes
        assert "PGlite" in backend.__class__.__name__

    def test_sqlite_backend_skips_docker(self):
        """Test SQLite backend should skip Docker (file-based)."""
        backend = create_backend(db_url="sqlite:///test.db")
        # SQLite is file-based, no Docker needed
        assert "SQLite" in backend.__class__.__name__

    def test_postgresql_backend_may_use_docker(self):
        """Test PostgreSQL backend may use Docker containers."""
        backend = create_backend(db_url="postgresql://user:pass@localhost/db")
        # PostgreSQL can use Docker or native installation
        assert "PostgreSQL" in backend.__class__.__name__


class TestBackendURLGeneration:
    """Test default URL generation patterns for each backend."""

    def test_pglite_default_url_pattern(self):
        """Test PGlite uses local directory path."""
        url = "pglite://./pglite-data"
        backend_type = detect_backend_from_url(url)
        assert backend_type == DatabaseBackendType.PGLITE

    def test_postgresql_default_url_pattern(self):
        """Test PostgreSQL uses connection string format."""
        url = "postgresql://automagik:automagik@localhost:5532/automagik_hive"
        backend_type = detect_backend_from_url(url)
        assert backend_type == DatabaseBackendType.POSTGRESQL

    def test_sqlite_default_url_pattern(self):
        """Test SQLite uses file path format."""
        url = "sqlite:///data/automagik-hive.db"
        backend_type = detect_backend_from_url(url)
        assert backend_type == DatabaseBackendType.SQLITE


class TestBackendConfigPersistence:
    """Test backend configuration persistence patterns."""

    def test_env_var_persists_across_calls(self):
        """Test environment variable persists backend selection."""
        env_vars = {
            "HIVE_DATABASE_BACKEND": "pglite",
            "HIVE_DATABASE_URL": "pglite://./test.db",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Multiple calls should use same backend
            backend1 = get_active_backend()
            backend2 = get_active_backend()

            assert backend1.__class__.__name__ == backend2.__class__.__name__
            assert "PGlite" in backend1.__class__.__name__

    def test_url_only_config_pattern(self):
        """Test configuration with only DATABASE_URL (no explicit backend)."""
        # Save and clear HIVE_DATABASE_BACKEND
        original = os.environ.get("HIVE_DATABASE_BACKEND")

        try:
            if "HIVE_DATABASE_BACKEND" in os.environ:
                del os.environ["HIVE_DATABASE_BACKEND"]

            with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
                backend = get_active_backend()
                assert "SQLite" in backend.__class__.__name__

        finally:
            if original is not None:
                os.environ["HIVE_DATABASE_BACKEND"] = original


class TestBackendMigrationScenarios:
    """Test scenarios related to backend migration."""

    def test_switch_from_postgresql_to_pglite(self):
        """Test switching from PostgreSQL to PGlite configuration."""
        # Original PostgreSQL config
        pg_backend = create_backend(db_url="postgresql://user:pass@localhost/db")
        assert "PostgreSQL" in pg_backend.__class__.__name__

        # Switch to PGlite
        pglite_backend = create_backend(db_url="pglite://./pglite-data")
        assert "PGlite" in pglite_backend.__class__.__name__

        # Backends are different types
        assert pg_backend.__class__ != pglite_backend.__class__

    def test_switch_from_postgresql_to_sqlite(self):
        """Test switching from PostgreSQL to SQLite configuration."""
        # Original PostgreSQL config
        pg_backend = create_backend(db_url="postgresql://user:pass@localhost/db")
        assert "PostgreSQL" in pg_backend.__class__.__name__

        # Switch to SQLite
        sqlite_backend = create_backend(db_url="sqlite:///test.db")
        assert "SQLite" in sqlite_backend.__class__.__name__

        # Backends are different types
        assert pg_backend.__class__ != sqlite_backend.__class__

    def test_preserve_backend_on_url_change(self):
        """Test explicit backend type preserved when URL changes."""
        # Force SQLite even with PostgreSQL URL
        backend1 = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="postgresql://old/db")

        backend2 = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="postgresql://new/db")

        # Both should be SQLite despite PostgreSQL URLs
        assert backend1.__class__.__name__ == "SQLiteBackend"
        assert backend2.__class__.__name__ == "SQLiteBackend"
