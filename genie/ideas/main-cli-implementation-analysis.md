# Main CLI Implementation Analysis

## Current Status

✅ **CLI Integration Complete**: The `--main-*` commands are already integrated into `cli/main.py`
✅ **Docker Compose Updated**: `docker/main/docker-compose.yml` updated to DDD specification
✅ **Conditional Import**: Safe fallback when MainCommands not yet implemented

## Architecture Understanding

### Two Modes of Operation

1. **Local Development Mode** (existing):
   - Commands: `--serve`, `make dev`
   - Implementation: `uvicorn api.serve:app` directly
   - PostgreSQL: Shared (via .env)
   - API: Local process (no Docker)

2. **Production Docker Mode** (to implement):
   - Commands: `--main-install`, `--main-start`, `--main-stop`, etc.
   - Implementation: Docker Compose orchestration
   - PostgreSQL: Shared (via .env) - same instance
   - API: Docker container

### Key Design Principle

Both modes use **THE SAME** PostgreSQL instance and .env configuration. The only difference is how the API runs:
- Local: Direct uvicorn process
- Docker: Containerized FastAPI

## Implementation Requirements

### MainService Class
- Mirror AgentService pattern but for production Docker orchestration
- Handle docker-compose operations for main application
- Support persistent storage (unlike agent's ephemeral storage)
- Use .env directly (no credential overrides like agent)

### MainCommands Class  
- Mirror AgentCommands pattern
- Orchestrate MainService for CLI integration
- Follow exact same interface pattern as agent commands

### Docker Integration
- Use `docker/main/docker-compose.yml` (already updated)
- Container names: `hive-main-postgres`, `hive-main-app`
- Network: `hive_main_network`
- Persistent storage in `data/postgres`

## Critical Differences from Agent Pattern

| Aspect | Agent Pattern | Main Pattern |
|--------|---------------|--------------|
| **Storage** | Ephemeral | Persistent (`data/postgres`) |
| **Environment** | Test overrides | Pure .env inheritance |
| **Purpose** | Development/testing | Production |
| **Port Strategy** | Fixed test ports | Environment-driven |
| **Network** | Isolated | Integrated |

## Implementation Strategy

1. **TDD Phase**: Create failing tests first
   - `tests/cli/commands/test_main.py`
   - `tests/cli/core/test_main_service.py`

2. **Implementation Phase**: 
   - `cli/core/main_service.py`
   - `cli/commands/main.py`

3. **Integration Phase**:
   - Test main commands work
   - Validate both Docker and local modes coexist
   - Ensure shared PostgreSQL works correctly

## Expected Behavior

```bash
# Local development (existing)
uv run automagik-hive --serve          # Local uvicorn
make dev                               # Local uvicorn

# Production Docker (new)
uv run automagik-hive --main-install   # Docker containers
uv run automagik-hive --main-start     # Start Docker
uv run automagik-hive --main-status    # Check Docker status
uv run automagik-hive --main-stop      # Stop Docker
```

Both modes connect to the same PostgreSQL instance configured in .env.

## Next Steps

1. Follow TDD: Create tests first
2. Implement MainService (Docker orchestration)
3. Implement MainCommands (CLI interface)
4. Validate integration
5. Update todo list as completed