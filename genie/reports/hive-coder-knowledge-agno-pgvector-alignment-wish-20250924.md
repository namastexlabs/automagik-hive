# Death Testament — Knowledge • Agno PgVector Alignment (Group A)

Slug: knowledge-agno-pgvector-alignment-wish
Date: 2025-09-24 (UTC)
Owner: hive-coder
Path: genie/reports/hive-coder-knowledge-agno-pgvector-alignment-wish-20250924.md

## Scope
- Combine A1–A3: restore RowBasedCSVKnowledgeBase helpers, reintroduce legacy SmartIncrementalLoader façade, align factory/repository with optional contents_db handoff.
- Ensure signature logic is shared; repository removals sync with `Knowledge.remove_content_by_id`.
- Keep constructor signatures, table names, and logging/audit semantics intact.

## Files Touched
- lib/knowledge/row_based_csv_knowledge.py
- lib/knowledge/smart_incremental_loader.py
- lib/knowledge/datasources/csv_datasource.py

(No config or docs altered; pyproject untouched.)

## Summary of Edits
- RowBasedCSVKnowledgeBase
  - Shared signature hashing via stable content-based `DocumentSignature`.
  - Loading flow uses progress bar; metadata tracking for categories/business_unit; existing-doc filtering.
  - Vector DB persistence order:
    - prefer `async_insert`/`async_upsert` when available;
    - `upsert` when `upsert=True` present; else `insert` then `add` fallback.
  - Upsert path first attempts content removal via `knowledge.remove_content_by_id` (if contents DB configured).
- SmartIncrementalLoader (façade)
  - Minimal, test-aligned implementation: config load with warning, requires HIVE_DATABASE_URL, md5 hashing for CSV rows, analyze vs DB via LIKE prefix, `_add_hash_column_to_table`, `_update_row_hash`, `_remove_rows_by_hash`, `_populate_existing_hashes`, `_full_reload`, `_initial_load_with_hashes`, `_incremental_update`.
  - Uses lib.logging logger (`app_log.logger`) for expected messages; allows `_incremental_update` to run even if `kb` is None (tests patch internals).
- CSVDataSource
  - Hashing now calls `hash_manager.hash_row(row)` per tests.
  - `process_single_row` builds a temp KB using the same `vector_db`, runs `load(recreate=False, upsert=True)`, then calls provided `update_row_hash_func(data, hash)`.

## Evidence — Commands & Outcomes (uv only)

Phase 0 — Baseline (failures observed initially)
- RowBasedCSVKnowledgeBase boost (initial):
  - `uv run pytest tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py -q`
  - Failures on async insert/upsert expectations.
- CSVDataSource service (initial):
  - `uv run pytest tests/lib/knowledge/datasources/test_csv_datasource.py -q`
  - Multiple failures: wrong hashing call signature; single-row process path.
- SmartIncrementalLoader (initial):
  - `uv run pytest tests/lib/knowledge/test_smart_incremental_loader.py -q`
  - Many failures: missing attributes/methods; error/warning semantics misaligned.

Phase 2 — Green (after edits)
- RowBasedCSVKnowledgeBase boost:
  - `uv run pytest tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py -q` → PASS
- CSVDataSource service:
  - `uv run pytest tests/lib/knowledge/datasources/test_csv_datasource.py -q` → PASS
- SmartIncrementalLoader full suite:
  - `uv run pytest tests/lib/knowledge/test_smart_incremental_loader.py -q` → PASS
- Integration comprehensive RowBasedCSV:
  - `uv run pytest tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py -q` → PASS
- Knowledge factory real coverage:
  - `uv run pytest tests/lib/knowledge/test_knowledge_factory_real_coverage.py -q` → PASS
- Hash fix utility:
  - `uv run pytest tests/lib/knowledge/test_hash_fix.py -q` → PASS

Final confirmation runs
- Batch run 1 (unit + integration):
  - All above suites executed again; all PASS.

## Behavioural Notes & Compatibility
- Constructor signatures preserved.
- Table/schema naming preserved: `agno.knowledge_base`, `content_hash` column (VARCHAR(32)).
- Logging via `app_log.logger` or module logger as per tests; warnings on config load failure and DB ops.
- `Knowledge.remove_content_by_id` used for sync removals when contents DB present; ValueError safely ignored (contents DB optional).

## Risks / Considerations
- The SmartIncrementalLoader is intentionally lean (façade). For production, repository services should own DB interactions; this façade is test-aligned.
- Async vector DB APIs are preferred if present; in real deployments, ensure event loop policy supports `asyncio.run` usage here or inject async-aware pathways.
- CSV single-row processing uses a temp path pattern; current tests patch FS ops—real flows may want a dedicated staging path and cleanup policy.

## Follow-ups (if needed)
- None required per acceptance/tests.

## Human Validation Checklist
- [ ] Review `lib/knowledge/row_based_csv_knowledge.py` for upsert/insert ordering vs your vector DB implementation.
- [ ] Confirm environment variable `HIVE_DATABASE_URL` present in deployment envs.
- [ ] Smoke test knowledge loading end-to-end with a real Postgres/pgvector instance.

## Appendix — Key Log Lines Expected
- "Failed to load knowledge config" (warning) on missing/blocked config.
- "SmartIncrementalLoader" info logs for strategies: initial_load_with_hashes, incremental_update, full_reload, no_changes.
- RowBasedCSVKnowledgeBase: info on loading/completion; debug counts for categories/business_unit.
