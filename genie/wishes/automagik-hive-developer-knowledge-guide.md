# Automagik Hive Developer Knowledge Guide

## 🎯 Overview

Automagik Hive is an enterprise multi-agent AI framework built on **Agno (agno-agi/agno)** that enables rapid development of sophisticated multi-agent systems through YAML configuration. This guide provides comprehensive knowledge for developers to be productive with the codebase immediately.

## 🗺️ Codebase Architecture

### Core Structure
```
automagik-hive/
├── ai/                    # Multi-agent system core
│   ├── agents/           # Individual agent implementations
│   ├── teams/            # Team routing and coordination
│   ├── workflows/        # Multi-step orchestration
│   └── tools/            # Shared agent capabilities
├── api/                  # FastAPI service layer
├── lib/                  # Shared services and utilities
├── tests/               # Testing infrastructure
└── pyproject.toml       # UV package management
```

### Key Technologies
- **Framework**: Agno (agno-agi/agno) - Multi-agent framework
- **Database**: PostgreSQL with pgvector for embeddings
- **Package Manager**: UV (never use pip directly)
- **API**: FastAPI with async/await patterns
- **AI Models**: Anthropic Claude, OpenAI, Google, Cohere
- **MCP Integration**: Model Context Protocol for tool access

## 🤖 Agent System Deep Dive

### Agent Configuration Structure

Every agent follows this YAML pattern:

```yaml
# ai/agents/{agent-name}/config.yaml
agent:
  name: "🔧 Agent Display Name"
  agent_id: "agent-name"           # Must match directory name
  version: 1                       # Increment for changes
  description: "Detailed description of agent purpose"

model:
  provider: anthropic              # anthropic, openai, google, cohere
  id: claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 4000
  output_model:                    # Optional separate output model
    provider: anthropic
    id: claude-haiku-4-20250201

storage:
  type: postgres                   # Always postgres for production
  table_name: agent_name_storage   # Unique per agent
  auto_upgrade_schema: true

memory:
  num_history_runs: 30            # Conversation history retention
  enable_user_memories: true      # User-specific memory
  enable_agentic_memory: true     # Agent learning memory
  add_history_to_messages: true
  memory_retention_days: 180

# MCP servers for tool access
mcp_servers:
  - "automagik-forge:*"           # Task management
  - "postgres:query"              # Database access
  - "search-repo-docs:*"          # Documentation search
  
tools:                             # Agno built-in tools
- name: ShellTools

instructions: |
  Detailed agent instructions and personality
  
expected_output: |
  Description of expected agent outputs
  
success_criteria: |
  Measurable success criteria
```

### Agent Implementation Pattern

```python
# ai/agents/{agent-name}/agent.py
from agno import Agent

def get_{agent_name}_agent() -> Agent:
    """Create and return agent instance."""
    return Agent.from_yaml(__file__.replace("agent.py", "config.yaml"))

__all__ = [f"get_{agent_name}_agent"]
```

### Agent Registry System

Agents are automatically discovered and loaded via the registry:

```python
# Usage in code
from ai.agents.registry import get_agent

# Load any agent by ID
agent = await get_agent("template-agent")

# With specific version
agent = await get_agent("template-agent", version=2)

# With session context
agent = await get_agent("template-agent", session_id="user123")
```

### Version Management

**Critical**: Every config change MUST increment version number:

```yaml
agent:
  version: 2  # Increment when making ANY changes
```

The system tracks versions in the database and supports rollback to previous versions.

## 🏃‍♂️ Team System Architecture

### Team Configuration

Teams route requests to appropriate agents based on logic:

```yaml
# ai/teams/{team-name}/config.yaml
team:
  mode: route                      # route, sequence, parallel
  role: "Team Coordinator Role"
  name: Team Display Name
  team_id: team-name              # Must match directory
  version: 1

members:                          # Agent IDs to include
- agent-1
- agent-2
- agent-3

# Same model, storage, memory config as agents
# Plus team-specific settings:
context:
  share_member_interactions: true  # Share context between agents

streaming:
  stream_member_events: true      # Stream individual agent responses
  show_members_responses: true
```

### Team Implementation

```python
# ai/teams/{team-name}/team.py
from agno import Team

def get_{team_name}_team() -> Team:
    """Create team instance."""
    return Team.from_yaml(__file__.replace("team.py", "config.yaml"))
```

### Factory Function Patterns

The registry automatically discovers teams using these function patterns:
- `get_{team_name}_team` (primary)
- `create_{team_name}_team`
- `{team_name}_factory`
- Custom patterns via config.yaml

## 🔄 Workflow System

### Workflow Configuration

Workflows orchestrate multi-step processes:

```yaml
# ai/workflows/{workflow-name}/config.yaml
workflow:
  name: Workflow Display Name
  workflow_id: workflow-name
  version: 1
  background_execution: true      # Run in background

# Uses same model/storage/memory as agents
# Workflows can call agents and teams
```

### Workflow Implementation

```python
# ai/workflows/{workflow-name}/workflow.py
from agno import Workflow

def get_{workflow_name}_workflow() -> Workflow:
    """Create workflow instance."""
    return Workflow.from_yaml(__file__.replace("workflow.py", "config.yaml"))
```

## 🛠️ Configuration Patterns

### MCP Server Integration

All components can access MCP servers for external tools:

```yaml
mcp_servers:
  - "automagik-forge:*"           # Task management system
  - "ask-repo-agent:*"            # GitHub repository Q&A
  - "search-repo-docs:*"          # Library documentation
  - "send_whatsapp_message:*"     # WhatsApp messaging
  - "postgres:query"              # Direct SQL queries
  - "claude-mcp:*"                # Claude-specific tools
  - "automagik-hive:*"            # Hive API access
```

### Environment Configuration

Use `.env` files for configuration:

```bash
# Database
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/hive

# AI Provider API Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key

# Environment
HIVE_ENVIRONMENT=development
HIVE_LOG_LEVEL=INFO

# Agent Settings
HIVE_MAX_CONVERSATION_TURNS=20
HIVE_SESSION_TIMEOUT=1800
```

### Storage and Memory Patterns

**Database Schema**:
- Each agent gets its own table: `{agent_id}_storage`
- Shared schema: `agno.knowledge_base` for RAG
- Versioning: `hive.component_versions`

**Memory Configuration**:
```yaml
memory:
  num_history_runs: 30            # How many conversation to keep
  enable_user_memories: true      # User-specific long-term memory
  enable_agentic_memory: true     # Agent learning and adaptation
  add_history_to_messages: true   # Include history in context
  memory_retention_days: 180      # Cleanup old memories
```

## 🧠 Knowledge System (RAG)

### CSV-Based Knowledge Base

The system uses a shared CSV-based RAG system:

```python
# lib/knowledge/knowledge_factory.py
from lib.knowledge.knowledge_factory import get_knowledge_base

# Get shared knowledge base
kb = get_knowledge_base()

# Search with metadata filters
results = kb.search(
    query="How to create agents?",
    num_documents=5,
    filters={"domain": "development"}
)
```

### Knowledge Configuration

```yaml
# lib/knowledge/config.yaml
knowledge:
  csv_file_path: "knowledge_rag.csv"
  vector_db:
    table_name: "knowledge_base"
    embedder: "text-embedding-3-small"
    distance: "cosine"
  filters:
    valid_metadata_fields: ["domain", "component", "complexity"]
```

### CSV Structure

```csv
content,metadata_domain,metadata_component,metadata_complexity
"Agent creation requires YAML config",development,agents,beginner
"Teams route requests to agents",development,teams,intermediate
```

## 🚀 API Integration Patterns

### FastAPI Structure

```python
# api/serve.py - Production server
from agno import Agent, Team, Workflow
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/v1/agents/{agent_id}/chat")
async def chat_with_agent(agent_id: str, message: str):
    agent = await get_agent(agent_id)
    response = await agent.arun(message)
    return {"response": response}
```

### API Endpoints

Key endpoints available:
- `POST /api/v1/agents/{agent_id}/chat` - Chat with specific agent
- `GET /api/v1/agents` - List available agents
- `POST /api/v1/teams/{team_id}/chat` - Route to team
- `POST /api/v1/workflows/{workflow_id}/execute` - Run workflow
- `GET /health` - Health check
- `GET /version` - Version information

### Development vs Production

```python
# Development playground
# api/main.py
from agno import Playground
from ai.agents.registry import get_agent

agent = await get_agent("template-agent")
agent.playground()  # Interactive development

# Production server
# api/serve.py
from agno import FastAPIApp
app = FastAPIApp(agents=[agent])  # Scalable production
```

## 🧪 Development Workflows

### Package Management (UV)

**Never use python or pip directly**. Always use UV:

```bash
# Install dependencies
uv sync

# Add new package
uv add <package>

# Run Python commands
uv run python script.py
uv run pytest
uv run ruff check --fix
uv run mypy .
```

### Testing Patterns

```python
# tests/test_agent.py
import pytest
from ai.agents.registry import get_agent

@pytest.mark.asyncio
async def test_agent_creation():
    agent = await get_agent("template-agent")
    assert agent is not None
    
@pytest.mark.asyncio 
async def test_agent_response():
    agent = await get_agent("template-agent")
    response = await agent.arun("Hello")
    assert len(response) > 0
```

### Code Quality

Automated quality tools are configured:

```bash
# Formatting and linting
uv run ruff check --fix          # Auto-fix code issues
uv run ruff format               # Format code

# Type checking
uv run mypy .                    # Static type analysis

# Testing with coverage
uv run pytest --cov=ai --cov=api --cov=lib
```

### Agent Environment

Use Docker containers for development:

```bash
make agent                       # Start agent services
make agent-status               # Check status
make agent-logs                 # View logs
make agent-stop                 # Stop services

# Services run on:
# - Agent API: http://localhost:38886
# - Agent DB: postgresql://localhost:35532
```

## 🔧 MCP Tools Integration

### Available MCP Tools

The system provides these MCP tools:

1. **automagik-forge** - Project and task management
2. **ask-repo-agent** - GitHub repository Q&A
3. **search-repo-docs** - Library documentation search
4. **send_whatsapp_message** - WhatsApp messaging
5. **postgres** - Direct SQL database queries
6. **claude-mcp** - Claude-specific tools
7. **automagik-hive** - Hive API access

### Usage in Agents

MCP tools are automatically available in agents:

```yaml
# In agent config.yaml
mcp_servers:
  - "postgres:query"              # Enable SQL queries
  - "automagik-forge:*"           # Enable task management
```

### Database Queries

```python
# Agents can query the database directly
# Using postgres MCP tool:
"""
Query current system state:
SELECT * FROM hive.component_versions WHERE component_type = 'agent';

Query knowledge base:
SELECT content FROM agno.knowledge_base WHERE meta_data->>'domain' = 'development';
"""
```

## 📝 Best Practices

### Agent Development

1. **Start with template-agent** - Copy and customize
2. **Increment versions** - Always bump version on changes
3. **Use descriptive agent_ids** - Match directory names exactly
4. **Test thoroughly** - Create tests in `tests/agents/`
5. **Document behavior** - Clear instructions and success criteria

### Team Development

1. **Define clear routing logic** - Specify when each agent is used
2. **Share context appropriately** - Use `share_member_interactions`
3. **Test member coordination** - Verify proper request routing
4. **Version together** - Keep team and member versions in sync

### Configuration Management

1. **Use environment variables** - Keep secrets in `.env`
2. **Validate configs** - Test YAML parsing before deployment
3. **Monitor versions** - Track component versions in database
4. **Document changes** - Explain version increments

### Performance Optimization

1. **Shared knowledge base** - One instance across all agents
2. **Connection pooling** - PostgreSQL connection management
3. **Async patterns** - Use `await` for I/O operations
4. **Memory management** - Configure retention appropriately

## 🚨 Common Pitfalls

### Version Management
- **Never skip version increments** - Database tracks all versions
- **Test version rollback** - Ensure older versions work
- **Document breaking changes** - Note compatibility issues

### Database Issues
- **Connection limits** - Monitor PostgreSQL connections
- **Schema changes** - Use `auto_upgrade_schema: true`
- **Backup strategies** - Regular database backups

### Memory Usage
- **Long conversations** - Configure `num_history_runs`
- **User memories** - Monitor memory table growth
- **Cleanup policies** - Set `memory_retention_days`

## 🎯 Quick Start Checklist

To be productive with Automagik Hive:

- [ ] **Environment Setup**: Install UV, configure `.env`
- [ ] **Agent Services**: Run `make agent` for development
- [ ] **Database Access**: Verify PostgreSQL connection
- [ ] **Template Study**: Examine `template-agent` configuration
- [ ] **Create Test Agent**: Copy template and customize
- [ ] **MCP Integration**: Test available tools
- [ ] **Knowledge Base**: Load CSV data and test search
- [ ] **API Testing**: Verify FastAPI endpoints work
- [ ] **Quality Tools**: Run ruff, mypy, pytest
- [ ] **Version Control**: Practice version incrementing

## 📚 Additional Resources

- **Agno Documentation**: Framework-specific patterns
- **Component Guides**: See `ai/CLAUDE.md`, `api/CLAUDE.md`, `lib/CLAUDE.md`
- **Testing Patterns**: Check `tests/CLAUDE.md`
- **MCP Specifications**: Model Context Protocol details
- **PostgreSQL + pgvector**: Vector database optimization

## 🔄 Development Lifecycle

### Creating New Agents

1. Copy `ai/agents/template-agent/` to `ai/agents/new-agent/`
2. Update `config.yaml` with new `agent_id` and `name`
3. Modify `agent.py` function names to match
4. Customize instructions and behavior
5. Test with `uv run pytest tests/agents/`
6. Register automatically via discovery

### Deploying Changes

1. Increment version in `config.yaml`
2. Test locally with `make agent`
3. Run quality checks: `uv run ruff check --fix && uv run mypy .`
4. Verify tests pass: `uv run pytest`
5. Commit with proper co-authoring
6. Deploy to production environment

This guide provides the essential knowledge for productive development with Automagik Hive. The framework's YAML-driven configuration and Agno foundation enable rapid development of sophisticated multi-agent systems.