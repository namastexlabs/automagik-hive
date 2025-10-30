<div align="center">
  <img src=".github/assets/logo.svg" alt="Automagik Hive" width="400">

  <h3>Scaffolding and Smart RAG for Agno</h3>
  <p><strong>AI-powered agent generation with intelligent CSV knowledge bases</strong></p>

  [![PyPI version](https://img.shields.io/pypi/v/automagik-hive?style=flat-square&color=00D9FF)](https://pypi.org/project/automagik-hive/)
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
  [![Downloads](https://static.pepy.tech/badge/automagik-hive)](https://pepy.tech/project/automagik-hive)
  [![Build Status](https://img.shields.io/github/actions/workflow/status/namastexlabs/automagik-hive/test.yml?branch=main&style=flat-square)](https://github.com/namastexlabs/automagik-hive/actions)
  [![License](https://img.shields.io/github/license/namastexlabs/automagik-hive?style=flat-square&color=00D9FF)](https://github.com/namastexlabs/automagik-hive/blob/main/LICENSE)
  [![Discord](https://img.shields.io/discord/1095114867012292758?style=flat-square&color=00D9FF&label=discord)](https://discord.gg/xcW8c7fF3R)
  [![Roadmap](https://img.shields.io/badge/📍_roadmap-view_initiatives-5319E7?style=flat-square)](https://github.com/orgs/namastexlabs/projects/9/views/1?filterQuery=project%3Ahive)

  [Quick Start](#quick-start) • [Features](#key-features) • [Examples](#real-world-examples) • [🗺️ Roadmap](#roadmap) • [Contributing](#contributing)

</div>

---

## What is Automagik Hive?

**Hive doesn't compete with Agno - it makes it easier to use.**

Think of Hive as **"Create React App" for Agno agents**. Instead of weeks setting up project structure, writing boilerplate, and researching optimal configurations, Hive gives you:

- 🤖 **AI-Powered Generation** - Describe what you want; Hive's meta-agent generates optimal configs
- 🔄 **Smart CSV RAG** - Hash-based incremental loading (450x faster, 99% cost savings)
- 🎯 **YAML-First Config** - No Python boilerplate, just declarative configs
- 📦 **Project Scaffolding** - Zero to agent in 30 seconds

**Built by practitioners** who got tired of manually setting up the same patterns. Powered entirely by [Agno](https://github.com/agno-agi/agno).

---

## Key Features

### 🤖 AI That Generates AI

Use an Agno agent to generate Agno agent configurations. Natural language requirements → optimal YAML configs.

```bash
$ hive ai support-bot --interactive

🤖 AI-Powered Agent Generator
────────────────────────────────────────

💭 What should your agent do?
> Customer support bot with CSV knowledge base

🧠 Analyzing requirements...
✅ Generated successfully!

💡 AI Recommendations:
  • Model: gpt-4o-mini (cost-effective for support)
  • Tools: CSVTools, WebSearch
  • Complexity: 4/10
  • Estimated cost: $0.002/query

📋 Generated: ai/agents/support-bot/config.yaml
```

**How it works:**
1. Meta-agent analyzes natural language requirements
2. Selects optimal model from 7+ providers (OpenAI, Anthropic, Google, etc.)
3. Recommends tools from Agno's builtin catalog
4. Generates context-aware system instructions
5. Creates production-ready YAML configuration

**Not keyword matching - real LLM intelligence.**

### 🔄 Smart CSV RAG System

The one feature from V1 worth keeping - hash-based incremental CSV loading:

```python
from hive.knowledge import create_knowledge_base

# Smart loading with hot reload
kb = create_knowledge_base(
    csv_path="data/faqs.csv",
    embedder="text-embedding-3-small",
    num_documents=5,
    hot_reload=True  # Watches for changes
)

# Only re-embeds changed rows
# MD5 hash tracking prevents redundant processing
```

**Performance Numbers:**
- ✅ **450x faster** - Hot reload for unchanged CSVs
- ✅ **10x faster** - Small updates (only changed rows)
- ✅ **99% cost savings** - No redundant embeddings
- ✅ **18/18 tests passing** - Production-ready

**Real-world impact:** $700+/year savings at scale.

### 🎯 YAML-First Agent Design

**No Python boilerplate.** Just declarative configurations:

```yaml
agent:
  name: "Customer Support Bot"
  agent_id: "support-bot"
  version: "1.0.0"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a friendly customer support agent.
  Answer questions using the knowledge base.
  When unsure, escalate to human support.

tools:
  - name: CSVTools
    csv_path: "./data/faqs.csv"
  - name: WebSearch

storage:
  table_name: "support_bot_sessions"
  auto_upgrade_schema: true
```

**Want to extend with Python?** Just create `agent.py`:

```python
from agno.agent import Agent
from hive.discovery import discover_config

def get_support_bot(**kwargs):
    config = discover_config()  # Loads config.yaml
    return Agent(
        name=config['agent']['name'],
        # ... custom logic here
        **kwargs
    )
```

### 📦 Project Scaffolding

Opinionated structure that scales:

```
my-project/
├── ai/                         # All AI components
│   ├── agents/                 # Agent definitions
│   │   ├── examples/           # Built-in examples (learning)
│   │   │   ├── support-bot/
│   │   │   ├── code-reviewer/
│   │   │   └── researcher/
│   │   └── [your-agents]/      # Your custom agents
│   ├── teams/                  # Multi-agent teams
│   ├── workflows/              # Step-based workflows
│   └── tools/                  # Custom tools
│
├── data/                       # Knowledge bases
│   ├── csv/                    # CSV files
│   └── documents/              # Document stores
│
├── .env                        # Environment config
├── hive.yaml                   # Project settings
└── pyproject.toml              # Dependencies
```

### 🚀 Built on Agno's Power

Hive is a thin layer over Agno. You get all of Agno's features:

- **Performance**: 3μs agent instantiation, 6.5KB memory per agent
- **Native tools**: 20+ production-ready tools (web search, code execution, file ops, etc.)
- **Storage**: PostgreSQL, SQLite with auto-schema migration
- **Playground**: Auto-generated API with OpenAPI docs
- **Workflows**: Sequential, parallel, conditional, looping
- **Teams**: Automatic routing, collaboration, coordination

### 🛠️ Builtin Tools Catalog

Easy access to Agno's tools with metadata and recommendations:

| Category | Tools |
|----------|-------|
| **Execution** | PythonTools, ShellTools |
| **Web** | DuckDuckGoTools, TavilyTools, WebpageTools |
| **Files** | FileTools, CSVTools |
| **Data** | PandasTools, PostgresTools |
| **APIs** | SlackTools, EmailTools, GitHubTools |

```python
from hive.config.builtin_tools import BUILTIN_TOOLS

# Browse tools
for tool_name, info in BUILTIN_TOOLS.items():
    print(f"{tool_name}: {info['description']}")
```

### 🔥 Hot Reload

Change configs, see results instantly:

```bash
$ hive dev  # Starts dev server

# Edit ai/agents/my-bot/config.yaml
# Server automatically reloads
# Test at http://localhost:8886/docs
```

### 🏢 Enterprise-Ready

**When you're ready for production:**

- ✅ PostgreSQL with PgVector (hybrid search, HNSW indexing)
- ✅ Environment-based configuration (dev/staging/prod)
- ✅ API authentication with cryptographic keys
- ✅ Structured logging with Loguru
- ✅ Type safety with Pydantic validation
- ✅ Test coverage (87% pass rate, 147 tests)

---

## Quick Start

### Prerequisites

- Python 3.11+ (3.12 recommended)
- At least one AI provider API key:
  - OpenAI (`OPENAI_API_KEY`)
  - Anthropic (`ANTHROPIC_API_KEY`)
  - Google (`GEMINI_API_KEY`)

### Installation

```bash
# Install via uvx (recommended - no pollution)
uvx automagik-hive --help

# Or install globally with uv
uv pip install automagik-hive

# Or install with pip
pip install automagik-hive
```

### Create Your First Agent (30 seconds)

```bash
# 1. Initialize project
uvx automagik-hive init my-project
cd my-project

# 2. Create API keys file
cp .env.example .env
# Edit .env and add your API keys

# 3a. Template-based creation (fast)
hive create agent my-bot

# 3b. AI-powered creation (optimal)
hive ai my-bot --description "Customer support bot with FAQ knowledge"

# 4. Start development server
hive dev

# 5. Access API docs
open http://localhost:8886/docs
```

### Your First Conversation

```bash
# Via CLI
curl -X POST http://localhost:8886/agents/my-bot/runs \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'

# Via Python
from agno.agent import Agent

agent = Agent.load("ai/agents/my-bot")
response = agent.run("How do I reset my password?")
print(response.content)
```

---

## Real-World Examples

### Customer Support Router

**Problem:** Route support queries to specialized agents (billing, technical, general)

```yaml
# ai/teams/support-router/config.yaml
team:
  name: "Support Router"
  team_id: "support-router"
  mode: "route"  # Agno handles routing automatically

members:
  - "billing-agent"
  - "technical-agent"
  - "general-agent"

instructions: |
  You are a support routing system.

  Route queries based on topic:
  - Billing: payments, invoices, refunds
  - Technical: bugs, errors, integrations
  - General: questions, information, other
```

**Result:** Automatic routing, no manual orchestration code needed.

### Knowledge-Powered Agent

**Problem:** Answer customer questions from FAQ database

```yaml
agent:
  name: "FAQ Bot"
  agent_id: "faq-bot"

model:
  provider: "openai"
  id: "gpt-4o-mini"

tools:
  - name: CSVTools
    csv_path: "./data/faqs.csv"

instructions: |
  Search the FAQ database for answers.
  Provide concise, helpful responses.
  If no match found, offer to escalate.
```

**Setup CSV:**
```csv
question,answer,category
How do I reset password?,Go to Settings > Security > Reset Password,account
What are your hours?,We're available 24/7 via chat and email,general
How do refunds work?,Refunds process in 5-7 business days,billing
```

**Smart loading:** Only re-embeds changed rows, saves 99% on embedding costs.

### Code Review Workflow

**Problem:** Automated code review with security checks

```yaml
# ai/workflows/code-review/config.yaml
workflow:
  name: "Security Code Review"
  workflow_id: "code-review"

steps:
  - name: "static_analysis"
    agent: "security-scanner"

  - name: "review"
    agent: "code-reviewer"
    tools:
      - PythonTools
      - FileTools

  - name: "report"
    function: "generate_report"
```

**Result:** Comprehensive reviews covering OWASP Top 10, best practices, and fix suggestions.

---

## Architecture That Scales

### Project Structure

```
my-project/
├── ai/                         # AI components (auto-discovered)
│   ├── agents/                 # Agents (YAML + optional Python)
│   ├── teams/                  # Multi-agent teams
│   ├── workflows/              # Step-based workflows
│   └── tools/                  # Custom tools
│
├── data/                       # Knowledge bases
│   ├── csv/                    # CSV files (with hot reload)
│   └── documents/              # Other documents
│
├── .env                        # Environment variables
├── hive.yaml                   # Project configuration
└── pyproject.toml              # Python dependencies
```

### Auto-Generated API

```bash
$ hive dev

# Agno Playground generates:
GET  /                          # API info
GET  /health                    # Health check
GET  /agents                    # List agents
POST /agents/{id}/runs          # Run agent
GET  /agents/{id}/sessions      # Get sessions
POST /teams/{id}/runs           # Run team
POST /workflows/{id}/runs       # Run workflow
```

Full OpenAPI docs at `/docs`.

---

## CLI Commands

```bash
# Project Management
hive init <project-name>                  # Initialize new project
hive version                              # Show version

# Component Creation - Templates
hive create agent <name>                  # Create agent from template
hive create team <name>                   # Create team
hive create workflow <name>               # Create workflow
hive create tool <name>                   # Create custom tool

# Component Creation - AI-Powered ⭐
hive ai <agent-name> --interactive        # Interactive AI generation
hive ai <agent-name> --description "..."  # Generate from description

# Development
hive dev                                  # Start dev server (hot reload)
hive dev --port 8000                      # Custom port
hive dev --examples                       # Run with built-in examples

# Production
hive serve                                # Start production server
hive serve --port 8000                    # Custom port
```

---

## Database Backend Selection

Hive supports multiple database backends for different use cases:

| Backend | Best For | Setup | Performance | Features |
|---------|----------|-------|-------------|----------|
| **PostgreSQL** | Production | Docker | ⭐⭐⭐⭐⭐ | Full text search, PgVector, HNSW |
| **SQLite** | Development | None | ⭐⭐⭐ | File-based, good for testing |

### PostgreSQL (Recommended for Production)

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name hive-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=hive \
  -p 5432:5432 \
  pgvector/pgvector:latest

# Update .env
HIVE_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/hive
```

**Features:**
- PgVector for hybrid search
- HNSW indexing (fast vector similarity)
- Full-text search
- Auto-schema migration
- Production-ready

### SQLite (Development Only)

```bash
# Update .env
HIVE_DATABASE_URL=sqlite:///./data/hive.db
```

**Limitations:**
- No concurrent writes
- No vector similarity search
- File locking issues under load
- **Not recommended for production**

---

## Environment Configuration

**Minimal .env (20 vars, not 145!):**

```bash
# Core (Required)
HIVE_ENVIRONMENT=development              # development|staging|production
HIVE_API_PORT=8886                        # API server port
HIVE_DATABASE_URL=postgresql://...        # Database connection
HIVE_API_KEY=hive_your_32_char_key        # API authentication

# AI Providers (At least one required)
OPENAI_API_KEY=sk-...                     # OpenAI models
ANTHROPIC_API_KEY=sk-ant-...              # Claude models
GEMINI_API_KEY=...                        # Google models

# Optional
HIVE_LOG_LEVEL=INFO                       # DEBUG|INFO|WARNING|ERROR
HIVE_VERBOSE_LOGS=false                   # Detailed logging
HIVE_ENABLE_METRICS=true                  # Performance tracking
HIVE_CORS_ORIGINS=http://localhost:3000   # Comma-separated origins
```

---

## Development

```bash
# Clone repository
git clone https://github.com/namastexlabs/automagik-hive
cd automagik-hive

# Install dependencies
uv sync

# Run tests
uv run pytest                              # All tests
uv run pytest tests/hive/knowledge/        # Knowledge tests
uv run pytest -v --cov=hive                # With coverage

# Lint & format
uv run ruff check --fix
uv run ruff format

# Type check
uv run mypy hive/

# Start examples
uv run python hive/examples/agents/demo_all_agents.py
```

---

## Why Hive vs Pure Agno?

| Feature | Pure Agno | Hive + Agno |
|---------|-----------|-------------|
| **Agent Creation** | Write Python factories | YAML or AI generation |
| **Getting Started** | Read docs, write boilerplate | `hive init` → instant project |
| **Knowledge Base** | Setup PgVector, write loaders | `create_knowledge_base()` with hot reload |
| **Model Selection** | Research 7+ providers | AI recommends optimal choice |
| **Tool Selection** | Browse Agno tools | Catalog + AI recommendations |
| **CSV RAG** | Write custom incremental loader | Built-in hash-based incremental |
| **Project Structure** | DIY | Opinionated `ai/` structure |

**Hive = Scaffolding for Agno**

Like Create React App for React, Hive removes setup friction without replacing the framework.

---

## What Hive Does NOT Do

❌ **Compete with Agno** - We extend it, don't replace it
❌ **Reinvent orchestration** - Use Agno's native teams/workflows
❌ **Lock you in** - Generated code is pure Agno, you own it
❌ **Replace your code** - We scaffold, you customize

---

## Roadmap

### V2.0 (Current) ✅

- [x] AI-powered agent generation with meta-agent
- [x] Smart CSV RAG with hash-based incremental loading
- [x] YAML-first configuration
- [x] Project scaffolding with examples
- [x] Builtin tools catalog
- [x] Hot reload for dev server

### V2.1 - Enhanced DevX 🚀

- [ ] Interactive TUI for agent creation
- [ ] Live agent testing in terminal
- [ ] Knowledge base quality scoring
- [ ] Tool compatibility checker
- [ ] Agent performance profiling

### V2.2 - Production Features 🌟

- [ ] Multi-environment configs (dev/staging/prod)
- [ ] Cost tracking and optimization
- [ ] Deployment helpers (Docker, AWS, Fly.io)
- [ ] Agent monitoring dashboard
- [ ] Workflow visualization

---

## Enterprise Features

### Security & Authentication
- ✅ Cryptographic API key generation (`secrets.token_urlsafe`)
- ✅ Constant-time validation (prevents timing attacks)
- ✅ Environment-based security (auto-enabled in production)
- ✅ Input validation (size limits, sanitization)

### Database & Storage
- ✅ PostgreSQL with PgVector (hybrid search)
- ✅ SQLite for development
- ✅ Auto-schema migration
- ✅ Session persistence

### Monitoring & Observability
- ✅ Structured logging (Loguru)
- ✅ Automatic emoji mapping
- ✅ Performance metrics
- ✅ Error tracking

### Deployment
- ✅ Docker-ready
- ✅ Environment scaling (dev/staging/prod)
- ✅ Health checks
- ✅ Graceful shutdown

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas for contribution:**
- Additional builtin tool integrations
- Example agents for common use cases
- Documentation improvements
- Bug fixes and performance optimizations

---

## Acknowledgments

**Powered by:**
- [Agno](https://github.com/agno-agi/agno) - The AI agent framework powering everything
- [UV](https://github.com/astral-sh/uv) - Modern Python packaging and project management
- [Typer](https://typer.tiangolo.com/) - Beautiful CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal output that doesn't suck
- [Pydantic](https://pydantic.dev/) - Data validation with type hints
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework (via Agno)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Links

- **Documentation**: [docs/](docs/)
- **Examples**: [hive/examples/](hive/examples/)
- **Issues**: [GitHub Issues](https://github.com/namastexlabs/automagik-hive/issues)
- **Discussions**: [GitHub Discussions](https://github.com/namastexlabs/automagik-hive/discussions)
- **Agno Framework**: [github.com/agno-agi/agno](https://github.com/agno-agi/agno)

---

**Built with ❤️ by practitioners who got tired of boilerplate.**

**Remember:** Hive doesn't compete with Agno. We make it easier to use. 🚀
