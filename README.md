# 🚀 Automagik Hive V2

**AI that generates AI** - The YAML-first scaffolding and DevX layer for Agno that makes agent creation delightful.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

## What is Hive?

Think **"Create React App" but for Agno agents**. Hive is not a competing framework - it's a scaffolding layer that makes building with [Agno](https://github.com/agno-agi/agno) faster and more delightful.

### The Killer Feature

**Use Agno agents to generate Agno agent configurations** - describe what you want in natural language, and Hive's AI generator creates optimal YAML configs with intelligent model selection, tool recommendations, and production-ready instructions.

## Features

- 🤖 **AI-Powered Generation** - Natural language → optimized agent configs
- 🎯 **YAML-First Config** - Newbie-friendly agent creation
- 🔄 **Smart RAG System** - CSV hot reload with hash-based incremental loading
- 📦 **Version Management** - Track agent evolution over time
- 🚀 **API-Driven Lifecycle** - Create/update agents via REST
- 🛠️ **Builtin Tools Catalog** - 12 production-ready tools
- 🎨 **Project Templates** - Zero-to-agent in 30 seconds

## Quick Start

### Installation

```bash
# Install via uvx (recommended - no system pollution)
uvx automagik-hive --help

# Or install globally
uv pip install automagik-hive
```

### Create Your First Project

```bash
# Initialize project
uvx automagik-hive init my-project
cd my-project

# Option 1: Template-based (fast)
hive create agent my-bot

# Option 2: AI-powered (optimal)
hive ai my-bot --description "Customer support bot with CSV knowledge"

# Start dev server
hive dev
```

## AI-Powered Generation

The killer feature - use natural language to generate optimal agent configurations:

```bash
$ hive ai support-bot --interactive

🤖 AI-Powered Agent Generator
────────────────────────────────────────────────────────

💭 What should your agent do?
> I need a customer support bot that answers questions using
  a CSV knowledge base. Should be friendly and helpful.

🧠 Analyzing requirements...
🤖 Generating optimal configuration...
✅ Agent generated successfully!

💡 AI Recommendations:
  • Model: gpt-4o-mini (cost-effective for support tasks)
  • Tools: CSVTools, WebSearch (for knowledge lookup + fallback)
  • Temperature: 0.7 (balanced creativity/consistency)
  • Storage: PostgreSQL with auto-schema (production-ready)

📋 Next Steps:
  1. Add your CSV knowledge base to data/support_docs.csv
  2. Review and customize config.yaml
  3. Test: hive dev
```

**Generated config.yaml:**
```yaml
agent:
  name: "Customer Support Bot"
  agent_id: "support-bot"
  version: "1.0.0"

model:
  provider: "openai"
  id: "gpt-4o-mini"  # AI-selected for cost-effectiveness
  temperature: 0.7

instructions: |
  You are a friendly and helpful customer support agent.

  Your role is to answer customer questions using the knowledge base.
  Always be polite, concise, and solution-oriented.

  When you don't know something, offer to escalate to a human agent.

tools:
  - name: CSVTools
    csv_path: "./data/support_docs.csv"
  - name: WebSearch  # Fallback for questions not in KB

storage:
  table_name: "support_bot_sessions"
  auto_upgrade_schema: true
```

## Project Structure

When you run `hive init my-project`:

```
my-project/
├── ai/                         # All AI components
│   ├── agents/
│   │   ├── examples/           # Built-in examples (read-only)
│   │   │   ├── support-bot/    # Customer support w/ CSV
│   │   │   ├── code-reviewer/  # Code review w/ security
│   │   │   └── researcher/     # Web research w/ synthesis
│   │   └── [your-agents]/      # Your custom agents
│   │
│   ├── teams/                  # Multi-agent teams
│   │   ├── examples/
│   │   └── [your-teams]/
│   │
│   ├── workflows/              # Step-based workflows
│   │   ├── examples/
│   │   └── [your-workflows]/
│   │
│   └── tools/                  # Custom tools
│       ├── examples/
│       └── [your-tools]/
│
├── data/                       # Knowledge bases
│   ├── csv/                    # CSV knowledge
│   └── documents/              # Document stores
│
├── .env                        # Environment config
├── hive.yaml                   # Project config
└── pyproject.toml              # Python dependencies
```

## Smart RAG System

Hash-based incremental CSV loading with hot reload - one of the few gems from Hive V1:

```python
from hive.rag import create_knowledge_base

# Create knowledge base with hot reload
kb = create_knowledge_base(
    csv_path="data/knowledge.csv",
    embedder="text-embedding-3-small",
    num_documents=5,
    hot_reload=True
)

# Use with agent
agent = Agent(name="Bot", knowledge=kb)
```

**Performance:**
- ✅ **450x faster** for unchanged CSVs
- ✅ **10x faster** for small updates
- ✅ **99% cost savings** on embeddings

## Builtin Tools Catalog

12 production-ready tools:

| Category | Tools |
|----------|-------|
| **Execution** | PythonTools, ShellTools |
| **Web** | DuckDuckGoSearch, WebScraper, YoutubeTools |
| **Files** | FileTools, CSVTools |
| **Database** | SQLQuery |
| **APIs** | GitHubAPI, SlackAPI, EmailTools |
| **Compute** | Calculator |

```python
from hive.scaffolder.builtin_tools import search_tools, recommend_tools

# Search for tools
results = search_tools("web search")
# [{'name': 'DuckDuckGoSearch', 'description': '...', 'use_cases': [...]}]

# Get AI recommendations
recommendations = recommend_tools("I need to analyze CSV data and send Slack alerts")
# Recommends: CSVTools, SlackAPI
```

## CLI Commands

```bash
# Initialize project
hive init <project-name>

# Create components (templates)
hive create agent <name>
hive create team <name> --mode route|coordinate|collaborate
hive create workflow <name>
hive create tool <name>

# Create with AI (KILLER FEATURE)
hive ai <agent-name> --interactive
hive ai <agent-name> --description "Natural language description"

# Development
hive dev                    # Start dev server with hot reload
hive dev --port 8000        # Custom port
hive dev --reload           # Enable file watching

# Info
hive version                # Show version
hive --help                 # Show all commands
```

## Example Agents

### Customer Support Bot

```yaml
agent:
  name: "Customer Support Bot"
  agent_id: "support-bot"

model:
  provider: "openai"
  id: "gpt-4o-mini"

tools:
  - name: CSVTools
    csv_path: "./data/faqs.csv"
  - name: WebSearch

instructions: |
  You are a friendly customer support agent.
  Answer questions using the FAQ knowledge base.
  Be helpful and concise.
```

### Code Reviewer

```yaml
agent:
  name: "Security Code Reviewer"
  agent_id: "code-reviewer"

model:
  provider: "anthropic"
  id: "claude-sonnet-4"

tools:
  - name: FileTools
  - name: GitHubAPI

instructions: |
  You are a security-focused code reviewer.
  Check for OWASP Top 10 vulnerabilities.
  Provide educational feedback with fix suggestions.
```

### Research Assistant

```yaml
agent:
  name: "Research Assistant"
  agent_id: "researcher"

model:
  provider: "openai"
  id: "gpt-4o"

tools:
  - name: WebSearch
  - name: YoutubeTools
  - name: WebScraper

instructions: |
  You are a thorough research assistant.
  Search multiple sources, synthesize findings.
  Always cite sources with links.
```

## Environment Configuration

**Minimal .env (20 vars, not 145!):**

```bash
# Core (Required)
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql://localhost:5432/hive
HIVE_API_KEY=hive_your_key_here

# AI Providers (At least one required)
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key

# Optional
HIVE_LOG_LEVEL=INFO
HIVE_ENABLE_METRICS=true
HIVE_CORS_ORIGINS=http://localhost:3000
```

## API Server

```bash
# Start API server
hive dev

# Access docs
open http://localhost:8886/docs

# Create agent via API
curl -X POST http://localhost:8886/api/v1/agents \
  -H "X-API-Key: $HIVE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-bot",
    "description": "Customer support bot",
    "model": "gpt-4o-mini"
  }'
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint & format
uv run ruff check --fix
uv run ruff format

# Type check
uv run mypy .
```

## Why Hive vs Pure Agno?

| Feature | Pure Agno | With Hive |
|---------|-----------|-----------|
| **Agent Creation** | Write Python factory functions | YAML configs or AI generation |
| **Getting Started** | Study Agno docs, write boilerplate | `hive init` → instant project |
| **Knowledge Base** | Setup PgVector, write loaders | `create_knowledge_base()` + hot reload |
| **Project Structure** | DIY | Opinionated `ai/{agents,teams,workflows,tools}` |
| **Model Selection** | Research options, pick manually | AI recommends optimal model |
| **Tool Selection** | Browse Agno tools, wire up | Builtin catalog + AI recommendations |

**Hive is to Agno what Create React App is to React** - scaffolding that removes friction, not a competing framework.

## What Hive Does NOT Do

❌ Compete with Agno (we extend it)
❌ Reinvent agent orchestration (use Agno's native features)
❌ Replace your code (generate scaffolds, you own the result)
❌ Lock you in (generated code is pure Agno)

## Roadmap

### V2.0 (Current) - MVP Scaffolding
- [x] AI-powered agent generation
- [x] Smart RAG with incremental loading
- [x] YAML-first configuration
- [x] Builtin tools catalog
- [x] Project templates

### V2.1 - Enhanced DevX
- [ ] Interactive TUI for agent creation
- [ ] Live agent testing in terminal
- [ ] Knowledge base quality scoring
- [ ] Tool compatibility checker

### V2.2 - Production Features
- [ ] Multi-environment configs (dev/staging/prod)
- [ ] Agent performance monitoring
- [ ] Cost tracking and optimization
- [ ] Deployment helpers (Docker, AWS, etc.)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with ❤️ by the Automagik team.

**Powered by:**
- [Agno](https://github.com/agno-agi/agno) - The AI agent framework
- [UV](https://github.com/astral-sh/uv) - Modern Python packaging
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output

---

**Remember:** Hive doesn't compete with Agno. We make it easier to use. 🚀
