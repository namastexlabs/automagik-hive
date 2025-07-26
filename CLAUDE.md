# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automagik Hive is an enterprise multi-agent AI framework built on **Agno (agno-agi/agno)** that enables rapid development of sophisticated multi-agent systems through YAML configuration. It provides production-ready boilerplate for building intelligent agents, routing teams, and business workflows with enterprise-grade deployment capabilities.

## Key Architecture

### Codebase Exploration Command
```bash
# Use this tree command to explore the entire codebase structure
tree -I '__pycache__|.git|*.pyc|.venv|data|logs|.pytest_cache|*.egg-info|node_modules|.github|genie|scripts|common|docs|alembic' -P '*.py|*.yaml|*.yml|*.toml|*.md|Makefile|Dockerfile|*.ini|*.sh|*.csv|*.json' --prune -L 4
```

### 🗺️ Architecture Treasure Map
```
🧭 NAVIGATION ESSENTIALS
├── pyproject.toml              # UV package manager (use `uv add <package>` - never pip!)
├── Makefile                    # Command center: make install/dev/prod/test
├── .env.example                # Environment template (copy to .env)
├── CLAUDE.md                   # 👈 You are here

🤖 MULTI-AGENT CORE (Start Here for Agent Development)
├── ai/
│   ├── agents/registry.py      # 🏭 Agent factory - loads all agents
│   │   └── template-agent/     # 📋 Copy this to create new agents
│   ├── teams/registry.py       # 🏭 Team factory - routing logic
│   │   └── template-team/      # 📋 Copy this to create new teams  
│   └── workflows/registry.py   # 🏭 Workflow factory - orchestration
│       └── template-workflow/  # 📋 Copy this to create new workflows

🌐 API LAYER (Where HTTP Meets Agents)
├── api/
│   ├── serve.py                # 🚀 Production server (Agno FastAPIApp)
│   ├── main.py                 # 🛝 Dev playground (Agno Playground)
│   └── routes/v1_router.py     # 🛣️ Main API endpoints

📚 SHARED SERVICES (The Foundation)
├── lib/
│   ├── config/settings.py      # 🎛️ Global configuration hub
│   ├── knowledge/              # 🧠 CSV-based RAG system
│   │   ├── knowledge_rag.csv   # 📊 Data goes here
│   │   └── csv_hot_reload.py   # 🔄 Hot reload magic
│   ├── auth/service.py         # 🔐 API authentication
│   ├── utils/agno_proxy.py     # 🔌 Agno framework integration
│   └── versioning/             # 📦 Component version management

🧪 TESTING (TODO: Not implemented yet - create tests/scenarios/ for new features)
```

### Component Decision Framework
- **🤖 Individual Agents**: Single domain expertise (code editing, file management, project orchestration)
- **👥 Teams**: Multi-domain coordination using `mode="route"` (intelligent routing) or `mode="coordinate"` (collaboration)
- **⚡ Workflows**: Multi-step processes with parallel execution, conditional logic, and state management
- **🏭 Factory Pattern**: Registry-based component creation with version management and hot-reload

## Agent Environment Commands

### Essential Commands for AI Agents
**🤖 LLM-optimized commands - all non-blocking, return terminal immediately:**
```bash
# First-time setup (silent, no prompts, mirror environment)
make install-agent  # Creates .env.agent, ports 38886/35532, separate DB

# Daily agent operations 
make agent          # Start server in background, show startup logs, return terminal
make agent-logs     # View logs (non-blocking, last 50 lines)
make agent-restart  # Clean restart sequence  
make agent-stop     # Clean shutdown with PID management
make agent-status   # Quick environment check

# Your isolated agent environment:
# - Agent API: http://localhost:38886
# - Agent DB: postgresql://localhost:35532  
# - Agent config: .env.agent (auto-generated from .env.example)
# - Isolated containers: hive-agents-agent, hive-postgres-agent
# - Completely separate from any user environments
```

### Agent Development Workflow
```bash
# Package management (NEVER use python directly - always use uv)
uv sync                           # Install dependencies when needed
uv run ruff check --fix          # Lint and fix code automatically
uv run mypy .                    # Type checking for quality assurance
uv run pytest                   # Run tests to validate functionality

# Database operations (when working with data)
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head

# Testing commands for validation
uv run pytest tests/agents/      # Test agent functionality
uv run pytest tests/workflows/   # Test workflow orchestration  
uv run pytest tests/api/         # Test API endpoints
uv run pytest --cov=ai --cov=api --cov=lib  # With test coverage
```

## Core Development Patterns

### Development Principles
- **KISS, YAGNI, DRY**: Write simple, focused code that solves current needs without unnecessary complexity
- **SOLID Principles**: Apply where relevant, favor composition over inheritance
- **Modern Frameworks**: Use industry standard libraries over custom implementations
- **🚫 NO BACKWARD COMPATIBILITY**: Always break compatibility for clean, modern implementations
- **No Mocking/Placeholders**: Never mock, use placeholders, hardcode, or omit code
- **Explicit Side Effects**: Make side effects explicit and minimal
- **Honest Assessment**: Be brutally honest about whether ideas are good or bad

### YAML-First Configuration
All components use YAML configuration with hot reload capabilities:

```yaml
# Agent configuration example
agent:
  name: "Domain Specialist"
  agent_id: "domain-specialist"
  version: "1.0.0"  # CRITICAL: Bump version for ANY changes

model:
  provider: anthropic
  id: claude-sonnet-4-20250514
  temperature: 0.7

instructions: |
  You are a specialist who handles specific domain tasks
  with access to knowledge base and conversation memory.
```

### Agno Framework Integration
- **Playground Pattern**: Auto-generates API endpoints via `Playground()` 
- **FastAPI Integration**: Uses Agno's `FastAPIApp()` for production deployment
- **Storage**: PostgreSQL with pgvector support, automatic SQLite fallback
- **Streaming**: Real-time responses via Server-Sent Events and WebSocket

### Environment-Based Configuration
Configuration scales automatically from development to production:
- **Development**: Relaxed CORS, docs enabled, SQLite fallback
- **Production**: Strict security, API key required, PostgreSQL with connection pooling

## Key Technical Details

### Database Architecture
- **Primary**: PostgreSQL with pgvector for embeddings
- **Fallback**: SQLite for development
- **Migrations**: Alembic with automatic schema management
- **Connection**: Pool size 20, max overflow 30, connection recycling

### API Architecture
- **Framework**: FastAPI with automatic OpenAPI docs
- **Authentication**: API key middleware (configurable)
- **Streaming**: SSE and WebSocket support for real-time responses
- **CORS**: Environment-based origin configuration

### Knowledge Management
- **Format**: CSV-based RAG with hot reload
- **Storage**: PostgreSQL with vector search capabilities
- **Filtering**: Business unit and context-aware retrieval
- **Performance**: Incremental loading with hash-based change detection

## Configuration Management

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Database (optional - auto-fallback to SQLite)
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@host:port/db

# API Configuration
RUNTIME_ENV=dev|staging|prd
HIVE_API_PORT=8886
HIVE_API_HOST=0.0.0.0
```

### Component Creation
```bash
# Create new components from templates
cp -r ai/agents/template-agent ai/agents/my-new-agent
cp -r ai/teams/template-team ai/teams/my-routing-team
cp -r ai/workflows/template-workflow ai/workflows/my-workflow

# CRITICAL: After copying, immediately update version in config.yaml
# Remember: ANY change requires version bump in YAML config
```

## Performance Characteristics

- **Startup Time**: 3-5s development, 8-12s production (includes migrations)
- **Response Time**: <200ms development, <500ms production
- **Concurrent Users**: 10-50 development, 1000+ production with scaling
- **Memory Usage**: ~200MB development, ~500MB per worker production

## Important Development Rules

### Automagik Hive Specific
- **Agent Development**: Always use YAML configuration files following existing architecture patterns
- **🚨 CRITICAL VERSION BUMPING**: For ANY change to agents/teams/workflows (code, config, tools, instructions), the version MUST be bumped in the YAML config file
- **Testing Required**: Every new agent must have corresponding unit and integration tests
- **Knowledge Base**: Use CSV-based RAG system with hot reload for context-aware responses
- **No Hardcoding**: Never hardcode values - always use .env files and YAML configs
- **🚫 NO LEGACY CODE**: Remove backward compatibility code immediately - clean implementations only
- **🎯 KISS Principle**: Simplify over-engineered components, eliminate redundant layers

### File Organization & Modularity
- **Small Focused Files**: Default to multiple small files (<350 lines) rather than monolithic ones
- **Single Responsibility**: Each file should have one clear purpose
- **Separation of Concerns**: Separate utilities, constants, types, components, and business logic
- **Composition Over Inheritance**: Use inheritance only for true 'is-a' relationships
- **Clear Structure**: Follow existing project structure, create new directories when appropriate
- **Proper Imports/Exports**: Design for reusability and maintainability

### Python Development
- **Never use python directly**: Always use `uv run` for python commands
- **UV Package Management**: Use `uv add <package>` for dependencies, never pip

### Git Commit Requirements
- **📧 MANDATORY**: ALWAYS co-author commits with: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`

## Component-Specific Guides

For detailed implementation guidance, see component-specific CLAUDE.md files:
- `ai/CLAUDE.md` - Multi-agent system orchestration
- `api/CLAUDE.md` - FastAPI integration patterns  
- `lib/config/CLAUDE.md` - Configuration management
- `lib/knowledge/CLAUDE.md` - Knowledge base management
- `tests/CLAUDE.md` - Testing patterns

This framework provides a production-ready foundation for building sophisticated multi-agent AI systems with enterprise-grade deployment capabilities.