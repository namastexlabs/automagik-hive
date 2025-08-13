"""Tests for common.notifications module."""

import os
import time
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from common.notifications import (
    NotificationLevel,
    NotificationMessage,
    NotificationProvider,
    WhatsAppProvider,
    LogProvider,
    NotificationService,
    get_notification_service,
    send_notification,
    send_critical_alert,
    send_warning_alert,
    send_error_alert,
)


class TestNotificationLevel:
    """Test NotificationLevel enum."""

    def test_notification_level_values(self):
        """Test NotificationLevel enum values."""
        assert NotificationLevel.INFO == "info"
        assert NotificationLevel.WARNING == "warning"
        assert NotificationLevel.CRITICAL == "critical"
        assert NotificationLevel.ERROR == "error"

    def test_notification_level_inheritance(self):
        """Test NotificationLevel inherits from str and Enum."""
        assert isinstance(NotificationLevel.INFO, str)
        assert NotificationLevel.INFO == "info"


class TestNotificationMessage:
    """Test NotificationMessage dataclass."""

    def test_notification_message_creation(self):
        """Test creating NotificationMessage with required fields."""
        message = NotificationMessage(
            title="Test Title",
            message="Test message content",
            level=NotificationLevel.INFO,
            source="test_source"
        )
        
        assert message.title == "Test Title"
        assert message.message == "Test message content"
        assert message.level == NotificationLevel.INFO
        assert message.source == "test_source"
        assert message.timestamp is not None
        assert message.metadata is not None

    def test_notification_message_with_timestamp(self):
        """Test creating NotificationMessage with custom timestamp."""
        custom_timestamp = 1234567890.0
        message = NotificationMessage(
            title="Test",
            message="Test",
            level=NotificationLevel.WARNING,
            source="test",
            timestamp=custom_timestamp
        )
        
        assert message.timestamp == custom_timestamp

    def test_notification_message_with_metadata(self):
        """Test creating NotificationMessage with custom metadata."""
        metadata = {"key": "value", "number": 42}
        message = NotificationMessage(
            title="Test",
            message="Test",
            level=NotificationLevel.ERROR,
            source="test",
            metadata=metadata
        )
        
        assert message.metadata == metadata

    def test_notification_message_auto_timestamp(self):
        """Test NotificationMessage automatically sets timestamp."""
        before_time = time.time()
        message = NotificationMessage(
            title="Test",
            message="Test",
            level=NotificationLevel.CRITICAL,
            source="test"
        )
        after_time = time.time()
        
        assert before_time <= message.timestamp <= after_time

    def test_notification_message_auto_metadata(self):
        """Test NotificationMessage automatically initializes metadata."""
        message = NotificationMessage(
            title="Test",
            message="Test",
            level=NotificationLevel.INFO,
            source="test"
        )
        
        assert message.metadata == {}


class TestNotificationProvider:
    """Test NotificationProvider abstract base class."""

    def test_notification_provider_is_abstract(self):
        """Test NotificationProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            NotificationProvider()

    def test_notification_provider_requires_send_implementation(self):
        """Test subclasses must implement send method."""
        class IncompleteProvider(NotificationProvider):
            def is_available(self) -> bool:
                return True
        
        with pytest.raises(TypeError):
            IncompleteProvider()


class TestWhatsAppProvider:
    """Test WhatsAppProvider implementation."""

    @patch.dict(os.environ, {"WHATSAPP_NOTIFICATION_GROUP": "test_group"})
    def test_whatsapp_provider_creation_with_env_group(self):
        """Test creating WhatsAppProvider with environment group ID."""
        provider = WhatsAppProvider()
        assert provider.group_id == "test_group"

    def test_whatsapp_provider_creation_with_explicit_group(self):
        """Test creating WhatsAppProvider with explicit group ID."""
        provider = WhatsAppProvider(group_id="explicit_group")
        assert provider.group_id == "explicit_group"

    @patch.dict(os.environ, {}, clear=True)
    def test_whatsapp_provider_creation_without_group(self):
        """Test creating WhatsAppProvider without group ID."""
        provider = WhatsAppProvider()
        assert provider.group_id is None

    def test_whatsapp_provider_cooldown_initialization(self):
        """Test WhatsAppProvider initializes cooldown properly."""
        provider = WhatsAppProvider()
        assert provider.cooldown_seconds == 300
        assert provider._last_notification == {}

    @patch.dict(os.environ, {"HIVE_WHATSAPP_NOTIFICATIONS_ENABLED": "false"})
    @pytest.mark.asyncio
    async def test_whatsapp_send_disabled(self):
        """Test WhatsApp sending when disabled."""
        provider = WhatsAppProvider()
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await provider.send(message)
        assert result is False

    @patch("lib.mcp.get_mcp_tools")
    @patch.dict(os.environ, {"HIVE_WHATSAPP_NOTIFICATIONS_ENABLED": "true"})
    @pytest.mark.asyncio
    async def test_whatsapp_send_success(self, mock_get_mcp_tools):
        """Test successful WhatsApp notification sending."""
        mock_tools = AsyncMock()
        mock_tool_function = AsyncMock()
        mock_tool_function.entrypoint = AsyncMock(return_value={"status": "sent"})
        mock_tools.functions = {"send_text_message": mock_tool_function}
        mock_get_mcp_tools.return_value.__aenter__.return_value = mock_tools

        provider = WhatsAppProvider(group_id="test_group")
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await provider.send(message)
        assert result is True

    @patch("lib.mcp.get_mcp_tools")
    @patch.dict(os.environ, {"HIVE_WHATSAPP_NOTIFICATIONS_ENABLED": "true"})
    @pytest.mark.asyncio
    async def test_whatsapp_send_mcp_failure(self, mock_get_mcp_tools):
        """Test WhatsApp sending with MCP failure."""
        mock_get_mcp_tools.side_effect = Exception("MCP connection failed")

        provider = WhatsAppProvider()
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.ERROR,
            source="test"
        )

        result = await provider.send(message)
        assert result is True  # Returns True because it logs as fallback

    @pytest.mark.asyncio
    async def test_whatsapp_send_cooldown(self):
        """Test WhatsApp sending respects cooldown."""
        provider = WhatsAppProvider()
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.WARNING,
            source="test"
        )

        # Simulate recent notification
        cooldown_key = f"{message.source}:{message.level}:{message.title}"
        provider._last_notification[cooldown_key] = time.time()

        with patch.dict(os.environ, {"HIVE_WHATSAPP_NOTIFICATIONS_ENABLED": "true"}):
            result = await provider.send(message)
        
        assert result is False

    def test_whatsapp_provider_emoji_mapping(self):
        """Test WhatsApp provider emoji mapping."""
        provider = WhatsAppProvider()
        
        assert provider._get_emoji(NotificationLevel.INFO) == "ℹ️"
        assert provider._get_emoji(NotificationLevel.WARNING) == "⚠️"
        assert provider._get_emoji(NotificationLevel.CRITICAL) == "🚨"
        assert provider._get_emoji(NotificationLevel.ERROR) == "❌"

    def test_whatsapp_provider_is_available(self):
        """Test WhatsApp provider availability check."""
        provider = WhatsAppProvider()
        assert provider.is_available() is True


class TestLogProvider:
    """Test LogProvider implementation."""

    def test_log_provider_creation(self):
        """Test creating LogProvider."""
        provider = LogProvider()
        assert provider.logger is not None

    def test_log_provider_creation_with_custom_logger(self):
        """Test creating LogProvider with custom logger name."""
        provider = LogProvider(logger_name="custom_logger")
        assert provider.logger is not None

    @patch("common.notifications.logger")
    @pytest.mark.asyncio
    async def test_log_provider_send_info(self, mock_logger):
        """Test LogProvider sends INFO notifications."""
        provider = LogProvider()
        message = NotificationMessage(
            title="Test Info",
            message="Test info message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await provider.send(message)
        assert result is True
        mock_logger.info.assert_called_once()

    @patch("common.notifications.logger")
    @pytest.mark.asyncio
    async def test_log_provider_send_warning(self, mock_logger):
        """Test LogProvider sends WARNING notifications."""
        provider = LogProvider()
        message = NotificationMessage(
            title="Test Warning",
            message="Test warning message",
            level=NotificationLevel.WARNING,
            source="test"
        )

        result = await provider.send(message)
        assert result is True
        mock_logger.warning.assert_called_once()

    @patch("common.notifications.logger")
    @pytest.mark.asyncio
    async def test_log_provider_send_error(self, mock_logger):
        """Test LogProvider sends ERROR notifications."""
        provider = LogProvider()
        message = NotificationMessage(
            title="Test Error",
            message="Test error message",
            level=NotificationLevel.ERROR,
            source="test"
        )

        result = await provider.send(message)
        assert result is True
        mock_logger.error.assert_called_once()

    @patch("common.notifications.logger")
    @pytest.mark.asyncio
    async def test_log_provider_send_critical(self, mock_logger):
        """Test LogProvider sends CRITICAL notifications."""
        provider = LogProvider()
        message = NotificationMessage(
            title="Test Critical",
            message="Test critical message",
            level=NotificationLevel.CRITICAL,
            source="test"
        )

        result = await provider.send(message)
        assert result is True
        mock_logger.critical.assert_called_once()

    @patch("common.notifications.logger")
    @pytest.mark.asyncio
    async def test_log_provider_send_exception(self, mock_logger):
        """Test LogProvider handles exceptions."""
        provider = LogProvider()
        mock_logger.info.side_effect = Exception("Logger error")
        
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await provider.send(message)
        assert result is False

    def test_log_provider_is_available(self):
        """Test LogProvider is always available."""
        provider = LogProvider()
        assert provider.is_available() is True


class TestNotificationService:
    """Test NotificationService central service."""

    def test_notification_service_initialization(self):
        """Test NotificationService initializes with default providers."""
        service = NotificationService()
        
        assert "log" in service.providers
        assert "whatsapp" in service.providers
        assert isinstance(service.providers["log"], LogProvider)
        assert isinstance(service.providers["whatsapp"], WhatsAppProvider)

    def test_notification_service_register_provider(self):
        """Test registering custom notification provider."""
        service = NotificationService()
        mock_provider = MagicMock(spec=NotificationProvider)
        
        service.register_provider("custom", mock_provider)
        assert "custom" in service.providers
        assert service.providers["custom"] is mock_provider

    @patch("common.notifications.LogProvider")
    @pytest.mark.asyncio
    async def test_notification_service_send_with_default_provider(self, mock_log_provider):
        """Test NotificationService sends with default provider."""
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True
        mock_log_provider.return_value = mock_provider
        
        service = NotificationService()
        service.providers["log"] = mock_provider
        service.default_provider = "log"
        
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await service.send(message)
        assert result is True
        mock_provider.send.assert_called_once_with(message)

    @patch("common.notifications.LogProvider")
    @pytest.mark.asyncio
    async def test_notification_service_send_with_specific_provider(self, mock_log_provider):
        """Test NotificationService sends with specific provider."""
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True
        mock_log_provider.return_value = mock_provider
        
        service = NotificationService()
        service.providers["custom"] = mock_provider
        
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await service.send(message, provider_name="custom")
        assert result is True
        mock_provider.send.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_notification_service_send_unknown_provider(self):
        """Test NotificationService handles unknown provider."""
        service = NotificationService()
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await service.send(message, provider_name="unknown")
        assert result is False

    @patch("common.notifications.LogProvider")
    @pytest.mark.asyncio
    async def test_notification_service_fallback_to_log(self, mock_log_provider):
        """Test NotificationService falls back to log provider."""
        mock_unavailable_provider = MagicMock()
        mock_unavailable_provider.is_available.return_value = False
        
        mock_log_provider_instance = AsyncMock()
        mock_log_provider_instance.send.return_value = True
        mock_log_provider.return_value = mock_log_provider_instance
        
        service = NotificationService()
        service.providers["unavailable"] = mock_unavailable_provider
        service.providers["log"] = mock_log_provider_instance
        
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await service.send(message, provider_name="unavailable")
        assert result is True
        mock_log_provider_instance.send.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_notification_service_send_alert(self):
        """Test NotificationService send_alert convenience method."""
        service = NotificationService()
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True
        service.providers["log"] = mock_provider
        service.default_provider = "log"

        result = await service.send_alert(
            title="Test Alert",
            message="Test alert message",
            source="test_source",
            level=NotificationLevel.WARNING
        )
        
        assert result is True
        mock_provider.send.assert_called_once()
        
        # Verify the message was created correctly
        call_args = mock_provider.send.call_args[0][0]
        assert call_args.title == "Test Alert"
        assert call_args.message == "Test alert message"
        assert call_args.source == "test_source"
        assert call_args.level == NotificationLevel.WARNING

    def test_notification_service_get_available_providers(self):
        """Test NotificationService get_available_providers."""
        service = NotificationService()
        mock_available = MagicMock()
        mock_available.is_available.return_value = True
        mock_unavailable = MagicMock()
        mock_unavailable.is_available.return_value = False
        
        service.providers["available"] = mock_available
        service.providers["unavailable"] = mock_unavailable
        
        providers = service.get_available_providers()
        assert providers["available"] is True
        assert providers["unavailable"] is False


class TestNotificationConvenienceFunctions:
    """Test convenience functions for notifications."""

    @patch("common.notifications.get_notification_service")
    @pytest.mark.asyncio
    async def test_send_notification_function(self, mock_get_service):
        """Test send_notification convenience function."""
        mock_service = AsyncMock()
        mock_service.send_alert.return_value = True
        mock_get_service.return_value = mock_service

        result = await send_notification(
            title="Test",
            message="Test message",
            source="test",
            level=NotificationLevel.INFO
        )
        
        assert result is True
        mock_service.send_alert.assert_called_once_with(
            "Test", "Test message", "test", NotificationLevel.INFO
        )

    @patch("common.notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_critical_alert(self, mock_send):
        """Test send_critical_alert convenience function."""
        mock_send.return_value = True
        
        result = await send_critical_alert("Critical", "Critical message", "test")
        
        assert result is True
        mock_send.assert_called_once_with(
            "Critical", "Critical message", "test", NotificationLevel.CRITICAL
        )

    @patch("common.notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_warning_alert(self, mock_send):
        """Test send_warning_alert convenience function."""
        mock_send.return_value = True
        
        result = await send_warning_alert("Warning", "Warning message", "test")
        
        assert result is True
        mock_send.assert_called_once_with(
            "Warning", "Warning message", "test", NotificationLevel.WARNING
        )

    @patch("common.notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_error_alert(self, mock_send):
        """Test send_error_alert convenience function."""
        mock_send.return_value = True
        
        result = await send_error_alert("Error", "Error message", "test")
        
        assert result is True
        mock_send.assert_called_once_with(
            "Error", "Error message", "test", NotificationLevel.ERROR
        )

    def test_get_notification_service_function(self):
        """Test get_notification_service function."""
        service = get_notification_service()
        assert isinstance(service, NotificationService)
        
        # Should return the same instance (singleton pattern)
        service2 = get_notification_service()
        assert service is service2


class TestNotificationIntegration:
    """Test notification system integration scenarios."""

    @patch("lib.mcp.get_mcp_tools")
    @patch.dict(os.environ, {
        "HIVE_WHATSAPP_NOTIFICATIONS_ENABLED": "true",
        "WHATSAPP_NOTIFICATION_GROUP": "test_group"
    })
    @pytest.mark.asyncio
    async def test_end_to_end_notification_flow(self, mock_get_mcp_tools):
        """Test complete notification flow."""
        mock_tools = AsyncMock()
        mock_tool_function = AsyncMock()
        mock_tool_function.entrypoint = AsyncMock(return_value={"status": "sent"})
        mock_tools.functions = {"send_text_message": mock_tool_function}
        mock_get_mcp_tools.return_value.__aenter__.return_value = mock_tools

        # Create notification message
        message = NotificationMessage(
            title="System Alert",
            message="Test system notification",
            level=NotificationLevel.WARNING,
            source="integration_test",
            metadata={"test_id": "test_123"}
        )

        # Send via service
        service = NotificationService()
        result = await service.send(message, provider_name="whatsapp")

        assert result is True

    def test_multiple_notification_levels(self):
        """Test handling different notification levels."""
        levels = [
            NotificationLevel.INFO,
            NotificationLevel.WARNING,
            NotificationLevel.ERROR,
            NotificationLevel.CRITICAL
        ]

        for level in levels:
            message = NotificationMessage(
                title=f"Test {level.value.upper()}",
                message=f"Test message for {level.value}",
                level=level,
                source="test"
            )
            assert message.level == level
            assert level.value.upper() in message.title

    @pytest.mark.asyncio
    async def test_notification_service_provider_fallback_chain(self):
        """Test notification service provider fallback chain."""
        service = NotificationService()
        
        # Mock unavailable primary provider
        mock_primary = MagicMock()
        mock_primary.is_available.return_value = False
        
        # Mock available fallback provider (log provider)
        mock_fallback = MagicMock()
        mock_fallback.send = AsyncMock(return_value=True)
        
        service.providers["primary"] = mock_primary
        service.providers["log"] = mock_fallback
        
        message = NotificationMessage(
            title="Test",
            message="Test message",
            level=NotificationLevel.INFO,
            source="test"
        )

        result = await service.send(message, provider_name="primary")
        assert result is True
        mock_fallback.send.assert_called_once_with(message)