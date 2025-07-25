# CLAUDE.md - API

🗺️ **FastAPI Integration & Deployment Domain**

## 🧭 Navigation

**🔙 Main Hub**: [/CLAUDE.md](../CLAUDE.md)  
**🔗 Core**: [AI System](../ai/CLAUDE.md) | [Config](../lib/config/CLAUDE.md) | [Auth](../lib/auth/CLAUDE.md)  
**🔗 Support**: [Logging](../lib/logging/CLAUDE.md) | [Testing](../tests/CLAUDE.md)

## Purpose

FastAPI-based web interface for multi-agent framework. Auto-generates endpoints via Agno integration with streaming support.

## Architecture

**Core Files**:
```
api/
├── serve.py     # 🚀 Production FastAPI app 
├── main.py      # 💻 Development playground
└── routes/      # 🛣️ Route organization
```

**Agno Integration**:
- `Playground()` → Auto-generates all endpoints
- `FastAPIApp()` → Production deployment
- Streaming → SSE/WebSocket via `run_stream()`

## Quick Start

**Development**:
```bash
make dev  # Starts main.py with Playground auto-endpoints
```

**Production**:
```bash
make prod  # Starts serve.py with FastAPIApp
```

## Auto-Generated Endpoints

**Playground pattern**:
```python
# main.py - Development auto-endpoints
playground = Playground(
    agents=[all_agents],
    teams=[all_teams], 
    workflows=[all_workflows],
    app_id="automagik-hive"
)

app.include_router(playground.get_router())
# ✅ Automatically creates /agents/, /teams/, /workflows/ endpoints
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
- **Authentication**: API key middleware ([Auth patterns](../lib/auth/CLAUDE.md))
- **Configuration**: Environment-based settings ([Config patterns](../lib/config/CLAUDE.md))
- **Storage**: PostgreSQL with SQLite fallback
- **Monitoring**: Built-in logging and metrics

## Critical Rules

- **Agno-First**: Use `Playground()` and `FastAPIApp()`, avoid manual routes
- **Environment-Based**: Different security/CORS for dev/prod
- **Streaming-First**: Use `run_stream()` for real-time responses  
- **Auto-Registration**: Components auto-expose via framework
- **Version Support**: Dynamic versioning via API parameters

## Performance Targets

- **Response**: <500ms standard, <2s streaming initiation
- **Concurrent**: 1000+ users with connection pooling
- **Streaming**: SSE/WebSocket for real-time updates
- **Scale**: Environment-based from dev to enterprise

Navigate to [AI System](../ai/CLAUDE.md) to understand what gets exposed or [Auth](../lib/auth/CLAUDE.md) for security patterns.