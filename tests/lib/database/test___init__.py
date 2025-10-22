"""Tests for lib/database/__init__.py - Backend factory exports."""

import pytest


class TestDatabaseModuleExports:
    """Test that database module exports the correct interface."""

    def test_get_database_backend_exported(self):
        """Test that get_database_backend function is exported."""
        from lib.database import get_database_backend

        assert callable(get_database_backend)

    def test_base_database_backend_exported(self):
        """Test that BaseDatabaseBackend class is exported."""
        from lib.database import BaseDatabaseBackend

        assert BaseDatabaseBackend is not None
        # Verify it's an abstract base class
        import inspect

        assert inspect.isabstract(BaseDatabaseBackend)

    def test_database_backend_type_exported(self):
        """Test that DatabaseBackendType enum is exported."""
        from lib.database import DatabaseBackendType

        assert hasattr(DatabaseBackendType, "PGLITE")
        assert hasattr(DatabaseBackendType, "POSTGRESQL")
        assert hasattr(DatabaseBackendType, "SQLITE")

    def test_module_docstring_exists(self):
        """Test that module has proper documentation."""
        import lib.database

        assert lib.database.__doc__ is not None
        assert len(lib.database.__doc__) > 0
        assert "database backend" in lib.database.__doc__.lower()


class TestBackendFactoryImports:
    """Test backend factory can be imported and used."""

    def test_get_database_backend_signature(self):
        """Test get_database_backend has correct signature."""
        import inspect

        from lib.database import get_database_backend

        sig = inspect.signature(get_database_backend)
        params = list(sig.parameters.keys())

        # Should accept optional backend_type parameter
        assert "backend_type" in params or len(params) == 0

    def test_provider_submodule_accessible(self):
        """Test that providers submodule is accessible."""
        from lib.database import providers

        assert providers is not None
        assert hasattr(providers, "__path__")  # It's a package

    def test_backend_type_enum_values(self):
        """Test DatabaseBackendType enum has expected values."""
        from lib.database import DatabaseBackendType

        # Test enum members exist
        assert "PGLITE" in DatabaseBackendType.__members__
        assert "POSTGRESQL" in DatabaseBackendType.__members__
        assert "SQLITE" in DatabaseBackendType.__members__

        # Test enum values are strings
        assert isinstance(DatabaseBackendType.PGLITE.value, str)
        assert isinstance(DatabaseBackendType.POSTGRESQL.value, str)
        assert isinstance(DatabaseBackendType.SQLITE.value, str)


class TestBackendFactoryDefaultBehavior:
    """Test default backend selection behavior."""

    def test_get_backend_without_args_uses_settings(self, mock_env_vars):
        """Test that get_database_backend uses settings when no args provided."""
        from lib.database import get_database_backend

        # Should not raise error and return a backend instance
        backend = get_database_backend()
        assert backend is not None

    def test_get_backend_with_explicit_type(self, mock_env_vars):
        """Test get_database_backend with explicit backend type."""
        from lib.database import DatabaseBackendType, get_database_backend

        backend = get_database_backend(backend_type=DatabaseBackendType.SQLITE)
        assert backend is not None

    def test_get_backend_returns_base_interface(self, mock_env_vars):
        """Test that returned backend implements BaseDatabaseBackend."""
        from lib.database import BaseDatabaseBackend, get_database_backend

        backend = get_database_backend()
        assert isinstance(backend, BaseDatabaseBackend)

    def test_get_backend_invalid_type_raises_error(self, mock_env_vars):
        """Test that invalid backend type raises appropriate error."""
        from lib.database import get_database_backend

        with pytest.raises((ValueError, TypeError)):
            get_database_backend(backend_type="invalid_type")
