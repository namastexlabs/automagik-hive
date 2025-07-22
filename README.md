# Automagik Hive

<div align="center">

![Automagik Logo](.github/images/automagik-logo.png)

**Enterprise Multi-Agent AI Framework**

*Production-grade boilerplate for building sophisticated multi-agent systems with intelligent routing and enterprise-grade deployment capabilities*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Agno Framework](https://img.shields.io/badge/agno-v1.7.5-green.svg)](https://github.com/phidatahq/agno)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16+-blue.svg)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.116+-red.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

[Quick Start](#quick-start) • [Architecture](#architecture) • [Features](#features) • [Documentation](#documentation) • [Deployment](#deployment)

</div>

## 🚀 Overview

Automagik Hive is a production-ready enterprise multi-agent framework built on **Clean Architecture** principles with **Agno v1.7.5** at its core. It provides sophisticated multi-agent orchestration, intelligent routing, and enterprise-grade deployment capabilities through YAML-first configuration and modern containerization.

**Key Differentiators:**
- **YAML-First Configuration** with hot reload capabilities
- **Intelligent Team Routing** using Agno's mode="route" for domain specialists  
- **Enterprise-Grade Knowledge Management** with CSV-based RAG and vector search
- **Workflows 2.0** with parallel execution, conditional logic, and state management
- **Production-Ready Deployment** with multi-stage Docker builds and orchestration

## 🏗️ Architecture

The system follows clean architecture principles with intelligent routing teams that analyze queries and distribute them to specialized domain agents. Each agent has dedicated knowledge base access with intelligent filtering for precise and contextual responses.

```mermaid
graph TB
    %% Developer Starting Point
    Developer[👨‍💻 Framework Users<br/>Multi-Agent Developers<br/>Enterprise Teams<br/>AI System Builders] --> Framework
    
    %% Core Framework - Automagik Hive
    subgraph Framework[🏗️ Automagik Hive Framework]
        subgraph Core[⚡ Core Framework - Agno v1.7.5]
            AgnoCore[🤖 Agno Framework<br/>Agent Primitives<br/>Team Orchestration<br/>Storage Abstractions]
            ModelProviders[🧠 Model Providers<br/>Anthropic Claude<br/>OpenAI GPT<br/>Google Gemini<br/>Cohere]
            AgentMemory[💾 Agent Memory<br/>PostgreSQL Storage<br/>Session Management<br/>Context Persistence]
        end
        
        subgraph ComponentSystem[🔧 Component System]
            YAMLConfigs[📄 YAML Configurations<br/>Agent Definitions<br/>Team Compositions<br/>Workflow Processes]
            VersionFactory[🏭 Version Factory<br/>Component Versioning<br/>Dynamic Loading<br/>Hot Reload]
            ComponentRegistry[📚 Component Registry<br/>Agent Discovery<br/>Team Loading<br/>Workflow Management]
        end
        
        subgraph KnowledgeSystem[🧠 Enterprise Knowledge]
            CSVKnowledge[📊 CSV Knowledge Base<br/>Business Data<br/>Hot Reload<br/>Vector Search]
            IncrementalLoader[🔄 Incremental Loader<br/>Smart Updates<br/>Hash Detection<br/>Zero Downtime]
            VectorDB[🔍 PgVector Integration<br/>Semantic Search<br/>Embedding Storage<br/>Query Optimization]
        end
    end
    
    %% What Developers Build With Framework
    subgraph UserSystems[🎯 What You Build]
        subgraph Agents[🤖 Custom Agents]
            DomainAgents[🏢 Domain Specialists<br/>Business Logic<br/>Expertise Areas<br/>Tool Integration]
            RoutingAgents[🚦 Routing Agents<br/>Query Analysis<br/>Intent Detection<br/>Agent Selection]
            HumanEscalation[👤 Human Escalation<br/>Frustration Detection<br/>Handoff Triggers<br/>Support Integration]
        end
        
        subgraph Teams[👥 Agent Teams]
            RoutingTeams[🎯 Routing Teams<br/>mode: route<br/>Intelligent Distribution<br/>Specialist Coordination]
            CollaborativeTeams[🤝 Collaborative Teams<br/>mode: coordinate<br/>Multi-Agent Tasks<br/>Shared Context]
            WorkflowTeams[⚡ Workflow Teams<br/>Process Execution<br/>State Management<br/>Task Sequences]
        end
        
        subgraph Workflows[⚙️ Business Workflows]
            ConversationFlow[💬 Conversation Workflows<br/>Typification<br/>Quality Analysis<br/>Satisfaction Tracking]
            EscalationFlow[🚨 Escalation Workflows<br/>Human Handoff<br/>Notification Systems<br/>Context Transfer]
            BusinessProcesses[📋 Business Processes<br/>Custom Logic<br/>Integration Points<br/>Automation Rules]
        end
    end
    
    %% Deployment & Infrastructure
    subgraph Infrastructure[🏭 Deployment Infrastructure]
        subgraph API[🌐 FastAPI Application]
            PlaygroundAPI[🎮 Playground API<br/>Auto-Generated<br/>CRUD Operations<br/>Real-time Testing]
            ProductionAPI[🚀 Production API<br/>Authentication<br/>Rate Limiting<br/>Monitoring]
            StreamingAPI[📡 Streaming API<br/>Server-Sent Events<br/>WebSocket Support<br/>Real-time Updates]
        end
        
        subgraph Database[🗄️ Database Layer]
            PostgresDB[(🐘 PostgreSQL<br/>Component Versions<br/>Agent Sessions<br/>Knowledge Storage)]
            Migrations[📋 Alembic Migrations<br/>Schema Evolution<br/>Version Control<br/>Automated Updates]
            Monitoring[📊 Performance Monitoring<br/>Query Optimization<br/>Connection Pooling<br/>Health Checks]
        end
        
        subgraph Deployment[🚀 Deployment Options]
            DockerDeploy[🐳 Docker Deployment<br/>Multi-stage Builds<br/>Production Ready<br/>Scaling Support]
            K8sDeploy[☸️ Kubernetes<br/>Horizontal Scaling<br/>High Availability<br/>Enterprise Features]
            CloudDeploy[☁️ Cloud Platforms<br/>AWS/GCP/Azure<br/>Managed Services<br/>Auto-scaling]
        end
    end
    
    %% External Integrations
    subgraph Integrations[🔌 Integration Ecosystem]
        MCPProtocol[🔗 MCP Protocol<br/>Model Context Protocol<br/>Tool Integration<br/>External Services]
        NotificationSystems[📱 Notification Systems<br/>WhatsApp Business<br/>Slack Integration<br/>Email Automation]
        BusinessSystems[🏢 Business Systems<br/>CRM Integration<br/>ERP Connectivity<br/>API Gateways]
    end
    
    %% Framework Flow
    Developer --> YAMLConfigs
    YAMLConfigs --> VersionFactory
    VersionFactory --> ComponentRegistry
    ComponentRegistry --> AgnoCore
    
    %% Component Creation Flow
    AgnoCore --> DomainAgents
    AgnoCore --> RoutingTeams
    AgnoCore --> ConversationFlow
    
    %% Knowledge Flow
    CSVKnowledge --> IncrementalLoader
    IncrementalLoader --> VectorDB
    VectorDB --> DomainAgents
    
    %% Team Composition
    DomainAgents --> RoutingTeams
    RoutingTeams --> CollaborativeTeams
    CollaborativeTeams --> WorkflowTeams
    
    %% Workflow Integration
    WorkflowTeams --> ConversationFlow
    ConversationFlow --> EscalationFlow
    EscalationFlow --> BusinessProcesses
    
    %% API Generation
    UserSystems --> PlaygroundAPI
    PlaygroundAPI --> ProductionAPI
    ProductionAPI --> StreamingAPI
    
    %% Storage Integration
    AgentMemory --> PostgresDB
    ComponentRegistry --> PostgresDB
    VectorDB --> PostgresDB
    
    %% External Connections
    HumanEscalation --> NotificationSystems
    BusinessProcesses --> BusinessSystems
    DomainAgents --> MCPProtocol
    
    %% Deployment Flow
    ProductionAPI --> DockerDeploy
    DockerDeploy --> K8sDeploy
    K8sDeploy --> CloudDeploy
    
    %% Monitoring Integration
    PostgresDB --> Monitoring
    ProductionAPI --> Monitoring
    UserSystems --> Monitoring
    
    %% Styling
    classDef developer fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000000
    classDef framework fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000000
    classDef userSystems fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000000
    classDef infrastructure fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000000
    classDef integrations fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000000
    classDef agno fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000000
    classDef components fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000000
    classDef knowledge fill:#fff8e1,stroke:#f9a825,stroke-width:2px,color:#000000
    
    class Developer developer
    class Framework,Core,AgnoCore,ModelProviders,AgentMemory framework
    class ComponentSystem,YAMLConfigs,VersionFactory,ComponentRegistry components
    class KnowledgeSystem,CSVKnowledge,IncrementalLoader,VectorDB knowledge
    class UserSystems,Agents,Teams,Workflows,DomainAgents,RoutingAgents,HumanEscalation,RoutingTeams,CollaborativeTeams,WorkflowTeams,ConversationFlow,EscalationFlow,BusinessProcesses userSystems
    class Infrastructure,API,Database,Deployment,PlaygroundAPI,ProductionAPI,StreamingAPI,PostgresDB,Migrations,Monitoring,DockerDeploy,K8sDeploy,CloudDeploy infrastructure
    class Integrations,MCPProtocol,NotificationSystems,BusinessSystems integrations
```

## ⚡ Quick Start

### Universal Installation (Recommended)

Get started on any machine with our universal installer that handles all dependencies:

```bash
# One-command installation (handles everything)
curl -sSL https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh | bash

# Or download and run locally
wget https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/install.sh
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Detect your operating system (Linux, macOS, Windows/WSL)
- ✅ Install Python 3.12+ via uv (if needed)
- ✅ Install all system dependencies (curl, git, openssl, make)
- ✅ Offer optional Docker setup with secure PostgreSQL credentials
- ✅ Run `make install` automatically
- ✅ Validate everything works correctly

### Manual Installation

#### Option 1: Local Development
```bash
# Install dependencies (local only)
make install

# Start development server
make dev
```

#### Option 2: Production with Docker
```bash
# Start production stack
make prod

# Check status
make status
```

Available endpoints:
- **API**: http://localhost:8886 (configurable via HIVE_API_PORT)
- **Docs**: http://localhost:8886/docs (Swagger UI)
- **Health**: http://localhost:8886/api/v1/health

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

## 📚 Documentation

### Quick References
- **[Agent Development](ai/agents/CLAUDE.md)** - Creating and configuring agents
- **[Team Orchestration](ai/teams/CLAUDE.md)** - Setting up routing teams
- **[Workflow Creation](ai/workflows/CLAUDE.md)** - Building multi-step processes
- **[API Integration](api/CLAUDE.md)** - FastAPI endpoints and streaming
- **[Knowledge Management](lib/knowledge/)** - RAG system configuration

### Configuration Examples

#### Agent Configuration (`ai/agents/my-agent/config.yaml`)
```yaml
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

#### Team Configuration (`ai/teams/routing-team/config.yaml`)
```yaml
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

### Setting Up Development Environment

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Code quality checks
uv run ruff check --fix
uv run mypy .

# Database development
uv run alembic revision --autogenerate -m "Add feature"
uv run alembic upgrade head
```

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
- **[Agno v1.7.5](https://github.com/phidatahq/agno)** - Multi-agent orchestration framework
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

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Agno Framework](https://github.com/phidatahq/agno)** for providing the multi-agent foundation
- **[FastAPI](https://fastapi.tiangolo.com/)** for the excellent API framework
- **[Anthropic](https://www.anthropic.com/)** for Claude AI capabilities
- **Open Source Community** for the amazing tools and libraries

---

<div align="center">

**[🏠 Homepage](https://docs.automagik.ai)** • **[📧 Contact](mailto:hive@namastex.ai)** • **[🐛 Issues](https://github.com/namastexlabs/automagik-hive/issues)** • **[💬 Discussions](https://github.com/namastexlabs/automagik-hive/discussions)**

Made with ❤️ by the **Automagik Team**

</div>
