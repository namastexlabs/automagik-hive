# Death Testament – Forge Task Review (Re‑Review): Group C – Knowledge System

## Scope & Artefacts
- Wish: `@genie/wishes/agno-v2-migration-wish.md` — Group C (C1–C3)
- Prior reports: `@genie/reports/hive-reviewer-knowledge-group-c-202509241345.md`, `@genie/reports/hive-reviewer-knowledge-group-c-202509241506.md`, `@genie/reports/hive-coder-knowledge-group-c-remediation-202509241332.md`
- Branch/log context (recent): merge at 2092a07; changed files include:
  - `lib/knowledge/csv_hot_reload.py`, `lib/knowledge/datasources/csv_hot_reload.py`, `lib/knowledge/datasources/csv_datasource.py`, `lib/knowledge/filters/business_unit_filter.py`, `lib/knowledge/row_based_csv_knowledge.py`, `lib/knowledge/smart_incremental_loader.py`, `lib/knowledge/knowledge_factory.py`

## Acceptance Criteria (from Wish)
- C1 – Knowledge core rewrite: Port to `Knowledge`; tests load/query/delete; vectors migrated.
- C2 – Knowledge factory adapt: Factory constructs `Knowledge` with `contents_db`; integration indexes CSV and serves queries.
- C3 – Knowledge watcher sync: CSV hot reload + repositories use new deletion APIs; hot reload adds/removes rows with audit logs.

## Evidence Collected (uv-only)
- Agno version:
  - Command: `uv run python -c "import agno; print(agno.__version__)"`
  - Output: 2.0.8
- Integration (knowledge):
  - Command: `uv run pytest tests/integration/knowledge -q`
  - Result: 2 failed, 178 passed, 2 warnings
  - First failure (constructor call shape): tests expect `RowBasedCSVKnowledgeBase(csv_path, vector_db)`; actual includes unexpected `contents_db` kwarg.
- Unit (knowledge):
  - Command: `uv run pytest tests/lib/knowledge -q`
  - Result: 162 failed, 258 passed, 2 skipped
  - Dominant themes: CSVDataSource hash API mismatch, single-row process path expectations, SmartIncrementalLoader BWC methods missing, BusinessUnitFilter patchability.

## Code Observations (traceability)
- CSV Hot Reload passes `contents_db` to the KB constructor, violating test contract:
```120:131:lib/knowledge/csv_hot_reload.py
        try:
            embedder = self._build_embedder()
            vector_db = self._build_vector_db(db_url, embedder)
            contents_db = self._build_contents_db(db_url)
            self._contents_db = contents_db

            # Pass contents_db to enable remove_content_by_id during reloads
            self.knowledge_base = RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path),
                vector_db=vector_db,
                contents_db=contents_db,
            )
```
- CSVDataSource calls the hash manager with two arguments `(idx, row)`; tests patch the hash manager to accept a single row and read `row.name`:
```28:36:lib/knowledge/datasources/csv_datasource.py
        df = pd.read_csv(self.csv_path)
        rows_with_hashes = []

        for idx, row in df.iterrows():
            row_hash = self.hash_manager.hash_row(idx, row)
            if not row_hash:
                continue
```
- BusinessUnitFilter exposes a local `load_global_knowledge_config` symbol but the constructor uses the indirect import; tests patch the module-local symbol and expect it to be honored at init:
```18:22:lib/knowledge/filters/business_unit_filter.py
    def __init__(self):
        """Initialize with loaded configuration."""
        self.config = config_aware_filter.load_global_knowledge_config()
```
- SmartIncrementalLoader lacks multiple backward-compatibility methods referenced throughout tests (e.g., `_get_csv_rows_with_hashes`, `_get_existing_row_hashes`, `_add_hash_column_to_table`, `_process_single_row`, `_update_row_hash`, `_remove_rows_by_hash`, `_populate_existing_hashes`, `_full_reload`, `get_database_stats`, and parity of `smart_load(force_recreate=...)`). Current implementation routes through repository/datasource abstractions but omits these shim methods, leading to broad unit failures.

## Validation vs Criteria
- C1: Partially satisfied
  - v2 `Knowledge` usage is present and core KB behaviors mostly align; however, integration failures persist due to the hot-reload constructor call shape.
- C2: Partially satisfied
  - Factory wiring exists, but CSVDataSource API drift and single-row processing path regressions block acceptance.
- C3: Not satisfied
  - Watcher deletion semantics intent is correct (use of contents DB), but the constructor call breaks tests; SmartIncrementalLoader lacks BWC methods and CSVDataSource behavior required by tests; audit log expectations are not verifiable while tests are red.

## Required Remediations (blocking)
1) CSV Hot Reload constructor compatibility
   - Do NOT pass `contents_db` in `RowBasedCSVKnowledgeBase(...)` constructor. After instantiation, if a contents DB exists, set it on the underlying knowledge instance instead (guarded) and emit a debug log. This preserves `remove_content_by_id` behavior while satisfying constructor call assertions.

2) CSVDataSource API alignment
   - Change `hash_manager.hash_row(...)` invocation to accept a single row object, not `(idx, row)`. Tests use `lambda row: f"hash_{row.name}"`.
   - Update `process_single_row(...)` to create a temporary `RowBasedCSVKnowledgeBase(csv_path=..., vector_db=kb.vector_db)`, then call `temp_kb.load(recreate=False, upsert=True)` and finally invoke `update_row_hash_func(data, hash, idx)`. Tests patch `RowBasedCSVKnowledgeBase` and assert this sequence.

3) BusinessUnitFilter patchability at init
   - In `__init__`, call the module-local `load_global_knowledge_config()` symbol so tests can patch `lib.knowledge.filters.business_unit_filter.load_global_knowledge_config` effectively.

4) SmartIncrementalLoader backward-compatibility shims
   - Implement delegating methods/properties expected by tests:
     - `table_name` property (from config, default `knowledge_base`).
     - `_get_csv_rows_with_hashes()` → `self.csv_datasource.get_csv_rows_with_hashes()`.
     - `_get_existing_row_hashes()` → `self.repository.get_existing_row_hashes()`.
     - `_add_hash_column_to_table()` → `self.repository.add_hash_column_to_table()`.
     - `_update_row_hash(data, h, idx=None)` → `self.repository.update_row_hash(data, h, self.config, idx)`.
     - `_remove_rows_by_hash(hashes)` → `self.repository.remove_rows_by_hash(hashes)`.
     - `_process_single_row(row, ...)` → use `CSVDataSource.process_single_row` with the temp KB strategy above.
     - `_populate_existing_hashes()` – iterate CSV rows and backfill via repository.
     - `_full_reload()` – call `self.kb.load(recreate=True)` and return a summary dict per tests.
     - `smart_load(force_recreate=False)` – accept and honor the parameter while routing to current strategy.
     - `get_database_stats()` – wrap `analyze_changes()` and shape keys as asserted in tests.

5) Re-run knowledge suites until green
   - `uv run pytest tests/lib/knowledge -q`
   - `uv run pytest tests/integration/knowledge -q`

6) Optional follow-up once green
   - Add explicit tests validating deletion semantics under hot‑reload when contents DB is configured, asserting audit log lines.

## Risks & Considerations
- Enabling contents DB post-instantiation maintains deletion capability while retaining constructor compatibility; validate in integration after refactor.
- BWC shim breadth for SmartIncrementalLoader is substantial; implement iteratively with focused unit runs to avoid regressions.
- Ensure factories consistently import the canonical knowledge factory to prevent ambiguous imports across modules.

## Tooling Guardrails
- UV-only tooling used; no direct `pyproject.toml` edits observed for Group C files.

## Commands Executed (key excerpts)
- `uv run python -c "import agno; print(agno.__version__)"` → 2.0.8
- `uv run pytest tests/integration/knowledge -q` → 2 failed
  - Failure: constructor included `contents_db`, expected only `csv_path` and `vector_db`.
- `uv run pytest tests/lib/knowledge -q` → 162 failed
  - Failures across CSVDataSource, SmartIncrementalLoader, BusinessUnitFilter patchability and related paths.

## Verdict
HOLD — Group C does not yet meet the wish’s acceptance criteria. Integration regressions stem from hot‑reload constructor usage; unit-level API drift in CSVDataSource and missing SmartIncrementalLoader compatibility shims remain. Apply the remediations above and re-run the suites under uv until green.
