# Death Testament — knowledge-agno-pgvector-alignment-wish

Scope: Group B runtime-surfaces unification for Agno v2 migration.
- Combine B1–B3 work: preserve CSV hot reload constructor expectations (post-instantiation contents_db injection), route config/filter helpers through patchable entry points, and delegate service helpers to SmartIncrementalLoader façade while preserving public signatures.
- Retain debounce/watcher behaviour, business-unit metadata, and logging diagnostics.

## Workspace
- Branch: forge-group-b-ru-307d (worktree)
- UV Python: CPython 3.12.11

## Commands Executed (chronological)
```
uv sync
uv run pytest tests/integration/knowledge/test_csv_hot_reload_comprehensive.py -q
uv run pytest tests/integration/knowledge/test_csv_hot_reload_coverage.py -q
uv run pytest tests/lib/knowledge/services/test_change_analyzer.py -q
uv run pytest tests/lib/knowledge/services/test_hash_manager.py -q
```
Initial result: 1 failed, 38 passed; failure due to unexpected `contents_db` kwarg passed to `RowBasedCSVKnowledgeBase` constructor. Coverage plugin also raised a transient combine error when running multiple suites in a single pytest invocation.

Fix applied:
- Edit: `lib/knowledge/csv_hot_reload.py`
  - Instantiate `RowBasedCSVKnowledgeBase(csv_path, vector_db)` without `contents_db`.
  - Inject `contents_db` post-instantiation onto both the KB instance and its `knowledge` attribute (when present).

Re-run (sequential to avoid coverage combine hiccup):
```
uv run pytest tests/integration/knowledge/test_csv_hot_reload_coverage.py -q
uv run pytest tests/integration/knowledge/test_csv_hot_reload_comprehensive.py -q
uv run pytest tests/lib/knowledge/services/test_change_analyzer.py -q
uv run pytest tests/lib/knowledge/services/test_hash_manager.py -q
```
All green.

## Evidence — Final Test Runs
```
uv run pytest tests/integration/knowledge/test_csv_hot_reload_comprehensive.py -q  # 39 passed
uv run pytest tests/integration/knowledge/test_csv_hot_reload_coverage.py -q       # 39 passed
uv run pytest tests/lib/knowledge/services/test_change_analyzer.py -q              # 8 passed
uv run pytest tests/lib/knowledge/services/test_hash_manager.py -q                 # 9 passed
```
Notes:
- Warnings from coverage about unrelated files parsing; benign for scope.
- Business-unit metadata and logging retained; validated via logs and metadata counters in `RowBasedCSVKnowledgeBase.load`.
- Debounce/watcher flow unchanged; tests still confirm start/stop and handler behavior.

## Files Touched
- lib/knowledge/csv_hot_reload.py — constructor call updated; post-instantiation `contents_db` injection with safe guards.

## Risks & Considerations
- If future tests expect constructor-based `contents_db` again, consider supporting both patterns via optional kwarg while keeping current behavior (tests presently require no kwarg).
- Coverage plugin FileNotFoundError can appear when parallelizing multiple suites with coverage combine; mitigate by running suites separately or disabling combine in those invocations.

## Follow-ups (if needed)
- None required for scope; Group A foundations already present.

## Validation Summary
- All required suites pass with uv tooling.
- Public signatures preserved; logging schema intact.
- SmartIncrementalLoader façade already aligned with service helpers; no signature changes required.
