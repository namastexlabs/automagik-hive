"""Tests for lib.exceptions module."""

import pytest

from lib.exceptions import (
    AutomagikHiveError,
    ComponentLoadingError,
    MemoryFactoryError,
    NotificationError,
)


class TestAutomagikHiveError:
    """Test AutomagikHiveError base exception."""

    def test_automagik_hive_error_creation(self):
        """Test creating AutomagikHiveError with message."""
        error = AutomagikHiveError("Test error message")
        assert str(error) == "Test error message"

    def test_automagik_hive_error_inheritance(self):
        """Test AutomagikHiveError inherits from Exception."""
        error = AutomagikHiveError("Test")
        assert isinstance(error, Exception)


class TestMemoryFactoryError:
    """Test MemoryFactoryError exception."""

    def test_memory_factory_error_creation(self):
        """Test creating MemoryFactoryError with message."""
        error = MemoryFactoryError("Memory creation failed")
        assert str(error) == "Memory creation failed"

    def test_memory_factory_error_inheritance(self):
        """Test MemoryFactoryError inherits from AutomagikHiveError."""
        error = MemoryFactoryError("Test")
        assert isinstance(error, AutomagikHiveError)
        assert isinstance(error, Exception)


class TestNotificationError:
    """Test NotificationError exception."""

    def test_notification_error_creation(self):
        """Test creating NotificationError with message."""
        error = NotificationError("Notification delivery failed")
        assert str(error) == "Notification delivery failed"

    def test_notification_error_inheritance(self):
        """Test NotificationError inherits from AutomagikHiveError."""
        error = NotificationError("Test")
        assert isinstance(error, AutomagikHiveError)
        assert isinstance(error, Exception)


class TestComponentLoadingError:
    """Test ComponentLoadingError exception."""

    def test_component_loading_error_creation(self):
        """Test creating ComponentLoadingError with message."""
        error = ComponentLoadingError("Component loading failed")
        assert str(error) == "Component loading failed"

    def test_component_loading_error_inheritance(self):
        """Test ComponentLoadingError inherits from AutomagikHiveError."""
        error = ComponentLoadingError("Test")
        assert isinstance(error, AutomagikHiveError)
        assert isinstance(error, Exception)


class TestExceptionRaising:
    """Test exception raising scenarios."""

    def test_automagik_hive_error_raising(self):
        """Test raising AutomagikHiveError."""
        with pytest.raises(AutomagikHiveError, match="Test error"):
            raise AutomagikHiveError("Test error")

    def test_memory_factory_error_raising(self):
        """Test raising MemoryFactoryError."""
        with pytest.raises(MemoryFactoryError, match="Memory failed"):
            raise MemoryFactoryError("Memory failed")

    def test_notification_error_raising(self):
        """Test raising NotificationError."""
        with pytest.raises(NotificationError, match="Notification failed"):
            raise NotificationError("Notification failed")

    def test_component_loading_error_raising(self):
        """Test raising ComponentLoadingError."""
        with pytest.raises(ComponentLoadingError, match="Component failed"):
            raise ComponentLoadingError("Component failed")


class TestExceptionCatching:
    """Test exception catching with inheritance."""

    def test_catch_specific_as_base_exception(self):
        """Test catching specific exceptions as base AutomagikHiveError."""
        with pytest.raises(AutomagikHiveError):
            raise MemoryFactoryError("Memory error")

        with pytest.raises(AutomagikHiveError):
            raise NotificationError("Notification error")

        with pytest.raises(AutomagikHiveError):
            raise ComponentLoadingError("Component error")

    def test_catch_all_as_exception(self):
        """Test catching all custom exceptions as base Exception."""
        with pytest.raises(Exception):
            raise AutomagikHiveError("Base error")

        with pytest.raises(Exception):
            raise MemoryFactoryError("Memory error")