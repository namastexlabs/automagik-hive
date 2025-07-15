# Genie Agents Project Structure

This document provides the complete technology stack and file tree structure for the Genie Agents Enterprise Multi-Agent System. **AI agents MUST read this file to understand the project organization before making any changes.**

## Technology Stack

### Core Agent Development Framework
- **Agno Framework 1.7.0+** - The central orchestration framework for building multi-agent systems
  - Team routing with `mode="route"` for intelligent agent selection
  - Session management for conversation continuity
  - Built-in tool support and agent composition
  - Memory and context management
- **Python 3.12+** with **UV** - Modern Python runtime with fast dependency management

### Agent Infrastructure
- **FastAPI 0.116.0+** - RESTful API layer for agent interactions
- **Pydantic 2.0+** - Agent configuration validation and schema management
- **YAML Configuration** - Declarative agent definitions with hot reload support
- **Factory Pattern** - Dynamic agent instantiation and version management

### AI Model Providers
- **Anthropic API** - Primary: Claude models (Sonnet, Opus) for agent intelligence
- **OpenAI API** - Alternative: GPT models for cost-effective agents
- **Cohere API** - Additional: Command models for specialized tasks
- **MCP 1.10.1+** - Model Context Protocol for enhanced agent capabilities

### Data & Knowledge Layer
- **PostgreSQL 16+** - Primary database with pgvector for semantic search
- **SQLAlchemy 2.0+** - ORM with async support for data persistence
- **Alembic 1.16.4+** - Database schema versioning and migrations
- **Redis** - Session state and conversation memory caching
- **CSV Knowledge Base** - Hot-reloadable domain knowledge with RAG
- **Sentence Transformers 2.2.0+** - Embeddings for knowledge retrieval

### Real-time Communication
- **HTTPX 0.28.1+** - Async HTTP client for external API calls
- **WebSocket** - Real-time client-server communication (via FastAPI)
- **Watchdog 6.0.0+** - File system monitoring for hot reload capabilities

### Monitoring & Observability
- **Prometheus** - Metrics collection and monitoring
- **Grafana** - Dashboard visualization for system metrics
- **psutil 5.9.0+** - System resource monitoring
- **Custom Analytics Engine** - Built-in performance tracking

### Development & Quality Tools
- **Black 23.0+** - Code formatting
- **Flake8 6.0+** - Code quality and linting
- **MyPy 1.5+** - Static type checking with strict mode
- **Pytest 8.4.1+** - Testing framework with async support
- **Pre-commit 3.4.0+** - Git hooks for code quality
- **Ruff** - Fast Python linter
- **Make** - Task automation and build orchestration

### AI/ML Technologies
- **Sentence Transformers 2.2.0+** - Text embeddings for RAG
- **pgvector 0.2.0+** - Vector similarity search in PostgreSQL
- **Pandas 2.0.0+** - Data manipulation for knowledge base
- **NumPy 1.24.0+** - Numerical computations

### Security & Infrastructure
- **NGINX** - Reverse proxy with SSL termination
- **Docker 24.0+** - Containerization
- **Docker Compose 2.0+** - Multi-container orchestration
- **GitHub Actions** - CI/CD pipeline with security scanning

## Complete Project Structure

```
genie-agents/
├── README.md                           # Enterprise Multi-Agent System overview
├── CLAUDE.md                           # Master AI context and development guidelines
├── MCP-ASSISTANT-RULES.md              # Coding standards for Gemini consultation
├── Makefile                            # Task automation (setup, test, deploy)
├── pyproject.toml                      # Python project configuration with UV
├── uv.lock                             # Dependency lock file
├── docker-compose.yml                  # Development environment orchestration
├── docker-compose.full.yml             # Production deployment with monitoring
├── Dockerfile                          # Container image for production
├── deploy.sh                           # Deployment automation script
├── .claude/                            # Claude Code configuration
│   ├── commands/                       # Custom AI commands
│   │   ├── code-review.md              # Automated code review
│   │   ├── create-docs.md              # Documentation generation
│   │   └── gemini-consult.md           # Gemini consultation integration
│   └── hooks/                          # Event-driven automation
│       ├── gemini-context-injector.sh  # Auto-inject context for Gemini
│       ├── subagent-context-injector.sh# Context for spawned agents
│       └── config/                     
│           └── sensitive-patterns.json # Security pattern detection
├── agents/                             # CORE: Agent definitions and factories
│   ├── CLAUDE.md                       # Agent development patterns
│   ├── registry.py                     # Central agent registry and factory
│   ├── version_factory.py              # Agent versioning system
│   ├── settings.py                     # Agent configuration schemas
│   ├── tools/                          # Shared agent tools
│   │   └── agent_tools.py              # Common tool implementations
│   ├── adquirencia/                    # Acquiring specialist agent
│   │   ├── agent.py                    # Factory: create_adquirencia_agent()
│   │   └── config.yaml                 # YAML configuration
│   ├── emissao/                        # Emission specialist agent
│   │   ├── agent.py                    # Factory: create_emissao_agent()
│   │   └── config.yaml                 # YAML configuration
│   ├── pagbank/                        # PagBank domain agent
│   │   ├── agent.py                    # Factory: create_pagbank_agent()
│   │   └── config.yaml                 # YAML configuration
│   ├── human_handoff/                  # Escalation to human support
│   │   ├── agent.py                    # Factory: create_human_handoff_agent()
│   │   └── config.yaml                 # YAML configuration
│   └── whatsapp_notifier/              # WhatsApp notification agent
│       ├── agent.py                    # Factory: create_whatsapp_agent()
│       ├── config.yaml                 # YAML configuration
│       └── README.md                   # Integration guide
├── teams/                              # CORE: Team orchestration with Agno
│   ├── CLAUDE.md                       # Team routing patterns
│   └── ana/                            # Main routing team
│       ├── team.py                     # Team(mode="route") implementation
│       ├── config.yaml                 # Routing logic configuration
│       └── demo_logging.py             # Example implementation
├── api/                                # FastAPI web interface
│   ├── CLAUDE.md                       # API development guidelines
│   ├── main.py                         # FastAPI application entry
│   ├── serve.py                        # Uvicorn server launcher
│   ├── settings.py                     # API configuration
│   ├── routes/                         # API endpoints
│   │   ├── v1_router.py                # Main API router
│   │   ├── health.py                   # Health check endpoints
│   │   ├── agent_versions.py           # Agent version management
│   │   └── monitoring.py               # Metrics endpoints
│   └── monitoring/                     # Real-time monitoring system
│       ├── metrics_collector.py        # Performance metrics
│       ├── analytics_engine.py         # Usage analytics
│       ├── alert_manager.py            # Alert configuration
│       ├── system_monitor.py           # Resource monitoring
│       └── dashboard.html              # Web dashboard
├── context/                            # Knowledge and memory systems
│   ├── knowledge/                      # RAG knowledge base
│   │   ├── csv_knowledge_base.py       # Core knowledge retrieval
│   │   ├── knowledge_rag.csv           # Domain knowledge data
│   │   ├── csv_hot_reload.py           # Hot reload capability
│   │   ├── agentic_filters.py          # Agent-specific filtering
│   │   ├── enhanced_csv_reader.py      # Advanced CSV parsing
│   │   └── smart_incremental_loader.py # Incremental updates
│   └── memory/                         # Conversation memory
│       ├── memory_manager.py           # Session memory handling
│       ├── memory_config.py            # Memory configuration
│       └── pattern_detector.py         # Conversation patterns
├── workflows/                          # Complex multi-step workflows
│   ├── CLAUDE.md                       # Workflow patterns
│   ├── human_handoff/                  # Human escalation workflow
│   │   ├── workflow.py                 # Handoff orchestration
│   │   ├── models.py                   # Data models
│   │   └── config.yaml                 # Workflow configuration
│   └── conversation_typification/      # Conversation classification
│       ├── workflow.py                 # Classification pipeline
│       ├── hierarchy.json              # Category hierarchy
│       ├── models.py                   # Type models
│       └── README.md                   # Integration guide
├── db/                                 # Database layer
│   ├── CLAUDE.md                       # Database patterns
│   ├── alembic.ini                     # Migration configuration
│   ├── session.py                      # Database sessions
│   ├── settings.py                     # DB configuration
│   ├── migrations/                     # Schema migrations
│   │   ├── env.py                      # Alembic environment
│   │   └── versions/                   # Migration scripts
│   │       └── 001_create_agent_versions.py
│   ├── services/                       # Database services
│   │   └── agent_version_service.py    # Version management
│   └── tables/                         # SQLAlchemy models
│       ├── base.py                     # Base model class
│       └── agent_versions.py           # Agent version tracking
├── config/                             # Application configuration
│   ├── CLAUDE.md                       # Configuration patterns
│   ├── database.py                     # Database config
│   ├── postgres_config.py              # PostgreSQL settings
│   ├── models.py                       # Config models
│   └── settings.py                     # Global settings
├── utils/                              # Shared utilities
│   ├── log.py                          # Logging configuration
│   ├── dttm.py                         # Date/time utilities
│   ├── formatters.py                   # Output formatting
│   └── team_utils.py                   # Team helper functions
├── tests/                              # Comprehensive test suite
│   ├── CLAUDE.md                       # Testing guidelines
│   ├── conftest.py                     # Pytest configuration
│   ├── unit/                           # Unit tests
│   │   ├── test_agent_versioning.py    # Version system tests
│   │   ├── test_knowledge_base.py      # Knowledge tests
│   │   └── test_knowledge_validation.py# Validation tests
│   ├── integration/                    # Integration tests
│   │   ├── test_infrastructure.py      # System tests
│   │   └── test_knowledge_retrieval.py # RAG tests
│   ├── monitoring/                     # Monitoring tests
│   │   └── test_monitoring_integration.py
│   └── workflows/                      # Workflow tests
│       └── test_typification.py        # Classification tests
├── scripts/                            # Automation scripts
│   ├── _utils.sh                       # Shared utilities
│   ├── dev_setup.sh                    # Development setup
│   ├── run-development.sh              # Dev environment
│   ├── run-production.sh               # Production runner
│   └── test_*_logging.py               # Test scripts
├── monitoring/                         # Observability configuration
│   ├── prometheus.yml                  # Prometheus config
│   └── grafana/                        # Grafana dashboards
│       ├── dashboards/                 # Dashboard definitions
│       └── datasources/                # Data sources
├── docs/                               # Project documentation
│   ├── ai-context/                     # AI-specific docs
│   │   ├── project-structure.md        # This file
│   │   ├── docs-overview.md            # Documentation map
│   │   ├── system-integration.md       # Integration guide
│   │   ├── deployment-infrastructure.md# Deployment docs
│   │   └── handoff.md                  # Task handoff guide
│   └── specs/                          # Feature specifications
└── data/                               # Application data
    ├── pagbank.db                      # Agent database
    └── automagik.db                    # System database
```


## Key Development Patterns

### Agent Development Pattern
1. Create agent directory under `agents/`
2. Define `config.yaml` with agent configuration
3. Implement factory function in `agent.py`
4. Register in `agents/registry.py`
5. Add to team routing configuration

### Team Routing with Agno
```python
# teams/ana/team.py
team = Team(
    mode="route",  # Intelligent routing mode
    agents=[agent1, agent2, agent3],
    routing_logic=config.routing_instructions
)
```

### Knowledge Integration
- CSV-based knowledge in `context/knowledge/knowledge_rag.csv`
- Hot reload capability for real-time updates
- Agent-specific filtering via business unit tags

### Session Management
- PostgreSQL for persistent session storage
- Redis for active session caching
- Pattern detection for conversation insights

---

*This document represents the complete Genie Agents project structure. The system is designed for enterprise-grade multi-agent development with Agno at its core.*