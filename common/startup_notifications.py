"""Startup Notifications.

Handles notifications when the server starts up and shuts down.
"""

import asyncio
from datetime import datetime

from lib.config.server_config import get_server_config
from lib.logging import logger

from .notifications import NotificationLevel, send_notification


async def send_startup_notification(startup_display=None):
    """Send comprehensive notification when server starts."""
    try:
        # Add a small delay to ensure MCP connection manager is ready
        await asyncio.sleep(0.5)

        # Build rich startup message
        message = _build_startup_message(startup_display)

        # Use asyncio.create_task to isolate the notification sending
        async def isolated_send():
            await send_notification(
                title="🚀 Automagik Hive Server Started",
                message=message,
                source="server-startup",
                level=NotificationLevel.INFO,
            )

        # Run in isolated task to prevent context manager conflicts
        await asyncio.create_task(isolated_send())
        logger.info("Startup notification sent")
    except Exception as e:
        logger.error(f"📱 Failed to send startup notification: {e}")


def _build_startup_message(startup_display=None):
    """Build rich startup notification message."""
    # Basic system info
    config = get_server_config()
    environment = config.environment
    port = config.port
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message_parts = [
        "🎯 *Automagik Hive Multi-Agent System*",
        f"📅 Started: {timestamp}",
        f"🌍 Environment: {environment.upper()}",
        f"🌐 Port: {port}",
        "",
    ]

    if startup_display:
        # Add component status
        total_agents = len(startup_display.agents)
        total_teams = len(startup_display.teams)
        total_workflows = len(startup_display.workflows)
        total_errors = len(startup_display.errors)

        message_parts.extend(
            [
                "📊 *System Components:*",
                f"🤖 Agents: {total_agents}",
                f"🏢 Teams: {total_teams}",
                f"⚡ Workflows: {total_workflows}",
                "",
            ]
        )

        # Add agents with versions
        if startup_display.agents:
            message_parts.append("🤖 *Active Agents:*")
            for agent_id, info in startup_display.agents.items():
                status_icon = "✅" if info["status"] == "✅" else "❌"
                version_info = (
                    f"v{info['version']}" if info["version"] != "latest" else "latest"
                )
                message_parts.append(f"{status_icon} {agent_id} ({version_info})")
            message_parts.append("")

        # Add workflows with versions
        if startup_display.workflows:
            message_parts.append("⚡ *Active Workflows:*")
            for workflow_id, info in startup_display.workflows.items():
                status_icon = "✅" if info["status"] == "✅" else "❌"
                version_info = (
                    f"v{info['version']}" if info["version"] != "latest" else "latest"
                )
                message_parts.append(f"{status_icon} {workflow_id} ({version_info})")
            message_parts.append("")

        # Add error summary if any
        if startup_display.errors:
            message_parts.extend([f"⚠️ *Issues Found: {total_errors}*", ""])
            for error in startup_display.errors[:3]:  # Show first 3 errors
                message_parts.append(
                    f"❌ {error['component']}: {error['message'][:50]}..."
                )
            if total_errors > 3:
                message_parts.append(f"... and {total_errors - 3} more issues")
            message_parts.append("")

        # System status summary
        successful_components = sum(
            1
            for items in [
                startup_display.agents,
                startup_display.teams,
                startup_display.workflows,
            ]
            for item in items.values()
            if item["status"] == "✅"
        )
        total_components = total_agents + total_teams + total_workflows

        if total_errors == 0:
            message_parts.append("✅ *All systems operational*")
        else:
            message_parts.append(
                f"⚠️ *{successful_components}/{total_components} components healthy*"
            )
    else:
        message_parts.extend(
            ["✅ Server started successfully", "📊 Component details unavailable"]
        )

    message_parts.extend(["", f"🔗 API: {config.get_base_url()}"])

    return "\n".join(message_parts)


async def send_shutdown_notification():
    """Send notification when server shuts down."""
    try:
        # Use asyncio.create_task to isolate the notification sending
        async def isolated_send():
            await send_notification(
                title="Automagik Hive Server Shutdown",
                message="The automagik-hive server is shutting down.",
                source="server-shutdown",
                level=NotificationLevel.WARNING,
            )

        # Run in isolated task to prevent context manager conflicts
        await asyncio.create_task(isolated_send())
        logger.info("Shutdown notification sent")
    except Exception as e:
        logger.error(f"📱 Failed to send shutdown notification: {e}")


async def send_error_notification(error_message: str, source: str = "server-error"):
    """Send notification when server encounters an error."""
    try:
        await send_notification(
            title="Automagik Hive Server Error",
            message=f"Server error occurred: {error_message}",
            source=source,
            level=NotificationLevel.ERROR,
        )
        logger.info(f"📱 Error notification sent: {error_message}")
    except Exception as e:
        logger.error(f"📱 Failed to send error notification: {e}")


async def send_mcp_server_error(server_name: str, error_message: str):
    """Send notification when MCP server encounters an error."""
    try:
        await send_notification(
            title=f"MCP Server Error: {server_name}",
            message=f"MCP server '{server_name}' encountered an error: {error_message}",
            source="mcp-server-error",
            level=NotificationLevel.CRITICAL,
        )
        logger.info(f"📱 MCP server error notification sent: {server_name}")
    except Exception as e:
        logger.error(f"📱 Failed to send MCP server error notification: {e}")


async def send_health_check_notification(component: str, status: str, message: str):
    """Send notification for health check results."""
    try:
        level = (
            NotificationLevel.INFO if status == "healthy" else NotificationLevel.WARNING
        )

        await send_notification(
            title=f"Health Check: {component}",
            message=f"Component '{component}' is {status}. {message}",
            source="health-check",
            level=level,
        )
        logger.info(f"📱 Health check notification sent: {component} - {status}")
    except Exception as e:
        logger.error(f"📱 Failed to send health check notification: {e}")


# Convenience function for common notification patterns
async def notify_system_event(
    title: str, message: str, level: NotificationLevel = NotificationLevel.INFO
):
    """Generic system event notification."""
    try:
        await send_notification(
            title=title, message=message, source="system-event", level=level
        )
        logger.info(f"📱 System event notification sent: {title}")
    except Exception as e:
        logger.error(f"📱 Failed to send system event notification: {e}")


async def notify_critical_error(
    title: str, message: str, source: str = "critical-error"
):
    """Critical error notification."""
    try:
        await send_notification(
            title=title,
            message=message,
            source=source,
            level=NotificationLevel.CRITICAL,
        )
        logger.info(f"📱 Critical error notification sent: {title}")
    except Exception as e:
        logger.error(f"📱 Failed to send critical error notification: {e}")


async def notify_performance_issue(
    component: str, metric: str, value: str, threshold: str
):
    """Performance issue notification."""
    try:
        await send_notification(
            title=f"Performance Issue: {component}",
            message=f"{component} {metric} is {value} (threshold: {threshold}). This may affect system performance.",
            source="performance-monitor",
            level=NotificationLevel.WARNING,
        )
        logger.info(f"📱 Performance issue notification sent: {component}")
    except Exception as e:
        logger.error(f"📱 Failed to send performance issue notification: {e}")


async def notify_user_action(action: str, user_id: str, details: str = ""):
    """User action notification for important events."""
    try:
        message = f"User {user_id} performed action: {action}"
        if details:
            message += f". Details: {details}"

        await send_notification(
            title="Important User Action",
            message=message,
            source="user-action",
            level=NotificationLevel.INFO,
        )
        logger.info(f"📱 User action notification sent: {action}")
    except Exception as e:
        logger.error(f"📱 Failed to send user action notification: {e}")


async def notify_security_event(
    event_type: str, message: str, source: str = "security"
):
    """Security event notification."""
    try:
        await send_notification(
            title=f"Security Event: {event_type}",
            message=message,
            source=source,
            level=NotificationLevel.CRITICAL,
        )
        logger.info(f"📱 Security event notification sent: {event_type}")
    except Exception as e:
        logger.error(f"📱 Failed to send security event notification: {e}")


# Quick notification shortcuts
async def notify_info(title: str, message: str, source: str = "info"):
    """Quick info notification."""
    await send_notification(title, message, source, NotificationLevel.INFO)


async def notify_warning(title: str, message: str, source: str = "warning"):
    """Quick warning notification."""
    await send_notification(title, message, source, NotificationLevel.WARNING)


async def notify_error(title: str, message: str, source: str = "error"):
    """Quick error notification."""
    await send_notification(title, message, source, NotificationLevel.ERROR)


async def notify_critical(title: str, message: str, source: str = "critical"):
    """Quick critical notification."""
    await send_notification(title, message, source, NotificationLevel.CRITICAL)
