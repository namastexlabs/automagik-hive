# Storage Configuration Guide

Complete guide to configuring persistent storage for agents, teams, and workflows in Automagik Hive.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Factory Pattern](#factory-pattern)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Overview

Hive provides **automatic storage configuration** through YAML files. When you define a `storage:` section in your agent/team/workflow config, Hive's `ConfigGenerator` automatically creates and attaches the appropriate database instance.

### Key Benefits

✅ **Zero Boilerplate** - No manual database setup in Python code
✅ **Automatic Session Persistence** - Sessions saved automatically to PostgreSQL
✅ **API-Ready** - `/api/v1/sessions` endpoints work out of the box
✅ **Hot Reload** - Update storage config without code changes
✅ **Type-Safe** - Full integration with Agno's `PostgresDb` class

## Quick Start

### Step 1: Configure Storage in YAML

```yaml
# ai/agents/my-agent/config.yaml
agent:
  name: my-agent
  model: openai:gpt-4o-mini

storage:
  type: postgres
  connection: ${HIVE_DATABASE_URL}
  table_name: my_agent_sessions

instructions: |
  You are a helpful assistant...
```

### Step 2: Set Environment Variable

```bash
# .env
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/hive_db
```

### Step 3: Use ConfigGenerator (Recommended Pattern)

```python
# ai/agents/my-agent/agent.py
from pathlib import Path
from agno.agent import Agent
from hive.scaffolder.generator import generate_agent_from_yaml

def get_my_agent(**kwargs) -> Agent:
    """Create agent with automatic storage configuration."""
    config_path = Path(__file__).parent / "config.yaml"
    return generate_agent_from_yaml(str(config_path), **kwargs)
```

**That's it!** Storage is automatically configured and sessions persist to PostgreSQL.

## Configuration Reference

### Storage Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ Yes | Storage backend type (`postgres` or `sqlite`) |
| `connection` | string | ⚠️ Conditional | Database connection string (required for PostgreSQL) |
| `table_name` | string | ❌ No | Table name for sessions (default: `agent_sessions`) |

### PostgreSQL Configuration

```yaml
storage:
  type: postgres
  connection: ${HIVE_DATABASE_URL}  # From environment variable
  table_name: my_custom_sessions_table
```

**Connection String Format:**
```
postgresql://username:password@host:port/database
```

**Environment Variable Fallback:**
- If `connection` is omitted, Hive uses `HIVE_DATABASE_URL` environment variable
- Throws clear error if neither is provided

### SQLite Configuration

```yaml
storage:
  type: sqlite
  db_file: ./data/my_agent.db  # Local SQLite file
  table_name: sessions
```

**Note:** SQLite is great for development but PostgreSQL is recommended for production.

## Factory Pattern

### ✅ Recommended: Use ConfigGenerator

**Hive's ConfigGenerator automatically handles storage** - this is the recommended pattern for all agents/teams/workflows:

```python
from pathlib import Path
from agno.agent import Agent
from hive.scaffolder.generator import generate_agent_from_yaml

def get_my_agent(**kwargs) -> Agent:
    config_path = Path(__file__).parent / "config.yaml"
    return generate_agent_from_yaml(str(config_path), **kwargs)
```

**Benefits:**
- ✅ 3 lines instead of 50+
- ✅ Automatic storage initialization
- ✅ Tool loading, knowledge setup, model parsing
- ✅ Consistent behavior across all components
- ✅ All Hive examples use this pattern

### ❌ Not Recommended: Manual Factory Pattern

Before Hive v1.0.0rc6, examples used manual YAML parsing. **This pattern is deprecated** and doesn't support storage:

```python
# ❌ OLD PATTERN - DO NOT USE
def get_my_agent(**kwargs) -> Agent:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    model = OpenAIChat(id=config["model"]["id"])
    tools = [FileTools()]

    # ❌ Storage config is ignored!
    # db = ???  <- Not initialized

    return Agent(
        name=config["agent"]["name"],
        model=model,
        tools=tools,
        **kwargs
    )
```

**Problems:**
- ❌ Ignores `storage:` config in YAML
- ❌ Duplicate boilerplate across every factory
- ❌ No automatic database initialization
- ❌ Sessions don't persist
- ❌ `/api/v1/sessions` endpoints fail

**Solution:** Use `generate_agent_from_yaml()` instead (see recommended pattern above).

## Troubleshooting

### Issue: "RuntimeError: coroutine raised StopIteration"

**Cause:** Agent/team doesn't have `db` attribute set, so AgentOS can't discover databases.

**Solution:** Use `generate_agent_from_yaml()` factory pattern:

```python
# ✅ CORRECT - Uses ConfigGenerator
from hive.scaffolder.generator import generate_agent_from_yaml

def get_my_agent(**kwargs):
    return generate_agent_from_yaml("config.yaml", **kwargs)
```

### Issue: "Environment variable not set: HIVE_DATABASE_URL"

**Cause:** Storage config references `${HIVE_DATABASE_URL}` but it's not in your `.env` file.

**Solution:** Add database URL to `.env`:

```bash
# .env
HIVE_DATABASE_URL=postgresql://localhost:5432/hive_db
```

### Issue: "PostgreSQL storage requires 'connection' in config or HIVE_DATABASE_URL"

**Cause:** No database connection specified in YAML and no `HIVE_DATABASE_URL` environment variable.

**Solution:** Either add connection to YAML or set environment variable:

```yaml
# Option 1: Explicit in YAML
storage:
  type: postgres
  connection: postgresql://localhost:5432/hive_db
```

```bash
# Option 2: Environment variable (recommended)
export HIVE_DATABASE_URL=postgresql://localhost:5432/hive_db
```

### Issue: Sessions not persisting

**Checklist:**

1. ✅ Using `generate_agent_from_yaml()` factory?
2. ✅ `storage:` section defined in YAML?
3. ✅ `HIVE_DATABASE_URL` environment variable set?
4. ✅ PostgreSQL running and accessible?
5. ✅ Database/table exists and has correct permissions?

**Verify storage is enabled:**

```python
agent = get_my_agent()
print(f"Database: {'Enabled' if agent.db else 'Disabled'}")
# Should print: Database: Enabled
```

## Examples

### Example 1: Agent with Storage

```yaml
# ai/agents/support-bot/config.yaml
agent:
  name: support-bot
  id: support-bot
  model: openai:gpt-4o-mini

storage:
  type: postgres
  connection: ${HIVE_DATABASE_URL}
  table_name: support_bot_sessions

tools:
  - FileTools
  - DuckDuckGoTools

instructions: |
  You are a customer support agent...
```

```python
# ai/agents/support-bot/agent.py
from pathlib import Path
from agno.agent import Agent
from hive.scaffolder.generator import generate_agent_from_yaml

def get_support_bot(**kwargs) -> Agent:
    config_path = Path(__file__).parent / "config.yaml"
    return generate_agent_from_yaml(str(config_path), **kwargs)
```

**Usage:**

```python
from ai.agents.support_bot import get_support_bot

# Create agent with persistent sessions
agent = get_support_bot()

# Run with session ID - automatically persisted
response = agent.run("Hello!", session_id="user_123")

# Sessions are stored in PostgreSQL table: support_bot_sessions
```

### Example 2: Team with Storage

```yaml
# ai/teams/dev-team/config.yaml
team:
  name: "Development Team"
  team_id: "dev-team"
  mode: "collaborate"

model:
  provider: "openai"
  id: "gpt-4o-mini"

storage:
  type: postgres
  table_name: "dev_team_sessions"

members:
  - planner
  - coder
  - reviewer

instructions: |
  You are a collaborative development team...
```

```python
# ai/teams/dev-team/team.py
from pathlib import Path
from agno.team import Team
from hive.scaffolder.generator import generate_team_from_yaml

def get_dev_team(**kwargs) -> Team:
    config_path = Path(__file__).parent / "config.yaml"
    return generate_team_from_yaml(str(config_path), **kwargs)
```

### Example 3: Multiple Agents with Shared Database

All agents can use the same PostgreSQL database with different table names:

```yaml
# Agent 1
storage:
  type: postgres
  connection: ${HIVE_DATABASE_URL}
  table_name: agent1_sessions

# Agent 2
storage:
  type: postgres
  connection: ${HIVE_DATABASE_URL}
  table_name: agent2_sessions
```

Each agent gets its own isolated table for session storage.

### Example 4: Development vs Production

Use environment variables to switch between SQLite (dev) and PostgreSQL (prod):

```yaml
# config.yaml
storage:
  type: ${STORAGE_TYPE}  # postgres or sqlite
  connection: ${DATABASE_URL}
  table_name: my_sessions
```

```bash
# Development (.env.dev)
STORAGE_TYPE=sqlite
DATABASE_URL=./dev.db

# Production (.env.prod)
STORAGE_TYPE=postgres
DATABASE_URL=postgresql://prod-host:5432/prod_db
```

## API Integration

When storage is configured, AgentOS automatically discovers databases and enables session endpoints:

### List Sessions

```bash
GET /api/v1/sessions/{agent_name}

# Example
curl http://localhost:8886/api/v1/sessions/support-bot
```

**Response:**
```json
[
  {
    "session_id": "user_123",
    "messages": [...],
    "created_at": "2024-01-08T10:30:00Z",
    "updated_at": "2024-01-08T10:35:00Z"
  }
]
```

### Get Specific Session

```bash
GET /api/v1/sessions/{agent_name}/{session_id}
```

### Create/Update Session

Sessions are created automatically when you call `agent.run()` with a `session_id`.

## Best Practices

### 1. Always Use ConfigGenerator

```python
# ✅ GOOD
from hive.scaffolder.generator import generate_agent_from_yaml
agent = generate_agent_from_yaml("config.yaml")

# ❌ BAD
with open("config.yaml") as f:
    config = yaml.safe_load(f)
    # Manual parsing ignores storage config
```

### 2. Use Environment Variables for Connection Strings

```yaml
# ✅ GOOD - Secure and environment-specific
storage:
  connection: ${HIVE_DATABASE_URL}

# ❌ BAD - Hardcoded credentials
storage:
  connection: postgresql://admin:password123@localhost/db
```

### 3. Unique Table Names per Agent

```yaml
# ✅ GOOD
storage:
  table_name: support_bot_sessions

# ❌ POTENTIALLY CONFUSING
storage:
  table_name: sessions  # Shared by all agents
```

### 4. Test Storage Configuration

```python
def get_my_agent(**kwargs):
    agent = generate_agent_from_yaml("config.yaml", **kwargs)

    # Verify storage is enabled
    if not agent.db:
        raise RuntimeError("Storage configuration failed!")

    return agent
```

## Migration Guide

### Migrating from Manual Factory Pattern

If you have existing agents using the manual factory pattern:

**Before:**
```python
def get_my_agent(**kwargs):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    model = OpenAIChat(id=config["model"]["id"])
    tools = [FileTools()]

    return Agent(
        name=config["agent"]["name"],
        model=model,
        tools=tools,
        **kwargs
    )
```

**After:**
```python
from hive.scaffolder.generator import generate_agent_from_yaml

def get_my_agent(**kwargs):
    return generate_agent_from_yaml("config.yaml", **kwargs)
```

**Benefits:**
- 50+ lines → 3 lines
- Storage automatically configured
- Tool loading handled
- Knowledge setup handled
- Model parsing handled
- Future-proof

## Additional Resources

- [Agno Documentation](https://docs.agno.com)
- [Hive Examples](../hive/examples/)
- [GitHub Issue #117](https://github.com/namastexlabs/automagik-hive/issues/117)
- [ConfigGenerator Source](../hive/scaffolder/generator.py)

## Support

Having issues? Check:

1. [Troubleshooting](#troubleshooting) section above
2. [GitHub Issues](https://github.com/namastexlabs/automagik-hive/issues)
3. [Discord Community](https://discord.gg/xcW8c7fF3R)
