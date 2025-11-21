# Agent Implementation Patterns

This directory contains example agents demonstrating different implementation patterns available in Automagik Hive.

## Pattern Overview

Automagik Hive supports two agent implementation patterns:

1. **YAML-Only Pattern** - Pure configuration, no Python code required
2. **Python Factory Pattern** - Programmatic control with Python factory function

## YAML-Only Pattern (Recommended for Beginners)

### When to Use

- Simple agents with static configuration
- Declarative instructions and settings
- No custom initialization logic needed
- Non-technical team members need to edit agents

### Example: researcher

The `researcher` agent demonstrates pure YAML configuration.

**Structure:**
```
researcher/
├── config.yaml    # Complete agent configuration
└── README.md      # Agent documentation
```

**Pros:**
- No Python knowledge required
- Easier to maintain and read
- Faster to create and modify
- Version control friendly
- Auto-discovered by Hive

**Cons:**
- Limited to static configuration
- Cannot add custom logic or dynamic behavior
- No runtime conditionals or complex initialization

### YAML-Only Example

```yaml
agent:
  name: researcher
  id: researcher
  description: Web research agent that searches and synthesizes information

model:
  id: gpt-4o
  temperature: 0.7

instructions: |
  You are a research assistant that helps users find information.

  Your capabilities:
  - Search and summarize information
  - Compare different sources
  - Provide cited references

tools:
  - PythonTools
  - FileTools
```

**Usage:**
```python
from hive.discovery import discover_agents

# Auto-discovered from YAML
agents = discover_agents()
researcher = agents['researcher']

# Use the agent
response = researcher.run("Summarize AI trends in 2025")
print(response.content)
```

## Python Factory Pattern (Advanced)

### When to Use

- Dynamic tool loading based on runtime conditions
- Custom initialization logic
- Complex model selection
- Advanced state management
- Runtime validation or preprocessing

### Example: support-bot

The `support-bot` agent demonstrates the Python factory pattern.

**Structure:**
```
support-bot/
├── config.yaml    # Base configuration
├── agent.py       # Custom factory function
└── README.md      # Agent documentation
```

**Pros:**
- Full programmatic control
- Dynamic behavior based on runtime conditions
- Custom tool loading and validation
- Complex initialization logic
- Can override or extend YAML config

**Cons:**
- Requires Python knowledge
- More code to maintain
- Harder for non-developers to modify

### Python Factory Example

```python
"""Support Bot Agent"""

from pathlib import Path
import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.file import FileTools


def get_support_bot_agent(**kwargs) -> Agent:
    """Create support-bot agent with YAML configuration.

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Agent: Configured agent instance
    """
    # Load YAML configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract config sections
    agent_config = config.get("agent", {})
    model_config = config.get("model", {})

    # Create Model instance
    model = OpenAIChat(
        id=model_config.get("id"),
        temperature=model_config.get("temperature", 0.7)
    )

    # Prepare tools (can add custom logic here)
    tools = [FileTools()]

    # Build agent parameters
    agent_params = {
        "name": agent_config.get("name"),
        "model": model,
        "instructions": config.get("instructions"),
        "description": agent_config.get("description"),
        "tools": tools if tools else None,
        **kwargs,
    }

    # Create agent
    agent = Agent(**agent_params)

    # Set agent id as instance attribute
    if agent_config.get("id"):
        agent.id = agent_config.get("id")

    return agent
```

**Usage:**
```python
from hive.discovery import discover_agents

# Python factory takes precedence
agents = discover_agents()
support_bot = agents['support-bot']

# Use the agent with custom kwargs
response = support_bot.run(
    "How do I reset my password?",
    session_id="user-123"
)
print(response.content)
```

## Pattern Decision Guide

| Requirement | YAML-Only | Python Factory |
|-------------|-----------|----------------|
| Static instructions | ✅ Perfect | ⚠️ Overkill |
| Fixed model configuration | ✅ Perfect | ⚠️ Overkill |
| Dynamic tool loading | ❌ Not possible | ✅ Required |
| Runtime model selection | ❌ Not possible | ✅ Required |
| Custom initialization | ❌ Not possible | ✅ Required |
| Environment-based config | ❌ Not possible | ✅ Required |
| Non-technical team edits | ✅ Easy | ❌ Harder |
| Version control diffs | ✅ Clean | ⚠️ Code diffs |

## Discovery Behavior

The `discover_agents()` function handles both patterns:

1. **YAML-Only**: Loads agent directly from `config.yaml`
2. **Python Factory**: Imports and calls `get_{agent_name}_agent()` function

**Priority**: Python factory takes precedence if both exist.

### Discovery Example

```python
from hive.discovery import discover_agents

# Discovers all agents in hive/ai/agents/ and hive/examples/agents/
agents = discover_agents()

# Available agents:
# - 'researcher' (YAML-only)
# - 'support-bot' (Python factory)
# - 'code-reviewer' (Python factory)

print(f"Found {len(agents)} agents:")
for agent_id, agent in agents.items():
    print(f"  - {agent_id}: {agent.name}")
```

## Migration Path

### Starting with YAML-Only

Most agents should start with YAML-only:

```bash
# Create YAML-only agent
hive create agent my-bot

# Edit config.yaml
vim hive/ai/agents/my-bot/config.yaml

# Test it
hive dev
```

### Upgrading to Python Factory

When you need custom logic, add Python:

```bash
# Create agent.py in existing agent directory
cd hive/ai/agents/my-bot

# Create factory function
cat > agent.py << 'EOF'
"""My Bot Agent"""

from pathlib import Path
import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_my_bot_agent(**kwargs) -> Agent:
    """Create my-bot agent with custom logic."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Add custom logic here
    # ...

    agent = Agent(...)
    agent.id = config["agent"]["id"]
    return agent
EOF
```

The Python factory will now take precedence, but can still load base config from `config.yaml`.

## Development Workflow

### Testing Individual Agents

#### YAML-Only Agent
```bash
# Load via discovery
uv run python -c "
from hive.discovery import discover_agents
agents = discover_agents()
response = agents['researcher'].run('Test query')
print(response.content)
"
```

#### Python Factory Agent
```bash
# Test factory directly
cd hive/examples/agents/support-bot
uv run python agent.py

# Or via discovery
uv run python -c "
from hive.discovery import discover_agents
agents = discover_agents()
response = agents['support-bot'].run('Test query')
print(response.content)
"
```

### Validating Discovery

```bash
# List all discovered agents
uv run python -c "
from hive.discovery import discover_agents
agents = discover_agents()
print(f'Discovered {len(agents)} agents:')
for agent_id in agents:
    print(f'  - {agent_id}')
"
```

## Best Practices

### YAML-Only Pattern

1. **Keep it simple**: If you need complex logic, use Python factory
2. **Use clear instructions**: Make agent behavior explicit in YAML
3. **Document tools**: List all tools needed in config.yaml
4. **Version carefully**: YAML changes affect all agent instances

### Python Factory Pattern

1. **Load from YAML first**: Use YAML as base config, override in Python
2. **Follow naming convention**: `get_{agent_name}_agent(**kwargs)`
3. **Accept kwargs**: Allow runtime overrides via `**kwargs`
4. **Set agent.id**: Always set `agent.id` as instance attribute
5. **Document custom logic**: Explain why Python factory is needed

### Both Patterns

1. **Consistent structure**: Keep agent directories organized
2. **Test thoroughly**: Verify agent works via discovery
3. **Document usage**: Create clear README for each agent
4. **Version bump**: Increment version in config.yaml on changes

## Troubleshooting

### Agent Not Discovered

```bash
# Check agent directory structure
ls -la hive/ai/agents/my-agent/

# Expected for YAML-only:
# config.yaml

# Expected for Python factory:
# config.yaml
# agent.py
```

### Import Errors

```bash
# For Python factory, ensure function name matches pattern
# get_{agent_name}_agent

# Example: agent named "my-bot" needs:
def get_my_bot_agent(**kwargs) -> Agent:
    ...
```

### YAML Validation Errors

```bash
# Validate YAML syntax
uv run python -c "
import yaml
with open('hive/ai/agents/my-agent/config.yaml') as f:
    config = yaml.safe_load(f)
    print('Valid YAML')
    print(config)
"
```

## Example Agents Summary

| Agent | Pattern | Purpose | Model | Tools |
|-------|---------|---------|-------|-------|
| **researcher** | YAML-Only | Information gathering and synthesis | GPT-4o | PythonTools, FileTools |
| **support-bot** | Python Factory | Customer support with knowledge base | GPT-4o | FileTools |
| **code-reviewer** | Python Factory | Python code analysis and review | Claude Sonnet 4 | PythonTools, FileTools |

## Next Steps

1. Review the example agents in this directory
2. Choose the pattern that fits your use case
3. Create your first agent using `hive create agent`
4. Test discovery to verify your agent loads correctly
5. Iterate and expand your agent's capabilities

## Additional Resources

- **Main Documentation**: See project README for full Automagik Hive docs
- **Agent CLAUDE.md**: @hive/ai/agents/CLAUDE.md for detailed guidance
- **Discovery Documentation**: @hive/discovery/CLAUDE.md for discovery internals
- **CLI Documentation**: @hive/cli/CLAUDE.md for command-line usage

---

**Questions?** Check the main project documentation or explore the example agents to learn more.
