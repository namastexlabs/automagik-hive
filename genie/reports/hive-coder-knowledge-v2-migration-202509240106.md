# Death Testament – Knowledge v2 Migration

## Scope & Changes
- Reimplemented `RowBasedCSVKnowledgeBase` to wrap Agno v2 `Knowledge`, compute stable document signatures, and coordinate vector/content DB operations.
- Updated knowledge factory to provision Postgres contents DB (with graceful fallback) and align embedder imports with the new Agno module layout.
- Adjusted repositories, smart loader, and CSV datasource to use the new add/remove APIs, propagate knowledge context, and streamline incremental updates.
- Added backward-compatibility shim `lib/knowledge/csv_hot_reload.py` for legacy import paths.
- Refreshed tests targeting CSV knowledge to accommodate async insertion semantics and new metadata handling.

## Validation
- `uv run pytest tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py -q` ✅
- `uv run pytest tests/integration/knowledge -q` ❌ (52 failures across csv-hot-reload + knowledge integration suites)

## Outstanding Risks / Follow-ups
1. Integration suites expect legacy module attributes (e.g., `lib.knowledge.csv_hot_reload.PgVector`) and synchronous vector operations; additional compatibility adapters or test updates required.
2. Multiple integration assertions rely on exact logging side effects; further alignment of logging strategy may be necessary.
3. Need a coordinated plan to reconcile knowledge hash storage with repository expectations for change detection across the entire stack.

## Notes
- Coverage warnings stem from unrelated files (`lib/utils/error_handlers.py`, `lib/utils/fallback_model.py`) that predate this change.
