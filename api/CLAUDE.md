# API Component - Component Context (Tier 2)

> **Note**: This is component-specific context. See root **CLAUDE.md** for master project context and coding standards.

## Purpose
The API component serves as the FastAPI-based web interface for the Automagik Multi-Agent Framework, providing HTTP endpoints for user interactions through specialized AI agents. It orchestrates requests between clients and the routing team, enabling seamless communication with domain specialists while maintaining session continuity and supporting real-time streaming responses. The API layer abstracts complex multi-agent orchestration into simple REST endpoints with comprehensive monitoring, authentication, and error handling.

## Current Status: Production Ready ✅
- **Agno-first FastAPI integration** with auto-generated endpoints via Playground
- **Dynamic agent versioning** support without file system changes
- **Streaming responses** via Server-Sent Events (SSE) and WebSocket
- **Environment-based configuration** scaling from development to production
- **Comprehensive error handling** with proper taxonomy and trace IDs
- **PostgreSQL/SQLite storage** with automatic failover
- **Rate limiting and security** with API key authentication

## Component-Specific Development Guidelines
- **FastAPI Framework**: Leverage Agno's built-in FastAPI integration with auto-generated endpoints via `Playground()` and `FastAPIApp()`
- **Agno-First Architecture**: All endpoints auto-register through Agno framework - avoid manual FastAPI route definitions
- **Streaming-First Design**: Implement real-time responses using Agno's native `run_stream()` methods for SSE and WebSocket
- **Environment-Based Configuration**: Scale security and features from development (relaxed) to production (strict) based on `RUNTIME_ENV`
- **Dynamic Versioning**: Support agent/team version control via API parameters, not file system changes
- **Error Consistency**: Maintain comprehensive error taxonomy with proper trace IDs and categorization
- **Performance Focus**: Built-in caching, request batching, and connection pooling for high-load scenarios

## Key Component Structure

### Core API Modules (`api/`)
- **serve.py** - Production FastAPI app factory with Agno integration and environment configuration
  - FastAPI app creation using `create_automagik_api()` factory pattern
  - Environment-based settings (dev/staging/production) with security scaling
  - Agno `FastAPIApp()` integration with automatic storage and monitoring setup
- **playground.py** - Development playground with auto-generated endpoints
  - Agno `Playground()` integration with all agents, teams, and workflows
  - Auto-registration of endpoints for agents, teams, workflows via `get_router()`
  - Development-specific features (debugging, platform registration)

### Router Hierarchy (`routes/`)
- **v1_router.py** - Main API version router with hierarchical endpoint organization
- **playground_router.py** - Agno playground integration for development and testing
- **health_router.py** - Health checks and system status monitoring endpoints

### Configuration Layer (`settings/`)
- **api_settings.py** - Environment-based configuration with security and performance scaling
- **cors_config.py** - Cross-Origin Resource Sharing setup for development and production
- **rate_limiting.py** - Request rate limiting and throttling configuration

## Implementation Highlights

### Agno-First FastAPI Integration
- **Technical Implementation**: Uses Agno's `Playground()` and `FastAPIApp()` for automatic endpoint generation and registration
- **Architecture Decision**: Eliminates manual FastAPI route definitions in favor of framework-driven auto-registration
- **Performance Considerations**: Built-in session management, storage optimization, and monitoring integration
- **Integration Points**: Seamless connection with agents, teams, workflows through factory patterns and YAML configuration

### Dynamic Agent Versioning
- **Implementation Pattern**: API-driven version control via query parameters (`?version=27`) without file system changes
- **Quality Measures**: Version validation, rollback capabilities, and comprehensive testing across versions
- **Scalability Considerations**: Database-driven configuration enables hot-reload and zero-downtime updates

### Real-Time Streaming Architecture
- **Technical Details**: Server-Sent Events (SSE) and WebSocket support using Agno's native `run_stream()` methods
- **Dependencies**: FastAPI's `StreamingResponse` integration with Agno's async streaming capabilities
- **Configuration**: Environment-based streaming settings with development debugging and production optimization

## Critical Implementation Details

### Agno Playground Auto-Registration
**Pattern Description**: Eliminates manual FastAPI route definitions through framework-driven auto-registration

```python
# Playground pattern - auto-generates all endpoints
from agno.playground import Playground

# Create comprehensive playground
playground = Playground(
    agents=[domain_a_agent, domain_b_agent, domain_c_agent, human_handoff_agent],
    teams=[routing_team],
    workflows=[human_handoff_workflow, typification_workflow],
    app_id="automagik-multi-agent-system"
)

# Get router with all endpoints auto-registered
playground_router = playground.get_router()
```

### Real-Time Streaming Architecture
**Architecture Decision**: Use Agno's native streaming for real-time user interactions

```python
# Server-Sent Events with Agno integration
async def generate():
    async for chunk in agent.run_stream(
        messages=request.messages,
        session_id=request.session_id,
        stream=True,
        stream_intermediate_steps=True
    ):
        yield f"data: {json.dumps({
            'content': chunk.content,
            'metadata': chunk.metadata,
            'thinking': getattr(chunk, 'thinking', None)
        })}

"
```

### Environment-Based Security Scaling
**Integration Description**: Scale security from development to production automatically

```python
# Environment-based configuration scaling
class ApiSettings(BaseSettings):
    runtime_env: str = "dev"
    api_key_required: bool = Field(default_factory=lambda: os.getenv("RUNTIME_ENV") == "prd")
    docs_enabled: bool = Field(default_factory=lambda: os.getenv("RUNTIME_ENV") != "prd")
    
    @field_validator("cors_origins", mode="before")
    def set_cors_origins(cls, cors_origins, info):
        if info.data.get("runtime_env") == "dev":
            return ["*"]  # Development: allow all
        return ["https://your-production-domain.com"]  # Production: strict
```

## Development Notes

### Current Challenges
- **Streaming Performance**: High concurrency can impact SSE connection stability - implement connection pooling and timeout management
- **Environment Configuration**: Complex scaling from development to production requires careful environment variable management and security considerations

### Future Considerations
- **GraphQL Integration**: Planned enhancement to support GraphQL endpoints alongside REST for more flexible client interactions
- **Microservice Architecture**: Future evolution towards service mesh architecture with API gateway integration for better scalability

### Performance Metrics
- **Response Time**: Target <500ms for standard requests, <2s for streaming initiation
- **Concurrent Users**: Support 1000+ concurrent connections with proper connection pooling and resource management

---

*This component documentation provides context for AI-assisted development within the API layer. For system-wide patterns and standards, reference the master CLAUDE.md file.*