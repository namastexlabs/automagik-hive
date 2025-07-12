# PagBank Multi-Agent System - Project Structure

This document provides the complete technology stack and file tree structure for the PagBank Multi-Agent System. **AI agents MUST read this file to understand the project organization before making any changes.**

## Technology Stack

### Backend Technologies
- **Python 3.11+** with **UV** - Modern Python dependency management and packaging
- **Agno Framework** - Multi-agent orchestration framework with built-in memory, routing, and persistence
- **FastAPI** - Web framework with type hints and async support for API endpoints
- **Uvicorn** - ASGI server for production deployment
- **Pydantic** - Data validation and settings management with type safety

### Database & Storage
- **PostgreSQL** - Primary database for production environments with full ACID compliance
- **SQLite** - Automatic fallback database for development and testing environments
- **Agno Built-in Storage** - Session management, conversation memory, and pattern persistence
- **CSV Knowledge Base** - Hot-reloadable knowledge system with RAG capabilities

### AI & Multi-Agent Infrastructure
- **Agno Orchestrator** - Main routing logic and agent coordination
- **Specialist Agents** - Business unit specific agents (Adquirência, Emissão, PagBank, Human Handoff)
- **Claude AI Integration** - Primary LLM for all agent interactions
- **Memory Management** - Session persistence, pattern detection, and context preservation
- **Knowledge RAG System** - CSV-based retrieval augmented generation

### Development & Quality Tools
- **UV** - Python package manager and virtual environment management
- **Pytest** - Comprehensive testing framework with coverage reporting
- **Ruff** - Fast Python linter and formatter (configured via pyproject.toml)
- **Pre-commit Hooks** - Automated code quality checks and formatting
- **Type Hints** - Full mypy-compatible type annotations throughout codebase

### Integration Services & APIs
- **WhatsApp Business API** - Customer communication channel via Evolution API
- **MCP (Model Context Protocol)** - AI agent communication and tool integration
- **PostgreSQL Connection Pooling** - Managed by Agno framework for optimal performance
- **Hot Reload Systems** - Real-time knowledge base updates without restart

### Development Workflow
- **Genie Framework** - Multi-agent development orchestration system
- **Pattern-Based Development** - Reusable patterns stored in `genie/reference/`
- **Parallel Agent Development** - Coordinated changes across multiple specialist agents
- **Task Management** - Active development tracking in `genie/active/`

## Complete Project Structure

```
pagbank-multiagents/
├── README.md                           # Project overview and setup instructions
├── CLAUDE.md                           # Master AI context and development guidelines
├── pyproject.toml                      # UV package configuration and dependencies
├── uv.lock                             # Locked dependency versions
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore patterns
├── agents/                             # Multi-agent system core
│   ├── CLAUDE.md                       # Agent-specific development context
│   ├── __init__.py                     # Package initialization
│   ├── orchestrator/                   # Main routing and coordination logic
│   │   ├── __init__.py
│   │   ├── main_orchestrator.py        # Central agent coordinator
│   │   ├── routing_logic.py            # Business unit routing algorithms
│   │   ├── human_handoff_detector.py   # Frustration detection and escalation
│   │   ├── clarification_handler.py    # Query clarification logic
│   │   ├── response_models.py          # Pydantic response schemas
│   │   └── state_synchronizer.py       # Agent state management
│   ├── specialists/                    # Business unit specific agents
│   │   ├── __init__.py
│   │   ├── base_agent.py               # Abstract base class for all specialists
│   │   ├── adquirencia_agent.py        # Merchant services agent
│   │   ├── emissao_agent.py            # Card issuance agent
│   │   ├── pagbank_agent.py            # Digital banking agent
│   │   └── human_handoff_agent.py      # Human escalation agent
│   ├── prompts/                        # Centralized prompt management
│   │   ├── __init__.py
│   │   ├── prompt_manager.py           # Dynamic prompt loading and management
│   │   ├── specialist_prompts.py       # Specialist agent prompts
│   │   ├── base/                       # Core system prompts
│   │   │   ├── __init__.py
│   │   │   ├── system_prompts.py       # Base system instructions
│   │   │   ├── response_templates.py   # Response formatting templates
│   │   │   └── error_prompts.py        # Error handling prompts
│   │   ├── orchestrator/               # Orchestrator specific prompts
│   │   │   ├── __init__.py
│   │   │   ├── routing_prompts.py      # Routing decision prompts
│   │   │   └── clarification_prompts.py # Query clarification prompts
│   │   ├── specialists/                # Business unit specific prompts
│   │   │   ├── __init__.py
│   │   │   ├── adquirencia_prompts.py  # Merchant services prompts
│   │   │   ├── emissao_prompts.py      # Card issuance prompts
│   │   │   ├── pagbank_prompts.py      # Digital banking prompts
│   │   │   └── human_handoff_prompts.py # Escalation prompts
│   │   └── escalation/                 # Escalation specific prompts
│   │       ├── __init__.py
│   │       └── human_escalation_prompts.py # Human handoff templates
│   ├── tools/                          # Shared agent tools and utilities
│   │   ├── __init__.py
│   │   └── agent_tools.py              # Common tools across all agents
│   ├── adquirencia/                    # Merchant services configuration
│   │   ├── agent.py                    # Agent implementation
│   │   └── config.yaml                 # Business unit configuration
│   ├── emissao/                        # Card issuance configuration
│   │   ├── agent.py                    # Agent implementation
│   │   └── config.yaml                 # Business unit configuration
│   └── pagbank/                        # Digital banking configuration
│       ├── agent.py                    # Agent implementation
│       └── config.yaml                 # Business unit configuration
├── teams/                              # Agno teams integration
│   └── CLAUDE.md                       # Teams-specific development context
├── workflows/                          # Agno workflows integration
│   ├── CLAUDE.md                       # Workflows-specific development context
│   └── human_handoff.py                # Human escalation workflow
├── api/                                # FastAPI application layer
│   ├── CLAUDE.md                       # API-specific development context
│   ├── playground.py                   # Agno Playground interface (port 7777)
│   └── serve.py                        # Production API server
├── config/                             # System configuration management
│   ├── CLAUDE.md                       # Configuration-specific context
│   ├── __init__.py
│   ├── settings.py                     # Application settings via Pydantic
│   ├── models.py                       # Configuration data models
│   ├── database.py                     # Database connection configuration
│   ├── postgres_config.py              # PostgreSQL specific configuration
│   ├── sample-agent-complete.yaml      # Example agent configuration
│   ├── environments/                   # Environment-specific configs
│   │   └── CLAUDE.md                   # Environment configuration context
│   └── models/                         # Configuration model definitions
│       └── CLAUDE.md                   # Model-specific context
├── context/                            # Knowledge and memory management
│   ├── knowledge/                      # Knowledge base system
│   │   ├── __init__.py
│   │   ├── csv_knowledge_base.py       # Main CSV knowledge interface
│   │   ├── knowledge_rag.csv           # Hot-reloadable knowledge data
│   │   ├── enhanced_csv_reader.py      # Advanced CSV parsing with filtering
│   │   ├── agentic_filters.py          # Business unit specific filtering
│   │   ├── csv_hot_reload.py           # Real-time knowledge updates
│   │   ├── hot_reload_manager.py       # File system monitoring
│   │   ├── smart_incremental_loader.py # Efficient knowledge loading
│   │   ├── knowledge_parser.py         # Knowledge data processing
│   │   └── simple_example.py           # Knowledge system examples
│   ├── memory/                         # Session and pattern management
│   │   ├── __init__.py
│   │   ├── memory_manager.py           # Main memory interface
│   │   ├── session_manager.py          # Session persistence
│   │   ├── pattern_detector.py         # Conversation pattern analysis
│   │   └── memory_config.py            # Memory system configuration
│   └── storage/                        # Data storage abstractions
├── db/                                 # Database infrastructure
│   └── CLAUDE.md                       # Database-specific development context
├── data/                               # Database files and data storage
│   ├── README.md                       # Data directory documentation
│   ├── ana_memory.db                   # SQLite memory database
│   └── pagbank.db                      # SQLite main database
├── tests/                              # Comprehensive test suite
│   ├── CLAUDE.md                       # Testing-specific development context
│   ├── __init__.py
│   ├── conftest.py                     # Pytest configuration and fixtures
│   ├── unit/                           # Unit tests for individual components
│   │   ├── __init__.py
│   │   ├── test_business_unit_agents.py # Agent-specific unit tests
│   │   ├── test_knowledge_base.py      # Knowledge system tests
│   │   ├── test_knowledge_validation.py # Knowledge validation tests
│   │   ├── test_routing_logic.py       # Routing algorithm tests
│   │   ├── test_routing_logic_simple.py # Simplified routing tests
│   │   ├── application/                # Application layer tests
│   │   └── domain/                     # Domain logic tests
│   ├── integration/                    # Integration tests across components
│   │   ├── __init__.py
│   │   ├── test_end_to_end_flow.py     # Full conversation flow tests
│   │   ├── test_hybrid_unit_routing.py # Cross-unit routing tests
│   │   ├── test_infrastructure.py      # Infrastructure integration tests
│   │   └── test_knowledge_retrieval.py # Knowledge system integration
│   ├── performance/                    # Performance benchmarking
│   │   └── test_baseline_metrics.py    # Performance baseline tests
│   ├── test_mcp_integration.py         # MCP protocol integration tests
│   ├── test_memory_manager.py          # Memory system tests
│   ├── test_orchestrator.py            # Orchestrator tests
│   └── test_session_manager.py         # Session management tests
├── scripts/                            # Automation and utility scripts
│   ├── preprocessing/                  # Knowledge base preprocessing
│   │   ├── README.md                   # Preprocessing documentation
│   │   ├── generate_rag_csv.py         # RAG CSV generation
│   │   └── validate_knowledge.py       # Knowledge validation
│   ├── set_evolution_env.py            # WhatsApp environment setup
│   ├── start_with_whatsapp.py          # WhatsApp integration startup
│   └── update_imports.py               # Import path maintenance
├── docs/                               # Project documentation
│   ├── ARCHITECTURE_DETAILED.md        # Detailed system architecture
│   ├── DEMO_SCRIPT.md                  # System demonstration guide
│   ├── DEMO_SCRIPT_PRIORITY.md         # Priority demo scenarios
│   ├── DEVELOPMENT_GUIDELINES.md       # Development best practices
│   ├── MCP_CONFIG_EXAMPLE.md           # MCP configuration examples
│   ├── MCP_INTEGRATION_GUIDE.md        # MCP integration documentation
│   ├── SPECIALIST_TEAMS_INTEGRATION.md # Teams integration guide
│   └── knowledge_examples/             # Knowledge base examples
│       ├── antecipacao.md              # Sales anticipation examples
│       ├── cartoes.md                  # Card services examples
│       └── conta.md                    # Account management examples
├── genie/                              # Development orchestration system
│   ├── CLAUDE.md                       # Genie framework context
│   ├── ai-context/                     # AI-specific development context
│   │   └── project-structure.md        # This file
│   ├── active/                         # Current development tasks (MAX 5 files)
│   │   ├── ccdk-commands-evaluation.md # CCDK command evaluation
│   │   ├── ccdk-documentation-evaluation.md # Documentation analysis
│   │   ├── ccdk-hooks-evaluation.md    # Git hooks evaluation
│   │   ├── epic-status.md              # Epic progress tracking
│   │   └── genie-framework-ccdk-enhancement.md # Framework enhancement
│   ├── reference/                      # Reusable development patterns
│   │   ├── csv_typification_analysis.md # CSV analysis patterns
│   │   └── typification_hierarchy_analysis.md # Hierarchy patterns
│   ├── archive/                        # Completed development tasks
│   │   ├── README.md                   # Archive documentation
│   │   ├── 2025-01-12-platform-strategy.md # Completed strategy
│   │   ├── agent-coordination.md       # Agent coordination patterns
│   │   ├── agno-parameter-investigation.md # Agno research
│   │   └── scripts/                    # Archive maintenance scripts
│   ├── todo/                           # Future development planning
│   │   └── pagbank-v2*.md              # V2 transformation planning
│   ├── Claude-Code-Development-Kit/    # CCDK integration
│   │   ├── README.md                   # CCDK documentation
│   │   ├── docs/                       # CCDK documentation
│   │   ├── commands/                   # CCDK commands
│   │   └── hooks/                      # Git hooks and automation
│   └── agno-demo-app/                  # Agno framework reference
│       ├── agents/                     # Reference agent implementations
│       ├── teams/                      # Reference team implementations
│       ├── workflows/                  # Reference workflow implementations
│       └── api/                        # Reference API implementations
├── utils/                              # Shared utility functions
│   ├── __init__.py
│   ├── formatters.py                   # Data formatting utilities
│   └── team_utils.py                   # Team management utilities
├── logs/                               # Application logging directory
├── schema/                             # Database schema definitions
└── pagbank.egg-info/                   # Package metadata (auto-generated)
    ├── PKG-INFO                        # Package information
    ├── SOURCES.txt                     # Source file listing
    ├── dependency_links.txt            # Dependency links
    ├── requires.txt                    # Requirements listing
    └── top_level.txt                   # Top-level modules
```

## Key Development Patterns

### Multi-Agent Architecture
- **Orchestrator Pattern**: Central routing via `agents/orchestrator/main_orchestrator.py`
- **Specialist Pattern**: Business unit agents in `agents/specialists/`
- **Tool Sharing**: Common tools in `agents/tools/` shared across all agents
- **Prompt Management**: Centralized prompts in `agents/prompts/` with business unit specialization

### Knowledge Management
- **Hot Reload System**: Real-time CSV updates via `context/knowledge/csv_hot_reload.py`
- **RAG Integration**: Retrieval augmented generation via `context/knowledge/knowledge_rag.csv`
- **Business Unit Filtering**: Contextual knowledge via `context/knowledge/agentic_filters.py`
- **Memory Persistence**: Session management via `context/memory/session_manager.py`

### Development Workflow
- **Genie Framework**: Task orchestration in `genie/active/` (maximum 5 active files)
- **Pattern Reuse**: Successful patterns stored in `genie/reference/`
- **Archive System**: Completed work moved to `genie/archive/` with date prefixes
- **CCDK Integration**: Development kit in `genie/Claude-Code-Development-Kit/`

### Testing Strategy
- **Unit Tests**: Component isolation in `tests/unit/`
- **Integration Tests**: Cross-component testing in `tests/integration/`
- **Performance Tests**: Baseline metrics in `tests/performance/`
- **End-to-End Tests**: Full conversation flows testing all agents

### Configuration Management
- **Environment Variables**: Configured via `.env` files with `PB_AGENTS_` prefix
- **Database Configuration**: Automatic PostgreSQL/SQLite fallback via Agno
- **Agent Configuration**: YAML-based configuration per business unit
- **Settings Management**: Pydantic-based validation in `config/settings.py`

---

*This document provides the complete technical foundation for the PagBank Multi-Agent System. All AI agents must reference this structure before making changes to ensure consistency with the established architecture and development patterns.*