# Slack Notifier Tool

A wrapper around Agno's SlackTools for sending notifications, alerts, and messages to Slack channels.

## Overview

This tool provides a simple interface for Slack integration:

- **Standard Notifications** - Send regular messages to channels
- **Urgent Alerts** - Send high-priority notifications with visual indicators
- **Thread Replies** - Reply within existing message threads
- **Simulation Mode** - Test without Slack credentials

## When to Use This Tool

Use the Slack notifier when:

- Sending automated status updates
- Alerting teams about critical events
- Integrating workflows with team communication
- Building notification systems
- Creating monitoring alerts

**Examples:**
- Deployment notifications
- Error alerts from production
- Daily summary reports
- Customer inquiry notifications
- System health checks

## Structure

```
slack-notifier/
├── config.yaml     # Tool configuration
├── tool.py         # Implementation wrapping SlackTools
└── README.md       # This file
```

## Setup

### 1. Create Slack Bot

1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app or use existing one
3. Add Bot Token Scopes:
   - `chat:write` - Send messages
   - `chat:write.public` - Post to public channels
   - `channels:read` - List channels
4. Install app to workspace
5. Copy Bot User OAuth Token

### 2. Configure Environment

Add to `.env`:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
```

### 3. Invite Bot to Channels

In each Slack channel:
```
/invite @YourBotName
```

## Usage

### Basic Notification

```python
from my_test_project.ai.tools.examples.slack_notifier.tool import get_slack_notifier_tool

# Create tool
notifier = get_slack_notifier_tool()

# Send notification
result = notifier.send_notification(
    message="Deployment completed successfully",
    channel="#deployments"
)

print(f"Status: {result['status']}")
print(f"Message ID: {result['message_id']}")
```

### Urgent Alerts

```python
# Send urgent notification with visual indicators
result = notifier.send_alert(
    message="Database connection lost - immediate attention required",
    channel="#alerts"
)

# Urgent messages are prefixed with 🚨 *URGENT* 🚨
```

### Thread Replies

```python
# Reply to existing thread
result = notifier.send_thread_reply(
    message="Issue has been resolved",
    channel="#alerts",
    thread_ts="1234567890.123456"  # Original message timestamp
)
```

### Check Configuration

```python
notifier = get_slack_notifier_tool()

if notifier.is_configured:
    print("✅ Slack integration ready")
else:
    print("⚠️  Running in simulation mode - add SLACK_BOT_TOKEN")
```

## Integration with Agents

### Agent with Slack Notifications

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from my_test_project.ai.tools.examples.slack_notifier.tool import get_slack_notifier_tool

def get_notifier_agent(**kwargs):
    notifier = get_slack_notifier_tool()

    def send_slack_message(message: str, channel: str = "#notifications"):
        """Send message to Slack."""
        result = notifier.send_notification(message=message, channel=channel)
        return result

    return Agent(
        name="Notification Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[send_slack_message],
        instructions="""You can send notifications to Slack.
        Use the send_slack_message tool when asked to notify someone.""",
        **kwargs
    )

# Usage
agent = get_notifier_agent()
response = agent.run("Notify the team that the release is ready in #releases")
```

### Workflow with Slack Notifications

```python
from agno.workflow import Workflow, Step, StepOutput

notifier = get_slack_notifier_tool()

def deploy_and_notify(step_input) -> StepOutput:
    """Deploy and send Slack notification."""

    # Simulate deployment
    deploy_result = deploy_application()

    # Notify team
    notifier.send_notification(
        message=f"Deployment {deploy_result['version']} completed successfully",
        channel="#deployments"
    )

    return StepOutput(content="Deployment and notification complete")

workflow = Workflow(
    name="Deploy with Notifications",
    steps=[Step(name="Deploy", function=deploy_and_notify)]
)
```

## Configuration (config.yaml)

```yaml
tool:
  name: "Slack Notifier"
  tool_id: "slack-notifier"
  version: "1.0.0"

  parameters:
    default_channel: "#notifications"  # Default target
    timeout_seconds: 30                # Request timeout
    retry_attempts: 3                  # Retry failed sends
    include_timestamp: true            # Add timestamps

  integration:
    slack_config:
      use_slack_tools: true
      bot_token_env: "SLACK_BOT_TOKEN"  # Environment variable
      default_icon: ":robot_face:"      # Bot emoji
      username: "Automagik Bot"         # Display name
```

## Customization

### Change Default Channel

Edit `config.yaml`:
```yaml
parameters:
  default_channel: "#your-channel"
```

### Customize Bot Appearance

```yaml
integration:
  slack_config:
    default_icon: ":rocket:"
    username: "Deploy Bot"
```

### Add Custom Formatting

Modify `_format_message()` in `tool.py`:

```python
def _format_message(self, message: str, urgent: bool) -> str:
    """Add custom formatting."""
    if urgent:
        return f"🚨 *URGENT* 🚨\n\n{message}"

    # Add custom formatting
    return f":robot_face: {message}"
```

## Advanced Features

### Rich Message Formatting

```python
# Use Slack's mrkdwn format
result = notifier.send_notification(
    message="""
*Deployment Summary*
• Environment: Production
• Version: v2.1.0
• Status: ✅ Success
• Duration: 3m 45s

<https://dashboard.example.com|View Dashboard>
""",
    channel="#deployments"
)
```

### Batch Notifications

```python
channels = ["#team-a", "#team-b", "#team-c"]
message = "System maintenance scheduled for tonight"

results = []
for channel in channels:
    result = notifier.send_notification(message=message, channel=channel)
    results.append(result)

print(f"Sent to {len([r for r in results if r['status'] == 'success'])} channels")
```

### Error Handling

```python
try:
    result = notifier.send_notification(
        message="Important update",
        channel="#general"
    )

    if result['status'] == 'success':
        print(f"Message sent: {result['message_id']}")
    elif result['status'] == 'simulated':
        print("⚠️  Running in simulation mode")
    else:
        print(f"Error: {result.get('error')}")

except Exception as e:
    print(f"Failed to send notification: {e}")
```

## Testing

Run the standalone test:

```bash
cd /home/cezar/automagik/automagik-hive/my-test-project
python -m ai.tools.examples.slack_notifier.tool
```

Expected output:
- Tool initialization
- Configuration status
- Simulation of 3 notification types
- Results summary

## Simulation Mode

Without `SLACK_BOT_TOKEN`, tool runs in simulation mode:

```
📱 Simulated Slack Notification:
   Channel: #alerts
   Urgent: True
   Message:
🚨 *URGENT* 🚨

Database connection failed
```

Perfect for:
- Development without Slack access
- Testing notification logic
- CI/CD environments
- Demo purposes

## Integration with Tool Registry

Add to your tool registry:

```python
from ai.tools.examples.slack_notifier.tool import get_slack_notifier_tool

tools = {
    "slack-notifier": get_slack_notifier_tool,
    # ... other tools
}
```

## Related Examples

- **research-workflow** - Sequential workflow with notifications
- **parallel-workflow** - Parallel processing with alerts
- **csv-analyzer** - Data analysis tool example

## Best Practices

1. **Use appropriate channels** - Route messages to relevant channels
2. **Reserve urgency** - Only mark truly urgent items
3. **Keep messages concise** - Slack favors brief, actionable messages
4. **Use threads** - Reply in threads to keep channels clean
5. **Handle errors gracefully** - Always check result status
6. **Rate limit awareness** - Slack has rate limits for messages
7. **Test in dev channels** - Use test channels before production

## Troubleshooting

**"No SLACK_BOT_TOKEN found"**
- Add token to `.env` file
- Verify environment variable name matches config
- Restart application after adding token

**Messages not appearing**
- Check bot is invited to channel
- Verify channel name includes `#`
- Confirm bot has `chat:write` scope

**Permission errors**
- Add required bot scopes in Slack API dashboard
- Reinstall app to workspace
- Check bot permissions in channel

**Rate limit errors**
- Implement delays between messages
- Use batch operations sparingly
- Cache message IDs to avoid duplicates

## Learn More

- [Agno SlackTools Documentation](https://docs.agno.com/tools/slack)
- [Slack API Documentation](https://api.slack.com/docs)
- [Bot Token Scopes](https://api.slack.com/scopes)
- [Slack Message Formatting](https://api.slack.com/reference/surfaces/formatting)

## Security Notes

- **Never commit tokens** - Always use environment variables
- **Rotate tokens regularly** - Update tokens periodically
- **Limit bot permissions** - Only grant necessary scopes
- **Monitor usage** - Watch for unauthorized access
- **Use workspace apps** - Prefer workspace apps over user tokens
