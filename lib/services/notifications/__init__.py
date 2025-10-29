"""Notification services for system events."""

# Core notification components
from lib.services.notifications.notifications import (
    LogProvider,
    NotificationLevel,
    NotificationMessage,
    NotificationProvider,
    NotificationService,
    WhatsAppProvider,
    get_notification_service,
    send_critical_alert,
    send_error_alert,
    send_notification,
    send_warning_alert,
)

# Startup/shutdown notification functions
from lib.services.notifications.startup_notifications import (
    _build_startup_message,
    notify_critical,
    notify_critical_error,
    notify_error,
    notify_info,
    notify_performance_issue,
    notify_security_event,
    notify_system_event,
    notify_user_action,
    notify_warning,
    send_error_notification,
    send_health_check_notification,
    send_mcp_server_error,
    send_shutdown_notification,
    send_startup_notification,
)

__all__ = [
    # Classes
    "NotificationLevel",
    "NotificationMessage",
    "NotificationProvider",
    "NotificationService",
    "LogProvider",
    "WhatsAppProvider",
    # Core notification functions
    "get_notification_service",
    "send_notification",
    "send_critical_alert",
    "send_warning_alert",
    "send_error_alert",
    # Startup/shutdown functions
    "send_startup_notification",
    "send_shutdown_notification",
    "send_error_notification",
    "send_mcp_server_error",
    "send_health_check_notification",
    # Notify functions
    "notify_system_event",
    "notify_critical_error",
    "notify_performance_issue",
    "notify_user_action",
    "notify_security_event",
    "notify_info",
    "notify_warning",
    "notify_error",
    "notify_critical",
    # Internal functions (for tests)
    "_build_startup_message",
]
