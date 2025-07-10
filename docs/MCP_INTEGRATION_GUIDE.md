# MCP Tools Integration Guide for Agno Agents

This guide explains how to properly integrate MCP (Model Context Protocol) tools in Agno agents, with a focus on handling async/sync contexts and practical examples.

## Table of Contents
1. [Basic MCP Tools Integration](#basic-mcp-tools-integration)
2. [Handling Async MCP Tools in Synchronous Agents](#handling-async-mcp-tools-in-synchronous-agents)
3. [WhatsApp/Evolution API Integration Example](#whatsappevolution-api-integration-example)
4. [Best Practices](#best-practices)
5. [Common Issues and Solutions](#common-issues-and-solutions)

## Basic MCP Tools Integration

### 1. Simple Async Integration (Recommended)

The cleanest way to use MCP tools is in an async context:

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

async def run_agent_with_mcp():
    # Initialize MCP tools with a command
    async with MCPTools(command="uvx mcp-server-git") as mcp_tools:
        # Create agent with MCP tools
        agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            tools=[mcp_tools],
            instructions=["You are a helpful assistant."],
            markdown=True,
            show_tool_calls=True,
        )
        
        # Run agent asynchronously
        await agent.aprint_response("What is the license for this project?", stream=True)

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_agent_with_mcp())
```

### 2. Integration with Environment Variables

For tools like Evolution API that need environment configuration:

```python
import os
from agno.tools.mcp import MCPTools

# Configure environment
env = {
    **os.environ,
    "EVOLUTION_API_BASE_URL": "http://192.168.112.142:8080",
    "EVOLUTION_API_API_KEY": "YOUR_API_KEY",
    "EVOLUTION_API_INSTANCE": "SofIA",
    "EVOLUTION_API_FIXED_RECIPIENT": "5511999999999@s.whatsapp.net"
}

# Create MCP tools with custom environment
mcp_tools = MCPTools(
    command="uvx automagik-tools@0.7.3 tool evolution-api",
    env=env
)
```

## Handling Async MCP Tools in Synchronous Agents

When integrating MCP tools in synchronous agent contexts (like the PagBank agents), you need to handle the async nature properly:

### Option 1: Initialize at Agent Creation (Using asyncio)

```python
import asyncio
import logging
from agno.tools.mcp import MCPTools

class MySpecialistAgent:
    def __init__(self):
        self.logger = logging.getLogger("my_agent")
        self.mcp_tools = None
        self._init_mcp_tools()
    
    def _init_mcp_tools(self):
        """Initialize MCP tools in a synchronous context"""
        try:
            # Create MCP tools instance
            self.mcp_tools = MCPTools(
                command="uvx automagik-tools@0.7.3 tool evolution-api",
                env=self._get_env_config()
            )
            
            # Handle async initialization
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create a task
                    asyncio.create_task(self.mcp_tools.initialize())
                else:
                    # If no loop is running, run the initialization
                    loop.run_until_complete(self.mcp_tools.initialize())
            except RuntimeError:
                # No event loop exists, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.mcp_tools.initialize())
                
            self.logger.info("MCP tools initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP tools: {e}")
            self.mcp_tools = None
```

### Option 2: Use nest_asyncio (For Complex Cases)

When running in environments like Jupyter or where event loops conflict:

```python
import nest_asyncio
import asyncio
from agno.tools.mcp import MCPTools

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

async def initialize_mcp_tools():
    async with MCPTools(command="uvx mcp-server-git") as mcp_tools:
        # Your agent code here
        pass

# Can now run even if there's already an event loop
asyncio.run(initialize_mcp_tools())
```

### Option 3: Synchronous Wrapper for MCP Tools

Create a synchronous wrapper for agents that must remain synchronous:

```python
import asyncio
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

class SyncMCPToolsWrapper:
    """Synchronous wrapper for MCP tools"""
    
    def __init__(self, command: str, env: Optional[Dict[str, str]] = None):
        self.command = command
        self.env = env
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loop = None
        self._mcp_tools = None
        self._initialize()
    
    def _initialize(self):
        """Initialize MCP tools in a separate thread with its own event loop"""
        def init_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            
            async def init_tools():
                from agno.tools.mcp import MCPTools
                self._mcp_tools = MCPTools(command=self.command, env=self.env)
                await self._mcp_tools.initialize()
            
            loop.run_until_complete(init_tools())
            return loop
        
        self._executor.submit(init_in_thread).result()
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call an MCP tool synchronously"""
        def run_in_thread():
            async def call():
                # This would need to be adapted based on actual MCP tool interface
                return await self._mcp_tools.call(tool_name, **kwargs)
            
            return self._loop.run_until_complete(call())
        
        return self._executor.submit(run_in_thread).result()
    
    def cleanup(self):
        """Clean up resources"""
        if self._loop:
            self._loop.close()
        self._executor.shutdown()
```

## WhatsApp/Evolution API Integration Example

Here's a complete example of integrating WhatsApp messaging through Evolution API MCP:

```python
import asyncio
import os
from typing import Dict, Any
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

class WhatsAppNotificationAgent:
    """Agent that can send WhatsApp messages via Evolution API"""
    
    def __init__(self):
        self.mcp_tools = None
        self.agent = None
        
    async def initialize(self):
        """Initialize the agent with MCP tools"""
        # Configure Evolution API environment
        env = {
            **os.environ,
            "EVOLUTION_API_BASE_URL": "http://your-evolution-api:8080",
            "EVOLUTION_API_API_KEY": "your-api-key",
            "EVOLUTION_API_INSTANCE": "your-instance",
            "EVOLUTION_API_FIXED_RECIPIENT": "5511999999999@s.whatsapp.net"
        }
        
        # Initialize MCP tools
        self.mcp_tools = MCPTools(
            command="uvx automagik-tools@0.7.3 tool evolution-api",
            env=env
        )
        await self.mcp_tools.initialize()
        
        # Create agent with MCP tools
        self.agent = Agent(
            model=Claude(id="claude-sonnet-4-20250514"),
            tools=[self.mcp_tools],
            instructions=[
                "You are a WhatsApp notification agent.",
                "Use the mcp_evolution-api_send_message tool to send messages.",
                "Format messages professionally with emojis when appropriate."
            ],
            show_tool_calls=True,
            markdown=True
        )
    
    async def send_notification(self, message: str) -> Dict[str, Any]:
        """Send a WhatsApp notification"""
        prompt = f"""Use the mcp_evolution-api_send_message tool to send this message:

{message}

Make sure to send it to the configured recipient."""
        
        response = await self.agent.arun(prompt)
        return {"success": True, "response": response}
    
    async def cleanup(self):
        """Clean up resources"""
        if self.mcp_tools:
            # MCP tools cleanup is handled by context manager
            pass

# Usage example
async def main():
    notifier = WhatsAppNotificationAgent()
    await notifier.initialize()
    
    # Send a notification
    result = await notifier.send_notification(
        "🚨 URGENT: System alert detected. Please check immediately."
    )
    print(result)
    
    await notifier.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

### 1. Always Use Context Managers

```python
async with MCPTools(command="...") as mcp_tools:
    # Your code here
    pass
# Resources are automatically cleaned up
```

### 2. Handle Initialization Errors

```python
try:
    mcp_tools = MCPTools(command="uvx mcp-server-git")
    await mcp_tools.initialize()
except Exception as e:
    logger.error(f"Failed to initialize MCP tools: {e}")
    # Fallback logic or graceful degradation
```

### 3. Pass MCP Tools to Agent Tools List

```python
agent = Agent(
    model=model,
    tools=[mcp_tools],  # MCP tools added to agent's tool list
    # other parameters...
)
```

### 4. Use Proper Tool Names

When prompting the agent to use MCP tools, use the exact tool name:

```python
# The tool name format is typically: mcp_<server-name>_<action>
prompt = "Use the mcp_evolution-api_send_message tool to send a WhatsApp message..."
```

## Common Issues and Solutions

### Issue 1: Event Loop Already Running

**Error**: `RuntimeError: This event loop is already running`

**Solution**: Use one of these approaches:
```python
# Option 1: Use nest_asyncio
import nest_asyncio
nest_asyncio.apply()

# Option 2: Create task instead of run_until_complete
if loop.is_running():
    asyncio.create_task(mcp_tools.initialize())
else:
    loop.run_until_complete(mcp_tools.initialize())
```

### Issue 2: MCP Tools Not Found by Agent

**Problem**: Agent doesn't recognize MCP tool commands

**Solution**: Ensure tools are properly added to agent:
```python
# Correct
agent = Agent(tools=[mcp_tools])

# Also ensure the agent uses the exact tool name in prompts
```

### Issue 3: Environment Variables Not Passed

**Problem**: MCP server doesn't receive configuration

**Solution**: Pass environment explicitly:
```python
env = {
    **os.environ,  # Include existing environment
    "MY_API_KEY": "value",
    # other variables...
}
mcp_tools = MCPTools(command="...", env=env)
```

### Issue 4: Synchronous Context Conflicts

**Problem**: Need to use MCP tools in synchronous code

**Solution**: Use the synchronous wrapper pattern or initialize at startup:
```python
# Initialize once at startup
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(initialize_mcp_tools())

# Then use in synchronous code
agent.run(prompt)  # Agent internally handles async tools
```

## Alternative: Direct API Integration

If MCP tools integration proves too complex, consider direct API integration:

```python
from agno.tools import tool
import httpx

@tool(show_result=True)
def send_whatsapp_message(message: str, recipient: str = None) -> str:
    """Send a WhatsApp message via Evolution API"""
    url = "http://your-evolution-api:8080/message/send"
    headers = {"apikey": "your-api-key"}
    
    data = {
        "instance": "your-instance",
        "to": recipient or "5511999999999@s.whatsapp.net",
        "message": {"text": message}
    }
    
    response = httpx.post(url, json=data, headers=headers)
    return f"Message sent: {response.status_code}"

# Use with agent
agent = Agent(
    model=model,
    tools=[send_whatsapp_message],
    instructions=["You can send WhatsApp messages using the send_whatsapp_message tool."]
)
```

## Conclusion

MCP tools provide powerful integrations for Agno agents, but require careful handling of async/sync contexts. Choose the integration approach that best fits your architecture:

1. **Pure Async**: Cleanest approach for new projects
2. **Async with Sync Wrapper**: For existing synchronous codebases
3. **Direct Tool Integration**: When MCP adds unnecessary complexity

Always test your integration thoroughly and handle errors gracefully to ensure reliable agent operations.