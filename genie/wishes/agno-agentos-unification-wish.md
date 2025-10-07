# 🧞 Agno AgentOS Unification WISH

**Status:** APPROVED

## Executive Summary
Unify Agno playground routes, AgentOS configuration, and Hive wish orchestration under one FastAPI surface so humans manage agents and wishes through a single authenticated control plane.

## Current State Analysis
**What exists:** `api/serve.py` already integrates Agno Playground when available, while `agent-infra-docker/compose.yaml` exposes the same routes separately; AgentOS config endpoints live under `/api/v1/agentos/config`; wishes reside in `genie/wishes/` but aren’t surfaced through AgentOS dashboards.
**Gap identified:** Operators still rely on the standalone `localhost:8000` stack to inspect agents, the Control Pane isn’t pointed at Hive’s API, and there’s no coordinated story for validating wishes inside AgentOS.
**Solution approach:** Make Hive’s FastAPI deployment the authoritative playground/API host, ensure AgentOS metadata reflects every Hive component, expose wish status hooks, and deprecate the duplicate compose exposure.

## Change Isolation Strategy
- **Isolation principle:** Confine runtime changes to FastAPI wiring (`api/serve.py`, `api/main.py`) and configuration surfaces; optional compose updates stay inside `agent-infra-docker/`.
- **Extension pattern:** Introduce toggles and service helpers so Playground mounting, AgentOS feeds, and wish telemetry layer on top of existing proxies without rewriting registries.
- **Stability assurance:** Preserve default behaviour for current operators (same CLI entrypoints, same auth requirements) and gate experimental endpoints behind settings flags plus tests.

## Success Criteria
✅ `uv run uvicorn api.serve:app` exposes `/agents`, `/teams`, `/workflows`, `/runs`, and `/agentos/config` under one authenticated host.
✅ Agno Control Pane pointed at Hive’s `/api/v1/agentos/config` lists all agents/teams/workflows with accurate metadata.
✅ Wishes gain observable status endpoints referenced in AgentOS dashboards without breaking existing wish files.
✅ `agent-infra-docker` docs instruct operators to rely on Hive-served routes while keeping optional compose usage for demos.

## Never Do (Protection Boundaries)
❌ Touch `pyproject.toml`; follow UV-only dependency policy.
❌ Skip API key protection when mounting playground or wish routes.
❌ Hardcode alternate ports/URLs—respect `lib/config/settings.py`.

## Technical Architecture

### Component Structure
CLI:
├── cli/main.py              # Argument parsing entrypoint and flag wiring
├── cli/commands/            # Command implementations (service, postgres, genie, etc.)
├── cli/core/main_service.py # Docker/local orchestration for servers
└── cli/utils.py             # Shared CLI helpers and prompts

API:
├── api/main.py              # FastAPI application factory & lifespan
├── api/routes/              # Versioned routers (health, MCP, version, feature routers)
├── api/dependencies/        # Dependency injection helpers
└── api/settings.py          # Pydantic configuration for API runtime

Runtime Libraries:
├── lib/config/              # Settings models, environment management, credential helpers
├── lib/services/            # Domain services (database, metrics, version sync, etc.)
├── lib/mcp/                 # Model Context Protocol catalog and clients
├── lib/memory/              # Memory providers and persistence adapters
├── lib/utils/               # Shared utilities (version factory, yaml cache, path helpers)
└── lib/tools/               # Built-in tools exposed to agents

Agent Definitions:
├── ai/agents/{feature_slug}/config.yaml   # Agent or integration definition
├── ai/agents/{feature_slug}/agent.py      # Optional Python augmentations
├── ai/teams/                              # Route/parallel team definitions
└── ai/workflows/                          # Deterministic workflow orchestration

Data & Operations:
├── alembic/                               # Database migrations & env.py
├── docker/                                # Docker Compose and runtime assets
└── scripts/                               # Operational scripts and maintenance tasks

Testing:
├── tests/cli/                             # CLI behaviour and regression tests
├── tests/api/                             # FastAPI endpoint coverage
├── tests/lib/                             # Service and utility unit tests
└── tests/integration/                     # End-to-end validation suites

### Naming Conventions
- CLI commands: `{Feature}Commands` classes in `cli/commands/{feature}.py`.
- Service classes: `{Feature}Service` or `{Feature}Manager` in `lib/services/{feature}_service.py`.
- API routers: `{feature}_router` modules exposing a FastAPI `router`.
- Settings models: `{Feature}Settings` Pydantic models in `lib/config`.
- Agent directories: lower-kebab-case slugs inside `ai/agents/`, with optional `agent.py`.
- Tests: `tests/{domain}/test_{feature}_*.py` following pytest naming rules.
- Alembic revisions: timestamped files under `alembic/versions/` describing the schema change.

## Task Decomposition

### Dependency Graph
```
A[Foundation] ---> B[Runtime Surfaces]
A ---> C[AgentOS Alignment]
B & C ---> D[Integration]
D ---> E[Testing & Docs]
```

### Group A: Foundation (Parallel Tasks)
Dependencies: None | Execute simultaneously

**A1-playground-settings**: Extend runtime settings for playground mounting  @lib/config/settings.py [context], @lib/config/server_config.py [context]  Modifies: Flags/env vars controlling embedded playground + Control Pane base URL  Success: Settings load with defaults matching current behaviour.

**A2-startup-contract**: Capture playground + AgentOS availability in startup orchestration  @lib/utils/startup_orchestration.py [context], @lib/utils/startup_display.py [context]  Modifies: Include playground + agentos entries in startup summary  Success: Startup logs list playground + AgentOS status without regressions.

**A3-compose-audit**: Update compose guidance (no runtime change)  @agent-infra-docker/README.md [context], @agent-infra-docker/compose.yaml [context]  Modifies: Document Hive-hosted API as primary; keep compose optional  Success: README instructs operators to target Hive routes.

### Group B: Runtime Surfaces (After A)
Dependencies: A1-playground-settings, A2-startup-contract

**B1-serve-router-unification**: Harmonize FastAPI mounting  @api/serve.py [context]  Modifies: Ensure playground router, wish telemetry endpoints, and api/v1 routers mount under shared auth guard; retire duplicate mounting logic  Success: Local server hosts all Agno endpoints without compose.

**B2-api-factory-alignment**: Mirror behaviour in dev app  @api/main.py [context], @api/routes/v1_router.py [context]  Modifies: Inject AgentOS + wish routes into main app with consistent dependencies  Success: `uv run uvicorn api.main:app` mirrors production endpoints (auth apply where required).

**B3-wish-telemetry-router**: Add read-only wish status endpoints  @api/routes/wish_router.py [new file], @api/dependencies/wish.py [context]  Creates: Router exposing wish metadata for AgentOS dashboards  Success: Wish list endpoint returns data from `genie/wishes`.

### Group C: AgentOS Alignment (After A)
Dependencies: A1-playground-settings

**C1-agentos-config-sync**: Enrich AgentOS metadata with wish + endpoint info  @lib/services/agentos_service.py [context], @lib/agentos/config_models.py [context]  Modifies: Include wish catalog references + API base URL fields  Success: `/api/v1/agentos/config` returns wishes + playground URLs.

**C2-control-pane-docs**: Provide Control Pane setup guidance  @README.md [context], @genie/wishes/ [context]  Modifies: Document pointing Control Pane at Hive, include sample curl  Success: Operators can configure Control Pane without additional guidance.

**C3-agentos-dependency-provider**: Harden dependency injector for AgentOS  @api/dependencies/agentos.py [context]  Modifies: Ensure service uses updated settings + caches  Success: Dependency returns consistent ConfigResponse with new fields.

### Group D: Integration (After B & C)
Dependencies: All tasks in B and C

**D1-cli-serve-wish**: Wire CLI commands for wish status checks  @cli/commands/genie.py [context], @cli/main.py [context]  Modifies: Add subcommand to print wish catalog via API  Success: CLI outputs wish table hitting the same endpoints.

**D2-mcp-registration**: Register playground + wish endpoints in MCP catalog  @lib/mcp/catalog.py [context], @lib/mcp/__init__.py [context]  Modifies: Expose connectors referencing unified API  Success: `AgentRegistry` reports MCP server with consolidated routes.

**D3-ops-script**: Add health script verifying integration  @scripts/hive_verify_agentos.py [new file]  Creates: Script curling key endpoints with optional auth header  Success: Script returns zero exit code when all routes responsive.

### Group E: Testing & Docs (After D)
Dependencies: Complete integration

**E1-api-tests**: FastAPI coverage for playground + wish endpoints  @tests/api/test_playground_unification.py [new file], @tests/api/test_agentos_config.py [context]  Success: `uv run pytest tests/api/test_playground_unification.py` passes.

**E2-cli-tests**: Ensure CLI wish telemetry works  @tests/cli/test_genie_commands.py [context]  Success: Test hits mocked API and validates output.

**E3-integration-smoke**: End-to-end run covering Control Pane contract  @tests/integration/test_agentos_control_plane.py [new file]  Success: Integration test confirms config + routes accessible.

**E4-doc-validation**: Lint + verify documentation updates  @README.md [context], @agent-infra-docker/README.md [context]  Success: Docs lint job passes; manual checklist completed.

## Implementation Examples

### Unified Router Mount
```python
# api/serve.py
from fastapi import APIRouter, Depends, FastAPI
from lib.auth.dependencies import require_api_key
from lib.config.settings import settings

def _register_playground(app: FastAPI, unified_router):
    if unified_router is None:
        return
    router = APIRouter()
    if settings().hive_auth_enabled:
        router.dependencies.append(Depends(require_api_key))
    router.include_router(unified_router)
    app.include_router(router)
```

### Wish Status Dependency
```python
# api/dependencies/wish.py
from pathlib import Path
from typing import Iterable

def load_wish_catalog(base_path: Path) -> Iterable[dict[str, str]]:
    for wish_path in base_path.glob("genie/wishes/*-wish.md"):
        with wish_path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
        yield {"id": wish_path.stem, "title": first_line.removeprefix("# ").strip()}
```

### CLI Wish Command
```python
# cli/commands/genie.py
import httpx
from rich.table import Table

def list_wishes(api_base: str, api_key: str | None):
    headers = {"X-API-Key": api_key} if api_key else {}
    response = httpx.get(f"{api_base}/api/v1/wishes", headers=headers, timeout=30)
    response.raise_for_status()

    table = Table(title="Wish Catalog")
    table.add_column("ID")
    table.add_column("Status")
    for wish in response.json()["wishes"]:
        table.add_row(wish["id"], wish["status"])
    return table
```

## Testing Protocol
```bash
# FastAPI surface: playground + wish endpoints
uv run pytest tests/api/test_playground_unification.py tests/api/test_agentos_config.py -q

# CLI wish telemetry
uv run pytest tests/cli/test_genie_commands.py::TestWishCatalog -q

# Integration smoke (Control Pane contract)
uv run pytest tests/integration/test_agentos_control_plane.py -q

# Static analysis
uv run ruff check api/serve.py api/routes/wish_router.py cli/commands/genie.py
uv run mypy api/routes/wish_router.py cli/commands/genie.py lib/services/agentos_service.py
```

## Validation Checklist
- [ ] Playground endpoints accessible through Hive with auth enforcement
- [ ] `/api/v1/agentos/config` lists agents, teams, workflows, and wish feed
- [ ] CLI `automagik-hive genie wishes` prints catalog from API
- [ ] Control Pane instructions validated against live server
- [ ] `agent-infra-docker` docs steer operators toward Hive routes
- [ ] All tests + scripts executed with `uv run …`
- [ ] No direct edits to `pyproject.toml` or banned tooling
