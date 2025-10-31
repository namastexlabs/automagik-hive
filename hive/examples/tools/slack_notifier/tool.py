"""
Slack Notifier Tool

A wrapper around Agno's SlackTools for sending notifications to Slack.
Demonstrates tool integration with external services.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from agno.tools.slack import SlackTools


class SlackNotifierTool:
    """
    Slack notification tool with enhanced features.

    Wraps Agno's SlackTools to provide:
    - Simple notification interface
    - Urgent message handling
    - Thread support
    - Channel defaults
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialize Slack notifier tool.

        Args:
            config_path: Path to config.yaml (defaults to same directory)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        # Load configuration
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.tool_config = self.config.get("tool", {})
        self.params = self.tool_config.get("parameters", {})
        self.integration = self.tool_config.get("integration", {}).get("slack_config", {})

        # Initialize SlackTools
        self.slack = None
        self._initialize_slack()

    def _initialize_slack(self):
        """Initialize Agno SlackTools if token available."""
        token = os.getenv(self.integration.get("bot_token_env", "SLACK_BOT_TOKEN"))

        if not token:
            print(f"⚠️  {self.integration.get('bot_token_env')} not found in environment")
            print("   Tool will run in simulation mode")
            self.slack = None
        else:
            self.slack = SlackTools(
                token=token,
                username=self.integration.get("username", "Automagik Bot"),
                icon_emoji=self.integration.get("default_icon", ":robot_face:"),
            )
            print("✅ Slack integration initialized")

    def send_notification(
        self, message: str, channel: str | None = None, thread_ts: str | None = None, urgent: bool = False
    ) -> dict[str, Any]:
        """
        Send a notification to Slack.

        Args:
            message: Message content to send
            channel: Target channel (defaults to config default)
            thread_ts: Thread timestamp for replies
            urgent: Mark as urgent (adds prefix)

        Returns:
            Dict with status and result information
        """
        try:
            # Use default channel if not specified
            target_channel = channel or self.params.get("default_channel", "#notifications")

            # Format message
            formatted_message = self._format_message(message, urgent)

            # Send notification
            if self.slack:
                result = self.slack.send_message(channel=target_channel, text=formatted_message, thread_ts=thread_ts)

                return {
                    "status": "success",
                    "channel": target_channel,
                    "message_id": result.get("ts"),
                    "message": formatted_message,
                    "urgent": urgent,
                }
            else:
                # Simulation mode
                return self._simulate_send(target_channel, formatted_message, urgent)

        except Exception as e:
            return {"status": "error", "error": str(e), "channel": channel, "message": message}

    def _format_message(self, message: str, urgent: bool) -> str:
        """
        Format message with optional urgent prefix.

        Args:
            message: Original message
            urgent: Whether message is urgent

        Returns:
            Formatted message string
        """
        if urgent:
            return f"🚨 *URGENT* 🚨\n\n{message}"

        # Add timestamp if configured
        if self.params.get("include_timestamp", True):
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"[{timestamp}] {message}"

        return message

    def _simulate_send(self, channel: str, message: str, urgent: bool) -> dict[str, Any]:
        """
        Simulate sending message (when no token available).

        Args:
            channel: Target channel
            message: Formatted message
            urgent: Urgency flag

        Returns:
            Simulated result dict
        """
        print("\n📱 Simulated Slack Notification:")
        print(f"   Channel: {channel}")
        print(f"   Urgent: {urgent}")
        print(f"   Message:\n{message}\n")

        return {
            "status": "simulated",
            "channel": channel,
            "message_id": "simulated-msg-123",
            "message": message,
            "urgent": urgent,
            "note": "No SLACK_BOT_TOKEN found - running in simulation mode",
        }

    def send_thread_reply(self, message: str, channel: str, thread_ts: str) -> dict[str, Any]:
        """
        Send a reply in an existing thread.

        Args:
            message: Reply message
            channel: Channel containing thread
            thread_ts: Thread timestamp to reply to

        Returns:
            Result dict with status
        """
        return self.send_notification(message=message, channel=channel, thread_ts=thread_ts, urgent=False)

    def send_alert(self, message: str, channel: str | None = None) -> dict[str, Any]:
        """
        Send an urgent alert notification.

        Args:
            message: Alert message
            channel: Target channel (optional)

        Returns:
            Result dict with status
        """
        return self.send_notification(message=message, channel=channel, urgent=True)

    @property
    def is_configured(self) -> bool:
        """Check if tool is properly configured with Slack token."""
        return self.slack is not None


# Factory function for tool registry
def get_slack_notifier_tool(**kwargs) -> SlackNotifierTool:
    """
    Create Slack notifier tool instance.

    Args:
        **kwargs: Runtime overrides

    Returns:
        SlackNotifierTool: Configured tool instance
    """
    return SlackNotifierTool()


# Quick test function
if __name__ == "__main__":
    print("Testing Slack Notifier Tool...")

    # Create tool
    tool = get_slack_notifier_tool()
    print(f"✅ Tool created: {tool.tool_config.get('name')}")
    print(f"✅ Version: {tool.tool_config.get('version')}")
    print(f"✅ Configured: {tool.is_configured}")

    # Test notifications
    print("\n📨 Testing notifications...\n")

    # Standard notification
    result1 = tool.send_notification(message="System startup complete", channel="#general")
    print(f"Standard notification: {result1['status']}")

    # Urgent notification
    result2 = tool.send_alert(message="Database connection failed - immediate attention required", channel="#alerts")
    print(f"Urgent alert: {result2['status']}")

    # Thread reply
    result3 = tool.send_thread_reply(
        message="Investigation complete - issue resolved", channel="#alerts", thread_ts="1234567890.123456"
    )
    print(f"Thread reply: {result3['status']}")

    print("\n✅ All tests completed")
    print("\nNote: Add SLACK_BOT_TOKEN to .env for real Slack integration")
