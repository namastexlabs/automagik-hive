# Automagik Hive

<div align="center">

![Automagik Logo](.github/images/automagik-logo.png)

**Enterprise Multi-Agent AI Development Framework**

*Production-grade platform for building intelligent agent ecosystems with MCP integration, specialized development agents, and autonomous orchestration capabilities*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Agno Framework](https://img.shields.io/badge/agno-v1.7.5-green.svg)](https://github.com/agno-agi/agno)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16+-blue.svg)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.116+-red.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-integrated-purple.svg)](https://modelcontextprotocol.io/)
[![UV](https://img.shields.io/badge/UV-native-orange.svg)](https://docs.astral.sh/uv/)

[Getting Started](#-getting-started) • [Agent Ecosystem](#-specialized-agent-ecosystem) • [MCP Integration](#-mcp-integration) • [Development](#-development) • [Deployment](#-deployment)

</div>

## 🚀 Overview

Automagik Hive is a **next-generation multi-agent AI development framework** that transforms how developers build and orchestrate intelligent systems. Built on **Agno v1.7.5** with extensive **Model Context Protocol (MCP)** integration, it provides a complete ecosystem for rapid development of sophisticated multi-agent applications.

**What makes it revolutionary:** 
- **Specialized Agent Ecosystem**: Pre-built development agents for planning, coding, testing, quality assurance, and debugging
- **MCP-Native Integration**: Direct access to databases, external services, and development tools through standardized protocols
- **Dual Environment Architecture**: Separate user and agent environments for optimal development workflows
- **Autonomous Orchestration**: Intelligent agent routing and task delegation with minimal human intervention

```mermaid
graph TD
    Dev[👨‍💻 Developer] --> Hive[🏗️ Automagik Hive]
    
    Hive --> AgentEco[🤖 Specialized Agent Ecosystem]
    Hive --> MCP[🔌 MCP Integration]
    Hive --> DualEnv[⚡ Dual Environment]
    
    AgentEco --> Planning[📋 genie-dev-planner]
    AgentEco --> Design[🏗️ genie-dev-designer]  
    AgentEco --> Coding[💻 genie-dev-coder]
    AgentEco --> Testing[🧪 genie-testing-*]
    AgentEco --> Quality[✅ genie-quality-*]
    
    MCP --> Postgres[🐘 PostgreSQL]
    MCP --> Forge[🔨 automagik-forge]
    MCP --> External[🌐 External Services]
    
    DualEnv --> UserEnv[👤 User Environment<br/>:8886]
    DualEnv --> AgentEnv[🤖 Agent Environment<br/>:38886]
    
    classDef dev fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000000
    classDef hive fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000000
    classDef agents fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000000
    classDef mcp fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000000
    
    class Dev dev
    class Hive hive
    class AgentEco,Planning,Design,Coding,Testing,Quality agents
    class MCP,Postgres,Forge,External,DualEnv,UserEnv,AgentEnv mcp
```

## ⚡ Getting Started

### Quick Installation

**For Developers (Recommended):**
```bash
# Clone and install with full development stack
git clone https://github.com/namastexlabs/automagik-hive.git
cd automagik-hive
make install-agent  # Sets up agent environment (ports 38886/35532)
make agent          # Start agent environment in background
```

**For Production:**
```bash
# Full system installation
make install        # User environment setup
make prod          # Production Docker stack
```

### Dual Environment Architecture

Automagik Hive runs two specialized environments:

| Environment | Purpose | API Port | DB Port | Usage |
|-------------|---------|----------|---------|--------|
| **User Environment** | Production applications, custom agents | 8886 | 5532 | `make dev` / `make prod` |
| **Agent Environment** | AI development, specialized agents, MCP tools | 38886 | 35532 | `make agent` |

### First Steps

```bash
# 1. Start agent environment (for AI development)
make agent

# 2. Verify MCP connections
curl http://localhost:38886/health

# 3. Access specialized agents at:
# http://localhost:38886/docs
```

### Available Endpoints

**Agent Environment (AI Development):**
- **API**: http://localhost:38886 
- **Docs**: http://localhost:38886/docs
- **Agent Specialists**: Built-in development agents accessible via API

**User Environment (Production):**
- **API**: http://localhost:8886
- **Custom Agents**: Your business-specific agents
- **Production Features**: Full enterprise capabilities

## 🤖 Specialized Agent Ecosystem

Automagik Hive includes a comprehensive ecosystem of pre-built development agents that handle the entire software development lifecycle:

### Development Pipeline Agents

| Agent | Purpose | Specialization |
|-------|---------|----------------|
| **genie-dev-planner** | Requirements analysis & technical specifications | Converts user requirements into detailed technical plans |
| **genie-dev-designer** | System architecture & design documents | Creates comprehensive system designs and architectural decisions |
| **genie-dev-coder** | Implementation & code generation | Writes production-ready code based on specifications |
| **genie-dev-fixer** | Debugging & issue resolution | Systematic debugging and problem resolution |

### Quality Assurance Agents

| Agent | Purpose | Specialization |
|-------|---------|----------------|
| **genie-testing-maker** | Test suite creation | Generates comprehensive unit, integration, and end-to-end tests |
| **genie-testing-fixer** | Test maintenance & fixes | Resolves failing tests and improves test coverage |
| **genie-quality-ruff** | Code formatting & linting | Enforces code style using Ruff (replaces Black, isort, flake8) |
| **genie-quality-mypy** | Type checking & validation | Ensures type safety and catches type-related bugs |

### Meta-Development Agents

| Agent | Purpose | Specialization |
|-------|---------|----------------|
| **genie-agent-creator** | New agent development | Creates new specialized agents for custom needs |
| **genie-agent-enhancer** | Agent optimization | Improves existing agent capabilities and performance |
| **genie-claudemd** | Documentation management | Maintains and updates CLAUDE.md documentation system |
| **genie-clone** | Complex task coordination | Handles multi-faceted projects requiring parallel execution |

### Usage Pattern

```python
# Typical development workflow using specialized agents
1. genie-dev-planner    # "Create user authentication system"
2. genie-dev-designer   # Designs auth architecture
3. genie-testing-maker  # Creates comprehensive test suite  
4. genie-dev-coder      # Implements the system
5. genie-testing-fixer  # Ensures all tests pass
6. genie-quality-ruff   # Formats and lints code
7. genie-quality-mypy   # Validates type safety
```

## 🔌 MCP Integration

Automagik Hive leverages **Model Context Protocol (MCP)** for seamless integration with development tools and external services:

### Built-in MCP Servers

| Server | Purpose | Access |
|--------|---------|--------|
| **postgres** | Direct database queries and schema management | `postgresql://localhost:35532/hive_agent` |
| **automagik-forge** | Project and task management system | Task creation, tracking, and coordination |
| **search-repo-docs** | Documentation and code repository search | Access to library docs and code examples |
| **ask-repo-agent** | Repository Q&A and analysis | GitHub repository insights and guidance |
| **send_whatsapp_message** | External notifications and alerts | WhatsApp integration for status updates |

### MCP Configuration Example

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", 
               "postgresql+psycopg://user:pass@localhost:35532/hive_agent"]
    },
    "automagik-hive": {
      "command": "uvx",
      "args": ["automagik-tools@0.8.17", "tool", "automagik-hive"],
      "env": {
        "HIVE_API_BASE_URL": "http://localhost:38886",
        "HIVE_API_KEY": "hive_your_key_here"
      }
    }
  }
}
```

## ✨ Key Features

### 🤖 **Autonomous Development Capabilities**
- **Specialized Agent Ecosystem**: 15+ pre-built development agents covering the entire SDLC
- **Intelligent Task Orchestration**: Automatic routing of development tasks to appropriate specialists
- **TDD-Compliant Workflows**: Built-in Red-Green-Refactor cycle enforcement
- **Parallel Agent Execution**: Multiple agents working simultaneously on independent tasks

### 🔌 **Advanced MCP Integration**
- **Database Direct Access**: Real-time PostgreSQL queries and schema management
- **External Service Integration**: WhatsApp notifications, task management, documentation search
- **Development Tool Connectivity**: Direct access to testing frameworks, linters, and quality tools
- **Standardized Protocol Support**: Full MCP 1.0+ compliance with extensible server ecosystem

### 🏗️ **Enterprise Architecture**
- **Dual Environment Design**: Isolated user and agent environments with separate databases
- **UV-Native Package Management**: Modern Python tooling with lightning-fast dependency resolution
- **Production-Grade Infrastructure**: Docker orchestration, health monitoring, and auto-scaling
- **Comprehensive Testing**: 266+ test files covering all system components

### 🧠 **Intelligent Knowledge Management**
- **Vector-Enhanced RAG**: PostgreSQL + pgvector for semantic search and context retrieval
- **Hot-Reload CSV Integration**: Business data updates without system restart
- **Context-Aware Filtering**: Agents access only relevant knowledge for their domain
- **Version-Controlled Components**: Database-backed versioning with automatic sync services

### 🔒 **Security & Observability**
- **Multi-Layer Authentication**: API keys, environment isolation, and secure credential management
- **Comprehensive Logging**: Structured logging with trace IDs and error taxonomy
- **Health Monitoring**: Real-time system status with component-level health checks
- **MCP Security**: Secure external service connections with credential rotation

## 🔧 Development Configuration

### Specialized Agent Configuration

The development agents use sophisticated configurations optimized for software development workflows:

```yaml
# .claude/agents/genie-dev-coder.md example
agent:
  name: "Genie Development Coder"
  agent_id: "genie-dev-coder"
  version: "2.1.0"
  description: "TDD-compliant implementation specialist with comprehensive toolkits"

model:
  provider: anthropic 
  id: claude-sonnet-4-20250514
  temperature: 0.1  # Low temperature for precise code generation
  max_tokens: 4000

toolkits:
  - code_editing_toolkit      # File operations, code modifications
  - code_understanding_toolkit # AST analysis, dependency tracking  
  - file_management_toolkit   # Project structure management

instructions: |
  You are GENIE DEV CODER - the implementation specialist of the Genie hive.
  
  CORE RESPONSIBILITIES:
  - Implement features based on DDD (Design Decision Documents)
  - Follow TDD Red-Green-Refactor cycle religiously
  - Write production-ready, type-safe Python code
  - Ensure comprehensive error handling and logging
  - Integrate with existing codebase patterns seamlessly

memory:
  enable_context_preservation: true
  track_implementation_patterns: true
  learn_from_code_reviews: true
```

### MCP Server Configuration

```json
# .mcp.json - MCP server ecosystem configuration
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", 
               "postgresql+psycopg://user:pass@localhost:35532/hive_agent"]
    },
    "automagik-forge": {
      "type": "sse",
      "url": "http://localhost:8889/sse"
    },
    "search-repo-docs": {
      "command": "npx", 
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

### Environment Configuration

```bash
# .env.agent - Agent environment configuration
HIVE_API_PORT=38886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:35532/hive_agent
HIVE_API_KEY=hive_your_secure_key_here

# AI Provider Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Development-specific settings
RUNTIME_ENV=development
ENABLE_AGENT_TOOLKITS=true
MCP_SERVERS_CONFIG=.mcp.json
```

### Knowledge Base Integration

```csv
# lib/knowledge/knowledge_rag.csv - Development-focused knowledge
domain,topic,content,tags
development,testing,Use pytest with asyncio support for async tests,pytest,asyncio,testing
development,agents,Agno agents use YAML configuration with hot reload,agno,yaml,configuration
development,database,PostgreSQL with pgvector for semantic search,postgresql,pgvector,rag
```

## 🚀 Development Workflow

### Agent-Driven Development

```bash
# 1. Start agent environment
make agent-status    # Check if services are running
make agent          # Start agent environment (non-blocking)

# 2. Access development agents via API
curl -X POST http://localhost:38886/api/v1/agents/genie-dev-planner \
  -H "x-api-key: your_agent_key" \
  -d '{"message": "Plan a user authentication system"}'

# 3. Monitor progress
make agent-logs     # View agent activity
```

### Command Reference

| Command | Purpose | Environment |
|---------|---------|-------------|
| `make agent` | Start agent development environment | Agent (38886) |
| `make agent-stop` | Stop agent environment cleanly | Agent |
| `make agent-restart` | Restart agent environment | Agent |
| `make agent-logs` | View agent activity logs | Agent |
| `make dev` | Start local development server | User (8886) |
| `make prod` | Production Docker deployment | User (8886) |

## 🐳 Production Deployment

### Docker Deployment (Recommended)

```bash
# Full production stack
make install        # Set up user environment
make prod          # Start production containers

# Health check
curl http://localhost:8886/health
```

### Environment Variables

```bash
# User Environment (.env)
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_API_KEY=hive_your_production_key

# Agent Environment (.env.agent) 
HIVE_API_PORT=38886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:35532/hive_agent
HIVE_API_KEY=hive_your_agent_key

# AI Provider Keys (both environments)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# MCP Configuration
MCP_SERVERS_CONFIG=.mcp.json
ENABLE_MCP_INTEGRATION=true
```

### Production Architecture

```yaml
# docker-compose.yml structure
services:
  app:                    # User environment (8886)
    build: .
    ports: ["8886:8886"]
    depends_on: [postgres]
    
  postgres:               # User database (5532)
    image: pgvector/pgvector:pg16
    ports: ["5532:5432"]
    
  # Agent environment runs separately via docker-compose-agent.yml
```

## 💻 Development with Specialized Agents

### Using Development Agents

The specialized agent ecosystem handles most development tasks automatically:

```bash
# Development workflow using agents
1. Start agent environment
make agent

2. Access specialized agents via API:
   - POST /api/v1/agents/genie-dev-planner    # Requirements → Technical specs
   - POST /api/v1/agents/genie-dev-designer   # Specs → Architecture design  
   - POST /api/v1/agents/genie-testing-maker  # Design → Comprehensive tests
   - POST /api/v1/agents/genie-dev-coder      # Design → Implementation
   - POST /api/v1/agents/genie-quality-ruff   # Code → Formatted & linted
   - POST /api/v1/agents/genie-quality-mypy   # Code → Type-safe
```

### Creating Custom Agents

```bash
# Use the agent creation specialist
curl -X POST http://localhost:38886/api/v1/agents/genie-agent-creator \
  -H "x-api-key: your_key" \
  -d '{
    "message": "Create an agent for API documentation generation",
    "requirements": "Parse FastAPI code and generate OpenAPI docs"
  }'

# Or manually create traditional Agno agents
cp -r ai/agents/template-agent ai/agents/my-custom-agent
# Edit ai/agents/my-custom-agent/config.yaml
```

### Modern Development Commands

```bash
# UV-native package management (never use pip!)
uv add anthropic                    # Add dependency
uv remove old-package              # Remove dependency
uv sync                           # Sync dependencies

# Quality assurance with specialized agents
make agent                        # Ensure agent environment is running
# Use genie-quality-ruff and genie-quality-mypy via API

# Testing with specialized agents  
# Use genie-testing-maker and genie-testing-fixer via API

# Traditional testing (when needed)
uv run pytest                     # Run all tests
uv run pytest tests/agents/       # Test agent functionality
uv run pytest --cov=ai --cov=api --cov=lib  # With coverage
```

### Database Operations

```bash
# Database migrations
uv run alembic revision --autogenerate -m "Add feature"
uv run alembic upgrade head

# MCP database access
# Direct PostgreSQL queries via MCP postgres server
# No need for manual database scripts
```

### Agent Environment Management

```bash
# Agent environment lifecycle
make install-agent     # Initial setup (destructive reinstall)
make agent            # Start in background
make agent-restart    # Clean restart
make agent-stop       # Graceful shutdown
make agent-status     # Check service health
make agent-logs       # View activity logs
```

## 📊 System Metrics

### Environment Performance

| Environment | Purpose | Startup Time | Memory Usage | Concurrent Agents | Database |
|-------------|---------|--------------|--------------|-------------------|----------|
| **Agent Environment** | AI development, specialized agents | ~2-3s | ~300MB | 15+ specialists | PostgreSQL (35532) |
| **User Environment** | Production apps, custom agents | ~5-8s | ~500MB | 50+ custom | PostgreSQL (5532) |

### Agent Ecosystem Stats

| Component | Count | Test Coverage | Type Safety |
|-----------|-------|---------------|-------------|
| **Specialized Agents** | 15+ | 95%+ | Full MyPy |
| **Development Tools** | 8 toolkits | 90%+ | Type-safe |
| **MCP Servers** | 5+ integrated | 85%+ | Protocol-compliant |
| **Test Suite** | 266+ files | 90%+ | Comprehensive |

### Scaling Characteristics

- **Agent Concurrency**: 10+ specialized agents simultaneously
- **MCP Connections**: 5+ external services with connection pooling
- **Database Performance**: pgvector for sub-100ms semantic search
- **Memory Efficiency**: UV package management reduces overhead by ~40%

## 🛠️ Modern Tech Stack

### Core Multi-Agent Framework
- **[Agno v1.7.5](https://github.com/agno-agi/agno)** - Advanced multi-agent orchestration with streaming
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** - Standardized tool and service integration
- **[FastAPI 0.116+](https://fastapi.tiangolo.com/)** - High-performance async API framework
- **[UV Package Manager](https://docs.astral.sh/uv/)** - Lightning-fast Python dependency management

### AI & Language Models
- **[Anthropic Claude Sonnet 4](https://www.anthropic.com/)** - Primary reasoning and coding model
- **[OpenAI GPT-4](https://openai.com/)** - Alternative model support with streaming
- **[Google Gemini](https://ai.google.dev/)** - Specialized tasks and analysis
- **[Cohere](https://cohere.com/)** - Embedding generation and text classification

### Database & Vector Search
- **[PostgreSQL 16+](https://www.postgresql.org/)** - Primary database with ACID compliance
- **[pgvector](https://github.com/pgvector/pgvector)** - High-performance vector embeddings
- **[SQLAlchemy 2.0+](https://www.sqlalchemy.org/)** - Modern async ORM with type safety
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database schema migrations

### Development & Quality Tools
- **[Ruff](https://github.com/astral-sh/ruff)** - Ultra-fast Python linter/formatter (replaces Black, isort, flake8)
- **[MyPy](https://mypy.readthedocs.io/)** - Static type checking with strict enforcement
- **[Pytest](https://pytest.org/)** - Comprehensive testing framework with async support
- **[Docker](https://www.docker.com/)** - Containerization with multi-stage builds

### External Integrations
- **[automagik-forge](https://github.com/namastexlabs/automagik-forge)** - Project and task management
- **[Evolution API](https://evolution-api.com/)** - WhatsApp business messaging
- **[Context7](https://context7.com/)** - Repository documentation and code search

## 📚 Documentation & Resources

### Component Documentation
- **[Specialized Agents](.claude/agents/)** - Pre-built development agent ecosystem
- **[Agent Development](ai/agents/CLAUDE.md)** - Creating custom Agno agents
- **[MCP Integration](lib/mcp/CLAUDE.md)** - Model Context Protocol setup and usage
- **[API Development](api/CLAUDE.md)** - FastAPI endpoints and streaming capabilities
- **[Knowledge Management](lib/knowledge/CLAUDE.md)** - RAG system with pgvector

### Development Guides
- **[Development Workflow](#-development-workflow)** - Using specialized agents for development
- **[Environment Setup](#dual-environment-architecture)** - Agent vs User environment configuration
- **[Testing Strategy](tests/CLAUDE.md)** - Comprehensive testing with agent assistance
- **[Quality Assurance](#quality-assurance-agents)** - Automated code quality and type safety

### Architecture References
- **[System Architecture](#-overview)** - Multi-agent ecosystem overview
- **[MCP Server Configuration](#-mcp-integration)** - External service integrations
- **[Database Design](lib/models/)** - PostgreSQL schema and migrations
- **[Security Model](lib/auth/CLAUDE.md)** - Authentication and authorization

## 🤝 Contributing

We welcome contributions to the Automagik Hive ecosystem! Here's how to get involved:

### Development Contributions

1. **Fork** the repository and clone locally
2. **Set up development environment**: `make install-agent`
3. **Create feature branch**: `git checkout -b feature/agent-enhancement`
4. **Use specialized agents**: Let the development agents help build your feature
5. **Submit Pull Request**: Include tests and documentation

### Agent Development

```bash
# Create new specialized agent using the agent creator
curl -X POST http://localhost:38886/api/v1/agents/genie-agent-creator \
  -H "x-api-key: your_key" \
  -d '{"message": "Create agent for [your use case]"}'
```

### Commit Standards

All commits must be co-authored with the development team:
```bash
Co-Authored-By: Automagik Genie <genie@namastex.ai>
```

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- **[Agno Framework](https://github.com/agno-agi/agno)** - Multi-agent orchestration foundation
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Standardized AI tool integration
- **[UV Package Manager](https://docs.astral.sh/uv/)** - Modern Python dependency management
- **The AI Development Community** - For advancing multi-agent systems

---

<div align="center">

**[💬 Discord](https://discord.gg/CEbzP5Hteh)** • **[🐛 Issues](https://github.com/namastexlabs/automagik-hive/issues)** • **[💬 Discussions](https://github.com/namastexlabs/automagik-hive/discussions)** • **[📖 Documentation](https://docs.automagik.ai)**

**Built for the future of AI-driven development**

Made with ❤️ by the **Automagik Team**

</div>