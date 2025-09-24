# Death Testament – Forge Task Review: Agno v2 Migration (Knowledge/Runtime)

## Scope Reviewed
- Wish: `genie/wishes/agno-v2-migration-wish.md` (Approved; pinned to Agno 2.0.8). 
- Branch: `forge-review-thi-9384` (HEAD 575f83f) plus preceding related commits 715bc7c, 709c427.
- Files touched relevant to this task: knowledge stack (`lib/knowledge/*`), proxies/storage (`lib/utils/agno_storage_utils.py`, `proxy_*`), runtime startup (`lib/utils/startup_*`, `cli/commands/service.py`), tests under `tests/integration/knowledge`, `tests/lib/utils`, `tests/cli`.
- Implementer Death Testaments loaded:
  - @genie/reports/hive-coder-agno-v2-foundation-202509232259.md
  - @genie/reports/hive-coder-agno-v2-runtime-surfaces-202509240010.md
  - @genie/reports/hive-coder-knowledge-v2-migration-202509240106.md

## Acceptance Criteria Traceability
- A1 – agno v2 pin via uv: PASS
  - Evidence: `git diff` shows `pyproject.toml` change to `agno==2.0.8`; `uv run python -c 'import agno; print(agno.__version__)'` → 2.0.8.
- A2/A4 – proxies/storage emit v2 `db` + `dependencies`, drop legacy `context`/`storage` kwargs: PARTIAL
  - Code: `lib/utils/agno_storage_utils.py`, `proxy_agents.py`, `proxy_teams.py`, `proxy_workflows.py` updated.
  - Gap: Workflow proxy import path exists, but test `tests/lib/utils/test_agno_proxy.py` fails due to missing `lib.utils.proxy_workflows` attribute resolution during patching. Needs module availability or import exposure.
- A3 – Db factory refresh: PARTIAL
  - `lib/memory/memory_factory.py` updated; some tests green, but earlier logs from related branches showed NameError/legacy types; current branch passes memory/proxy tests except the workflow proxy issue.
- C1/C2/C3 – Knowledge v2 migration: HOLD
  - Code: `RowBasedCSVKnowledgeBase` wraps Agno v2 `Knowledge`; factory builds `PgVector` + optional `PostgresDb(contents_db)`; repository and datasource updated.
  - Tests: 10 FAILURES in `tests/integration/knowledge/*` on this branch.
    - Missing debug logging assertions (business unit/category summary).
    - PermissionError handling not preventing document load.
    - `upsert` path not invoking vector `upsert` (content removal without contents_db leads to no-op, but tests expect vector upsert behavior or logger filter use).
    - Logger filter for batch suppression not applied.
- D1/D3 – Migration script adapter: NOT FOUND
  - No `scripts/agno_db_migrate_v2.py` present; only testing scripts found in `scripts/`.
- D2 – Metrics schema shift: INCOMPLETE
  - `lib/metrics/agno_metrics_bridge.py` exists but grep found no `provider_metrics` usage; mapping for token fields not verified by tests on this run.
- E1/E2 – Agent/team v2 usage: PARTIAL
  - Proxies updated; many proxy tests pass. One workflow proxy failure remains.
- E4/F1 – Tests refreshed and passing: PARTIAL
  - Many suites pass (CLI, proxies mostly). Knowledge integration suite fails; overall suite not fully green.

## Evidence – Commands Executed
```bash
# Version pin verification
uv run python -c "import agno, sys; print(agno.__version__)"  # 2.0.8

# Diffs and scope
git diff --name-status origin/dev...HEAD

# Targeted tests
uv run pytest -q \
  tests/lib/knowledge/datasources/test_row_based_csv.py \
  tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py \
  tests/integration/knowledge/test_row_based_csv_knowledge_coverage.py \
  tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py
# → 10 failed, 96 passed

uv run pytest -q tests/lib/utils/test_proxy_agents.py tests/lib/utils/test_proxy_teams.py tests/lib/memory/test_memory_factory.py tests/lib/utils/test_agno_storage_utils.py tests/lib/utils/test_agno_proxy.py
# → 1 failed (workflow proxy import resolution), 147 passed

uv run pytest -q tests/cli/commands/test_service.py
# → 11 passed (trailing KeyboardInterrupt noise on teardown noted in DT)
```

## Risk Assessment
- Knowledge ingestion semantics deviate from test expectations (logging, error handling, upsert/filter behavior). High risk for production ingestion correctness.
- Missing migration runner (`scripts/agno_db_migrate_v2.py`) blocks D1/D3 acceptance and data migration evidence capture.
- Metrics v2 schema mapping not evidenced; potential telemetry regressions.
- Workflow proxy availability issue breaks API expected by tests (module import exposure).

## Verdict
HOLD – Do not approve. Core knowledge v2 acceptance criteria and migration tooling are not met; one proxy failure persists; metrics evidence missing.

## Required Remediation (delegate to hive-coder/hive-tests)
1) Knowledge v2 test fixes (hive-coder + hive-tests)
   - Emit category/business-unit debug logs as asserted by tests.
   - Handle PermissionError by returning zero documents.
   - Implement proper `upsert` semantics: when `upsert=True`, call vector `upsert` or remove existing by signature and re-add; ensure log filter for agno batch messages is applied and removed.
   - Ensure CSV reader resource cleanup signals expected by tests.
2) Add migration wrapper
   - Create `scripts/agno_db_migrate_v2.py` that invokes upstream `migrate_to_v2.py` with DB creds, dry-run/full modes, pre/post row counts; log to `genie/reports/`.
3) Metrics v2 bridge
   - Update `lib/metrics/agno_metrics_bridge.py` to map `prompt_tokens`→`input_tokens`, `completion_tokens`→`output_tokens`; nest provider metrics under `provider_metrics`; add tests.
4) Workflow proxy import
   - Ensure `lib/utils/proxy_workflows.py` is imported in `lib/utils/__init__.py` or adjust tests/mocks to import path; fix failing `test_get_agno_workflow_proxy_singleton_pattern`.
5) Re-run evidence
   - Provide `uv run pytest` outputs for knowledge/proxy/metrics suites and attach logs; update wish validation checklist items.

## Notes for Genie
- Align remediation with Wish Groups: C1/C2/C3, D1/D2/D3, B2 minor for workflow proxy exposure.
- Maintain uv-only tooling; avoid direct `pyproject.toml` edits going forward (pin already present via prior commit).
