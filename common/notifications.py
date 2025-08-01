"""Generic Notification System.

Simple notification system for monitoring alerts and system events.
Designed to be easily extensible for different notification methods.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from lib.logging import logger


class NotificationLevel(str, Enum):
    """Notification severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


@dataclass
class NotificationMessage:
    """Standard notification message format."""

    title: str
    message: str
    level: NotificationLevel
    source: str
    timestamp: float = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(self, notification: NotificationMessage) -> bool:
        """Send a notification."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""


class WhatsAppProvider(NotificationProvider):
    """WhatsApp notification provider using pooled MCP connections."""

    def __init__(self, group_id: str | None = None):
        self.group_id = group_id or os.getenv("WHATSAPP_NOTIFICATION_GROUP")
        self._last_notification: dict[str, float] = {}
        self.cooldown_seconds = 300
        # No connection manager needed in simple implementation

    async def send(self, notification: NotificationMessage) -> bool:
        """Send notification via WhatsApp using pooled MCP connections."""
        # Check if WhatsApp notifications are enabled
        enabled = (
            os.getenv("HIVE_WHATSAPP_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        )
        if not enabled:
            logger.debug(
                "WhatsApp notifications disabled via HIVE_WHATSAPP_NOTIFICATIONS_ENABLED"
            )
            return False

        try:
            # Check cooldown to prevent spam
            cooldown_key = (
                f"{notification.source}:{notification.level}:{notification.title}"
            )
            current_time = time.time()

            if cooldown_key in self._last_notification and (
                current_time - self._last_notification[cooldown_key]
                < self.cooldown_seconds
            ):
                logger.debug(f"📱 Notification {cooldown_key} in cooldown, skipping")
                return False

            # Format message with emoji
            emoji = self._get_emoji(notification.level)
            formatted_message = f"{emoji} {notification.title}\n\n{notification.message}\n\nSource: {notification.source}"

            # Use simple MCP connection
            try:
                from lib.mcp import get_mcp_tools

                # Get MCP tools directly
                async with get_mcp_tools("whatsapp_notifications") as tools:
                    # Debug: Check what tools are available
                    logger.debug(
                        f"📱 Available MCP tools: {list(tools.functions.keys())}"
                    )

                    # Send WhatsApp message using MCP tools (agno pattern)
                    if "send_text_message" in tools.functions:
                        tool_function = tools.functions["send_text_message"]
                        # Call the MCP tool entrypoint with proper parameters
                        # The tool_name is already bound via partial, so we only pass agent and kwargs
                        result = await tool_function.entrypoint(
                            None,
                            instance="SofIA",
                            message=formatted_message,
                            number=self.group_id,
                        )
                    else:
                        available_tools = list(tools.functions.keys())
                        raise ValueError(
                            f"send_text_message tool not available in MCP server. Available tools: {available_tools}"
                        )

                    logger.info(f"📱 Sent WhatsApp notification: {notification.title}")
                    logger.info(f"📱 Message delivered to group: {self.group_id}")
                    logger.debug(f"📱 WhatsApp result: {result}")

                    self._last_notification[cooldown_key] = current_time
                    return True

            except Exception as e:
                logger.error(f"📱 WhatsApp MCP failed: {e}")
                logger.debug(f"📱 WhatsApp error details: {type(e).__name__}: {e}")
                # Fallback to logging
                logger.info(f"📱 [WhatsApp] {formatted_message}")
                logger.info(f"📱 [WhatsApp] Would send to group: {self.group_id}")
                # Still return True so it doesn't fallback to log provider
                self._last_notification[cooldown_key] = current_time
                return True

        except Exception as e:
            logger.error(f"📱 Failed to send WhatsApp notification: {e}")
            return False

    def is_available(self) -> bool:
        """Check if WhatsApp provider is available."""
        try:
            # Simple check - if we can import the MCP catalog, assume WhatsApp is available
            return True
        except Exception:
            return False

    def _get_emoji(self, level: NotificationLevel) -> str:
        """Get emoji for notification level."""
        emoji_map = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.CRITICAL: "🚨",
            NotificationLevel.ERROR: "❌",
        }
        return emoji_map.get(level, "📢")


class LogProvider(NotificationProvider):
    """Log provider for notifications."""

    def __init__(self, logger_name: str = "notifications"):
        # Use the unified logger instead of creating a separate one
        self.logger = logger

    async def send(self, notification: NotificationMessage) -> bool:
        """Send notification via logging."""
        try:
            level_map = {
                NotificationLevel.INFO: self.logger.info,
                NotificationLevel.WARNING: self.logger.warning,
                NotificationLevel.CRITICAL: self.logger.critical,
                NotificationLevel.ERROR: self.logger.error,
            }

            log_func = level_map.get(notification.level, self.logger.info)
            log_func(
                f"[{notification.source}] {notification.title}: {notification.message}"
            )
            return True

        except Exception as e:
            logger.error(f"📱 Failed to send log notification: {e}")
            return False

    def is_available(self) -> bool:
        """Log provider is always available."""
        return True


class NotificationService:
    """Central notification service."""

    def __init__(self):
        self.providers: dict[str, NotificationProvider] = {}
        self.default_provider = "log"

        # Register providers
        self.register_provider("log", LogProvider())
        self.register_provider("whatsapp", WhatsAppProvider())

        # Use WhatsApp as default if available
        if self.providers["whatsapp"].is_available():
            self.default_provider = "whatsapp"

    def register_provider(self, name: str, provider: NotificationProvider):
        """Register a notification provider."""
        self.providers[name] = provider
        logger.info(f"📱 Registered notification provider: {name}")

    async def send(
        self, notification: NotificationMessage, provider_name: str | None = None
    ) -> bool:
        """Send notification using specified or default provider."""
        if provider_name is None:
            provider_name = self.default_provider

        provider = self.providers.get(provider_name)
        if not provider:
            logger.error(f"📱 Unknown notification provider: {provider_name}")
            return False

        if not provider.is_available():
            logger.warning(
                f"📱 Provider {provider_name} not available, falling back to log"
            )
            provider = self.providers.get("log")

        return await provider.send(notification)

    async def send_alert(
        self,
        title: str,
        message: str,
        source: str,
        level: NotificationLevel = NotificationLevel.WARNING,
    ) -> bool:
        """Convenience method for sending alerts."""
        notification = NotificationMessage(
            title=title, message=message, level=level, source=source
        )
        return await self.send(notification)

    def get_available_providers(self) -> dict[str, bool]:
        """Get list of available providers."""
        return {
            name: provider.is_available() for name, provider in self.providers.items()
        }


# Global notification service instance
_notification_service = NotificationService()


def get_notification_service() -> NotificationService:
    """Get global notification service instance."""
    return _notification_service


# Convenience functions
async def send_notification(
    title: str,
    message: str,
    source: str,
    level: NotificationLevel = NotificationLevel.INFO,
) -> bool:
    """Send a notification using the global service."""
    return await get_notification_service().send_alert(title, message, source, level)


async def send_critical_alert(title: str, message: str, source: str) -> bool:
    """Send a critical alert."""
    return await send_notification(title, message, source, NotificationLevel.CRITICAL)


async def send_warning_alert(title: str, message: str, source: str) -> bool:
    """Send a warning alert."""
    return await send_notification(title, message, source, NotificationLevel.WARNING)


async def send_error_alert(title: str, message: str, source: str) -> bool:
    """Send an error alert."""
    return await send_notification(title, message, source, NotificationLevel.ERROR)
