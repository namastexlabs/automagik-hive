# MCP Assistant Rules - Genie Agents

## Project Context
Enterprise-grade multi-agent system built on Agno Framework for intelligent conversation routing, knowledge management, and workflow orchestration. Production-ready with comprehensive monitoring, security layers, and seamless agent development patterns.

### Core Vision & Architecture
- **Product Goal**: Provide a scalable, extensible platform for building sophisticated AI agent systems with enterprise features
- **Target Platform**: Cloud-native web services, Docker containerized, with API-first design
- **Architecture**: Clean V2 Architecture with YAML-driven agent configuration, Agno Team routing, PostgreSQL backend
- **Key Technologies**: Agno Framework (central orchestration), FastAPI (web layer), PostgreSQL (data), Redis (sessions), Prometheus/Grafana (monitoring)

### Key Technical Principles
- **Agno-First Development**: Leverage Agno's Team(mode="route") for all agent orchestration and routing decisions
- **YAML-Driven Configuration**: Declarative agent definitions with hot reload for rapid iteration
- **Factory Pattern Everything**: Dynamic agent instantiation with version management and A/B testing support
- **Observable by Design**: Every interaction tracked with correlation IDs, metrics, and structured logging
- **Security at Boundaries**: Input validation, session isolation, and sanitized outputs at all system edges
- **Knowledge-Aware Agents**: CSV-based RAG system with agent-specific filtering for contextual responses

**Note:** The complete project structure and technology stack are provided in the attached `project-structure.md` file.

## Key Project Standards

### Core Principles
- **Agno Patterns First**: Always check Agno documentation for established patterns before custom implementations
- **Factory-Based Agents**: Every agent must have a factory function following the `get_[name]_agent()` pattern
- **YAML Configuration**: Agent behavior defined in `config.yaml`, code handles orchestration only
- **Test Everything**: Unit tests for agents, integration tests for teams, workflow tests for complex flows
- **Observable Agents**: Every agent interaction must emit metrics and structured logs
- **Fail Gracefully**: Agents should degrade functionality rather than crash on errors

### Configuration Management Rules
- **Never Hardcode Values**: Use environment variables (.env), YAML config files, or Pydantic Settings classes
- **Environment Variable Naming**: Use SCREAMING_SNAKE_CASE with descriptive prefixes (e.g., `ANTHROPIC_API_KEY`, `DATABASE_URL`)
- **Configuration Classes**: Use Pydantic BaseSettings for type-safe configuration with validation
- **Config File Organization**: YAML for agent configs, JSON for complex nested data, .env for secrets
- **Database Connections**: Always use connection pooling with proper pool sizing and recycling
- **Hierarchical Config**: Support environment-specific overrides (development/production)

### Configuration Patterns
```python
# Use Pydantic BaseSettings for type-safe configuration
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(20, env="DB_POOL_SIZE")
    max_overflow: int = Field(30, env="DB_MAX_OVERFLOW")
    pool_recycle: int = Field(3600, env="DB_POOL_RECYCLE")

# Load from .env automatically
db_settings = DatabaseSettings()
```

### Database Connection Patterns
```python
# Use connection pooling with proper configuration
db_engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    echo=False  # Only True for debugging
)

# Use context managers for sessions
with DatabaseSession() as session:
    result = session.query(Model).all()
```

### Code Organization
- **Agent Modules**: Each agent in its own directory with `agent.py`, `config.yaml`, and optional `README.md`
- **Keep Files Focused**: Max 300 lines per file - split utilities, models, and handlers
- **Factory Registration**: All agents registered in `agents/registry.py` for dynamic discovery
- **Shared Tools**: Common functionality in `agents/tools/` to avoid duplication
- **Team Organization**: Teams in `teams/` directory, each with routing configuration

### Python Standards
- **Type Everything**: Full type hints with Pydantic models for all data structures
- **Async First**: Use async/await for all I/O operations and agent interactions
- **Factory Functions**: `get_[name]_agent() -> Agent` pattern for all agents
- **Google Docstrings**: Every public function documented with Args, Returns, Raises
- **Error Context**: Include session_id, agent_id in all error messages and logs
- **Import Organization**: Group imports logically (standard library, third-party, local)
- **Path Handling**: Use pathlib.Path for all file operations
- **Optional Parameters**: Use Optional[T] instead of Union[T, None]
- **Exception Handling**: Use specific exceptions, log with context, never expose internals
- **Context Managers**: Use context managers for resource management (DB sessions, file handles)

### Type Hints & Documentation Standards
```python
# Required type hints for all functions
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path

def get_agent_config(
    agent_name: str,
    config_path: Optional[Path] = None,
    version: Optional[int] = None
) -> Dict[str, Any]:
    """Load agent configuration from YAML file.
    
    Args:
        agent_name: Name of the agent to load config for
        config_path: Optional path to config file (defaults to agent directory)
        version: Optional specific version to load
        
    Returns:
        Dictionary containing agent configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if config_path is None:
        config_path = Path(f"agents/{agent_name}/config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return config
```

### Current Pydantic Model Patterns
```python
# Use Pydantic BaseSettings for configuration
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class ApiSettings(BaseSettings):
    """API settings with environment variable support."""
    
    title: str = "PagBank Multi-Agent System"
    version: str = "2.0"
    environment: str = "development"
    docs_enabled: bool = True
    cors_origin_list: Optional[List[str]] = Field(None, validate_default=True)
    
    @field_validator("environment")
    def validate_environment(cls, environment: str) -> str:
        """Validate environment value."""
        valid_environments = ["development", "production"]
        if environment not in valid_environments:
            raise ValueError(f"Invalid environment: {environment}")
        return environment
    
    @field_validator("cors_origin_list", mode="before")
    def set_cors_origin_list(cls, cors_origin_list, info):
        """Set CORS origins based on environment."""
        environment = info.data.get("environment")
        
        if environment == "development":
            return ["http://localhost:3000", "http://localhost:8000", "*"]
        elif environment == "production":
            return ["https://app.pagbank.com.br", "https://pagbank.com.br"]
        
        return cors_origin_list or []
```

### File Organization & Modularity Standards
- **File Size Limit**: Keep files under 350 lines when possible
- **Single Responsibility**: Each file should have one clear purpose
- **Separation of Concerns**: Separate utilities, constants, types, and business logic
- **Import Organization**: Standard library → Third-party → Local imports
- **Directory Structure**: Follow established patterns in project structure

### Current File Organization Pattern
```python
# agents/pagbank/agent.py - Agent factory
from typing import Optional
import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agents.tools.agent_tools import get_agent_tools

# Keep business logic in separate modules
from .tools import create_knowledge_search_tool
from .config import load_agent_config
from .validators import validate_agent_params

def get_pagbank_agent(
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None
) -> Agent:
    """Factory function for PagBank agent."""
    config = load_agent_config()
    tools = create_knowledge_search_tool("PagBank", config)
    
    return Agent(
        agent_id=config["agent"]["agent_id"],
        name=config["agent"]["name"],
        role=config["agent"]["role"],
        instructions=config["instructions"],
        tools=tools,
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url or os.getenv("DATABASE_URL"),
            auto_upgrade_schema=True
        ),
        session_id=session_id,
        debug_mode=debug_mode
    )
```

### Environment Variable Naming Conventions
```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600

# API configuration
API_HOST=localhost
API_PORT=8000
API_WORKERS=1
ENVIRONMENT=development

# Agent configuration
ANTHROPIC_API_KEY=sk-ant-...
MAX_CONVERSATION_TURNS=20
SESSION_TIMEOUT=1800

# Knowledge base
CSV_HOT_RELOAD=true
KNOWLEDGE_UPDATE_INTERVAL=3600

# Monitoring
ENABLE_METRICS=true
METRICS_INTERVAL=60

# Alert configuration
RESEND_API_KEY=re_...
EMAIL_RECIPIENT=admin@company.com
```

### Error Handling & Logging Standards
- **Agent Exceptions**: Custom exceptions like `AgentNotFoundError`, `RoutingError`, `KnowledgeRetrievalError`
- **Structured Logs**: JSON format with fields: timestamp, level, correlation_id, agent_id, session_id, event, context
- **Log Categories**: `agent.routing`, `agent.execution`, `knowledge.retrieval`, `session.management`
- **Correlation IDs**: UUID4 format, passed through entire request lifecycle
- **Rich Logging**: Use RichHandler for development with structured output
- **Alert Integration**: Critical errors trigger alert manager notifications

### Current Logging Pattern
```python
# Use Rich logging for development
from rich.logging import RichHandler

def get_logger(logger_name: str) -> logging.Logger:
    rich_handler = RichHandler(
        show_time=False,
        rich_tracebacks=False,
        show_path=True,
        tracebacks_show_locals=False
    )
    rich_handler.setFormatter(
        logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]"
        )
    )
    
    logger = logging.getLogger(logger_name)
    logger.addHandler(rich_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger
```

### Alert Management Integration
```python
# Critical errors trigger alerts
from api.monitoring.alert_manager import alert_manager

try:
    result = risky_operation()
except CriticalError as e:
    logger.error(f"Critical error: {e}", extra={
        "correlation_id": session_id,
        "error_type": type(e).__name__,
        "context": {"operation": "risky_operation"}
    })
    # Alert manager will evaluate and send notifications
    await alert_manager.evaluate_alerts({
        "services": {
            "agent_service": {
                "status": "down",
                "message": str(e)
            }
        }
    })
```

### API Design Patterns
- **Versioned Endpoints**: `/api/v1/` prefix for all endpoints
- **Consistent Responses**: `{"data": {...}, "error": null, "metadata": {...}}`
- **Router Organization**: Separate routers for health, monitoring, agent versions
- **Health Checks**: `/health` (basic), `/health/detailed` (with dependencies)
- **OpenAPI Docs**: Auto-generated at `/docs` and `/redoc`
- **CORS Configuration**: Environment-specific CORS with Pydantic validation

### Current API Structure
```python
# Main router composition
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_check_router)
v1_router.include_router(agent_versions_router) 
v1_router.include_router(monitoring_router)

# CORS configuration with environment awareness
class ApiSettings(BaseSettings):
    environment: str = "development"
    cors_origin_list: Optional[List[str]] = Field(None, validate_default=True)
    
    @field_validator("cors_origin_list", mode="before")
    def set_cors_origin_list(cls, cors_origin_list, info: FieldValidationInfo):
        environment = info.data.get("environment")
        
        if environment == "development":
            return ["http://localhost:3000", "http://localhost:8000", "*"]
        elif environment == "production":
            return ["https://app.pagbank.com.br", "https://pagbank.com.br"]
        
        return cors_origin_list or []
```

### Database Session Management
```python
# FastAPI dependency injection pattern
def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for manual session handling
class DatabaseSession:
    def __enter__(self):
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
```

### Security & State Management
- **Input Validation**: Pydantic models for all API inputs, sanitize at boundaries
- **Session Management**: PostgreSQL for persistence, Redis for active sessions
- **Secret Management**: Environment variables only, never in code or configs
- **Agent Isolation**: Each agent runs in isolated context with limited permissions
- **Audit Trail**: All agent decisions logged with reasoning and context
- **Connection Security**: Use connection pooling with pre-ping and recycling
- **Database Extensions**: Auto-initialize pgvector for semantic search

### Current Security Patterns
```python
# Environment-based secret management
class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    
    def get_db_url(self) -> str:
        """Get database URL with connection parameters."""
        return self.url

# Input validation with Pydantic
class AgentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=50)
    session_id: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9-_]+$')
    message: str = Field(..., min_length=1, max_length=4000)
    
    @field_validator('message')
    def sanitize_message(cls, v):
        # Sanitize user input
        return v.strip()
```

### Authentication & Authorization Patterns
```python
# Session-based authentication
class SessionManager:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def validate_session(self, session_id: str) -> bool:
        """Validate session exists and is active."""
        try:
            session = self.db.query(Session).filter_by(id=session_id).first()
            return session is not None and session.is_active
        except Exception:
            return False
```

## Project-Specific Guidelines

### Agent Development Workflow
1. Define use case and routing logic
2. Create agent directory structure: `agents/[name]/`
3. Write `config.yaml` with instructions, model settings, and business logic
4. Implement factory function `get_[name]_agent()` with Agno Agent creation
5. Register in `agents/registry.py` with dynamic import mapping
6. Add to team configuration for routing in `teams/ana/config.yaml`
7. Write unit and integration tests
8. Update knowledge base if domain-specific

### Current Agent Factory Pattern
```python
# Every agent follows this exact pattern
def get_[name]_agent(
    version: Optional[int] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db_url: Optional[str] = None
) -> Agent:
    """Factory function for [Name] agent with versioning support."""
    
    # Load YAML configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Create agent with PostgreSQL storage
    return Agent(
        agent_id=config["agent"]["agent_id"],
        name=config["agent"]["name"],
        role=config["agent"]["role"],
        instructions=config["instructions"],
        model=Claude(
            id=config["model"]["id"],
            temperature=config["model"]["temperature"],
            max_tokens=config["model"]["max_tokens"]
        ),
        tools=create_agent_tools(config),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url or os.getenv("DATABASE_URL"),
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"]
        ),
        session_id=session_id,
        debug_mode=debug_mode
    )
```

### Agno Integration Patterns
- **Team Routing**: Use `Team(mode="route")` for intelligent agent selection
- **Session Context**: Pass `session_id` to maintain conversation continuity
- **Tool Usage**: Leverage Agno's built-in tools before creating custom ones
- **Memory Patterns**: Use Agno's memory features for context retention
- **PostgreSQL Storage**: All agents use PostgresStorage with auto-upgrade schemas
- **Generic Agent Registry**: Dynamic agent loading through `_agent_modules` mapping

### Current Team Factory Pattern
```python
# Ana team follows this exact pattern
def get_ana_team(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
    agent_names: Optional[list[str]] = None
) -> Team:
    """Ana Team factory with route mode for intelligent agent selection."""
    
    # Load YAML configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Default agent composition
    if agent_names is None:
        agent_names = ["adquirencia", "emissao", "pagbank", "human_handoff"]
    
    # Load agents using registry
    members = [
        get_agent(name, session_id=session_id, debug_mode=debug_mode, db_url=db_url)
        for name in agent_names
    ]
    
    return Team(
        name=config["team"]["name"],
        team_id=config["team"]["team_id"],
        mode="route",  # Key Agno pattern
        members=members,
        instructions=config["instructions"],
        model=Claude(
            id=model_id or config["model"]["id"],
            max_tokens=config["model"]["max_tokens"],
            temperature=config["model"]["temperature"]
        ),
        storage=PostgresStorage(
            table_name=config["storage"]["table_name"],
            db_url=db_url,
            auto_upgrade_schema=config["storage"]["auto_upgrade_schema"]
        ),
        session_id=session_id,
        user_id=user_id,
        debug_mode=debug_mode
    )
```

### Knowledge Base Management
- **CSV Format**: Maintain `knowledge_rag.csv` with columns: id, content, business_unit, tags
- **Hot Reload**: Changes detected automatically via file watcher with `CSV_HOT_RELOAD=true`
- **Agent Filtering**: Use business_unit to scope knowledge per agent
- **Embedding Updates**: Automatic re-embedding on content changes
- **Semantic Search**: pgvector integration for similarity search
- **Configurable Thresholds**: Agent-specific relevance thresholds in YAML

### Current Knowledge Integration Pattern
```python
# Knowledge tool creation for agents
def create_knowledge_search_tool(business_unit: str, config: dict = None) -> Function:
    """Create knowledge search tool configured for specific business unit."""
    
    # Extract config values
    knowledge_config = config.get("knowledge_filter", {})
    max_results = knowledge_config.get("max_results", 5)
    threshold = knowledge_config.get("relevance_threshold", 0.6)
    
    def knowledge_search(query: str, max_results: int = None) -> str:
        """Search knowledge base with business unit filtering."""
        result = search_knowledge_base(
            query=query,
            business_unit=business_unit,
            max_results=max_results or max_results,
            relevance_threshold=threshold
        )
        
        if not result["success"]:
            return f"Erro na busca: {result.get('error', 'Erro desconhecido')}"
        
        return format_knowledge_results(result["results"])
    
    return Function(
        function=knowledge_search,
        name="search_knowledge_base",
        description=f"Busca informações na base de conhecimento para {business_unit}"
    )
```

### Hot Reload Configuration
```yaml
# Agent config.yaml knowledge section
knowledge_filter:
  business_unit: "PagBank"
  max_results: 5
  relevance_threshold: 0.3
  csv_file_path: "context/knowledge/knowledge_rag.csv"
  search_config:
    enable_hybrid_search: true
    use_semantic_search: true
    include_metadata: true
```

### Performance & Monitoring
- **Connection Pooling**: PostgreSQL pools with proper sizing (pool_size=20, max_overflow=30)
- **Async Everything**: Non-blocking I/O for all external calls
- **Metric Collection**: Minimal overhead with Prometheus client
- **Knowledge Caching**: Embeddings cached in pgvector for fast retrieval
- **Session Cleanup**: Automatic cleanup of stale sessions after timeout
- **Alert Management**: Real-time monitoring with configurable thresholds
- **System Monitoring**: CPU, memory, disk usage tracking

### Current Monitoring Integration
```python
# Alert manager with configurable rules
class AlertManager:
    def __init__(self, config_path: str = "logs/alerts"):
        self.alert_rules = {
            "high_memory_usage": AlertRule(
                name="high_memory_usage",
                condition="memory_usage > threshold",
                threshold=85.0,
                severity=AlertSeverity.HIGH,
                message_template="High memory usage: {memory_usage:.1f}%",
                cooldown_minutes=15
            )
        }
        
        # Multiple delivery channels
        self.delivery_handlers = {
            'log': self._deliver_log,
            'email': self._deliver_email,
            'webhook': self._deliver_webhook,
            'whatsapp': self._deliver_whatsapp
        }
    
    async def evaluate_alerts(self, metrics: Dict[str, Any]):
        """Evaluate metrics against alert rules."""
        for rule_name, rule in self.alert_rules.items():
            if self._evaluate_rule_condition(rule, metrics):
                alert = self._create_alert(rule, metrics)
                await self._deliver_alert(alert)
```

### Database Performance Patterns
```python
# Optimized connection configuration
db_engine = create_engine(
    db_url,
    pool_pre_ping=True,      # Test connections before use
    pool_size=20,            # Base connection pool size
    max_overflow=30,         # Additional connections during peaks
    pool_recycle=3600,       # Recycle connections every hour
    echo=False               # SQL debugging (only for development)
)

# PostgreSQL extensions initialization
def init_database():
    """Initialize database with required extensions."""
    if "postgresql" in db_url.lower():
        with db_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
```

## Important Constraints
- You cannot create, modify, or execute code
- You operate in a read-only support capacity
- Your suggestions are for the primary AI (Claude Code) to implement
- Focus on analysis, understanding, and advisory support

## Quick Reference

### Key Commands
- **Development**: `uv run python api/serve.py` - Start development server
- **Testing**: `uv run pytest tests/` - Run test suite
- **Type Check**: `uv run mypy agents/ api/ --strict` - Validate types
- **Linting**: `uv run ruff check .` - Code quality check
- **Database**: `uv run alembic upgrade head` - Apply migrations
- **Hot Reload**: Set `CSV_HOT_RELOAD=true` for knowledge base updates
- **Production**: `make dev` - Start with proper configuration

### Important Paths
- **Agent Definitions**: `agents/*/config.yaml` - YAML configurations
- **Agent Registry**: `agents/registry.py` - Central registration with dynamic imports
- **Team Routing**: `teams/ana/config.yaml` - Routing configuration
- **Knowledge Base**: `context/knowledge/knowledge_rag.csv` - Domain knowledge
- **API Routes**: `api/routes/v1_router.py` - Endpoint definitions
- **Monitoring**: `api/monitoring/alert_manager.py` - Alert management system
- **Database**: `db/session.py` - Connection management with pooling
- **Configuration**: `config/settings.py` - Global settings with environment support
- **Environment**: `.env` - Environment variables for development

### Critical Documentation
- **Agno Docs**: Use `mcp__search-repo-docs` and `mcp__ask-repo-agent` for Agno patterns
- **Agent Patterns**: `agents/CLAUDE.md` - Development guidelines
- **API Patterns**: `api/CLAUDE.md` - API development standards
- **Team Patterns**: `teams/CLAUDE.md` - Routing configuration guide
- **Workflow Patterns**: `workflows/CLAUDE.md` - Complex flow orchestration