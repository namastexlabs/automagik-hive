# WhatsApp Notifier Agent

This agent handles WhatsApp notifications using MCP (Model Context Protocol) tools for integration with Evolution API.

## Overview

The WhatsApp Notifier Agent is designed to send notifications via WhatsApp using MCP tools, replacing the previous native implementation. This provides better integration with the Agno framework and supports the Evolution API configuration.

## Key Features

- **MCP Integration**: Uses MCP tools for WhatsApp functionality
- **Evolution API Support**: Configured for Evolution API v2
- **Clean Architecture**: Dedicated agent for notification handling
- **Environment Configuration**: Uses environment variables for API settings

## Environment Variables

Required environment variables:
```bash
EVOLUTION_API_BASE_URL=http://192.168.112.142:8080
EVOLUTION_API_API_KEY=BEE0266C2040-4D83-8FAA-A9A3EF89DDEF
EVOLUTION_API_INSTANCE=SofIA
EVOLUTION_API_FIXED_RECIPIENT=5511986780008@s.whatsapp.net  # Optional
```

## MCP Integration

### Current State
- Agent is configured to use MCP tools when available
- Simulates MCP calls for demonstration/testing
- Ready for production MCP server integration

### Production Setup
To use actual MCP tools in production:

1. **Install MCP WhatsApp Server**: Set up the MCP server for WhatsApp
2. **Configure MCPTools**: Add MCPTools to the agent's tools list
3. **Update Agent**: Replace simulation calls with actual MCP function calls

Example production configuration:
```python
async with MCPTools(command="mcp-server-whatsapp") as mcp_tools:
    agent = Agent(
        name="WhatsApp Notifier",
        model=Claude(id="claude-sonnet-4-20250514"),
        tools=[mcp_tools],
        instructions=instructions
    )
```

## Usage

### From Workflows
```python
from agents.whatsapp_notifier.agent import get_whatsapp_notifier

# Get the notifier agent
notifier = await get_whatsapp_notifier("pagbank_support")

# Send a message
result = await notifier.send_message(
    message="Hello from PagBank!",
    number="+5511999999999"  # Optional if fixed recipient is set
)
```

### Direct Function Call
```python
from agents.whatsapp_notifier.agent import send_whatsapp_notification

result = await send_whatsapp_notification(
    message="Urgent notification",
    number="+5511999999999",
    instance="pagbank_support"
)
```

## Integration with Human Handoff Workflow

The human handoff workflow now uses this agent for WhatsApp notifications:

1. **Escalation Detection**: Workflow detects need for human escalation
2. **Protocol Generation**: Creates escalation protocol with unique ID
3. **WhatsApp Notification**: Uses this agent to send notifications to support teams
4. **Team Routing**: Messages are routed to appropriate teams based on business unit

## Message Templates

The agent supports structured notifications with templates:

### Escalation Template
```
🚨 *Escalação PagBank*

📋 *Protocolo:* ESC-SESSION-20250714123456
👤 *Cliente:* João Silva
⚠️ *Urgência:* HIGH

📝 *Descrição:*
Cliente relatando problema com PIX que não está funcionando há 2 horas.
Valor envolvido: R$ 5.000,00

🕐 *Horário:* 14/07/2025 12:34
```

## Business Unit Routing

Messages are automatically routed to appropriate teams:

- **Adquirência**: +5511999999001 (machines, anticipation, sales)
- **Emissão**: +5511999999002 (cards, limits, invoices)  
- **PagBank**: +5511999999003 (account, PIX, app, transfers)
- **General**: +5511999999000 (fraud, security, disputes)

## Architecture Benefits

1. **Separation of Concerns**: Dedicated agent for WhatsApp functionality
2. **MCP Compliance**: Follows Agno framework patterns
3. **Testability**: Easy to test and mock for development
4. **Scalability**: Can be extended for other notification channels
5. **Maintainability**: Centralized WhatsApp logic

## Migration from Native Implementation

This agent replaces the previous native `send_whatsapp_message` function:

### Before (Native)
```python
from agents.tools.agent_tools import send_whatsapp_message

result = send_whatsapp_message("Hello World")
```

### After (MCP)
```python
from agents.whatsapp_notifier.agent import send_whatsapp_notification

result = await send_whatsapp_notification("Hello World")
```

## Testing

The agent includes simulation mode for testing without actual WhatsApp sends:

```python
# Agent automatically detects test environment
# and simulates MCP calls with proper result structure
result = await notifier.send_message("Test message")
assert result["success"] == True
assert "mcp_send_text_message" in result["method"]
```

## Future Enhancements

- **Media Support**: Add support for images, documents, audio
- **Template Engine**: Dynamic template system with variables
- **Delivery Tracking**: Message delivery confirmation
- **Rate Limiting**: Built-in rate limiting for API compliance
- **Retry Logic**: Automatic retry for failed messages
- **Analytics**: Message delivery analytics and reporting