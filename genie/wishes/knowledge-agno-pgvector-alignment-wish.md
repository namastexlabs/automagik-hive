# 🧞 Knowledge Agno Pgvector Alignment WISH

**Status:** READY_FOR_REVIEW

## Executive Summary
Reconcile the Agno v2 knowledge migration with the existing pgvector-backed incremental pipeline so row-based loaders, hot reload, and repositories operate on a single, test-backed contract.

## Current State Analysis
**What exists:** On `dev`, `RowBasedCSVKnowledgeBase` extends Agno's document knowledge with pgvector, `SmartIncrementalLoader` drives incremental loads through `_HashManager`, and `CSVHotReloadManager` lives under `lib/knowledge/datasources/`, all validated by 300+ knowledge tests.
**Gap identified:** The `wish/agno-v2-migration` branch introduces Agno v2 `Knowledge` instances, contents DB wiring, and new hash logic but breaks legacy contracts (e.g., `hash_row(row)` ➜ `hash_row(idx, row)`), eliminates SmartIncrementalLoader helper APIs the tests patch, and passes `contents_db` through constructors that mocks reject—resulting in 160+ unit failures and hot-reload regressions.
**Solution approach:** Implement adapters that let the new Agno v2 knowledge objects coexist with the pgvector pipeline: reintroduce the legacy SmartIncrementalLoader interface while delegating to the new primitives, stage `contents_db` assignments post-construction, and centralize hashing/signature helpers so both repositories and tests speak the same API.

## Change Isolation Strategy
- **Isolation principle:** Contain changes inside `lib/knowledge/**` and dependent services, leaving agents, proxies, and storage helpers untouched.
- **Extension pattern:** Wrap Agno v2 constructs with compatibility layers instead of rewriting callers; keep pgvector wiring in dedicated factory hooks.
- **Stability assurance:** Re-run the existing knowledge suites, maintaining CSV schemas, pgvector table names, and incremental loading semantics.

## Success Criteria
✅ `uv run pytest tests/lib/knowledge -q` passes with SmartIncrementalLoader, datasource, and repository suites restored.
✅ `uv run pytest tests/integration/knowledge -q` passes, including hot-reload constructor expectations and row-based knowledge coverage.
✅ `RowBasedCSVKnowledgeBase` exposes stable `build_document_from_row`/`get_signature` helpers backed by Agno `Knowledge` plus pgvector, with optional contents DB hooked in without API drift.
✅ Smart incremental loads remove/update knowledge rows in pgvector and the new contents DB consistently, logging change analysis without runtime warnings.

## Never Do (Protection Boundaries)
❌ Rename or drop the `agno.knowledge_base` pgvector table; migrations must preserve existing data.
❌ Remove incremental hashing or fall back to full recreates without documenting evidence.
❌ Bypass `KnowledgeRepository` or its audit logging when mutating knowledge records.

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
├── lib/knowledge/           # Knowledge loaders, repositories, datasources, smart loader
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
- Knowledge adapters: `{Component}Adapter` or `{Component}Bridge` in `lib/knowledge/`.
- Helper functions: `get_{thing}_signature`, `build_{thing}_document` for shared hashing APIs.
- Pgvector tables/fields: retain existing `knowledge_base` identifiers; new metadata columns follow snake_case.
- Tests: `tests/lib/knowledge/test_{topic}_*.py` mirroring the component under test.

## Task Decomposition

### Dependency Graph
```
A[Foundation] ---> B[Runtime Surfaces]
A ---> C[Knowledge Services]
B & C ---> D[Integration]
D ---> E[Testing & Docs]
```

### Group A: Foundation (Parallel Tasks)
Dependencies: None | Execute simultaneously

**A1-knowledge-signature-bridge**: `@lib/knowledge/row_based_csv_knowledge.py`, `@lib/knowledge/services/hash_manager.py`  
Modifies: Restore `RowBasedCSVKnowledgeBase` public helpers (`build_document_from_row`, `get_signature`, `add_document`) that wrap Agno v2 `Knowledge` while keeping pgvector-friendly Document structures; share signature logic with service helpers.  
Exports: Stable document/signature API consumed by loaders, repositories, and tests.  
Success: `tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py` and `tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py` pass without monkeypatch updates.

**A2-hash-manager-bwc**: `@lib/knowledge/smart_incremental_loader.py`, `@lib/knowledge/datasources/csv_datasource.py`, `@lib/knowledge/services/hash_manager.py`  
Modifies: Reintroduce `_HashManager.hash_row(row)` and legacy SmartIncrementalLoader helper methods `_get_csv_rows_with_hashes`, `_update_row_hash`, `_full_reload`, etc., delegating internally to the new knowledge-aware logic; guard optional knowledge usage without breaking call signatures.  
Exports: Backward-compatible SmartIncrementalLoader facade with Agno v2 internals.  
Success: `tests/lib/knowledge/datasources/test_csv_datasource.py` and the full `tests/lib/knowledge/test_smart_incremental_loader.py` suite succeed.

**A3-factory-repository-sync**: `@lib/knowledge/factories/knowledge_factory.py`, `@lib/knowledge/knowledge_factory.py`, `@lib/knowledge/repositories/knowledge_repository.py`  
Modifies: Ensure the factory returns a pgvector-backed knowledge instance with optional contents DB assigned post-construction, maintain thread-safe singleton semantics, and keep repository removal/update flows synchronized with Agno `Knowledge.remove_content_by_id` while tolerating contents DB absence.  
Exports: Factory and repository ready for downstream hot-reload and services.  
Success: `tests/lib/knowledge/test_knowledge_factory_real_coverage.py` and `tests/lib/knowledge/test_hash_fix.py` pass with Agno v2 wiring enabled.

### Group B: Runtime Surfaces (After A)
Dependencies: A1-knowledge-signature-bridge, A2-hash-manager-bwc, A3-factory-repository-sync

**B1-hot-reload-contract**: `@lib/knowledge/datasources/csv_hot_reload.py`, `@lib/knowledge/csv_hot_reload.py`  
Modifies: Keep constructor expectations (`RowBasedCSVKnowledgeBase(csv_path, vector_db)`) while injecting contents DB post-instantiation, invoke SmartIncrementalLoader with the restored API, and retain debounce & watcher behaviour.  
Exports: Hot reload manager that satisfies mock expectations and reuses the unified knowledge instance.  
Success: `tests/integration/knowledge/test_csv_hot_reload_comprehensive.py` + `_coverage.py` succeed with Agno v2 toggle on.

**B2-config-filter-compat**: `@lib/knowledge/config_aware_filter.py`, `@lib/knowledge/filters/business_unit_filter.py`  
Modifies: Route all config loads through patchable module-level helpers, surface business-unit metadata derived from the new signatures, and log diagnostics without duplicating configuration state.  
Exports: Filters that tests can patch and that leverage the updated knowledge metadata.  
Success: `tests/lib/knowledge/test_business_unit_filter.py` and related coverage suites pass.

**B3-services-alignment**: `@lib/knowledge/services/change_analyzer.py`, `@lib/knowledge/services/hash_manager.py`  
Modifies: Delegate to the new SmartIncrementalLoader facade while keeping public function signatures unchanged; ensure change analyzer reports account for contents DB removals.  
Exports: Service helpers compatible with CLI/QA tooling.  
Success: `tests/lib/knowledge/services/test_change_analyzer.py` and `tests/lib/knowledge/services/test_hash_manager.py` remain green under Agno v2.

### Group C: Knowledge Services (After A)
Dependencies: A1-knowledge-signature-bridge, A3-factory-repository-sync

**C1-status-snapshots**: `@lib/knowledge/services/change_analyzer.py`, `@lib/knowledge/smart_incremental_loader.py`  
Modifies: Provide structured status payloads (`new_rows`, `potential_removals`, contents DB warnings) used by observability workflows, ensuring Agno v2 metadata is present.  
Exports: Consistent status dictionaries for downstream dashboards/tests.  
Success: `tests/lib/knowledge/test_change_analyzer.py::TestChangeAnalyzerStatus` validations pass.

**C2-maintenance-hooks**: `@tests/integration/knowledge/test_comprehensive_knowledge.py`, `@lib/knowledge/factories/knowledge_factory.py`  
Modifies: Ensure maintenance workflows (full reload, forced embeddings) exercise the new adapters without manual mocks, updating fixtures where necessary.  
Exports: Integration paths that can trigger forced reloads safely.  
Success: Comprehensive knowledge integration tests assert regen + logging with Agno v2 constructs.

**C3-observability-logging**: `@lib/logging/__init__.py`, `@lib/knowledge/row_based_csv_knowledge.py` (logging hooks)  
Modifies: Normalize log keys for knowledge load/update events so QA scripts remain compatible and new Agno instrumentation is captured.  
Exports: Structured logs reused by QA pipelines.  
Success: Existing logging assertions in knowledge integration suites remain valid with additional fields documented.

### Group D: Integration (After B & C)
Dependencies: All tasks in B and relevant C tasks

**D1-smart-loader-wiring**: `@lib/knowledge/factories/knowledge_factory.py`, `@lib/knowledge/datasources/csv_hot_reload.py`  
Modifies: Ensure the factory, hot reload manager, and SmartIncrementalLoader share a single knowledge context (vector_db + optional contents_db), with dependency injection ready for CLI workers.  
Exports: Unified wiring diagram for knowledge refresh flows.  
Success: Manual smoke (`SmartIncrementalLoader(csv_path).smart_load()`) produces `strategy` summaries without errors.

**D2-rollback-safety**: `@lib/knowledge/repositories/knowledge_repository.py`, `@lib/knowledge/smart_incremental_loader.py`  
Modifies: Guard database operations with transactional removal + Knowledge cleanup, capturing audit logs and allowing safe dry runs.  
Exports: Rollback-aware incremental updates.  
Success: Repository tests confirm removal/update behaviours and log assertions.

**D3-configuration-parity**: `@lib/utils/version_factory.py`, `@lib/knowledge/config_aware_filter.py`  
Modifies: Ensure global config loader exposes both legacy and Agno v2 keys (hash columns, contents_db toggles) so tests referencing YAML continue to pass.  
Exports: Config surface consumed by loaders and filters.  
Success: Config-driven tests in `tests/lib/knowledge/test_knowledge_factory_coverage_boost.py` validate expected keys.

### Group E: Testing & Docs (After D)
Dependencies: Complete integration

**E1-test-suite-refresh**: `@tests/lib/knowledge/`, `@tests/integration/knowledge/`  
Creates/Modifies: Adjust fixtures/mocks to the restored interfaces, add regression tests for contents DB hand-off, and document assumptions inside test helpers.  
Success: Full knowledge suites pass under Agno v2 with pgvector enabled.

**E2-static-analysis**: `@pyproject.toml` (indirect via uv), `@lib/knowledge/**`  
Modifies: Run `uv run ruff check lib/knowledge` and `uv run mypy lib/knowledge` fixes to satisfy linters/mypy for new adapters without altering pyproject directly.  
Success: Ruff + mypy exit cleanly for knowledge modules.

**E3-wish-evidence**: `@genie/wishes/knowledge-agno-pgvector-alignment-wish.md`, `@genie/reports/`  
Modifies: Append validation evidence, commands, and Death Testament references once remediation completes.  
Success: Wish advanced to COMPLETED with linked reports and test logs.

## Implementation Examples

### Hash Manager Compatibility Hook
```python
# lib/knowledge/smart_incremental_loader.py
class _HashManager:
    def hash_row(self, row):
        if self.knowledge_base:
            document = self.knowledge_base.build_document_from_row(row.name, row.to_dict())
            if not document:
                return ""
            return self.knowledge_base.get_signature(document).content_hash
        return fallback_hash(row, self.hash_columns)
```

### Contents DB Hand-off
```python
# lib/knowledge/datasources/csv_hot_reload.py
kb = RowBasedCSVKnowledgeBase(csv_path=str(self.csv_path), vector_db=vector_db)
if contents_db is not None and getattr(kb, "knowledge", None):
    kb.knowledge.contents_db = contents_db
    logger.debug("Activated contents DB", table=contents_db.session_table)
```

### Repository Removal Coordination
```python
# lib/knowledge/repositories/knowledge_repository.py
removed_hashes = [row[0] for row in result.fetchall() if row[0]]
if removed_hashes and self.knowledge:
    for content_hash in removed_hashes:
        content_id = generate_id(content_hash)
        try:
            self.knowledge.remove_content_by_id(content_id)
        except ValueError:
            logger.debug("Contents DB unavailable during removal", hash=content_hash)
```

## Testing Protocol
```bash
# Knowledge unit suites
uv run pytest tests/lib/knowledge -q

# Integration + hot reload flows
uv run pytest tests/integration/knowledge -q

# Lint & typing for knowledge modules
uv run ruff check lib/knowledge
uv run mypy lib/knowledge
```

## Validation Checklist
- [ ] SmartIncrementalLoader helper methods reachable by legacy tests
- [ ] CSV hot reload instantiates knowledge base without constructor drift
- [ ] pgvector + contents DB runbooks documented with logging evidence
- [ ] Ruff + mypy clean for lib/knowledge modules
- [ ] Wish status updated with command outputs and linked Death Testaments

## Group E Validation Evidence (2025-09-25)

### Commands executed
```bash
uv run pytest tests/lib/knowledge -q
uv run pytest tests/integration/knowledge -q
uv run ruff check lib/knowledge
uv run mypy lib/knowledge
```

### Outcomes
- Unit tests (tests/lib/knowledge): 17 failed, 405 passed, 2 skipped
- Integration tests (tests/integration/knowledge): 180 passed, 2 warnings
- Ruff (lib/knowledge): 105 issues (67 auto-fixable)
- Mypy (lib/knowledge): 62 errors across 12 files

See detailed logs, failing test list, and representative diagnostics in:
- Death Testament: @genie/reports/hive-tests-knowledge-agno-pgvector-alignment-wish-group-e-20250925T1300Z.md

Status remains READY_FOR_REVIEW pending remediation decisions; evidence captured and linked.
