# 🧞 Agno v2 Migration WISH (Pinned to 2.0.8)

**Status:** APPROVED

## Executive Summary
Upgrade Automagik Hive’s agent platform to Agno v2, aligning dependencies, storage, knowledge, metrics, and runtime surfaces while keeping existing agent behaviours stable.

## Current State Analysis
**What exists:** Agents, teams, and workflows rely on Agno v1 APIs (`context`, `Memory`, `Playground`, legacy storage classes) with bespoke factories in `lib/` and runtime wiring in CLI/API layers.
**Gap identified:** Agno v2 renames core concepts (`dependencies`, `RunOutput`, unified Db/Knowledge/AgentOS), deprecates Memory wrappers, and introduces new metrics schemas that our integration does not yet support. Our shared storage helpers (`lib/utils/agno_storage_utils.py`) still construct v1 `agno.storage.*` classes and push the deprecated `mode`/`table_name` arguments; the proxy layer (`lib/utils/proxy_agents.py`, `lib/utils/proxy_teams.py`) continues to flatten `context` and wire `storage` instead of the required `dependencies` + unified `db`; template configs/tests enforce v1 keys (e.g., `.storage` assertions in `tests/ai/agents/template-agent/test_template_agent.py`); metrics bridges reference removed fields such as `prompt_tokens`/`completion_tokens` and lack a plan for `provider_metrics` uptake.
**Solution approach:** Stepwise migration: upgrade the dependency graph, refactor factories and runtime surfaces to new imports, adopt AgentOS interfaces, modernize knowledge/memory persistence, and refresh metrics + tests under TDD until the full suite passes with v2 semantics.

## Change Isolation Strategy
- **Isolation principle:** Introduce compatibility helpers inside existing `lib/` factories so higher layers adopt v2 without mass rewrites.
- **Extension pattern:** Wrap v2-specific constructs (Db, Knowledge, AgentOS interfaces) behind dedicated modules before touching agent/team definitions.
- **Stability assurance:** Maintain feature flags and smoke tests to certify agents and knowledge retrieval stay deterministic across the migration phase.

## Success Criteria
✅ Core libraries (agents/teams/workflows) instantiate with v2 APIs; no Playground/AgentOS changes (deferred to separate wish).
✅ Agents/teams/workflows instantiate with `dependencies=` and Agno v2 Db objects while passing smoke + unit tests.
✅ Knowledge base loaders leverage the new `Knowledge` API with vector tables populated via incremental loader checks.
✅ Metrics ingestion accepts v2 field names and legacy data migrates via `migrate_to_v2.py` without data loss.
✅ Shared proxy + helper layer constructs v2 `Db` objects, exposes `dependencies=...` in all agent/team factories, and drops `context`/`storage` kwargs before instantiation.
✅ Agent YAML/test assets reflect v2 schema (no `context`/`storage` keys, positive checks for `dependencies` + unified `db`).

## Never Do (Protection Boundaries)
❌ Edit `pyproject.toml` directly—use `uv` commands for dependency changes.
❌ Drop existing memory or knowledge tables without capturing backups (even though rollback unlikely).
❌ Remove regression tests or Death Testaments tied to agent orchestration.

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

Key impact zones: `lib/memory/memory_factory.py`, `lib/knowledge/*`, `lib/utils/proxy_*`, `lib/metrics/*`, `lib/versioning/agno_version_service.py`, `ai/teams/registry.py`, `ai/workflows/`, `tests/lib/*` (no API/CLI runtime changes).

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
A ---> C[Knowledge System]
A ---> D[Persistence & Metrics]
B & C & D ---> E[Agent Assets]
E ---> F[Testing & Docs]
```

### Group A: Foundation (Parallel Tasks)
Dependencies: None | Execute simultaneously

**A1-agno-version-upgrade**: Pin project to Agno 2.0.8 via `uv add agno==2.0.8` then `uv lock`. Verify with `uv run pip show agno` and `uv run python -c "import agno; print(agno.__version__)"`. Exports: `agno==2.0.8` locked for imports. Success: Version asserts exactly '2.0.8'; no transitive v1 pulls.

**A2-core-import-compat**: Audit shared wrappers for renamed APIs (`dependencies`, `RunOutput`, event classes)  @lib/utils/proxy_agents.py [context], @lib/utils/proxy_teams.py [context], @lib/utils/version_factory.py [context]  Modifies: Imports, constructor kwargs, streaming handlers  Exports: Helpers returning v2-compliant agents/teams  Success: Static type checks succeed; no import errors during smoke run.

**A3-db-factory-refresh**: Replace deprecated Memory/Storage classes with unified Db interfaces  @lib/memory/memory_factory.py [context], @lib/memory/__init__.py [context], @lib/config/settings.py [context]  Modifies: Factories to build `SqliteDb`/`PostgresDb`, toggles `enable_user_memories`; preserves existing memory/session data in agno schema  Exports: `create_*_memory` returning `(db, enable_user_memories)` tuple or helper  Success: Unit tests confirm Db wiring; memory tables created in agno schema; existing sessions remain accessible.

**A4-proxy-context-dependencies**: Rewrite shared storage helpers and proxies to emit Agno v2 constructs  @lib/utils/agno_storage_utils.py [context], @lib/utils/proxy_agents.py [context], @lib/utils/proxy_teams.py [context], @lib/utils/proxy_workflows.py [context]  Modifies: Switch to `agno.db.*` imports, map YAML to unified `db` plus `dependencies`, drop legacy `context`/`storage` kwargs  Exports: Agent/team/workflow factories instantiating successfully under v2 signatures  Success: Smoke agent load proves no `TypeError` for `context`/`mode`; proxy tests cover `dependencies` payloads.

### Group B: Runtime Surfaces (After A)
Dependencies: A1-agno-version-upgrade, A2-core-import-compat (focus on v2 APIs, defer AgentOS)



**B2-startup-pipeline-sync**: Align startup orchestration with v2 agent/team lifecycles (no AgentOS). @lib/utils/startup_orchestration.py [context], @lib/utils/startup_display.py [context] Modifies: Discovery to use v2 registries/`dependencies`. Exports: Summaries for v2. Success: Logs confirm v2 without runtime errors.

**B3-cli-runtime-bridge**: Ensure CLI services use v2 builders (no AgentOS). @cli/core/main_service.py [context], @cli/commands/service.py [context] Modifies: Bootstrap for v2 Db/agents. Exports: Zero-exit CLI with v2. Success: Smoke tests pass v2 injections.

### Group C: Knowledge System (After A)
Dependencies: A1-agno-version-upgrade, A3-db-factory-refresh

**C1-knowledge-core-rewrite**: Port to `Knowledge` (auto-reader, `add_content`/`remove_content_by_id`, `contents_db` for deletions; add `content_hash`/`content_id` cols via migration). @lib/knowledge/row_based_csv_knowledge.py [context] Modifies: Replace `DocumentKnowledgeBase` with `Knowledge`; re-index existing CSV via `add_content`. Exports: Subclass with row support. Success: Tests load/query/delete without v1 errors; vectors migrated.

**C2-knowledge-factory-adapt**: Refresh knowledge factory to construct `Knowledge` with `contents_db`  @lib/knowledge/factories/knowledge_factory.py [context]  Modifies: Embedder/VectorDb wiring, table names, incremental loader hooks  Exports: Factory returning ready-to-use knowledge instance  Success: Integration test indexes CSV and serves queries under v2.

**C3-knowledge-watcher-sync**: Update CSV hot reload + repositories for new deletion APIs  @lib/knowledge/datasources/csv_hot_reload.py [context], @lib/knowledge/repositories/knowledge_repository.py [context]  Modifies: Loader hooks, content removal paths  Exports: Repository capable of invoking `remove_content_by_id`  Success: Hot reload adds/removes rows using v2 API with audit logs.

### Group D: Persistence & Metrics (After A)
Dependencies: A1-agno-version-upgrade, A3-db-factory-refresh

**D1-storage-migration-runner**: Download/integrate Agno's `migrate_to_v2.py` (from https://github.com/agno-agi/agno/blob/main/libs/agno/scripts/migrate_to_v2.py). @scripts/ [context], @lib/utils/startup_orchestration.py [context] Creates: `scripts/agno_db_migrate_v2.py` wrapper with DB creds, logging (pre/post row counts for sessions/memories/metrics/knowledge/evals), idempotent dry-run/full modes. Exports: CLI tool (`uv run python scripts/agno_db_migrate_v2.py --dry-run`). Success: Run on staging; logs show no data loss (e.g., sessions preserved, metrics converted); old tables intact for rollback.

**D2-metrics-schema-shift**: Update bridges for v2 fields (`time`→`duration`, `prompt_tokens`→`input_tokens`, etc.), nest providers in `provider_metrics`, add `additional_metrics` for customs; handle v1→v2 parsing (post-script). @lib/metrics/agno_metrics_bridge.py [context], @lib/metrics/async_metrics_service.py [context] Modifies: Mappings, add compat layer for legacy sessions. Exports: Dict with v2 schema. Success: Tests parse/migrate sample v1 data; no key errors.

**D3-migration-script-adapter**: Validate upstream `migrate_to_v2.py` against Automagik schemas  @scripts/agno_db_migrate_v2.py [context], @lib/services/version_sync_service.py [context]  Modifies: Adds idempotent runner, captures before/after table snapshots, ensures metrics field rename coverage  Exports: Repeatable CLI tool with logging evidence  Success: Dry-run diff included in wish evidence; production run appended to Death Testament.

**D3-settings-surface**: Extend settings for configurable table names & feature toggles  @lib/config/settings.py [context], @lib/config/server_config.py [context]  Modifies: Settings models to expose new Db table parameters  Exports: `Settings` with defaults aligning to migration script  Success: Settings load with no regression; env overrides documented.

### Group E: Agent Assets (After B, C, D)
Dependencies: C1-knowledge-core-rewrite, D2-metrics-schema-shift

**E1-agent-definition-refresh**: Update all agent modules to use `dependencies` and `enable_user_memories`  @ai/agents/*/agent.py [context], @lib/utils/proxy_agents.py [context]  Modifies: Agent constructors, streaming consumption  Exports: Agents compatible with v2 runtime  Success: Sample agent runs return `RunOutput`; coverage tests pass.

**E2-team-behaviour-flags**: Configure teams with new coordination attributes  @ai/teams/registry.py [context], @ai/teams/*/team.py [context]  Modifies: Remove `mode`, add `respond_directly` etc.  Exports: Teams orchestrating with new semantics  Success: Team integration tests confirm delegation behaviour.

**E3-workflow-upgrade**: Full refactor per workflows v2 guide (stateless, `agno.workflows` imports, `input_schema`, no `monitoring`; add `store_events`/`events_to_skip` if needed). @ai/workflows/registry.py [context], @ai/workflows/template-workflow/workflow.py [context] Modifies: Primitives, add websocket if applicable (defer runtime). Exports: v2 objects. Success: Tests run end-to-end; no v1 deprecations.

**E4-config-schema-alignment**: Revise agent/team YAML + fixture expectations to remove v1 keys  @ai/agents/*/config.yaml [context], @tests/ai/agents/template-agent/test_template_agent.py [context], @tests/lib/utils/test_proxy_agents.py [context]  Modifies: Replace `storage`/`context` with `db`/`dependencies`, adjust tests to assert unified Db usage  Exports: Configs aligned with v2 loader semantics, regression suite green  Success: Updated tests confirm `db` + `dependencies`; no assertions reference `.storage`.

### Group F: Testing & Docs (After E)
Dependencies: All previous groups

**F1-test-suite-refresh**: Update tests and fixtures for v2 semantics  @tests/* [context]  Modifies: Assertions for new metric keys, agent outputs, knowledge loaders  Exports: Comprehensive tests covering migration paths  Success: `uv run pytest` passes across targeted suites.

**F2-documentation-pass**: Revise README + runbooks with Agno v2 instructions  @README.md [context], @docs/ [context]  Modifies: Usage guides, troubleshooting referencing AgentOS, Db tables  Exports: Docs aligned with new flow  Success: Docs lint + manual review confirm clarity.

**F3-validation-evidence**: Capture migration artefacts and Death Testaments  @genie/wishes/agno-v2-migration-wish.md [context], @genie/reports/ [context]  Modifies: Wish status, append evidence after execution  Exports: Final status + references  Success: Wish marked APPROVED → COMPLETED with linked reports.

## Implementation Examples

### Agent + Db Construction
```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url=settings.database_url, session_table="hive_sessions")
agent = Agent(
    name="support_bridge",
    instructions="Answer using latest policies.",
    dependencies={"policy_loader": load_policy_suite},
    db=db,
    enable_user_memories=True,
)
```




### Knowledge Content Management
```python
from agno.knowledge import Knowledge

knowledge = Knowledge(vector_db=db.vector_db, contents_db=db.contents_db)
knowledge.add_content(
    content_path="lib/knowledge/data/knowledge_rag.csv",
    metadata={"source": "csv", "ingestion": "row_based"},
)
```

## Testing Protocol
```bash\n# Dependency + import sanity (pinned to 2.0.8)\nuv run python -c "import agno, sys; assert agno.__version__ == '2.0.8'"\n\n# DB migration evidence\nuv run python scripts/agno_db_migrate_v2.py --dry-run  # Log pre/post counts\n\n# Core libraries\nuv run pytest tests/lib/test_proxy_agents.py tests/lib/test_proxy_teams.py -q\nuv run pytest tests/lib/memory/test_memory_factory.py tests/lib/knowledge/test_row_based_csv_knowledge.py\n\n# Runtime + API\nuv run pytest tests/api -q\nuv run pytest tests/integration/knowledge -q\n\n# Agents/teams/workflows (added for v2 coverage)\nuv run pytest tests/ai/ -q\nuv run pytest tests/integration/ -q  # Broad integration incl. workflows\n\n# Static analysis\nuv run ruff check lib/ api/ ai/\nuv run mypy lib/knowledge lib/memory lib/utils\n\n# Additional v2 static (metrics/versioning)\nuv run ruff check lib/metrics lib/versioning\nuv run mypy lib/metrics lib/versioning\n\n# Smoke (no serve)\nuv run python -c "from lib.utils.agno_proxy import create_sample_agent; agent = create_sample_agent(); assert 'dependencies' in agent.__init__.__code__.co_varnames"\n```

## Validation Checklist
- [ ] Agno v2 dependency recorded via `uv` tooling (no manual pyproject edits).
- [ ] Memory + knowledge factories instantiate v2 Db/Knowledge classes without legacy imports.

- [ ] Metrics bridge remaps fields and persists provider metrics.
- [ ] Database migration script executed with logs stored in `genie/reports/`.
- [ ] Table row counts logged and verified consistent pre/post migration.
- [ ] Test suites and lint checks pass on v2 stack (`uv run pytest`).
- [ ] Proxy layer smoke test confirms `dependencies` + unified `db` wiring across agents/teams/workflows.
- [ ] YAML/test updates merged; no fixtures reference deprecated keys or `.storage` attribute.
- [ ] Sample agent/team/workflow instantiate with v2 (dependencies/db, no context/storage).
- [ ] Knowledge base query returns valid results post-migration.
- [ ] Health endpoint responds correctly before server restart.
- [ ] Wish status updated with evidence once migration validated.

## Agno v2 Migration Guide Reference\nSee attached `genie/wishes/agno-v2-migration-guide.md` (full copy from https://docs.agno.com/how-to/v2-migration) for detailed before/after examples.\n\n## Human Review Options\n1. APPROVE – Bulletproof for v2 core migration; delegate to forge/hive-coder.\n2. REVISE – Add evals handling if needed (codebase scan shows none).\n3. EXECUTE PHASE 1 – Run DB script + dep pin now.
