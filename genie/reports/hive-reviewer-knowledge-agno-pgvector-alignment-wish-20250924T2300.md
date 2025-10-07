# Death Testament — Forge Task Review • Knowledge • Agno PgVector Alignment (Group A)

Slug: knowledge-agno-pgvector-alignment-wish
Date: 2025-09-24T23:00Z (UTC)
Owner: hive-reviewer
Path: genie/reports/hive-reviewer-knowledge-agno-pgvector-alignment-wish-20250924T2300.md

## Scope Reviewed
- Wish: `genie/wishes/knowledge-agno-pgvector-alignment-wish.md` — Group A foundation tasks A1–A3
- Implementer Death Testament: `genie/reports/hive-coder-knowledge-agno-pgvector-alignment-wish-20250924.md`
- Code files examined:
  - `lib/knowledge/row_based_csv_knowledge.py`
  - `lib/knowledge/smart_incremental_loader.py`
  - `lib/knowledge/datasources/csv_datasource.py`
  - `lib/knowledge/factories/knowledge_factory.py` (context)
  - `lib/knowledge/repositories/knowledge_repository.py` (context)

## Acceptance Criteria Extract (A1–A3)
- A1: Restore RowBasedCSVKnowledgeBase helpers (`build_document_from_row`, `get_signature`, `add_document`); stable signature logic; tests: `tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py`, `tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py` pass.
- A2: Reintroduce legacy SmartIncrementalLoader façade incl. `_HashManager.hash_row(row)` compatibility or knowledge-backed signature; datasource uses `hash_manager.hash_row(row)`; tests: `tests/lib/knowledge/datasources/test_csv_datasource.py`, `tests/lib/knowledge/test_smart_incremental_loader.py` pass.
- A3: Factory and repository sync with optional contents DB; repository removals call `Knowledge.remove_content_by_id`; tests: `tests/lib/knowledge/test_knowledge_factory_real_coverage.py`, `tests/lib/knowledge/test_hash_fix.py` pass.

## Evidence — Commands Executed (uv-only)
```bash
uv run pytest tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py -q      # PASS
uv run pytest tests/lib/knowledge/datasources/test_csv_datasource.py -q                  # PASS
uv run pytest tests/lib/knowledge/test_smart_incremental_loader.py -q                    # PASS (55 passed)
uv run pytest tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py -q  # 1 FAIL, 35 passed
uv run pytest tests/lib/knowledge/test_knowledge_factory_real_coverage.py -q             # PASS
uv run pytest tests/lib/knowledge/test_hash_fix.py -q                                    # PASS
```

Failure detail (integration suite):
- `TestRowBasedCSVVectorOperations::test_load_method_with_upsert` expects `vector_db.upsert` to be called when `upsert=True`. Current implementation prefers `async_insert` even when `upsert=True`, so `upsert` is never invoked, causing assertion failure.

## Findings vs Criteria
- A1: Largely met. Public helpers exist and function; content/signature logic stable. However, integration upsert path behavior diverges: when `upsert=True`, tests expect synchronous `upsert` call, not `async_insert`. This breaks one integration test.
- A2: Met. `_HashManager` in smart loader uses knowledge-backed signature when available; datasource calls `hash_manager.hash_row(row)`; both targeted test suites pass.
- A3: Met for scope evidenced by tests. Factory initializes shared KB; repository coordinates removals via `remove_content_by_id`. Targeted tests pass.

## Risks / Regressions
- Upsert semantics: Using `async_insert` when `upsert=True` may skip intended upsert behavior and conflicts with test contract. Potential drift under real PgVector implementations expecting `upsert` to maintain hash uniqueness.
- Minor: Preference order for async methods may surprise deployments lacking event loop policy.

## Remediation Required (HOLD)
- Edit `lib/knowledge/row_based_csv_knowledge.py` `_add_document` to honor `upsert=True`:
  - Preferred order when upsert=True: `async_upsert` → `upsert` → (fallback) `async_insert`/`insert`/`add`.
  - When upsert=False: keep current insert-first order.
- Re-run `uv run pytest tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py -q` and full Group A tests.

## Verdict
- HOLD — Group A nearly complete but fails one integration assertion tied to acceptance criteria. Require the upsert path fix before PASS.

## Follow-up Tasks for Genie
- Delegate to hive-coder: "Honor upsert flag in `RowBasedCSVKnowledgeBase._add_document` by preferring upsert methods; maintain existing logs/filters. Ensure integration test passes."
- Delegate to hive-tests (optional): Add assertion in unit tests to lock the upsert preference when `upsert=True`.

## Artifacts
- Implementer DT: `@genie/reports/hive-coder-knowledge-agno-pgvector-alignment-wish-20250924.md`
- Reviewer DT: `@genie/reports/hive-reviewer-knowledge-agno-pgvector-alignment-wish-20250924T2300.md`
