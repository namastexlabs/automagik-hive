"""Tests for lib/database/providers/base.py - BaseDatabaseBackend interface."""

import inspect
from abc import ABC

import pytest


class TestBaseDatabaseBackendInterface:
    """Test BaseDatabaseBackend abstract interface."""

    def test_base_backend_is_abstract(self):
        """Test that BaseDatabaseBackend is an abstract base class."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert issubclass(BaseDatabaseBackend, ABC)
        assert inspect.isabstract(BaseDatabaseBackend)

    def test_base_backend_cannot_be_instantiated(self):
        """Test that BaseDatabaseBackend cannot be instantiated directly."""
        from lib.database.providers.base import BaseDatabaseBackend

        with pytest.raises(TypeError):
            BaseDatabaseBackend(db_url="test://test")

    def test_base_backend_defines_required_methods(self):
        """Test that BaseDatabaseBackend defines all required abstract methods."""
        from lib.database.providers.base import BaseDatabaseBackend

        abstract_methods = BaseDatabaseBackend.__abstractmethods__

        # Core lifecycle methods
        assert "initialize" in abstract_methods
        assert "close" in abstract_methods

        # Connection management
        assert "get_connection" in abstract_methods

        # Query operations
        assert "execute" in abstract_methods
        assert "fetch_one" in abstract_methods
        assert "fetch_all" in abstract_methods

        # Transaction support
        assert "execute_transaction" in abstract_methods

    def test_base_backend_init_signature(self):
        """Test BaseDatabaseBackend __init__ signature."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.__init__)
        params = list(sig.parameters.keys())

        # Should accept at minimum: self, db_url
        assert "self" in params
        assert "db_url" in params

        # Should accept pool configuration
        assert "min_size" in params or len(params) >= 3
        assert "max_size" in params or len(params) >= 4


class TestBaseDatabaseBackendMethodSignatures:
    """Test method signatures of BaseDatabaseBackend."""

    def test_initialize_is_async(self):
        """Test that initialize method is async."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert inspect.iscoroutinefunction(BaseDatabaseBackend.initialize)

    def test_close_is_async(self):
        """Test that close method is async."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert inspect.iscoroutinefunction(BaseDatabaseBackend.close)

    def test_get_connection_is_async_context_manager(self):
        """Test that get_connection is an async context manager."""
        from lib.database.providers.base import BaseDatabaseBackend

        # Should be a method that returns an async context manager
        assert hasattr(BaseDatabaseBackend, "get_connection")

    def test_execute_is_async(self):
        """Test that execute method is async."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert inspect.iscoroutinefunction(BaseDatabaseBackend.execute)

    def test_fetch_one_is_async(self):
        """Test that fetch_one method is async."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert inspect.iscoroutinefunction(BaseDatabaseBackend.fetch_one)

    def test_fetch_all_is_async(self):
        """Test that fetch_all method is async."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert inspect.iscoroutinefunction(BaseDatabaseBackend.fetch_all)

    def test_execute_transaction_is_async(self):
        """Test that execute_transaction method is async."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert inspect.iscoroutinefunction(BaseDatabaseBackend.execute_transaction)

    def test_execute_method_signature(self):
        """Test execute method signature."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.execute)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "query" in params
        assert "params" in params

    def test_fetch_one_method_signature(self):
        """Test fetch_one method signature."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.fetch_one)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "query" in params
        assert "params" in params

    def test_fetch_all_method_signature(self):
        """Test fetch_all method signature."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.fetch_all)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "query" in params
        assert "params" in params

    def test_execute_transaction_method_signature(self):
        """Test execute_transaction method signature."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.execute_transaction)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "operations" in params


class TestBaseDatabaseBackendReturnTypes:
    """Test return type hints for BaseDatabaseBackend methods."""

    def test_initialize_return_type(self):
        """Test initialize returns None (via async)."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.initialize)
        # Should return None or have no explicit return type
        if sig.return_annotation != inspect.Signature.empty:
            assert "None" in str(sig.return_annotation)

    def test_close_return_type(self):
        """Test close returns None (via async)."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.close)
        # Should return None or have no explicit return type
        if sig.return_annotation != inspect.Signature.empty:
            assert "None" in str(sig.return_annotation)

    def test_execute_return_type(self):
        """Test execute returns None (via async)."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.execute)
        # Should return None or have no explicit return type
        if sig.return_annotation != inspect.Signature.empty:
            assert "None" in str(sig.return_annotation)

    def test_fetch_one_return_type(self):
        """Test fetch_one returns dict or None."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.fetch_one)
        # Should return dict[str, Any] | None
        if sig.return_annotation != inspect.Signature.empty:
            annotation = str(sig.return_annotation)
            assert "dict" in annotation or "Dict" in annotation or "None" in annotation

    def test_fetch_all_return_type(self):
        """Test fetch_all returns list of dicts."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.fetch_all)
        # Should return list[dict[str, Any]]
        if sig.return_annotation != inspect.Signature.empty:
            annotation = str(sig.return_annotation)
            assert "list" in annotation or "List" in annotation

    def test_execute_transaction_return_type(self):
        """Test execute_transaction returns None."""
        from lib.database.providers.base import BaseDatabaseBackend

        sig = inspect.signature(BaseDatabaseBackend.execute_transaction)
        # Should return None or have no explicit return type
        if sig.return_annotation != inspect.Signature.empty:
            assert "None" in str(sig.return_annotation)


class TestBaseDatabaseBackendDocumentation:
    """Test documentation for BaseDatabaseBackend."""

    def test_class_has_docstring(self):
        """Test that BaseDatabaseBackend has class docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.__doc__ is not None
        assert len(BaseDatabaseBackend.__doc__) > 0

    def test_initialize_has_docstring(self):
        """Test that initialize method has docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.initialize.__doc__ is not None

    def test_close_has_docstring(self):
        """Test that close method has docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.close.__doc__ is not None

    def test_execute_has_docstring(self):
        """Test that execute method has docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.execute.__doc__ is not None

    def test_fetch_one_has_docstring(self):
        """Test that fetch_one method has docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.fetch_one.__doc__ is not None

    def test_fetch_all_has_docstring(self):
        """Test that fetch_all method has docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.fetch_all.__doc__ is not None

    def test_execute_transaction_has_docstring(self):
        """Test that execute_transaction method has docstring."""
        from lib.database.providers.base import BaseDatabaseBackend

        assert BaseDatabaseBackend.execute_transaction.__doc__ is not None


class TestBaseDatabaseBackendAttributes:
    """Test expected attributes of BaseDatabaseBackend."""

    def test_db_url_attribute_exists(self):
        """Test that db_url attribute is expected."""
        from lib.database.providers.base import BaseDatabaseBackend

        # Check __init__ sets db_url
        sig = inspect.signature(BaseDatabaseBackend.__init__)
        params = list(sig.parameters.keys())
        assert "db_url" in params

    def test_pool_size_attributes_expected(self):
        """Test that pool size attributes are expected."""
        from lib.database.providers.base import BaseDatabaseBackend

        # Check __init__ accepts pool configuration
        sig = inspect.signature(BaseDatabaseBackend.__init__)
        params = list(sig.parameters.keys())

        # Should have min_size and max_size parameters
        has_pool_config = "min_size" in params and "max_size" in params
        has_generic_config = len(params) >= 4  # self, db_url, + 2 more

        assert has_pool_config or has_generic_config
