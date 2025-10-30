# Agents Guide

Learn how to create and manage AI agents in your Hive V2 project.

## What is an Agent?

An agent is an autonomous AI worker with a specific role. It can:
- Answer questions and provide information
- Make decisions based on instructions
- Use tools to interact with external systems
- Store and retrieve conversation history
- Integrate with knowledge bases

## Quick Start

### 1. Create Agent Directory

```bash
mkdir -p ai/agents/my-agent
cd ai/agents/my-agent
```

### 2. Create config.yaml

```yaml
agent:
  name: "My Agent"
  agent_id: "my-agent"
  description: "What this agent does"

model:
  provider: "openai"  # or "anthropic", "gemini", etc.
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a helpful assistant.

  Your role:
  - Help users with [specific task]
  - Be professional and friendly
```

### 3. Create agent.py

```python
"""My agent factory."""
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_my_agent(**kwargs) -> Agent:
    """Create agent from config."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    model = OpenAIChat(id=config["model"]["id"])
    agent = Agent(
        name=config["agent"]["name"],
        model=model,
        instructions=config["instructions"],
        **kwargs
    )
    return agent
```

## Directory Structure

```
ai/agents/
├── examples/           # Pre-built example agents
│   └── support-bot/
│       ├── config.yaml
│       └── agent.py
├── my-agent/          # Your custom agents
│   ├── config.yaml    # Configuration
│   └── agent.py       # Factory function
└── README.md          # This file
```

## Configuration Options

### Agent Config

```yaml
agent:
  name: "Display Name"
  agent_id: "unique-id"  # Used in API calls
  description: "What it does"
  version: "1.0.0"       # Optional
```

### Model Config

```yaml
model:
  provider: "openai"     # or: anthropic, gemini, groq, etc.
  id: "gpt-4o-mini"      # Model identifier
  temperature: 0.7       # 0=deterministic, 1=creative
  max_tokens: 1000       # Optional
  top_p: 0.9            # Optional
```

### Instructions

```yaml
instructions: |
  Your system prompt goes here.

  Be specific about:
  - What the agent should do
  - How it should behave
  - What constraints apply
```

## Adding Features

### 1. Add Tools

```yaml
tools:
  - name: "web_search"
    import_path: "agno.tools.WebSearch"
  - name: "calculator"
    import_path: "agno.tools.CalculatorTool"
```

### 2. Add Knowledge Base

```yaml
knowledge:
  type: "csv"
  source: "data/csv/knowledge.csv"
  num_documents: 5  # Return top 5 documents
```

### 3. Add Storage

```yaml
storage:
  type: "postgres"
  connection: "${HIVE_DATABASE_URL}"
  table_name: "agent_sessions"
  auto_upgrade_schema: true
```

## Testing Your Agent

### Python

```python
from hive.scaffolder.generator import generate_agent_from_yaml

# Load agent
agent = generate_agent_from_yaml("ai/agents/my-agent/config.yaml")

# Test it
response = agent.run("Hello! How can you help?")
print(response)
```

### Command Line

```bash
# If you have a Python script
python -c "
from hive.scaffolder.generator import generate_agent_from_yaml
agent = generate_agent_from_yaml('ai/agents/my-agent/config.yaml')
print(agent.run('Test message'))
"
```

### API

```bash
# Start server first: hive dev

# Then call the agent
curl -X POST http://localhost:8886/agents/my-agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "session_id": "optional-session-id"
  }'
```

## Advanced Features

### Multi-Turn Conversations

```python
agent = generate_agent_from_yaml("ai/agents/my-agent/config.yaml")

# First turn
response1 = agent.run("My name is Alice")
print(response1)

# Second turn - agent remembers context
response2 = agent.run("What's my name?")
print(response2)
```

### Override Configuration

```python
agent = generate_agent_from_yaml(
    "ai/agents/my-agent/config.yaml",
    temperature=0.5,  # Override temperature
    debug_mode=True   # Enable debug output
)
```

### Custom Instructions per Request

```python
agent = generate_agent_from_yaml("ai/agents/my-agent/config.yaml")
response = agent.run(
    "User question here",
    additional_instructions="Please be extra helpful"
)
```

## Best Practices

### 1. Clear Instructions

**Bad:**
```yaml
instructions: |
  You are helpful
```

**Good:**
```yaml
instructions: |
  You are a customer support agent.

  Your responsibilities:
  - Answer account-related questions
  - Provide billing information
  - Escalate to human if needed

  Always:
  - Be professional
  - Verify user identity
  - Explain fees clearly
```

### 2. Appropriate Temperature

- **0.1-0.3**: Factual, deterministic (Q&A, coding)
- **0.5-0.7**: Balanced (general purpose)
- **0.8-1.0**: Creative (brainstorming, writing)

### 3. Use Knowledge Bases

Don't put long context in instructions. Use knowledge bases instead:

```yaml
# Instead of:
instructions: |
  Our policies are:
  - [100 lines of policies]

# Do:
instructions: |
  Use the knowledge base for policy information.

knowledge:
  type: csv
  source: data/csv/policies.csv
```

### 4. Meaningful Agent IDs

```yaml
# Good:
agent_id: "billing-support-agent"
agent_id: "code-reviewer-ai"
agent_id: "research-summarizer"

# Avoid:
agent_id: "agent1"
agent_id: "my-ai"
agent_id: "helper"
```

## Common Patterns

### Customer Support Agent

```yaml
agent:
  name: "Support Agent"
  agent_id: "support-agent"

instructions: |
  You are a customer support specialist.

  When users contact:
  1. Greet them warmly
  2. Understand their issue
  3. Provide a solution or escalate
  4. Confirm resolution

tools:
  - "ticket_system"

knowledge:
  type: csv
  source: "data/csv/support-faq.csv"
```

### Technical Expert Agent

```yaml
agent:
  name: "Technical Expert"
  agent_id: "technical-expert"

model:
  id: "gpt-4o"  # Better for technical topics
  temperature: 0.3  # Precise answers

instructions: |
  You are a technical expert.

  When helping with:
  - Code: Provide working examples
  - Debugging: Ask clarifying questions
  - Architecture: Explain trade-offs

knowledge:
  type: csv
  source: "data/csv/technical-docs.csv"
```

### Research Agent

```yaml
agent:
  name: "Research Assistant"
  agent_id: "research-agent"

instructions: |
  You are a research assistant.

  Your tasks:
  - Gather information on topics
  - Synthesize findings
  - Cite sources
  - Highlight key insights

tools:
  - "web_search"
  - "document_reader"
```

## Troubleshooting

### Agent Not Found

```bash
# Make sure agent_id in config.yaml matches what you're calling
cat ai/agents/my-agent/config.yaml | grep agent_id

# Restart the server to reload agents
hive dev
```

### Weird Responses

```yaml
# Check instructions are clear
instructions: |
  Be specific about what you want the agent to do

# Check temperature is appropriate
model:
  temperature: 0.3  # If too random, lower this

# Enable debug mode
debug_mode: true  # See what's happening
```

### Memory Issues

```yaml
# Limit stored conversations
storage:
  max_sessions: 1000  # Old sessions auto-purge
  session_timeout: 3600  # 1 hour

# Or disable storage
storage: null  # Stateless agent
```

## See Also

- [Teams Guide](../teams/README.md) - Multiple agents working together
- [Workflows Guide](../workflows/README.md) - Multi-step processes
- [Tools Guide](../tools/README.md) - Custom agent capabilities
- [Main README](../../README.md) - Project overview

Happy building! 🚀
