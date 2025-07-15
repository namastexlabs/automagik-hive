# Genie Agents - Enterprise Multi-Agent System (claude-master)

## 1. Project Overview
- **Vision:** Production-ready enterprise boilerplate for building sophisticated multi-agent AI systems with intelligent routing, comprehensive monitoring, and enterprise-grade deployment capabilities
- **Current Phase:** Enterprise-ready deployment with full monitoring, security, and CI/CD integration
- **Key Architecture:** Clean V2 Architecture with YAML-driven agent configuration, Agno Framework integration for intelligent routing, PostgreSQL backend with auto-migrations
- **Development Strategy:** Microservices-ready architecture with Docker containerization, real-time monitoring via Prometheus/Grafana, and enterprise security layers

## 2. Project Structure

**⚠️ CRITICAL: AI agents MUST read the [Project Structure documentation](/docs/ai-context/project-structure.md) before attempting any task to understand the complete technology stack, file tree and project organization.**

Genie Agents follows a Clean V2 Architecture pattern with YAML-driven agent configuration and factory patterns. For the complete tech stack and file tree structure, see [docs/ai-context/project-structure.md](/docs/ai-context/project-structure.md).

## 3. Coding Standards & AI Instructions

### General Instructions
- Your most important job is to manage your own context. Always read any relevant files BEFORE planning changes.
- When updating documentation, keep updates concise and on point to prevent bloat.
- Write code following KISS, YAGNI, and DRY principles.
- When in doubt follow proven best practices for implementation.
- Do not commit to git without user approval.
- Do not run any servers, rather tell the user to run servers for testing.
- Always consider industry standard libraries/frameworks first over custom implementations.
- Never mock anything. Never use placeholders. Never omit code.
- Apply SOLID principles where relevant. Use modern framework features rather than reinventing solutions.
- Be brutally honest about whether an idea is good or bad.
- Make side effects explicit and minimal.
- Design database schema to be evolution-friendly (avoid breaking changes).

### Genie Agents Specific Instructions
- **Agent Development**: Always use YAML configuration files for new agents following the V2 architecture pattern
- **Team Routing**: Utilize Agno's Team(mode="route") for intelligent agent selection with confidence scoring
- **Database Operations**: Use SQLAlchemy ORM for all database interactions, raw SQL only for complex queries
- **Monitoring**: Include metrics collection for all new endpoints and agent interactions
- **Security**: All agent responses must be sanitized, never expose internal system details
- **Testing**: Every new agent must have corresponding unit and integration tests
- **Knowledge Base**: Use the CSV-based RAG system with hot reload for context-aware responses
- **Memory Management**: Implement session-based memory with pattern detection for conversation continuity
- **Configuration**: Never hardcode values - always use .env files and YAML configs
- **MCP Integration**: Use available MCP tools for WhatsApp notifications, Gemini consultation, and documentation lookup
- **V2 Architecture**: Follow the V2 pattern with agents, teams, and workflows all configured via YAML
- **Hot Reload**: Leverage CSV hot reload for instant knowledge base updates without server restart


### File Organization & Modularity
- Default to creating multiple small, focused files rather than large monolithic ones
- Each file should have a single responsibility and clear purpose
- Keep files under 350 lines when possible - split larger files by extracting utilities, constants, types, or logical components into separate modules
- Separate concerns: utilities, constants, types, components, and business logic into different files
- Prefer composition over inheritance - use inheritance only for true 'is-a' relationships, favor composition for 'has-a' or behavior mixing

- Follow existing project structure and conventions - place files in appropriate directories. Create new directories and move files if deemed appropriate.
- Use well defined sub-directories to keep things organized and scalable
- Structure projects with clear folder hierarchies and consistent naming conventions
- Import/export properly - design for reusability and maintainability

### Type Hints (REQUIRED)
- **Always** use type hints for function parameters and return values
- Use `from typing import` for complex types
- Prefer `Optional[T]` over `Union[T, None]`
- Use Pydantic models for data structures

```python
# Good
from typing import Optional, List, Dict, Tuple

async def process_audio(
    audio_data: bytes,
    session_id: str,
    language: Optional[str] = None
) -> Tuple[bytes, Dict[str, Any]]:
    """Process audio through the pipeline."""
    pass
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `VoicePipeline`)
- **Functions/Methods**: snake_case (e.g., `process_audio`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_AUDIO_SIZE`)
- **Private methods**: Leading underscore (e.g., `_validate_input`)
- **Pydantic Models**: PascalCase with `Schema` suffix (e.g., `ChatRequestSchema`, `UserSchema`)


### Documentation Requirements
- Every module needs a docstring
- Every public function needs a docstring
- Use Google-style docstrings
- Include type information in docstrings

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts.

    Args:
        text1: First text to compare
        text2: Second text to compare

    Returns:
        Similarity score between 0 and 1

    Raises:
        ValueError: If either text is empty
    """
    pass
```

### Security First
- Never trust external inputs - validate everything at the boundaries
- Keep secrets in environment variables, never in code
- Log security events (login attempts, auth failures, rate limits, permission denials) but never log sensitive data (audio, conversation content, tokens, personal info)
- Authenticate users at the API gateway level - never trust client-side tokens
- Use Row Level Security (RLS) to enforce data isolation between users
- Design auth to work across all client types consistently
- Use secure authentication patterns for your platform
- Validate all authentication tokens server-side before creating sessions
- Sanitize all user inputs before storing or processing

### Error Handling
- Use specific exceptions over generic ones
- Always log errors with context
- Provide helpful error messages
- Fail securely - errors shouldn't reveal system internals

### Observable Systems & Logging Standards
- Every request needs a correlation ID for debugging
- Structure logs for machines, not humans - use JSON format with consistent fields (timestamp, level, correlation_id, event, context) for automated analysis
- Make debugging possible across service boundaries

### State Management
- Have one source of truth for each piece of state
- Make state changes explicit and traceable
- Design for multi-service voice processing - use session IDs for state coordination, avoid storing conversation data in server memory
- Keep conversation history lightweight (text, not audio)

### API Design Principles
- RESTful design with consistent URL patterns
- Use HTTP status codes correctly
- Version APIs from day one (/v1/, /v2/)
- Support pagination for list endpoints
- Use consistent JSON response format:
  - Success: `{ "data": {...}, "error": null }`
  - Error: `{ "data": null, "error": {"message": "...", "code": "..."} }`


## 4. Multi-Agent Workflows & Context Injection

### Automatic Context Injection for Sub-Agents
When using the Task tool to spawn sub-agents, the core project context (CLAUDE.md, project-structure.md, docs-overview.md) is automatically injected into their prompts via the subagent-context-injector hook. This ensures all sub-agents have immediate access to essential project documentation without the need of manual specification in each Task prompt.


## 5. MCP Server Integrations

### Gemini Consultation Server
**When to use:**
- Complex coding problems requiring deep analysis or multiple approaches
- Code reviews and architecture discussions
- Debugging complex issues across multiple files
- Performance optimization and refactoring guidance
- Detailed explanations of complex implementations
- Highly security relevant tasks

**Automatic Context Injection:**
- The system automatically includes key project files for new sessions:
  - `/docs/ai-context/project-structure.md` - Complete project structure and tech stack
  - `/CLAUDE.md` - Project-specific coding standards and guidelines
- This ensures Gemini always has comprehensive understanding of your technology stack, architecture, and project standards

**Usage patterns:**
```python
# New consultation session (project structure auto-attached)
mcp__gemini__consult_gemini(
    specific_question="How should I optimize the Ana team routing?",
    problem_description="Need to improve agent selection accuracy in team routing",
    code_context="Current routing uses score-based selection...",
    attached_files=[
        "teams/ana/team.py",
        "teams/ana/config.yaml"
    ],
    preferred_approach="optimize"
)

# Follow-up in existing session
mcp__gemini__consult_gemini(
    specific_question="What about memory usage with large conversations?",
    session_id="session_123",
    additional_context="Implemented your suggestions, now seeing high memory usage"
)
```

**Key capabilities:**
- Persistent conversation sessions with context retention
- File attachment and caching for multi-file analysis
- Specialized assistance modes (solution, review, debug, optimize, explain)
- Session management for complex, multi-step problems

**Important:** Treat Gemini's responses as advisory feedback. Evaluate the suggestions critically, incorporate valuable insights into your solution, then proceed with your implementation.

### Advanced Documentation Servers

#### Search Repo Docs
**When to use:**
- Finding specific Agno framework documentation and code snippets
- Searching for implementation examples in library repositories
- Understanding framework-specific patterns and best practices
- Getting up-to-date information about Agno features

**Usage patterns:**
```python
# Resolve library to get available documentation
mcp__search-repo-docs__resolve-library-id(libraryName="agno")

# Get focused documentation on specific topics
mcp__search-repo-docs__get-library-docs(
    context7CompatibleLibraryID="/agno/agno",
    topic="Team routing",
    tokens=10000
)
```

#### Ask Repo Agent
**When to use:**
- Asking specific questions about GitHub repositories
- Understanding codebase architecture and patterns
- Finding implementation details in source code
- Getting contextual answers about how libraries work

**Usage patterns:**
```python
# Get repository structure
mcp__ask-repo-agent__read_wiki_structure(repoName="agno-org/agno")

# View repository documentation
mcp__ask-repo-agent__read_wiki_contents(repoName="agno-org/agno")

# Ask specific questions about the codebase
mcp__ask-repo-agent__ask_question(
    repoName="agno-org/agno",
    question="How does Team mode='route' select the appropriate agent?"
)
```

### WhatsApp Integration Server
**When to use:**
- Sending WhatsApp notifications to customers
- Human handoff workflows
- Alert notifications to administrators
- Customer communication automation

**Usage patterns:**
```python
# Send text message
mcp__send_whatsapp_message__send_text_message(
    instance="pagbank-instance",
    message="Your request has been processed successfully!",
    number="5511999999999"
)

# Send media with caption
mcp__send_whatsapp_message__send_media(
    instance="pagbank-instance",
    media="base64_encoded_image_data",
    mediatype="image",
    mimetype="image/jpeg",
    caption="Transaction receipt"
)

# Send location
mcp__send_whatsapp_message__send_location(
    instance="pagbank-instance",
    latitude=-23.5505,
    longitude=-46.6333,
    name="PagBank Office",
    address="São Paulo, Brazil"
)
```

**Key capabilities:**
- Text messages with mentions and link previews
- Media sharing (images, videos, documents)
- Audio message support
- Location sharing
- Contact information sharing
- Presence indicators (typing, recording)
- Message reactions
- Integration with Evolution API v2

**Configuration:**
```bash
# Required environment variables
EVOLUTION_API_BASE_URL=http://localhost:8080
EVOLUTION_API_INSTANCE=your-instance
EVOLUTION_API_KEY=your-api-key
EVOLUTION_API_FIXED_RECIPIENT=5511999999999
```

**Key capabilities:**
- Direct repository exploration and Q&A
- Source code understanding with context
- Pattern and implementation discovery
- Real-time documentation from GitHub repositories



## 6. Configuration Management

### Environment Configuration Pattern
Genie Agents uses a layered configuration approach:

**Never hardcode values - always use configuration files and environment variables.**

### Configuration Files Structure
```
├── .env                           # Main environment variables (required)
├── .env.example                   # Template with all available options
├── config/settings.py             # General application settings
├── api/settings.py                # API-specific settings
├── agents/settings.py             # Agent-specific settings
├── agents/{agent}/config.yaml     # Individual agent configurations
└── teams/{team}/config.yaml       # Team routing configurations
```

### Environment Variables (.env)

**Core Application:**
```bash
# Environment selection
ENVIRONMENT=development  # development|production
DEBUG=true              # Enable debug logging
DEMO_MODE=true          # Demo presentation features
AGNO_LOG_LEVEL=debug    # Agno framework verbosity

# API Server
PB_AGENTS_HOST=0.0.0.0
PB_AGENTS_PORT=9888

# Database (PostgreSQL required)
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/db

# Development Features
CSV_HOT_RELOAD=true     # Enable CSV file watching
```

**AI API Keys (Required):**
```bash
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
GEMINI_API_KEY=your-key-here
```

**WhatsApp Integration:**
```bash
EVOLUTION_API_BASE_URL=http://localhost:8080
EVOLUTION_API_INSTANCE=your-instance
EVOLUTION_API_KEY=your-key
EVOLUTION_API_FIXED_RECIPIENT=5511999999999
```

**Email Notifications:**
```bash
RESEND_API_KEY=your-resend-key
EMAIL_RECIPIENT=admin@yourcompany.com
```

**Monitoring System:**
```bash
# Feature toggles
MONITORING_METRICS_ENABLED=true
MONITORING_ALERTING_ENABLED=true
MONITORING_ANALYTICS_ENABLED=true

# Thresholds
MONITORING_RESPONSE_TIME_WARNING=2.0
MONITORING_RESPONSE_TIME_CRITICAL=5.0
MONITORING_SUCCESS_RATE_WARNING=95.0
MONITORING_SUCCESS_RATE_CRITICAL=90.0

# Storage paths
MONITORING_METRICS_STORAGE=logs/metrics
MONITORING_ALERT_STORAGE=logs/alerts
MONITORING_ANALYTICS_STORAGE=logs/analytics
```

### YAML Configuration Pattern

**Agent Configuration (agents/{agent}/config.yaml):**
```yaml
agent:
  agent_id: "specialist-name"
  version: 1
  name: "Specialist Name"
  role: "Domain Expert"
  description: "Expert in specific domain"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

instructions: |
  System instructions for the agent...

knowledge_filter:
  business_unit: "Domain Area"
  max_results: 5
  relevance_threshold: 0.6
  csv_file_path: "context/knowledge/knowledge_rag.csv"

tools:
  - "search_knowledge_base"
  - "domain_specific_tool"

storage:
  type: "postgres"
  table_name: "agent_table"
  auto_upgrade_schema: true

memory:
  add_history_to_messages: true
  num_history_runs: 5
```

**Team Configuration (teams/{team}/config.yaml):**
```yaml
team:
  name: "Team Name"
  team_id: "team-identifier"
  mode: "route"  # Key for intelligent routing
  description: "Team purpose and capabilities"

model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 1.0  # Required for thinking mode
  thinking:
    type: "enabled"
    budget_tokens: 1024

instructions: |
  Routing and coordination instructions...

storage:
  type: "postgres"
  table_name: "team_table"
  mode: "team"
  auto_upgrade_schema: true

memory:
  enable_user_memories: true
  enable_agentic_memory: true
  add_history_to_messages: true
  num_history_runs: 5
```

### Configuration Loading Pattern

```python
# Always load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Use Pydantic for settings validation
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 9888
    
    # Database configuration
    database_url: str
    
    # API keys (required)
    anthropic_api_key: str
    openai_api_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### Database Connection Configuration

**PostgreSQL (Required):**
```python
# config/postgres_config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**Auto-migrations with Alembic:**
```python
# db/session.py
def init_database():
    """Initialize database with auto-migrations"""
    from alembic import command
    from alembic.config import Config
    
    alembic_cfg = Config("db/alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

### Configuration Validation

```python
# config/settings.py
def validate_settings() -> Dict[str, bool]:
    """Validate all required configuration"""
    validations = {
        "database_url": bool(os.getenv("DATABASE_URL")),
        "anthropic_api_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "valid_port": 1 <= int(os.getenv("PB_AGENTS_PORT", "9888")) <= 65535,
        "environment": os.getenv("ENVIRONMENT") in ["development", "production"]
    }
    return validations
```

## 7. Development Server Configuration

### Simple Development Setup
```bash
# Quick start
make install  # Install dependencies
make dev      # Start development server
```

### Development vs Production

**Development Mode (`ENVIRONMENT=development`):**
- Hot reload enabled
- Debug logging active
- API documentation available
- CSV hot reload for knowledge base
- Permissive CORS policy

**Production Mode (`ENVIRONMENT=production`):**
- Docker containerized
- Optimized logging
- Restricted CORS
- Monitoring enabled
- Auto-scaling ready

### Server Access Points

**Development Server:**
- **API Documentation**: http://localhost:9888/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:9888/redoc (ReDoc)
- **Main API Endpoint**: http://localhost:9888
- **Health Check**: http://localhost:9888/api/v1/health
- **Monitoring Dashboard**: http://localhost:9888/api/v1/monitoring/dashboard

**Production Server:**
- **Main API**: http://localhost:9888 (or configured port)
- **Health Check**: http://localhost:9888/api/v1/health
- **Monitoring**: http://localhost:9888/api/v1/monitoring/*
- **WebSocket**: ws://localhost:9888/api/v1/monitoring/ws/realtime

### Knowledge Base Hot Reload

**CSV Hot Reload Manager:**
```bash
# Enable in .env
CSV_HOT_RELOAD=true

# Watch for changes
CSV_FILE_PATH=context/knowledge/knowledge_rag.csv
```

**Features:**
- Real-time file watching
- Instant knowledge base updates
- Smart incremental loading
- Change detection and logging
- Management-friendly editing

### API Endpoints Structure

**Unified Agno Framework Endpoints:**
```
/runs                     # Core execution (agents/teams/workflows)
/sessions                 # Session management
/agents                   # Agent management
/agents/{id}/runs         # Agent-specific execution
/agents/{id}/sessions     # Agent sessions
/agents/{id}/memories     # Agent memory
/teams                    # Team management
/teams/{id}/runs          # Team execution
/teams/{id}/sessions      # Team sessions
/teams/{id}/memories      # Team memory
/workflows                # Workflow management
/workflows/{id}/runs      # Workflow execution
/status                   # System status
```

**Custom Business Endpoints:**
```
/api/v1/health           # Health checks
/api/v1/monitoring/*     # Monitoring system
/api/v1/agents/*         # Agent versioning
/api/v1/monitoring/ws/realtime  # WebSocket monitoring
```

## 8. Post-Task Completion Protocol
After completing any coding task, follow this checklist:

### 1. Type Safety & Quality Checks
Run the appropriate commands based on what was modified:
- **Python projects**: Run mypy type checking
- **TypeScript projects**: Run tsc --noEmit
- **Other languages**: Run appropriate linting/type checking tools

### 2. Verification
- Ensure all type checks pass before considering the task complete
- If type errors are found, fix them before marking the task as done