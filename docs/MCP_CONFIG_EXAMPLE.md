# MCP Configuration Example for PagBank

This document shows how to properly configure MCP tools for the PagBank Multi-Agent System.

## .mcp.json Configuration

Here's the complete configuration for Evolution API integration:

```json
{
  "mcpServers": {
    "evolution-api": {
      "command": "uvx",
      "args": [
        "automagik-tools@0.7.3",
        "tool",
        "evolution-api"
      ],
      "env": {
        "EVOLUTION_API_BASE_URL": "http://192.168.112.142:8080",
        "EVOLUTION_API_API_KEY": "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF",
        "EVOLUTION_API_INSTANCE": "SofIA",
        "EVOLUTION_API_FIXED_RECIPIENT": "5511986780008@s.whatsapp.net"
      }
    }
  }
}
```

## Environment Variables Alternative

You can also set these as environment variables in your system:

```bash
export EVOLUTION_API_BASE_URL="http://192.168.112.142:8080"
export EVOLUTION_API_API_KEY="BEE0266C2040-4D83-8FAA-A9A3EF89DDEF"
export EVOLUTION_API_INSTANCE="SofIA"
export EVOLUTION_API_FIXED_RECIPIENT="5511986780008@s.whatsapp.net"
```

## Using in Code

### Option 1: Command String Format

```python
from agno.tools.mcp import MCPTools

# Using command string
mcp_tools = MCPTools(
    command="uvx automagik-tools@0.7.3 tool evolution-api",
    env={
        "EVOLUTION_API_BASE_URL": "http://192.168.112.142:8080",
        "EVOLUTION_API_API_KEY": "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF",
        "EVOLUTION_API_INSTANCE": "SofIA",
        "EVOLUTION_API_FIXED_RECIPIENT": "5511986780008@s.whatsapp.net"
    }
)
```

### Option 2: Separate Command and Args

```python
from agno.tools.mcp import MCPTools

# Using separate command and args (if supported)
mcp_tools = MCPTools(
    command="uvx",
    args=["automagik-tools@0.7.3", "tool", "evolution-api"],
    env={
        "EVOLUTION_API_BASE_URL": "http://192.168.112.142:8080",
        "EVOLUTION_API_API_KEY": "BEE0266C2040-4D83-8FAA-A9A3EF89DDEF",
        "EVOLUTION_API_INSTANCE": "SofIA",
        "EVOLUTION_API_FIXED_RECIPIENT": "5511986780008@s.whatsapp.net"
    }
)
```

## Tool Usage in Agent

Once configured, the Evolution API tool will be available as:

```
mcp_evolution-api_send_message
```

You can use it in agent prompts like:

```python
prompt = """Use the mcp_evolution-api_send_message tool to send this WhatsApp message:

Hello! This is a test message from PagBank.

Send it to the configured recipient."""
```

## Troubleshooting

1. **Tool Not Found**: Ensure the tool name matches exactly: `mcp_evolution-api_send_message`
2. **Connection Error**: Verify the Evolution API URL is accessible from your network
3. **Authentication Error**: Check that the API key is correct
4. **Version Error**: Make sure you're using automagik-tools version 0.7.3 or later

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure vaults for production
- Rotate API keys regularly
- Consider using IP whitelisting for the Evolution API server