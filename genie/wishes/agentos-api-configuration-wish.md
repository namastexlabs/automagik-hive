# 🧞 AgentOS API Configuration WISH

**Status:** READY_FOR_REVIEW

## Executive Summary
Expose a configurable AgentOS API surface that loads Agno v2 configuration from YAML or class definitions and serves it via protected FastAPI endpoints for the control plane.

## Current State Analysis
**What exists:** Agno v2 core migration established new dependency patterns, but Automagik Hive still lacks an AgentOS integration layer or configuration loader. API routers only ship health, version, and MCP surfaces; no endpoint returns AgentOS metadata.
**Gap identified:** Without an AgentOS service the control plane cannot discover agents, databases, quick prompts, or display names, blocking the v2 rollout. Configuration defaults live only in docs; settings provide no contract for supplying YAML paths or typed overrides. Registries currently expose identifiers via filesystem scans (agents/teams/workflows) but contain no quick prompt corpus, and database naming lives inside `HiveSettings` plus memory/knowledge factories.
**Solution approach:** Introduce dedicated AgentOS config models and loaders, wrap them in a service that assembles runtime metadata from existing registries/settings, seed a default YAML that supplies quick prompts + display names, and publish the result through a secured `/api/v1/agentos` router (with `/config` compatibility alias) that mirrors Agno’s schema with tests and documentation.

## Change Isolation Strategy
- **Isolation principle:** Keep AgentOS logic inside `lib/agentos/` and a single service entry point so the rest of the platform consumes a stable interface.
- **Extension pattern:** Layer YAML parsing and typed configuration on top of current settings, falling back to generated defaults when no file is provided.
- **Stability assurance:** Wire the new router through dependency providers and feature flags to ensure existing API clients and CLI flows remain unchanged until AgentOS is invoked.

## Success Criteria
-✅ Default YAML seeds quick prompts, display names, and database IDs derived from Automagik registries/settings.
✅ `AgentOSService.load_configuration()` returns an `AgentOSConfig` instance whether the source is YAML or Python.
✅ `/api/v1/agentos/config` responds with the documented JSON contract (OS id, databases, agents, teams, workflows, quick prompts, etc.).
✅ `/config` alias mirrors the versioned route so Agno AgentOS UI keeps working.
✅ Settings allow operators to point to an external AgentOS config file while validating path existence at startup.
✅ `uv run pytest` suites covering AgentOS service and API pass, and FastAPI dependency wiring enforces API key protection.
✅ README (or relevant ops docs) tells humans how to supply custom AgentOS configuration and inspect it through the API.

## Never Do (Protection Boundaries)
❌ Modify `pyproject.toml` directly or bypass `uv` for dependencies.
❌ Hardcode secrets, database URLs, or environment-specific metadata in AgentOS defaults.
❌ Expose AgentOS routes without API key protection or skip regression tests after wiring the service.

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
- AgentOS modules reside under `lib/agentos/` with descriptive filenames like `config_loader.py`.
- Service surface exported as `AgentOSService` in `lib/services/agentos_service.py` and re-exported via `lib/services/__init__.py`.
- API router module named `agentos_router.py`, exposing a FastAPI router variable `agentos_router` attached beneath `/api/v1/agentos`.
- Settings fields use `hive_agentos_*` prefixes (e.g., `hive_agentos_config_path`).
- Tests follow `tests/api/test_agentos_*.py` and `tests/lib/services/test_agentos_*.py` patterns.

## Task Decomposition

### Dependency Graph
```
A[Config Foundation] ---> B[Runtime Services]
A ---> C[API Surface]
B & C ---> D[Integration]
D ---> E[Testing & Docs]
```

### Group A: Config Foundation (Parallel)
Dependencies: None | Execute simultaneously

**A1-config-schemas**: Define AgentOS config dataclasses  @lib/agentos [context]  Creates: `lib/agentos/config_models.py` wrapping Agno `AgentOSConfig`, `ChatConfig`, etc., plus typed helpers for defaults  Exports: `AgentOSCasing` alias consumed by loaders  Success: Imported without circular deps; docstring explains fallback priorities.

**A2-config-loader**: Implement loader utilities  @lib/agentos [context]  Creates: `lib/agentos/config_loader.py` with `load_agentos_config(path: Path | None, overrides: dict | None)` reading YAML via `yaml.safe_load` and returning `AgentOSConfig` (fallback merges default quick prompts + DB metadata)  Success: Handles missing files via default builder; raises explicit errors when schema mismatches.

**A3-settings-surface**: Expose configuration knobs  @lib/config/settings.py [context]  Modifies: Add `hive_agentos_config_path`, `hive_agentos_enable_defaults`, and validation to ensure file existence when provided; document how the defaults harvest metadata from `HiveSettings`, `lib/memory/config.yaml`, and `lib/knowledge/config.yaml`  Success: Settings instantiate with/without env vars; new fields documented in class comments.

### Group B: Runtime Services (After A)
Dependencies: A1-config-schemas, A2-config-loader

**B1-service-layer**: Create service façade  @lib/services/__init__.py [context]  Creates: `lib/services/agentos_service.py` with `AgentOSService` caching config, mapping registry metadata (agents, teams, workflows, databases) via `list_available_*` helpers without instantiating heavy objects  Success: `.get_config()` returns dict matching Agno schema; includes quick prompt normalization.

**B2-default-artifacts**: Ship default config assets  @lib/agentos [context]  Creates: `lib/agentos/default_agentos.yaml` capturing starter quick prompts + display names aligned with template agents/teams/workflows and pre-populated database identifiers from Automagik settings  Success: Loader uses this file when path absent; comments clarify editing guidance without secrets.

### Group C: API Surface (After B)
Dependencies: Group B

**C1-dependency-provider**: Provide FastAPI dependency  @api/dependencies/__init__.py [context]  Creates: `api/dependencies/agentos.py` exposing `get_agentos_service()` returning singleton `AgentOSService`  Success: Importable without triggering heavy startup; dependency reused in router.

**C2-agentos-router**: Implement API contract  @api/routes [context]  Creates: `api/routes/agentos_router.py` with `/api/v1/agentos/config` GET endpoint serializing service output (+ `/config` alias if control plane still expects legacy path)  Success: Endpoint documented with response model; includes API key guard inherited from parent router.

**C3-schema-alignment**: Add Pydantic response model  @api/routes/agentos_router.py [context]  Creates: `AgentOSConfigResponse` model matching `/config` schema for validation  Success: Model ensures quick prompts keyed by agent/team/workflow and optional interface metadata.

### Group D: Integration (After B & C)
Dependencies: Groups B and C

**D1-router-registration**: Wire router  @api/routes/v1_router.py [context], @api/main.py [context]  Modifies: Include `agentos_router` under `/api/v1`, ensure dependency injection  Success: FastAPI app lists new route; OpenAPI docs show protected path.

**D2-runtime-factory**: Expose AgentOS builder  @lib/utils/startup_orchestration.py [context], @api/serve.py [context]  Modifies: Hook `AgentOSService` into startup display (metadata only) and ensure CLI orchestration can optionally build `AgentOS` when env flag set  Success: Startup log lists AgentOS status without affecting existing flows.

**D3-cli-bridge**: Provide CLI inspection command  @cli/commands/service.py [context]  Modifies: Add CLI subcommand `agentos-config` (behind feature flag) calling service and printing summary  Success: `uv run automagik-hive agentos-config --json` outputs config snapshot; tests cover Path.

### Group E: Testing & Docs (After D)
Dependencies: Groups A–D

**E1-service-tests**: Unit tests for loader + service  @tests/lib/services/test_agentos_service.py [context]  Creates: Tests covering YAML path missing, default fallback, quick prompt normalization  Success: `uv run pytest tests/lib/services/test_agentos_service.py -q` passes.

**E2-api-tests**: API contract regression  @tests/api/test_agentos_config.py [context]  Creates: FastAPI TestClient tests verifying `/api/v1/agentos/config` and `/config` return expected payload and respect auth  Success: Tests assert status codes 401/200 and schema fields for both routes.

**E3-cli-tests**: CLI smoke coverage  @tests/cli/test_agentos_command.py [context]  Creates: Test ensuring CLI command prints config JSON  Success: Pytest run passes with feature flag toggled.

**E4-docs-update**: Document configuration workflow  @README.md [context], @docs/operations.md [context]  Modifies: Add section on supplying YAML config, using new CLI command, and hitting API endpoint  Success: Documentation lint (if any) passes; links reference new files.

## Implementation Examples

### Loader Utility
```python
# lib/agentos/config_loader.py
from pathlib import Path
from typing import Any

import yaml
from agno.os.config import AgentOSConfig

from lib.agentos.config_models import build_default_agentos_config


def load_agentos_config(config_path: Path | None, overrides: dict[str, Any] | None = None) -> AgentOSConfig:
    if config_path and config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        base = AgentOSConfig.model_validate(payload)
    else:
        base = build_default_agentos_config()

    if overrides:
        return base.model_copy(update=overrides)
    return base
```

### FastAPI Router Pattern
```python
# api/routes/agentos_router.py
from fastapi import APIRouter, Depends

from api.dependencies.agentos import get_agentos_service
from lib.services.agentos_service import AgentOSService

agentos_router = APIRouter(prefix="/api/v1/agentos", tags=["agentos"])


@agentos_router.get("/config", response_model=dict[str, object])
async def get_agentos_config(service: AgentOSService = Depends(get_agentos_service)) -> dict[str, object]:
    return service.serialize()
```

### CLI Command Skeleton
```python
# cli/commands/service.py
class ServiceCommands:
    ...

    def agentos_config(self, json_output: bool = False) -> int:
        from lib.services.agentos_service import AgentOSService

        config = AgentOSService().serialize()
        if json_output:
            print(json.dumps(config, indent=2))
        else:
            self._display_table(config)
        return 0
```

## Testing Protocol
```bash
# Service + loader coverage
uv run pytest tests/lib/services/test_agentos_service.py -q

# API contract validation
uv run pytest tests/api/test_agentos_config.py -q

# CLI behaviour (feature flagged)
uv run pytest tests/cli/test_agentos_command.py -q
```

## Validation Checklist
- [ ] Settings accept and validate AgentOS config paths
- [ ] AgentOS service returns schema-compliant payloads
- [ ] API route protected by API key dependency
- [ ] CLI command mirrors API output when enabled
- [ ] Documentation explains YAML and class configuration paths
- [ ] Tests run using `uv` commands demonstrate success

## Human Options
1. Approve the wish as written so forge can begin planning execution.
2. Request refinements to the scope, tasks, or success criteria before approval.
3. Ask clarifying questions about assumptions, defaults, or validation strategy.
