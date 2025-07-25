# CLAUDE.md - MCP

🗺️ **Model Context Protocol Integration Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../../CLAUDE.md)  
**🔗 Core**: [AI System](../../ai/CLAUDE.md) | [Config](../config/CLAUDE.md) | [Auth](../auth/CLAUDE.md)  
**🔗 Support**: [API](../../api/CLAUDE.md) | [Logging](../logging/CLAUDE.md) | [Testing](../../tests/CLAUDE.md)

## Purpose

External service integration via Model Context Protocol. Connects agents to WhatsApp Evolution API, databases, memory systems, and other external tools through standardized interfaces.

## Quick Start

**Basic MCP usage**:
```python
from lib.mcp import get_mcp_tools

# Use MCP tools with async context manager
async with get_mcp_tools("whatsapp-server") as tools:
    result = await tools.call_tool("send_message", {
        "number": "+5511999999999",
        "message": "Hello from Automagik Hive!"
    })
```

**Server configuration (.mcp.json)**:
```json
{
  "mcpServers": {
    "whatsapp-server": {
      "type": "sse",
      "url": "http://localhost:8765/mcp/whatsapp/sse"
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
    }
  }
}
```

## Core Features

**SSE Servers**: Real-time streaming (WhatsApp Evolution API, Memory systems)  
**Command Servers**: Process-based tools (Database, file operations, utilities)  
**Connection Management**: Async context managers with proper lifecycle  
**Error Handling**: Graceful fallbacks with retry logic  
**Configuration**: `.mcp.json` file with environment variables

## Agent Integration

**MCP-enabled agent**:
```python
def get_agent_with_mcp_tools(**kwargs):
    config = yaml.safe_load(open("config.yaml"))
    
    return Agent(
        name=config['agent']['name'],
        instructions=config['instructions'],
        mcp_servers=["whatsapp-server", "postgres"],  # Agno integration
        **kwargs
    )
```

**Error handling with fallback**:
```python
from lib.mcp.exceptions import MCPConnectionError

try:
    async with get_mcp_tools("primary-server") as tools:
        result = await tools.call_tool("send_message", data)
except MCPConnectionError:
    # Fallback to alternative server
    async with get_mcp_tools("backup-server") as tools:
        result = await tools.call_tool("send_message", data)
```

## Critical Rules

- **Async Context Managers**: Always use `async with get_mcp_tools()` for proper lifecycle
- **Error Handling**: Implement graceful fallbacks with retry logic
- **Configuration**: Use `.mcp.json` exclusively, never hardcode server configs
- **Connection Cleanup**: Proper resource cleanup to prevent leaks
- **Security**: Never expose sensitive connection details in logs
- **Logging**: Use 🌐 emoji prefix for all MCP operations

## Integration

- **Agents**: MCP servers via `mcp_servers=["server-name"]` in agent factory
- **Teams**: Shared MCP resources across team members
- **Workflows**: MCP tools in step-based processes
- **API**: MCP tools exposed via FastAPI endpoints
- **Storage**: External database access via MCP postgres server

Navigate to [AI System](../../ai/CLAUDE.md) for multi-agent MCP integration or [Auth](../auth/CLAUDE.md) for secure connections.