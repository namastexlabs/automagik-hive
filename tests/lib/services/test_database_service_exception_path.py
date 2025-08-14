"""Specific test for the exception path in get_db_service that wasn't covered.

This test specifically targets lines 102-104 in database_service.py to ensure
the exception handling path in get_db_service is properly covered.
"""

import os
from unittest.mock import patch

import pytest

from lib.services.database_service import DatabaseService, get_db_service


class TestGetDbServiceExceptionPath:
    """Test the specific exception handling path in get_db_service."""

    @pytest.mark.asyncio
    async def test_get_db_service_exception_handling_no_cache(self):
        """Test get_db_service exception handling prevents caching failed instance."""
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
        ):
            # Clear global instance
            from lib.services import database_service

            database_service._db_service = None

            # Mock DatabaseService.initialize to raise an exception
            with patch.object(DatabaseService, "initialize") as mock_initialize:
                mock_initialize.side_effect = RuntimeError("Database initialization failed")

                # Call get_db_service - should raise exception and NOT cache the failed instance
                with pytest.raises(RuntimeError, match="Database initialization failed"):
                    await get_db_service()

                # Verify the failed service was not cached
                assert database_service._db_service is None

                # Verify initialize was called
                mock_initialize.assert_called_once()

            # Now test that a subsequent call (after fixing the issue) works properly
            with patch.object(DatabaseService, "initialize") as mock_initialize:
                mock_initialize.return_value = None  # Success

                service = await get_db_service()

                # Should create and cache a new service
                assert service is not None
                assert isinstance(service, DatabaseService)
                assert database_service._db_service is service
                mock_initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_service_different_exception_types(self):
        """Test get_db_service handles different types of exceptions properly."""
        exception_types = [
            (ValueError, "Invalid database configuration"),
            (ConnectionError, "Connection failed"),
            (TimeoutError, "Operation timed out"),
            (RuntimeError, "Runtime error occurred"),
        ]

        for exception_type, message in exception_types:
            with patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
            ):
                # Clear global instance for each test
                from lib.services import database_service

                database_service._db_service = None

                with patch.object(DatabaseService, "initialize") as mock_initialize:
                    mock_initialize.side_effect = exception_type(message)

                    # Should raise the specific exception type
                    with pytest.raises(exception_type, match=message):
                        await get_db_service()

                    # Should not cache the failed instance
                    assert database_service._db_service is None