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
- **Factory-Based Agents**: Every agent must have a factory function following the `create_[name]_agent()` pattern
- **YAML Configuration**: Agent behavior defined in `config.yaml`, code handles orchestration only
- **Test Everything**: Unit tests for agents, integration tests for teams, workflow tests for complex flows
- **Observable Agents**: Every agent interaction must emit metrics and structured logs
- **Fail Gracefully**: Agents should degrade functionality rather than crash on errors

### Code Organization
- **Agent Modules**: Each agent in its own directory with `agent.py`, `config.yaml`, and optional `README.md`
- **Keep Files Focused**: Max 300 lines per file - split utilities, models, and handlers
- **Factory Registration**: All agents registered in `agents/registry.py` for dynamic discovery
- **Shared Tools**: Common functionality in `agents/tools/` to avoid duplication
- **Team Organization**: Teams in `teams/` directory, each with routing configuration

### Python Standards
- **Type Everything**: Full type hints with Pydantic models for all data structures
- **Async First**: Use async/await for all I/O operations and agent interactions
- **Factory Functions**: `create_[name]_agent() -> Agent` pattern for all agents
- **Google Docstrings**: Every public function documented with Args, Returns, Raises
- **Error Context**: Include session_id, agent_id in all error messages and logs

### Error Handling & Logging
- **Agent Exceptions**: Custom exceptions like `AgentNotFoundError`, `RoutingError`, `KnowledgeRetrievalError`
- **Structured Logs**: JSON format with fields: timestamp, level, correlation_id, agent_id, session_id, event, context
- **Log Categories**: `agent.routing`, `agent.execution`, `knowledge.retrieval`, `session.management`
- **Correlation IDs**: UUID4 format, passed through entire request lifecycle

### API Design
- **Versioned Endpoints**: `/api/v1/agents/{agent_id}/chat` pattern
- **Consistent Responses**: `{"data": {...}, "error": null, "metadata": {...}}`
- **WebSocket Support**: `/ws/v1/agents/{agent_id}/stream` for real-time
- **Health Checks**: `/health` (basic), `/health/detailed` (with dependencies)
- **OpenAPI Docs**: Auto-generated at `/docs` and `/redoc`

### Security & State
- **Input Validation**: Pydantic models for all API inputs, sanitize at boundaries
- **Session Management**: PostgreSQL for persistence, Redis for active sessions
- **Secret Management**: Environment variables only, never in code or configs
- **Agent Isolation**: Each agent runs in isolated context with limited permissions
- **Audit Trail**: All agent decisions logged with reasoning and context

## Project-Specific Guidelines

### Agent Development Workflow
1. Define use case and routing logic
2. Create agent directory structure
3. Write `config.yaml` with instructions and model settings
4. Implement factory function with Agno Agent creation
5. Register in `agents/registry.py`
6. Add to team configuration for routing
7. Write unit and integration tests
8. Update knowledge base if domain-specific

### Agno Integration Patterns
- **Team Routing**: Use `Team(mode="route")` for intelligent agent selection
- **Session Context**: Pass `session_id` to maintain conversation continuity
- **Tool Usage**: Leverage Agno's built-in tools before creating custom ones
- **Memory Patterns**: Use Agno's memory features for context retention

### Knowledge Base Management
- **CSV Format**: Maintain `knowledge_rag.csv` with columns: id, content, business_unit, tags
- **Hot Reload**: Changes detected automatically via file watcher
- **Agent Filtering**: Use business_unit to scope knowledge per agent
- **Embedding Updates**: Automatic re-embedding on content changes

### Performance Considerations
- **Connection Pooling**: PostgreSQL and Redis pools pre-configured
- **Async Everything**: Non-blocking I/O for all external calls
- **Metric Collection**: Minimal overhead with Prometheus client
- **Knowledge Caching**: Embeddings cached in pgvector for fast retrieval
- **Session Cleanup**: Automatic cleanup of stale sessions after timeout

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

### Important Paths
- **Agent Definitions**: `agents/*/config.yaml` - YAML configurations
- **Agent Registry**: `agents/registry.py` - Central registration
- **Team Routing**: `teams/ana/config.yaml` - Routing configuration
- **Knowledge Base**: `context/knowledge/knowledge_rag.csv` - Domain knowledge
- **API Routes**: `api/routes/v1_router.py` - Endpoint definitions
- **Monitoring**: `api/monitoring/` - Real-time analytics

### Critical Documentation
- **Agno Docs**: Use `mcp__search-repo-docs` and `mcp__ask-repo-agent` for Agno patterns
- **Agent Patterns**: `agents/CLAUDE.md` - Development guidelines
- **API Patterns**: `api/CLAUDE.md` - API development standards
- **Team Patterns**: `teams/CLAUDE.md` - Routing configuration guide
- **Workflow Patterns**: `workflows/CLAUDE.md` - Complex flow orchestration