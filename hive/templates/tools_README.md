# Tools Guide

Add custom capabilities to your agents with tools.

## What is a Tool?

A tool is a function that an agent can call to interact with external systems. Examples:

- Web search
- Database queries
- API calls
- File operations
- Email sending
- Data processing

## Quick Start

### 1. Create Tool Directory

```bash
mkdir -p ai/tools/my-tool
cd ai/tools/my-tool
```

### 2. Create tool.py

```python
"""My custom tool."""
from typing import Any, Dict
from agno.tools import Tool

class MyTool(Tool):
    """Custom tool implementation."""

    id: str = "my-tool"
    description: str = "What this tool does"

    def execute(self, input_data: str, **kwargs) -> Any:
        """Execute the tool."""
        # Implement your logic
        result = f"Processing: {input_data}"
        return result
```

### 3. Add to Agent

```yaml
# In your agent config.yaml
tools:
  - name: "MyTool"
    import_path: "ai.tools.my_tool.MyTool"
```

## Directory Structure

```
ai/tools/
├── examples/           # Pre-built example tools
├── my-tool/
│   └── tool.py         # Tool implementation
└── README.md           # This file
```

## Built-In Tools

Agno includes many built-in tools:

### Web Tools

```yaml
tools:
  - name: "WebSearch"
    import_path: "agno.tools.WebSearch"
```

### Database Tools

```yaml
tools:
  - name: "SQLDatabaseTool"
    import_path: "agno.tools.SQLDatabaseTool"
    config:
      db_url: "postgresql://..."
```

### File Tools

```yaml
tools:
  - name: "FileTools"
    import_path: "agno.tools.FileTools"
```

## Creating Custom Tools

### Simple Tool

```python
"""Weather tool."""
from agno.tools import Tool

class WeatherTool(Tool):
    id: str = "weather"
    description: str = "Get weather information for a city"

    def execute(self, city: str, **kwargs) -> dict:
        """Get weather for a city."""
        # Call weather API or use mock data
        return {
            "city": city,
            "temperature": 72,
            "condition": "Sunny"
        }
```

### Tool with Parameters

```python
"""Calculator tool."""
from typing import Any
from agno.tools import Tool

class Calculator(Tool):
    id: str = "calculator"
    description: str = "Perform mathematical calculations"

    def execute(self, operation: str, a: float, b: float, **kwargs) -> Any:
        """Execute calculation."""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else None,
        }

        func = operations.get(operation)
        if func:
            return func(a, b)
        return None
```

### Tool with Config

```python
"""Database query tool."""
import os
from agno.tools import Tool

class DatabaseTool(Tool):
    id: str = "database"
    description: str = "Query the database"

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.connect()

    def connect(self):
        """Initialize database connection."""
        # Setup connection
        pass

    def execute(self, query: str, **kwargs) -> list:
        """Execute database query."""
        # Run query and return results
        return []
```

## Adding Tools to Agents

### In config.yaml

```yaml
agent:
  name: "Search Agent"
  agent_id: "search-agent"

tools:
  - name: "WebSearch"
    import_path: "agno.tools.WebSearch"

  - name: "MyCustomTool"
    import_path: "ai.tools.my_tool.MyTool"

instructions: |
  You can use the available tools to:
  - Search the web
  - Execute custom operations
```

### In Python

```python
def get_agent(**kwargs) -> Agent:
    from agno.tools import WebSearch
    from ai.tools.my_tool import MyTool

    agent = Agent(
        name="Search Agent",
        tools=[
            WebSearch(),
            MyTool()
        ],
        **kwargs
    )
    return agent
```

## Real-World Examples

### Email Tool

```python
"""Send email tool."""
import smtplib
from typing import Any
from agno.tools import Tool

class EmailTool(Tool):
    id: str = "email"
    description: str = "Send email to recipients"

    def execute(
        self,
        to: str,
        subject: str,
        body: str,
        **kwargs
    ) -> dict:
        """Send an email."""
        try:
            # SMTP logic here
            return {
                "status": "success",
                "message": f"Email sent to {to}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
```

### Slack Tool

```python
"""Post to Slack tool."""
import os
from typing import Any
from agno.tools import Tool

class SlackTool(Tool):
    id: str = "slack"
    description: str = "Post messages to Slack"

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def execute(self, channel: str, message: str, **kwargs) -> dict:
        """Post message to Slack."""
        # Post to webhook
        return {"status": "sent", "channel": channel}
```

### API Integration Tool

```python
"""External API tool."""
import requests
from typing import Any
from agno.tools import Tool

class APITool(Tool):
    id: str = "api"
    description: str = "Call external APIs"

    def execute(self, endpoint: str, method: str = "GET", **kwargs) -> dict:
        """Call an API endpoint."""
        try:
            if method == "GET":
                response = requests.get(endpoint)
            elif method == "POST":
                response = requests.post(endpoint, json=kwargs)
            else:
                return {"error": f"Method {method} not supported"}

            return {
                "status": "success",
                "data": response.json()
            }
        except Exception as e:
            return {"error": str(e)}
```

## Tool Best Practices

### 1. Clear Descriptions

```python
# Good
class MyTool(Tool):
    id: str = "fetch_user_data"
    description: str = "Fetch user information from database by user ID"

# Bad
class MyTool(Tool):
    id: str = "tool"
    description: str = "Get data"
```

### 2. Error Handling

```python
def execute(self, **kwargs) -> dict:
    """Execute with error handling."""
    try:
        result = self._do_work(**kwargs)
        return {
            "status": "success",
            "data": result
        }
    except ValueError as e:
        return {
            "status": "error",
            "error": f"Invalid input: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {e}"
        }
```

### 3. Type Hints

```python
from typing import Any, Dict, List

def execute(
    self,
    query: str,
    limit: int = 10,
    filters: Dict[str, Any] = None
) -> List[dict]:
    """Execute with clear type hints."""
    # Implementation
    return []
```

### 4. Secure Credentials

```python
# Good: Use environment variables
import os

class SecureTool(Tool):
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY not set")

# Bad: Hardcoded credentials
class BadTool(Tool):
    def __init__(self):
        self.api_key = "sk-1234567890"  # Never do this!
```

## Testing Tools

### Direct Testing

```python
from ai.tools.my_tool import MyTool

tool = MyTool()
result = tool.execute("test input")
print(result)
```

### With Agent

```python
from hive.scaffolder.generator import generate_agent_from_yaml

agent = generate_agent_from_yaml(
    "ai/agents/my-agent/config.yaml"
)

# Agent can now use your tool
response = agent.run("Use my-tool to do something")
```

## Troubleshooting

### Tool Not Available in Agent

```bash
# Check import path in config.yaml
cat ai/agents/my-agent/config.yaml | grep import_path

# Verify file exists
ls -la ai/tools/my_tool/tool.py

# Check class name matches
grep "class" ai/tools/my_tool/tool.py
```

### Tool Execution Fails

```python
# Enable debug output
agent = generate_agent_from_yaml(
    "ai/agents/my-agent/config.yaml",
    debug_mode=True
)

# The agent will show tool execution details
```

### Import Errors

```python
# Make sure import path is correct
# Format: "module.path.ClassName"

# Example:
# import_path: "ai.tools.my_tool.MyTool"
# means: from ai.tools.my_tool import MyTool

# Check __init__.py files exist
ls -la ai/tools/__init__.py
ls -la ai/tools/my_tool/__init__.py
```

## Advanced Patterns

### Async Tools

```python
import asyncio
from agno.tools import Tool

class AsyncTool(Tool):
    id: str = "async-tool"
    description: str = "Async tool example"

    async def execute(self, **kwargs) -> Any:
        """Execute asynchronously."""
        result = await self._async_operation(**kwargs)
        return result

    async def _async_operation(self, **kwargs):
        await asyncio.sleep(1)
        return "Done"
```

### Tool with Dependencies

```python
from agno.tools import Tool

class SmartTool(Tool):
    id: str = "smart"
    description: str = "Tool with dependencies"

    def __init__(self):
        self.db = connect_database()
        self.api = initialize_api()

    def execute(self, **kwargs) -> Any:
        db_result = self.db.query(...)
        api_result = self.api.call(...)
        return combine_results(db_result, api_result)
```

## See Also

- [Agents Guide](../agents/README.md) - Add tools to agents
- [Main README](../../README.md) - Project overview
- [Agno Tools Docs](https://docs.agno.com/tools)

Happy building! 🚀
