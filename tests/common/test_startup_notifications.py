"""Tests for common.startup_notifications module."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from common.startup_notifications import (
    send_startup_notification,
    send_shutdown_notification,
    send_error_notification,
    send_mcp_server_error,
    send_health_check_notification,
    notify_system_event,
    notify_critical_error,
    notify_performance_issue,
    notify_user_action,
    notify_security_event,
    notify_info,
    notify_warning,
    notify_error,
    notify_critical,
    _build_startup_message,
)
from common.notifications import NotificationLevel


class TestStartupNotificationFunctions:
    """Test startup notification functions."""

    @patch("common.startup_notifications.send_notification")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_send_startup_notification_without_display(self, mock_sleep, mock_send):
        """Test sending startup notification without startup display."""
        mock_send.return_value = True
        
        await send_startup_notification()
        
        mock_sleep.assert_called_once_with(0.5)
        mock_send.assert_called_once()
        
        # Verify the notification call
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "🚀 Automagik Hive Server Started"
        assert call_args["source"] == "server-startup"
        assert call_args["level"] == NotificationLevel.INFO

    @patch("common.startup_notifications.send_notification")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_send_startup_notification_with_display(self, mock_sleep, mock_send):
        """Test sending startup notification with startup display."""
        mock_send.return_value = True
        
        # Mock startup display
        mock_startup_display = MagicMock()
        mock_startup_display.agents = {
            "agent1": {"status": "✅", "version": "1.0"},
            "agent2": {"status": "❌", "version": "latest"}
        }
        mock_startup_display.teams = {
            "team1": {"status": "✅", "version": "2.0"}
        }
        mock_startup_display.workflows = {
            "workflow1": {"status": "✅", "version": "3.0"}
        }
        mock_startup_display.errors = [
            {"component": "agent2", "message": "Failed to initialize agent"}
        ]
        
        await send_startup_notification(startup_display=mock_startup_display)
        
        mock_sleep.assert_called_once_with(0.5)
        mock_send.assert_called_once()
        
        # Verify the notification includes display information
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "🚀 Automagik Hive Server Started"
        assert "🤖 Agents: 2" in call_args["message"]
        assert "🏢 Teams: 1" in call_args["message"]
        assert "⚡ Workflows: 1" in call_args["message"]

    @patch("common.startup_notifications.send_notification")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_send_startup_notification_exception_handling(self, mock_sleep, mock_send):
        """Test startup notification handles exceptions gracefully."""
        mock_send.side_effect = Exception("Notification failed")
        
        # Should not raise exception
        await send_startup_notification()
        
        mock_sleep.assert_called_once_with(0.5)
        mock_send.assert_called_once()

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_shutdown_notification(self, mock_send):
        """Test sending shutdown notification."""
        mock_send.return_value = True
        
        await send_shutdown_notification()
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Automagik Hive Server Shutdown"
        assert call_args["message"] == "The automagik-hive server is shutting down."
        assert call_args["source"] == "server-shutdown"
        assert call_args["level"] == NotificationLevel.WARNING

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_shutdown_notification_exception_handling(self, mock_send):
        """Test shutdown notification handles exceptions gracefully."""
        mock_send.side_effect = Exception("Notification failed")
        
        # Should not raise exception
        await send_shutdown_notification()
        
        mock_send.assert_called_once()

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_error_notification(self, mock_send):
        """Test sending error notification."""
        mock_send.return_value = True
        
        await send_error_notification("Database connection failed")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Automagik Hive Server Error"
        assert "Database connection failed" in call_args["message"]
        assert call_args["source"] == "server-error"
        assert call_args["level"] == NotificationLevel.ERROR

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_error_notification_with_custom_source(self, mock_send):
        """Test sending error notification with custom source."""
        mock_send.return_value = True
        
        await send_error_notification("Custom error", source="custom-source")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["source"] == "custom-source"

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_mcp_server_error(self, mock_send):
        """Test sending MCP server error notification."""
        mock_send.return_value = True
        
        await send_mcp_server_error("test-server", "Connection timeout")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "MCP Server Error: test-server"
        assert "test-server" in call_args["message"]
        assert "Connection timeout" in call_args["message"]
        assert call_args["source"] == "mcp-server-error"
        assert call_args["level"] == NotificationLevel.CRITICAL

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_health_check_notification_healthy(self, mock_send):
        """Test sending health check notification for healthy component."""
        mock_send.return_value = True
        
        await send_health_check_notification("database", "healthy", "All connections active")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Health Check: database"
        assert "database" in call_args["message"]
        assert "healthy" in call_args["message"]
        assert call_args["source"] == "health-check"
        assert call_args["level"] == NotificationLevel.INFO

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_send_health_check_notification_unhealthy(self, mock_send):
        """Test sending health check notification for unhealthy component."""
        mock_send.return_value = True
        
        await send_health_check_notification("redis", "unhealthy", "Connection refused")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Health Check: redis"
        assert "redis" in call_args["message"]
        assert "unhealthy" in call_args["message"]
        assert call_args["source"] == "health-check"
        assert call_args["level"] == NotificationLevel.WARNING


class TestConvenienceNotificationFunctions:
    """Test convenience notification functions."""

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_system_event(self, mock_send):
        """Test notify_system_event convenience function."""
        mock_send.return_value = True
        
        await notify_system_event("System Update", "System has been updated to v2.0")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "System Update"
        assert call_args["message"] == "System has been updated to v2.0"
        assert call_args["source"] == "system-event"
        assert call_args["level"] == NotificationLevel.INFO

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_system_event_with_custom_level(self, mock_send):
        """Test notify_system_event with custom level."""
        mock_send.return_value = True
        
        await notify_system_event("Critical Update", "Critical update required", NotificationLevel.CRITICAL)
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["level"] == NotificationLevel.CRITICAL

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_critical_error(self, mock_send):
        """Test notify_critical_error convenience function."""
        mock_send.return_value = True
        
        await notify_critical_error("System Failure", "Critical system component failed")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "System Failure"
        assert call_args["message"] == "Critical system component failed"
        assert call_args["source"] == "critical-error"
        assert call_args["level"] == NotificationLevel.CRITICAL

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_critical_error_with_custom_source(self, mock_send):
        """Test notify_critical_error with custom source."""
        mock_send.return_value = True
        
        await notify_critical_error("DB Error", "Database crashed", "database-service")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["source"] == "database-service"

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_performance_issue(self, mock_send):
        """Test notify_performance_issue convenience function."""
        mock_send.return_value = True
        
        await notify_performance_issue("API", "response_time", "2.5s", "1.0s")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Performance Issue: API"
        assert "API" in call_args["message"]
        assert "response_time" in call_args["message"]
        assert "2.5s" in call_args["message"]
        assert "1.0s" in call_args["message"]
        assert call_args["source"] == "performance-monitor"
        assert call_args["level"] == NotificationLevel.WARNING

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_user_action(self, mock_send):
        """Test notify_user_action convenience function."""
        mock_send.return_value = True
        
        await notify_user_action("login", "user123", "Login from new device")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Important User Action"
        assert "user123" in call_args["message"]
        assert "login" in call_args["message"]
        assert "Login from new device" in call_args["message"]
        assert call_args["source"] == "user-action"
        assert call_args["level"] == NotificationLevel.INFO

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_user_action_without_details(self, mock_send):
        """Test notify_user_action without details."""
        mock_send.return_value = True
        
        await notify_user_action("logout", "user456")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert "user456" in call_args["message"]
        assert "logout" in call_args["message"]
        # Should not contain "Details:" when no details provided
        assert "Details:" not in call_args["message"]

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_security_event(self, mock_send):
        """Test notify_security_event convenience function."""
        mock_send.return_value = True
        
        await notify_security_event("Failed Login", "Multiple failed login attempts detected")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["title"] == "Security Event: Failed Login"
        assert call_args["message"] == "Multiple failed login attempts detected"
        assert call_args["source"] == "security"
        assert call_args["level"] == NotificationLevel.CRITICAL

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_security_event_with_custom_source(self, mock_send):
        """Test notify_security_event with custom source."""
        mock_send.return_value = True
        
        await notify_security_event("Breach", "Security breach detected", "firewall")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args["source"] == "firewall"


class TestQuickNotificationShortcuts:
    """Test quick notification shortcut functions."""

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_info(self, mock_send):
        """Test notify_info shortcut function."""
        mock_send.return_value = True
        
        await notify_info("Info Title", "Info message")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0] == ("Info Title", "Info message", "info", NotificationLevel.INFO)

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_info_with_custom_source(self, mock_send):
        """Test notify_info with custom source."""
        mock_send.return_value = True
        
        await notify_info("Info Title", "Info message", "custom-source")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0] == ("Info Title", "Info message", "custom-source", NotificationLevel.INFO)

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_warning(self, mock_send):
        """Test notify_warning shortcut function."""
        mock_send.return_value = True
        
        await notify_warning("Warning Title", "Warning message")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0] == ("Warning Title", "Warning message", "warning", NotificationLevel.WARNING)

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_error(self, mock_send):
        """Test notify_error shortcut function."""
        mock_send.return_value = True
        
        await notify_error("Error Title", "Error message")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0] == ("Error Title", "Error message", "error", NotificationLevel.ERROR)

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notify_critical(self, mock_send):
        """Test notify_critical shortcut function."""
        mock_send.return_value = True
        
        await notify_critical("Critical Title", "Critical message")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0] == ("Critical Title", "Critical message", "critical", NotificationLevel.CRITICAL)


class TestBuildStartupMessage:
    """Test _build_startup_message helper function."""

    @patch("common.startup_notifications.get_server_config")
    @patch("common.startup_notifications.datetime")
    def test_build_startup_message_without_display(self, mock_datetime, mock_get_config):
        """Test building startup message without startup display."""
        # Mock datetime
        mock_datetime.now.return_value.strftime.return_value = "2024-01-01 12:00:00"
        
        # Mock server config
        mock_config = MagicMock()
        mock_config.environment = "development"
        mock_config.port = 8000
        mock_config.get_base_url.return_value = "http://localhost:8000"
        mock_get_config.return_value = mock_config
        
        message = _build_startup_message()
        
        assert "🎯 *Automagik Hive Multi-Agent System*" in message
        assert "📅 Started: 2024-01-01 12:00:00" in message
        assert "🌍 Environment: DEVELOPMENT" in message
        assert "🌐 Port: 8000" in message
        assert "✅ Server started successfully" in message
        assert "🔗 API: http://localhost:8000" in message

    @patch("common.startup_notifications.get_server_config")
    @patch("common.startup_notifications.datetime")
    def test_build_startup_message_with_display(self, mock_datetime, mock_get_config):
        """Test building startup message with startup display."""
        # Mock datetime
        mock_datetime.now.return_value.strftime.return_value = "2024-01-01 12:00:00"
        
        # Mock server config
        mock_config = MagicMock()
        mock_config.environment = "production"
        mock_config.port = 80
        mock_config.get_base_url.return_value = "https://api.example.com"
        mock_get_config.return_value = mock_config
        
        # Mock startup display
        mock_display = MagicMock()
        mock_display.agents = {
            "agent1": {"status": "✅", "version": "1.0"},
            "agent2": {"status": "❌", "version": "latest"}
        }
        mock_display.teams = {
            "team1": {"status": "✅", "version": "2.0"}
        }
        mock_display.workflows = {
            "workflow1": {"status": "✅", "version": "3.0"},
            "workflow2": {"status": "✅", "version": "latest"}
        }
        mock_display.errors = [
            {"component": "agent2", "message": "Failed to initialize agent component"},
            {"component": "db", "message": "Database connection timeout"}
        ]
        
        message = _build_startup_message(startup_display=mock_display)
        
        assert "🎯 *Automagik Hive Multi-Agent System*" in message
        assert "📅 Started: 2024-01-01 12:00:00" in message
        assert "🌍 Environment: PRODUCTION" in message
        assert "🌐 Port: 80" in message
        assert "📊 *System Components:*" in message
        assert "🤖 Agents: 2" in message
        assert "🏢 Teams: 1" in message
        assert "⚡ Workflows: 2" in message
        assert "🤖 *Active Agents:*" in message
        assert "✅ agent1 (v1.0)" in message
        assert "❌ agent2 (latest)" in message
        assert "⚡ *Active Workflows:*" in message
        assert "✅ workflow1 (v3.0)" in message
        assert "✅ workflow2 (latest)" in message
        assert "⚠️ *Issues Found: 2*" in message
        assert "❌ agent2: Failed to initialize agent component..." in message
        assert "❌ db: Database connection timeout..." in message
        assert "🔗 API: https://api.example.com" in message

    @patch("common.startup_notifications.get_server_config")
    @patch("common.startup_notifications.datetime")
    def test_build_startup_message_with_many_errors(self, mock_datetime, mock_get_config):
        """Test building startup message with many errors (truncation)."""
        # Mock datetime and config
        mock_datetime.now.return_value.strftime.return_value = "2024-01-01 12:00:00"
        mock_config = MagicMock()
        mock_config.environment = "test"
        mock_config.port = 3000
        mock_config.get_base_url.return_value = "http://localhost:3000"
        mock_get_config.return_value = mock_config
        
        # Mock startup display with many errors
        mock_display = MagicMock()
        mock_display.agents = {}
        mock_display.teams = {}
        mock_display.workflows = {}
        mock_display.errors = [
            {"component": f"component{i}", "message": f"Error message {i} that is very long and detailed"}
            for i in range(5)
        ]
        
        message = _build_startup_message(startup_display=mock_display)
        
        assert "⚠️ *Issues Found: 5*" in message
        # Should show first 3 errors
        assert "❌ component0: Error message 0 that is very long and detailed..." in message
        assert "❌ component1: Error message 1 that is very long and detailed..." in message
        assert "❌ component2: Error message 2 that is very long and detailed..." in message
        # Should show truncation message
        assert "... and 2 more issues" in message

    @patch("common.startup_notifications.get_server_config")
    @patch("common.startup_notifications.datetime")
    def test_build_startup_message_all_healthy(self, mock_datetime, mock_get_config):
        """Test building startup message with all components healthy."""
        # Mock datetime and config
        mock_datetime.now.return_value.strftime.return_value = "2024-01-01 12:00:00"
        mock_config = MagicMock()
        mock_config.environment = "production"
        mock_config.port = 443
        mock_config.get_base_url.return_value = "https://hive.example.com"
        mock_get_config.return_value = mock_config
        
        # Mock startup display with no errors
        mock_display = MagicMock()
        mock_display.agents = {
            "agent1": {"status": "✅", "version": "1.0"},
            "agent2": {"status": "✅", "version": "2.0"}
        }
        mock_display.teams = {
            "team1": {"status": "✅", "version": "1.0"}
        }
        mock_display.workflows = {
            "workflow1": {"status": "✅", "version": "1.0"}
        }
        mock_display.errors = []
        
        message = _build_startup_message(startup_display=mock_display)
        
        assert "✅ *All systems operational*" in message
        assert "⚠️" not in message  # No warnings


class TestStartupNotificationErrorHandling:
    """Test error handling in startup notifications."""

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notification_function_exception_handling(self, mock_send):
        """Test notification functions handle exceptions gracefully."""
        functions_to_test = [
            (send_error_notification, ("test error",)),
            (send_mcp_server_error, ("server", "error")),
            (send_health_check_notification, ("component", "status", "message")),
            (notify_system_event, ("title", "message")),
            (notify_critical_error, ("title", "message")),
            (notify_performance_issue, ("component", "metric", "value", "threshold")),
            (notify_user_action, ("action", "user")),
            (notify_security_event, ("event", "message")),
        ]
        
        for func, args in functions_to_test:
            mock_send.side_effect = Exception("Notification failed")
            
            # Should not raise exception
            await func(*args)
            
            mock_send.assert_called()
            mock_send.reset_mock()


class TestStartupNotificationIntegration:
    """Test startup notification integration scenarios."""

    @patch("common.startup_notifications.send_notification")
    @patch("asyncio.sleep")
    @pytest.mark.asyncio
    async def test_complete_startup_flow(self, mock_sleep, mock_send):
        """Test complete startup notification flow."""
        mock_send.return_value = True
        
        # Mock complex startup display
        startup_display = MagicMock()
        startup_display.agents = {
            "genie-dev": {"status": "✅", "version": "2.1"},
            "genie-testing": {"status": "✅", "version": "latest"},
            "failing-agent": {"status": "❌", "version": "1.0"}
        }
        startup_display.teams = {
            "dev-team": {"status": "✅", "version": "1.5"}
        }
        startup_display.workflows = {
            "deployment": {"status": "✅", "version": "3.0"},
            "testing": {"status": "✅", "version": "latest"}
        }
        startup_display.errors = [
            {"component": "failing-agent", "message": "Agent failed to load configuration file"}
        ]
        
        # Send startup notification
        await send_startup_notification(startup_display=startup_display)
        
        # Verify asyncio delay
        mock_sleep.assert_called_once_with(0.5)
        
        # Verify notification was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        
        # Verify content includes all components
        message = call_args["message"]
        assert "🤖 Agents: 3" in message
        assert "🏢 Teams: 1" in message
        assert "⚡ Workflows: 2" in message
        assert "✅ genie-dev (v2.1)" in message
        assert "✅ genie-testing (latest)" in message
        assert "❌ failing-agent (v1.0)" in message
        assert "⚠️ *Issues Found: 1*" in message
        assert "failing-agent: Agent failed to load configuration file..." in message

    @patch("common.startup_notifications.send_notification")
    @pytest.mark.asyncio
    async def test_notification_chain(self, mock_send):
        """Test chain of different notification types."""
        mock_send.return_value = True
        
        # Send various notifications
        await send_startup_notification()
        await send_error_notification("Test error")
        await send_mcp_server_error("test-server", "Connection failed")
        await notify_critical_error("Critical issue", "System down")
        await send_shutdown_notification()
        
        # Verify all notifications were sent
        assert mock_send.call_count == 5
        
        # Verify notification types
        call_args_list = mock_send.call_args_list
        assert "🚀 Automagik Hive Server Started" in call_args_list[0][1]["title"]
        assert "Automagik Hive Server Error" in call_args_list[1][1]["title"]
        assert "MCP Server Error: test-server" in call_args_list[2][1]["title"]
        assert "Critical issue" in call_args_list[3][1]["title"]
        assert "Automagik Hive Server Shutdown" in call_args_list[4][1]["title"]