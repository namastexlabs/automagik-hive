# Death Testament — Hive Reviewer • Group A: Foundation – Review after fix (integration upsert)

Slug: group-a-foundation-review-after-fix
Date: 2025-09-24T23:35Z (UTC)
Owner: hive-reviewer
Path: genie/reports/hive-reviewer-group-a-foundation-review-after-fix-20250924T2335Z.md

## Scope Reviewed
- Wish: @genie/wishes/knowledge-agno-pgvector-alignment-wish.md (Group A focus: A1/A2/A3; integration emphasis on upsert semantics)
- Implementer report: @genie/reports/hive-coder-group-a-foundation-fix-integration-case-upsert-20250924T2019.md
- Code: @lib/knowledge/row_based_csv_knowledge.py (method `_add_document` selection logic)
- Git: Last commit "Group A: Foundation - Fix integration (case upsert)"

## Acceptance Criteria Traced
- When `upsert=True`, honor upsert semantics in `RowBasedCSVKnowledgeBase._add_document`.
- Preferred order under upsert per integration contract: `upsert_available()` → `upsert` (sync) first; otherwise try `async_upsert` if coroutine; then fallback to `upsert` sync; finally to insert flavors.
- When `upsert=False`, keep insert-first ordering (async_insert → insert → add).

## Evidence Collected
- Diff shows `_add_document` implements the required selection order, with defensive logging and fallbacks.
- Targeted tests via uv tooling:
  - `uv run pytest -q tests/integration/knowledge/test_row_based_csv_knowledge_coverage.py::TestRowBasedCSVVectorOperations::test_load_method_with_upsert` → PASS
  - `uv run pytest -q tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py::TestRowBasedCSVVectorOperations::test_load_method_with_upsert` → PASS
  - Full files:
    - `uv run pytest -q tests/integration/knowledge/test_row_based_csv_knowledge_coverage.py` → 36 passed
    - `uv run pytest -q tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py` → 36 passed
- Unit coverage boost suite:
  - `uv run pytest -q tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py` → 1 failed, 18 passed
  - Failure: `TestVectorDatabaseLoading::test_load_method_with_upsert` expects `async_insert` to be awaited when `upsert=True` and `upsert_available=True`. New contract prefers sync `upsert`, so the assertion is incompatible with the updated acceptance criteria.

## Independent Validation Notes
- Running tests strictly via `uv run pytest ...` as required. No forbidden edits or pyproject changes observed. The only code change in the last commit is `lib/knowledge/row_based_csv_knowledge.py` and the coder Death Testament (OK for evidence).
- `grep` confirms tests set `upsert_available=True` in integration suites; code honors that path by calling `vector_db.upsert(...)`.

## Verdict
HOLD (conditional). Integration acceptance is satisfied (both integration upsert tests PASS; full integration files PASS). However, one unit test in `tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py::TestVectorDatabaseLoading::test_load_method_with_upsert` asserts the old behavior (async_insert on upsert), which conflicts with the updated contract. This test must be updated to assert `upsert` when `upsert_available=True`.

## Required Follow-ups
1. Update unit test expectations:
   - In `tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py::TestVectorDatabaseLoading::test_load_method_with_upsert`, change assertions to expect sync `upsert` call when `upsert_available=True`, and zero awaits on `async_upsert`/`async_insert`.
   - Optionally add a separate test case where `upsert_available=False` and `async_upsert` is a coroutine to assert the async upsert path.
2. Add a unit test to lock `upsert_available()` gating behavior (as suggested by implementer report Follow-ups).
3. Re-run: `uv run pytest tests/lib/knowledge -q` and ensure green across knowledge unit suites.

## Risks
- Divergence between integration and unit tests can regress future refactors if not reconciled now.
- Async handling across environments: ensure `async_upsert` detection uses `inspect.iscoroutinefunction` (already implemented) and remains covered.

## Approval Condition
- Switch to PASS once the unit test is corrected to align with the accepted integration contract and knowledge unit suites are green under uv.
