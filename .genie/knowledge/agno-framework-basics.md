# Agno Framework Basics - Complete Reference

**Research Date:** 2025-10-30
**Sources:** Agno Documentation, Automagik Hive Codebase, Integration Tests
**Status:** Production-Ready Patterns

---

## Table of Contents

1. [Minimal Agent Creation](#minimal-agent-creation)
2. [Agent Execution Patterns](#agent-execution-patterns)
3. [Model Configuration](#model-configuration)
4. [Instructions Patterns](#instructions-patterns)
5. [Tools Integration](#tools-integration)
6. [Storage Configuration](#storage-configuration)
7. [Best Practices](#best-practices)
8. [Common Patterns from Production Code](#common-patterns-from-production-code)

---

## Minimal Agent Creation

### Basic Import Pattern

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
```

### Simplest Working Agent

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

# Create agent with minimal configuration
agent = Agent(
    model=Claude(id="claude-sonnet-4-5-20250929"),
    markdown=True
)

# Run agent
agent.print_response("Hello, how are you?")
```

### Agent with Name and Instructions

```python
agent = Agent(
    name="My Assistant",
    model=Claude(id="claude-sonnet-4-5-20250929"),
    instructions="You are a helpful assistant. Answer questions clearly and concisely.",
    markdown=True
)
```

### Production-Ready Agent Pattern

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

def create_agent(**kwargs):
    """Factory function for agent creation."""
    agent = Agent(
        name="Production Agent",
        model=Claude(
            id="claude-3-5-haiku-20241022",
            temperature=0.7
        ),
        instructions="You are a helpful assistant.",
        markdown=True,
        **kwargs  # Runtime overrides
    )

    # Set agent_id as instance attribute (NOT in constructor)
    agent.agent_id = "my-agent"

    return agent
```

---

## Agent Execution Patterns

### 1. Synchronous Execution (.run)

```python
# Basic run - returns RunOutput object
response = agent.run("What is 2+2?")
print(response.content)  # Access content attribute
```

### 2. Asynchronous Execution (.arun)

```python
import asyncio

async def main():
    response = await agent.arun("What is the capital of France?")
    print(response.content)

asyncio.run(main())
```

### 3. Print Response (Convenience Method)

```python
# Directly print response to terminal
agent.print_response("Tell me a joke")
```

### 4. Multi-Turn Conversations

```python
async def conversation():
    # Turn 1: Set context
    response1 = await agent.arun("My favorite color is blue.")
    print(response1.content)

    # Turn 2: Agent remembers context
    response2 = await agent.arun("What is my favorite color?")
    print(response2.content)  # Will mention "blue"
```

### 5. Concurrent Requests

```python
import asyncio

async def concurrent_queries():
    agents = [create_agent() for _ in range(3)]
    queries = [
        "What is 2+2?",
        "What is the capital of Japan?",
        "Name a primary color."
    ]

    # Run all concurrently
    responses = await asyncio.gather(
        *[agent.arun(query) for agent, query in zip(agents, queries)]
    )

    for i, response in enumerate(responses):
        print(f"Response {i}: {response.content}")
```

---

## Model Configuration

### OpenAI Models

```python
from agno.models.openai import OpenAIChat

# Basic OpenAI model
model = OpenAIChat(id="gpt-4o-mini")

# With temperature control
model = OpenAIChat(
    id="gpt-4o-mini",
    temperature=0.7  # 0.0 = deterministic, 1.0 = creative
)

# Fast model for simple tasks
fast_model = OpenAIChat(id="gpt-4o-mini", temperature=0.0)

# Creative model for writing
creative_model = OpenAIChat(id="gpt-4o", temperature=0.9)
```

### Anthropic Models (Claude)

```python
from agno.models.anthropic import Claude

# Latest Claude Sonnet
model = Claude(id="claude-sonnet-4-5-20250929")

# Haiku (fastest, cheapest)
model = Claude(
    id="claude-3-5-haiku-20241022",
    temperature=0.7
)

# With temperature
model = Claude(
    id="claude-3-5-haiku-20241022",
    temperature=0.0  # Deterministic for math/logic
)
```

### API Key Management

**Environment Variables** (Recommended):

```bash
# Export in shell or .env file
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**In Code** (Not Recommended):

```python
# Agno automatically reads from environment
# No need to pass API keys explicitly
agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))
```

### Model Selection by Use Case

```python
# Simple queries, fast response
simple_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", temperature=0.7)
)

# Complex reasoning
complex_agent = Agent(
    model=Claude(id="claude-sonnet-4-5-20250929", temperature=0.7)
)

# Math and logic (deterministic)
math_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini", temperature=0.0)
)

# Creative writing
creative_agent = Agent(
    model=Claude(id="claude-3-5-haiku-20241022", temperature=0.9)
)
```

---

## Instructions Patterns

### Basic Instructions

```python
agent = Agent(
    model=model,
    instructions="You are a helpful assistant. Answer questions clearly and concisely."
)
```

### Domain-Specific Instructions

```python
# Customer Support Agent
support_agent = Agent(
    model=model,
    instructions="""You are a customer support specialist.

    Your role:
    - Provide friendly, professional assistance
    - Answer questions clearly and concisely
    - Escalate complex issues when needed
    - Always maintain a positive tone
    """
)

# Math Specialist
math_agent = Agent(
    model=model,
    instructions="""You are a math specialist.

    Guidelines:
    - Solve mathematical problems step by step
    - Show your work clearly
    - Provide the final answer in this format: ANSWER: [number]
    - Double-check calculations for accuracy
    """
)

# Creative Writer
writer_agent = Agent(
    model=model,
    instructions="""You are a creative writing assistant.

    Your approach:
    - Generate engaging, original content
    - Be creative but stay on topic
    - Adapt style to the requested format
    - Maintain consistent voice and tone
    """
)
```

### Multi-Section Instructions

```python
instructions = """
## Role
You are a technical documentation assistant.

## Capabilities
- Write clear, concise technical documentation
- Explain complex concepts simply
- Provide code examples when relevant
- Follow industry best practices

## Guidelines
- Use active voice
- Include examples
- Organize with headers
- Keep explanations brief

## Output Format
- Use markdown formatting
- Include code blocks for examples
- Add bullet points for lists
"""

agent = Agent(model=model, instructions=instructions)
```

### Instructions Best Practices

1. **Be Specific**: Define role, capabilities, and constraints
2. **Use Structure**: Headers, bullets, sections for clarity
3. **Include Examples**: Show expected behavior
4. **Set Boundaries**: Clarify what agent should/shouldn't do
5. **Define Format**: Specify output structure when needed

---

## Tools Integration

### Built-in Agno Tools

```python
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.shell import ShellTools
from agno.tools.python import PythonTools

# Agent with web search
search_agent = Agent(
    model=model,
    tools=[DuckDuckGoTools()],
    instructions="Use web search to find up-to-date information."
)

# Agent with shell access
dev_agent = Agent(
    model=model,
    tools=[ShellTools()],
    instructions="You can run shell commands to help with development tasks."
)
```

### Custom Tools (Functions)

```python
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle.

    Args:
        length: Length of rectangle
        width: Width of rectangle

    Returns:
        Area in square units
    """
    return length * width

# Agent with custom tool
agent = Agent(
    model=model,
    tools=[calculate_area],
    instructions="You can calculate areas using the calculate_area tool."
)
```

### Multiple Tools

```python
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools

def custom_tool(query: str) -> str:
    """Custom processing function."""
    return f"Processed: {query}"

# Agent with multiple tools
agent = Agent(
    model=model,
    tools=[
        DuckDuckGoTools(),
        PythonTools(),
        custom_tool
    ],
    instructions="Use appropriate tools to answer questions."
)
```

### Tool Return Types

Agno supports various tool return types:

```python
def dict_tool() -> dict:
    """Returns dictionary."""
    return {"key": "value"}

def list_tool() -> list:
    """Returns list."""
    return [1, 2, 3]

def generator_tool():
    """Yields values."""
    for i in range(5):
        yield i

# All work with Agno
agent = Agent(
    model=model,
    tools=[dict_tool, list_tool, generator_tool]
)
```

---

## Storage Configuration

### SQLite Storage (Development)

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=model,
    db=SqliteDb(db_file="agno.db"),
    add_history_to_context=True  # Enable conversation history
)
```

### PostgreSQL Storage (Production)

```python
from agno.agent import Agent
from agno.storage.postgres import PostgresStorage

agent = Agent(
    model=model,
    storage=PostgresStorage(
        table_name="my_agent_sessions",
        db_url="postgresql://user:pass@localhost/db",
        auto_upgrade_schema=True  # Auto-migrate schema
    ),
    add_history_to_context=True
)
```

### Storage Configuration from Environment

```python
import os
from agno.storage.postgres import PostgresStorage

def create_agent_with_storage():
    storage = PostgresStorage(
        table_name="agent_sessions",
        db_url=os.getenv("HIVE_DATABASE_URL"),
        auto_upgrade_schema=True
    )

    return Agent(
        model=model,
        storage=storage,
        add_history_to_context=True
    )
```

---

## Best Practices

### 1. Factory Pattern for Agents

```python
def get_agent(**kwargs):
    """Create agent with factory pattern."""
    agent = Agent(
        name=kwargs.get("name", "Default Agent"),
        model=kwargs.get("model", Claude(id="claude-3-5-haiku-20241022")),
        instructions=kwargs.get("instructions", "You are a helpful assistant."),
        markdown=True
    )

    # Set agent_id as instance attribute
    if "agent_id" in kwargs:
        agent.agent_id = kwargs["agent_id"]

    return agent
```

### 2. Configuration-Driven Agents

```python
import yaml

def create_agent_from_config(config_path: str):
    """Create agent from YAML configuration."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract config sections
    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Create model
    if model_config.get("provider") == "openai":
        model = OpenAIChat(
            id=model_config.get("id"),
            temperature=model_config.get("temperature", 0.7)
        )
    elif model_config.get("provider") == "anthropic":
        model = Claude(
            id=model_config.get("id"),
            temperature=model_config.get("temperature", 0.7)
        )

    # Create agent
    agent = Agent(
        name=agent_config.get("name"),
        model=model,
        instructions=config.get("instructions"),
        markdown=True
    )

    if agent_config.get("agent_id"):
        agent.agent_id = agent_config["agent_id"]

    return agent
```

### 3. Error Handling

```python
async def safe_agent_run(agent, query: str):
    """Run agent with error handling."""
    try:
        response = await agent.arun(query)
        return response.content
    except Exception as e:
        print(f"Agent error: {e}")
        return None
```

### 4. Response Validation

```python
async def validated_run(agent, query: str):
    """Run with response validation."""
    response = await agent.arun(query)

    # Validate response
    if not response or not response.content:
        raise ValueError("Empty response from agent")

    if len(response.content) < 10:
        raise ValueError("Response too short")

    return response.content
```

### 5. Timeout Handling

```python
import asyncio

async def run_with_timeout(agent, query: str, timeout: float = 30.0):
    """Run agent with timeout."""
    try:
        response = await asyncio.wait_for(
            agent.arun(query),
            timeout=timeout
        )
        return response.content
    except asyncio.TimeoutError:
        print(f"Agent timed out after {timeout}s")
        return None
```

---

## Common Patterns from Production Code

### Pattern 1: Test Agent Factory (from Automagik Hive)

```python
def create_test_agent(config: dict, model_override=None):
    """Create agent from config dict (production pattern)."""
    from agno.models.anthropic import Claude
    from agno.models.openai import OpenAIChat

    # Resolve model
    if model_override:
        model = model_override
    else:
        model_config = config.get("model", {})
        provider = model_config.get("provider", "openai")
        model_id = model_config.get("id", "gpt-4o-mini")
        temperature = model_config.get("temperature", 0.7)

        if provider == "openai":
            model = OpenAIChat(id=model_id, temperature=temperature)
        elif provider == "anthropic":
            model = Claude(id=model_id, temperature=temperature)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # Create agent
    agent_config = config.get("agent", {})
    agent = Agent(
        name=agent_config.get("name", "Test Agent"),
        model=model,
        instructions=config.get("instructions", "You are a helpful assistant."),
        markdown=True
    )

    # Set agent_id if provided
    if "agent_id" in agent_config:
        agent.agent_id = agent_config["agent_id"]

    return agent
```

### Pattern 2: Quality Validation (from Integration Tests)

```python
def validate_response(response: str, criteria: dict) -> dict:
    """Validate agent response quality."""
    results = {
        "has_content": bool(response and response.strip()),
        "min_length": len(response) >= criteria.get("min_length", 0),
        "contains_keywords": False,
        "not_error": "error" not in response.lower()
    }

    # Check keywords
    keywords = criteria.get("should_contain", [])
    if keywords:
        results["contains_keywords"] = any(
            kw.lower() in response.lower() for kw in keywords
        )
    else:
        results["contains_keywords"] = True

    return results

def calculate_quality_score(results: dict) -> float:
    """Calculate quality score (0.0 - 1.0)."""
    return sum(results.values()) / len(results)
```

### Pattern 3: Retry Logic with Backoff

```python
import asyncio

async def retry_agent_run(
    agent,
    query: str,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """Execute agent run with exponential backoff."""
    delay = initial_delay

    for attempt in range(max_attempts):
        try:
            return await agent.arun(query)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise  # Re-raise on final attempt

            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= backoff_factor
```

### Pattern 4: Agent with Multiple Configurations

```python
# Standard configs from production
TEST_AGENT_CONFIGS = {
    "simple": {
        "agent": {
            "name": "Simple Agent",
            "agent_id": "simple-agent",
            "version": 1
        },
        "model": {
            "provider": "openai",
            "id": "gpt-4o-mini",
            "temperature": 0.7
        },
        "instructions": "You are a helpful assistant."
    },
    "math_specialist": {
        "agent": {
            "name": "Math Specialist",
            "agent_id": "math-specialist",
            "version": 1
        },
        "model": {
            "provider": "openai",
            "id": "gpt-4o-mini",
            "temperature": 0.0  # Deterministic
        },
        "instructions": """You are a math specialist.
        Solve problems step by step.
        Format: ANSWER: [number]"""
    },
    "creative_writer": {
        "agent": {
            "name": "Creative Writer",
            "agent_id": "creative-writer",
            "version": 1
        },
        "model": {
            "provider": "anthropic",
            "id": "claude-3-5-haiku-20241022",
            "temperature": 0.9  # Creative
        },
        "instructions": """You are a creative assistant.
        Generate engaging, original content."""
    }
}

# Usage
agent = create_test_agent(TEST_AGENT_CONFIGS["math_specialist"])
```

---

## Quick Reference

### Minimal Agent (3 Lines)

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
agent = Agent(model=Claude(id="claude-sonnet-4-5-20250929"))
```

### Production Agent (10 Lines)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    name="My Agent",
    model=OpenAIChat(id="gpt-4o-mini", temperature=0.7),
    instructions="You are a helpful assistant.",
    markdown=True
)
agent.agent_id = "my-agent"
response = await agent.arun("Hello!")
```

### Complete Agent Factory (20 Lines)

```python
import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_agent(**kwargs):
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    agent = Agent(
        name=config["agent"]["name"],
        model=OpenAIChat(
            id=config["model"]["id"],
            temperature=config["model"]["temperature"]
        ),
        instructions=config["instructions"],
        markdown=True,
        **kwargs
    )
    agent.agent_id = config["agent"]["agent_id"]
    return agent
```

---

## Key Takeaways

1. **Agent Creation**: Import Agent + Model → Instantiate → Set agent_id as attribute
2. **Execution**: Use `.run()` sync, `.arun()` async, or `.print_response()` convenience
3. **Models**: Configure via model objects (OpenAIChat, Claude) with id + temperature
4. **Instructions**: String-based, can be multi-line, structured with markdown
5. **Tools**: Pass list of functions or Agno tool classes
6. **Storage**: PostgreSQL for production, SQLite for development
7. **Best Practice**: Use factory pattern + YAML configs for production agents

---

**End of Document**
