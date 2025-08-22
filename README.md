# Automagik Hive

<div align="center">

![Automagik Logo](.github/images/automagik-logo.png)

**Enterprise Multi-Agent AI Framework**

*Production-grade boilerplate for building sophisticated multi-agent systems with intelligent routing and enterprise-grade deployment capabilities*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Agno Framework](https://img.shields.io/badge/agno-v1.7.5-green.svg)](https://github.com/agno-agi/agno)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16+-blue.svg)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.116+-red.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

[Getting Started](#-getting-started) • [Architecture](#%EF%B8%8F-architecture) • [Features](#-features) • [Configuration](#-configuration) • [Deployment](#-deployment)

</div>

## 🚀 Overview

Automagik Hive is a production-ready enterprise multi-agent framework that transforms how you build AI-powered applications. Built on **Clean Architecture** principles with **Agno v1.7.5** at its core, it enables rapid development of sophisticated multi-agent systems through simple YAML configuration.

**What makes it special:** Instead of writing complex code, you define intelligent agents, routing teams, and business workflows in YAML files. Automagik Hive automatically handles orchestration, memory management, knowledge integration, API generation, and enterprise deployment.

```mermaid
graph LR
    You[👨‍💻 You] --> Build{What You Can Build}
    
    Build --> Agent[🤖 Smart Agents]
    Build --> Team[👥 Agent Teams]
    Build --> Workflow[⚡ Workflows]
    
    Agent --> Framework[🏗️ Automagik Hive]
    Team --> Framework
    Workflow --> Framework
    
    Framework --> Features{Core Features}
    Features --> Knowledge[📚 Smart Knowledge]
    Features --> API[🌐 Instant APIs]
    Features --> Deploy[🚀 Easy Deploy]
    
    classDef you fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000000
    classDef build fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000000
    classDef framework fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000000
    classDef features fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000000
    
    class You you
    class Agent,Team,Workflow build
    class Framework framework
    class Knowledge,API,Deploy features
```

## ⚡ Getting Started

### Universal Installation (Recommended)

Get started on any machine with our universal installer:

```bash
# One-command installation (handles everything)
curl -sSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh | bash

# Or download and run locally
wget https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Detect your OS (Linux, macOS, Windows/WSL)
- ✅ Install Python 3.12+ via uv (if needed)
- ✅ Install system dependencies
- ✅ Optional Docker setup with secure PostgreSQL
- ✅ Run `make install` automatically
- ✅ Validate everything works

### Alternative Installation Methods

<details>
<summary><strong>Local Development</strong></summary>

```bash
# Install dependencies (local only)
make install

# Start development server
make dev
```
</details>

<details>
<summary><strong>Production with Docker</strong></summary>

```bash
# Start production stack
make prod

# Check status
make status
```
</details>

<details>
<summary><strong>Development Environment</strong></summary>

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Code quality checks
uv run ruff check --fix
uv run mypy .
```
</details>

### Quick Access

Available endpoints:
- **API**: http://localhost:8886 (configurable via HIVE_API_PORT)
- **Docs**: http://localhost:8886/docs (Swagger UI)
- **Health**: http://localhost:8886/api/v1/health

## 🏗️ Architecture

### 🤖 **Smart Agents**
Create intelligent agents that understand your business domain and remember conversations.

### 👥 **Agent Teams** 
Build teams that intelligently route requests to the right specialist using Agno's mode="route".

### ⚡ **Business Workflows**
Automate complex business processes with multi-step workflows and human handoff capabilities.

### 🌐 **Instant Production APIs**
Your agents become APIs automatically - no code required. Real-time streaming, authentication, and Docker-ready deployment.

### 📚 **Smart Knowledge Base**
Import your business data via CSV and get instant semantic search with hot reload capabilities.

## ✨ Features

### 🔧 **Enterprise Configuration Management**
- **YAML-First Architecture**: All components configured via YAML with hot reload
- **Environment Scaling**: Automatic security/feature scaling from dev to production  
- **Version Management**: Database-driven component versioning with sync services
- **Registry Patterns**: Centralized component discovery and batch optimization

### 🧠 **Advanced Knowledge Management**
- **CSV-Based RAG**: Business data integration with vector search capabilities
- **Smart Incremental Loading**: Efficient updates with hash-based change detection
- **Business Unit Filtering**: Context-aware knowledge retrieval
- **PostgreSQL Vector Storage**: Production-grade persistence with pgvector

### 🚀 **Production-Ready Deployment**
- **Multi-Stage Docker**: UV-native builds with security hardening
- **Container Orchestration**: Docker Compose with health checks and dependencies
- **Database Migrations**: Alembic integration with automatic schema management
- **Performance Optimization**: Connection pooling, caching, and startup orchestration

### 🔒 **Enterprise Security & Monitoring**
- **API Authentication**: Configurable API key middleware
- **Structured Logging**: Comprehensive error taxonomy with trace IDs
- **Health Monitoring**: Detailed system status and component health
- **MCP Integration**: Secure external system connectivity

## 📚 Configuration

### Agent Configuration

```yaml
# ai/agents/my-agent/config.yaml
agent:
  name: "Customer Support Specialist"
  agent_id: "customer-support"
  version: "1.0.0"
  description: "Handles customer inquiries with domain expertise"

model:
  provider: anthropic
  id: claude-sonnet-4-20250514
  temperature: 0.7
  max_tokens: 2000

instructions: |
  You are a customer support specialist who helps with billing,
  account issues, and product questions. You have access to our
  knowledge base and remember previous conversations.

knowledge_filter:
  enable_agentic_knowledge_filters: true
  search_knowledge: true
  max_results: 5
  business_unit_filter: "customer_support"

memory:
  enable_user_memories: true
  add_history_to_messages: true
  read_chat_history: true
```

### Team Configuration

```yaml
# ai/teams/routing-team/config.yaml
team:
  mode: route
  name: "Customer Service Routing Team"
  team_id: "customer-routing"
  version: "1.0.0"

model:
  provider: anthropic
  id: claude-sonnet-4-20250514
  temperature: 0.7

members:
  - billing-specialist
  - technical-support
  - account-management

instructions: |
  You are a customer service routing team.
  Route billing questions to billing-specialist
  Route technical issues to technical-support
  Route account changes to account-management
```

### Knowledge Base Setup

```csv
# lib/knowledge/knowledge_rag.csv
business_unit,question,answer,solution
Support,How do I reset my password?,Click Account > Reset Password,account_recovery
Billing,When is my payment due?,Payments are due on the 15th of each month,payment_schedule
```

**Key Benefits:**
- 🔄 **Hot Reload**: Edit CSV, changes apply instantly
- 🔍 **Vector Search**: Semantic search powered by PostgreSQL + pgvector
- 🎯 **Smart Filtering**: Agents only see relevant knowledge
- 📈 **Scalable**: Handles large knowledge bases efficiently

## 🐳 Deployment

### Docker Deployment (Recommended)

```bash
# Production deployment
docker-compose up --build -d

# Check service health
docker-compose ps
docker-compose logs app
```

### Environment Variables

```bash
# Database Configuration
HIVE_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/hive

# API Configuration  
RUNTIME_ENV=prd                    # dev/staging/prd
HIVE_API_PORT=8886
HIVE_API_HOST=0.0.0.0
HIVE_API_WORKERS=4

# AI Provider Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional Integrations
MCP_SERVERS_CONFIG=mcp_config.json
```

### Kubernetes (Advanced)

```yaml
# k8s/deployment.yaml example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: automagik-hive
spec:
  replicas: 3
  selector:
    matchLabels:
      app: automagik-hive
  template:
    metadata:
      labels:
        app: automagik-hive
    spec:
      containers:
      - name: hive-app
        image: automagik-hive:latest
        ports:
        - containerPort: 8886
        env:
        - name: HIVE_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## 🔧 Development

### Creating New Components

```bash
# Create new agent
cp -r ai/agents/template-agent ai/agents/my-new-agent
# Edit ai/agents/my-new-agent/config.yaml

# Create new team
cp -r ai/teams/template-team ai/teams/my-routing-team
# Edit ai/teams/my-routing-team/config.yaml

# Create new workflow
cp -r ai/workflows/template-workflow ai/workflows/my-workflow
# Edit ai/workflows/my-workflow/config.yaml
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test suites
uv run pytest tests/agents/
uv run pytest tests/workflows/
uv run pytest tests/api/

# Run with coverage
uv run pytest --cov=ai --cov=api --cov=lib
```

### Database Development

```bash
# Database development
uv run alembic revision --autogenerate -m "Add feature"
uv run alembic upgrade head
```

## 📊 Performance

### Benchmarks

| Metric | Development | Production |
|--------|-------------|------------|
| **Startup Time** | ~3-5s | ~8-12s (includes migrations) |
| **Response Time** | <200ms | <500ms (with database) |
| **Concurrent Users** | 10-50 | 1000+ (with proper scaling) |
| **Memory Usage** | ~200MB | ~500MB (per worker) |
| **Database Connections** | 5-10 | 50-200 (pooled) |

### Scaling Recommendations

- **Small Deployment**: 1-2 workers, 1GB RAM, PostgreSQL
- **Medium Deployment**: 4-8 workers, 4GB RAM, PostgreSQL with replicas
- **Large Deployment**: 16+ workers, 8GB+ RAM, PostgreSQL cluster
- **Enterprise**: Kubernetes with horizontal pod autoscaling

## 🛠️ Tech Stack

### Core Framework
- **[Agno v1.7.5](https://github.com/agno-agi/agno)** - Multi-agent orchestration framework
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern API framework with auto-docs
- **[PostgreSQL + pgvector](https://github.com/pgvector/pgvector)** - Vector database for embeddings
- **[UV](https://docs.astral.sh/uv/)** - Modern Python package manager

### AI Providers
- **[Anthropic Claude](https://www.anthropic.com/)** - Primary reasoning model
- **[OpenAI GPT](https://openai.com/)** - Alternative model support
- **[Cohere](https://cohere.com/)** - Embedding and classification
- **[Google AI](https://ai.google.dev/)** - Gemini model integration

### Infrastructure
- **[Docker](https://www.docker.com/)** - Containerization with multi-stage builds
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migrations
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM with async support
- **[Pydantic](https://pydantic.dev/)** - Data validation and serialization

## 📚 Documentation

### Quick References
- **[Agent Development](ai/agents/CLAUDE.md)** - Creating and configuring agents
- **[Team Orchestration](ai/teams/CLAUDE.md)** - Setting up routing teams
- **[Workflow Creation](ai/workflows/CLAUDE.md)** - Building multi-step processes
- **[API Integration](api/CLAUDE.md)** - FastAPI endpoints and streaming
- **[Knowledge Management](lib/knowledge/)** - RAG system configuration

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Commit Standards

All commits should be co-authored with:
```bash
Co-Authored-By: Automagik Genie <genie@namastex.ai>
```

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Agno Framework](https://github.com/agno-agi/agno)** for providing the multi-agent foundation

---

<div align="center">

**[💬 Discord](https://discord.gg/CEbzP5Hteh)** • **[🐛 Issues](https://github.com/namastexlabs/automagik-hive/issues)** • **[💬 Discussions](https://github.com/namastexlabs/automagik-hive/discussions)**

Made with ❤️ by the **Automagik Team**

</div>