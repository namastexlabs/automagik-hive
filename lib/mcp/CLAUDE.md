# CLAUDE.md - MCP

## Context & Scope

[CONTEXT]
- Explains Model Context Protocol integrations for external services (WhatsApp, Postgres, etc.).
- Covers `.mcp.json` configuration, async lifecycle management, and fallbacks.
- Coordinate with `/CLAUDE.md`, `api/CLAUDE.md`, and `lib/config/CLAUDE.md` before altering MCP wiring.

[CONTEXT MAP]
@lib/mcp/
@lib/mcp/__init__.py
@lib/mcp/connection_manager.py
@lib/mcp/catalog.py
@lib/mcp/exceptions.py
.mcp.json

[SUCCESS CRITERIA]
✅ MCP servers connect, execute, and cleanly close via async context managers.
✅ `.mcp.json` stays in sync with actual integrations.
✅ Agents/teams/workflows specify `mcp_servers` accurately.
✅ Tests cover primary + fallback paths.

[NEVER DO]
❌ Hardcode MCP server details in Python; always update `.mcp.json`.
❌ Ignore connection cleanup or exception handling.
❌ Expose credentials in logs or documentation.
❌ Skip tests for new MCP integrations.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Audit MCP usage
   - Inspect `.mcp.json` and associated helper utilities.
   - Identify agents/workflows relying on the server(s).
   - Review tests around MCP tooling.

2. [Implementation] Update integration
   - Adjust configuration, connection helpers, or exceptions.
   - Provide fallback strategies and retry logic.
   - Document new tools/servers in this guide.

3. [Verification] Validate connectivity
   - Run pytest suites touching MCP code.
   - Execute manual smoke tests (send message, DB query) via MCP.
   - Capture evidence in the active wish/Forge record.
</task_breakdown>
```

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
