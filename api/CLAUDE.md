# CLAUDE.md - API

## Context & Scope

[CONTEXT]
- Describes the FastAPI/Agno surface for Automagik Hive.
- Covers development vs production startup, routing, streaming, and dependencies.
- Coordinate with `/CLAUDE.md`, `lib/config/CLAUDE.md`, and `lib/auth/CLAUDE.md` before API changes.

[CONTEXT MAP]
@api/
@api/routes/
@api/dependencies/

[SUCCESS CRITERIA]
✅ `make dev` and `make prod` start without startup orchestration failures.
✅ Playground auto-exposes agents/teams/workflows with correct routing.
✅ Streaming endpoints deliver chunked responses via SSE/WebSocket.
✅ Environment toggles (docs, auth, CORS) behave per settings.

[NEVER DO]
❌ Create manual routes when Playground/FastAPIApp already expose endpoints.
❌ Disable authentication in production.
❌ Hardcode URLs or secrets inside code; rely on settings.
❌ Skip pytest/API tests after route or dependency changes.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Assess API impact
   - Identify which file (serve.py, main.py, routes, dependencies) changes.
   - Review related settings in `lib/config` and auth dependencies.
   - Check existing tests under `tests/api/`.

2. [Implementation] Apply API changes
   - Update routes, dependencies, or startup logic.
   - Keep Playground/FastAPIApp as the primary exposure path.
   - Adjust settings models and documentation when toggles change.

3. [Verification] Validate API health
   - Run `uv run pytest tests/api/` and relevant integration tests.
   - Start dev server (`make dev`) to confirm endpoints and streaming.
   - Capture evidence (logs, curl outputs) in the active wish/Forge log.
</task_breakdown>
```

## Purpose

FastAPI-based web interface for multi-agent framework. Auto-generates endpoints via Agno integration with streaming support.

## Architecture

**Core Files**:
```
api/
├── serve.py         # 🚀 Production FastAPI app with orchestrated startup
├── main.py          # 💻 Development playground
├── settings.py      # 🎛️ API configuration and environment settings
├── routes/          # 🛣️ Route organization
│   ├── v1_router.py     # Business endpoints aggregator
│   ├── mcp_router.py    # MCP server status endpoints
│   ├── version_router.py# Version information endpoints
│   └── health.py        # Health check endpoints
└── dependencies/    # 🔧 Shared dependencies and validation
```

**Agno Integration**:
- `Playground()` → Auto-generates all endpoints
- `AGUIApp()` → Single-agent UI interface (optional)
- `FastAPIApp()` → Production deployment
- Streaming → SSE/WebSocket via `run_stream()`
- Factory Pattern → Lazy app creation via `app()` factory

## Quick Start

**Development**:
```bash
# From Claude Code - use Bash tool with background parameter:
Bash(command="make dev", run_in_background=True)

# From terminal:
make dev  # Starts main.py with Playground auto-endpoints
```

**Production**:
```bash
make prod  # Starts serve.py with FastAPIApp
```

## Auto-Generated Endpoints

**Playground pattern**:
```python
# serve.py - Unified API with auto-endpoints
playground = Playground(
    agents=agents_list,
    teams=teams_list,
    workflows=workflows_list,
    app_id="automagik_hive"
)

# Get unified router with all endpoints
unified_router = playground.get_async_router()
app.include_router(unified_router)
# ✅ Automatically creates /agents/, /teams/, /workflows/ endpoints
```

**AGUI Integration** (Optional):
```python
if settings().hive_enable_agui:
    agui_app = AGUIApp(
        agent=selected_agent,
        name=selected_agent.name,
        app_id=f"{selected_agent.agent_id}_agui"
    )
    app.mount("/agui", agui_app.get_app())
```

**Business Endpoints**:
```python
# v1_router aggregates business endpoints
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_check_router)
v1_router.include_router(version_router)
v1_router.include_router(mcp_router)
```

## Streaming Support

**Real-time responses**:
```python
# Server-Sent Events
async def stream_response():
    async for chunk in agent.run_stream(
        messages=request.messages,
        stream=True,
        stream_intermediate_steps=True
    ):
        yield f"data: {json.dumps(chunk.content)}\n\n"
```

## Startup & Shutdown

**Orchestrated Startup**:
```python
# Sequential startup with progress tracking
startup_results = await orchestrated_startup(quiet_mode=is_reloader_context)

# Results contain:
# - registries.agents: Loaded agent instances
# - registries.teams: Available team factories
# - registries.workflows: Workflow registry
# - services.auth_service: Authentication service
# - services.metrics_service: Metrics collection
```

**Graceful Shutdown**:
```python
# Multi-step shutdown with progress display
shutdown_progress = create_automagik_shutdown_progress()
with shutdown_progress.step(0):  # Stopping server
with shutdown_progress.step(1):  # Cancelling background tasks
with shutdown_progress.step(2):  # Cleaning up services
with shutdown_progress.step(3):  # Clearing temporary files
with shutdown_progress.step(4):  # Finalizing shutdown
```

## Environment Scaling

**Dev vs Production**:
```python
class ApiSettings(BaseSettings):
    runtime_env: str = "dev"
    api_key_required: bool = Field(default_factory=lambda: os.getenv("RUNTIME_ENV") == "prd")
    docs_enabled: bool = Field(default_factory=lambda: os.getenv("RUNTIME_ENV") != "prd")

    cors_origins: List[str] = Field(default_factory=lambda:
        ["*"] if os.getenv("RUNTIME_ENV") == "dev"
        else ["https://your-domain.com"]
    )
```

## Integration

- **AI Components**: All agents/teams/workflows auto-exposed
- **Authentication**: API key middleware with conditional protection
- **Configuration**: Environment-based settings ([Config patterns](../lib/config/CLAUDE.md))
- **Storage**: PostgreSQL with auto-schema migration
- **Monitoring**: Async metrics service with background processing
- **MCP Support**: Server status and connection testing endpoints
- **Notifications**: Optional startup/shutdown notifications (production)
- **AGUI**: Optional single-agent UI interface
- **Middleware**: AgentRunErrorHandler for robust error handling

## Critical Rules

- **Agno-First**: Use `Playground()` and `FastAPIApp()`, avoid manual routes
- **Environment-Based**: Different security/CORS for dev/prod
- **Streaming-First**: Use `run_stream()` for real-time responses
- **Auto-Registration**: Components auto-expose via framework
- **Version Support**: Dynamic versioning via API parameters
- **Factory Pattern**: Use `app()` factory function for lazy loading
- **Orchestrated Startup**: Sequential initialization with progress tracking
- **Auth Protection**: Conditional based on environment and settings

## Performance Targets

- **Response**: <500ms standard, <2s streaming initiation
- **Concurrent**: 1000+ users with connection pooling
- **Streaming**: SSE/WebSocket for real-time updates
- **Scale**: Environment-based from dev to enterprise
- **Startup**: Orchestrated sequential loading with metrics integration
- **Shutdown**: Graceful multi-step cleanup with progress display

## MCP Endpoints

**Available Routes**:
- `GET /api/v1/mcp/status` - Overall MCP system status
- `GET /api/v1/mcp/servers` - List available MCP servers
- `GET /api/v1/mcp/servers/{server_name}/test` - Test server connection

## Development URLs

**Local Development**:
- 📖 API Docs: `http://localhost:8886/docs`
- 🚀 Main API: `http://localhost:8886`
- 💗 Health: `http://localhost:8886/api/v1/health`
- 🎨 AGUI: `http://localhost:8886/agui` (if enabled)

Navigate to [AI System](../ai/CLAUDE.md) to understand what gets exposed or [Auth](../lib/auth/CLAUDE.md) for security patterns.
