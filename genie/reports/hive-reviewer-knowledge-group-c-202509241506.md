# Death Testament – Forge Task Review (Re‑Review): Group C – Knowledge System

## Scope
- Wish: `genie/wishes/agno-v2-migration-wish.md` — Group C (C1–C3)
- This review reassesses Group C after recent remediation attempts.
- Focused coverage: knowledge integration and unit suites, watcher/hot‑reload behavior, factories, and filters.

## Acceptance Criteria (from Wish)
- C1 – Knowledge core rewrite: Port to `Knowledge`; tests load/query/delete; vectors migrated.
- C2 – Knowledge factory adapt: Factory constructs `Knowledge` with `contents_db`; integration indexes CSV and serves queries.
- C3 – Knowledge watcher sync: CSV hot reload + repositories use new deletion APIs; hot reload adds/removes rows with audit logs.

## Evidence Collected (uv-only)
- Agno version: `uv run python -c "import agno; print(agno.__version__)"` → 2.0.8
- Integration (knowledge):
  - `uv run pytest tests/integration/knowledge -q` → FAIL (2 failed)
- Unit (knowledge):
  - `uv run pytest tests/lib/knowledge -q` → FAIL (162 failed, 258 passed, 2 skipped)

Key failure themes:
- Integration failures triggered by constructor signature mismatch in hot reload.
- Broad unit failures in CSV datasource and SmartIncrementalLoader due to API drift vs tests and missing compatibility shims.
- Config filter patchability not honored in constructor path.

## Code Observations (traceability)
- CSV Hot Reload is now passing `contents_db` to the KB constructor, breaking tests that assert the prior call shape:
```120:131:lib/knowledge/csv_hot_reload.py
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
- CSV Data Source calls the hash manager with (index, row), but tests expect it to receive a single row object and use row.name internally:
```31:37:lib/knowledge/datasources/csv_datasource.py
            for idx, row in df.iterrows():
                row_hash = self.hash_manager.hash_row(idx, row)
                if not row_hash:
                    continue
                rows_with_hashes.append(
                    {"index": idx, "hash": row_hash, "data": row.to_dict()}
                )
```
- BusinessUnitFilter exposes a module-local `load_global_knowledge_config`, but its constructor still pulls from `config_aware_filter`, so test-time patching of the local symbol doesn’t affect initialization:
```18:22:lib/knowledge/filters/business_unit_filter.py
    def __init__(self):
        """Initialize with loaded configuration."""
        self.config = config_aware_filter.load_global_knowledge_config()
```
- SmartIncrementalLoader diverges from test‑expected surface area. Many helper methods and attributes referenced by tests are missing or renamed (table_name, _get_existing_row_hashes, _get_csv_rows_with_hashes, _add_hash_column_to_table, _process_single_row, _update_row_hash, _full_reload, get_database_stats, etc.). Representative definition:
```97:131:lib/knowledge/smart_incremental_loader.py
class SmartIncrementalLoader:
    """Incremental CSV → PgVector loader with per-row hashing."""
    def __init__(self, csv_path: str | Path, kb: Any | None = None):
        self.csv_path = Path(csv_path)
        self.config = _load_config()
        self.kb = kb or self._create_default_kb()
        self.db_url = os.getenv("HIVE_DATABASE_URL")
        ...
```

## Validation vs Criteria
- C1: Partially satisfied
  - v2 `Knowledge` is used in `RowBasedCSVKnowledgeBase`. Integration queries/loads largely worked previously; current hot-reload change regresses the integration tests.
- C2: Partially satisfied
  - Factory wiring to v2 appears, but significant unit failures in datasource/smart loader prevent acceptance.
- C3: Not satisfied
  - Watcher deletion semantics intention is good (using `contents_db`), but integration tests expect the older constructor call; hot‑reload does not yet deliver deletion with audit logs under the test harness. Unit suites for incremental loading are red due to API drift.

## Risks & Regressions
- Regression in integration hot‑reload tests caused by adding `contents_db` kwarg to KB constructor call (strict mock assertions).
- High test surface red in SmartIncrementalLoader due to missing BWC shim methods; functional risk if deployed without parity.
- Business unit filter remains unpatchable in tests via the module-local symbol during __init__, masking config errors in CI.

## Required Remediations (blocking)
1) Restore test compatibility for CSV Hot Reload constructor
   - Do NOT pass `contents_db` to `RowBasedCSVKnowledgeBase` at creation time. Instead, after instantiation:
     - If `contents_db` exists, set `manager.knowledge_base.knowledge.contents_db = contents_db` (guarded) to enable `remove_content_by_id` without breaking constructor call assertions.
   - Add debug log indicating contents DB activation.

2) Align CSVDataSource with test contract
   - Change `get_csv_rows_with_hashes()` to call `hash_manager.hash_row(row)` (single argument: Series/dict), not `(idx, row)`.
   - Implement `process_single_row()` using a temporary `RowBasedCSVKnowledgeBase` and call `load(recreate=False, upsert=True)` as tests assert; then invoke `update_row_hash_func(data, hash, idx)`.

3) SmartIncrementalLoader BWC shim
   - Provide compatibility methods/props delegating to new repository/datasource:
     - `table_name` property (from config with default `knowledge_base`).
     - `_get_csv_rows_with_hashes()` → `self.csv_datasource.get_csv_rows_with_hashes()`.
     - `_get_existing_row_hashes()` → `self.repository.get_existing_row_hashes()`.
     - `_add_hash_column_to_table()` → `self.repository.add_hash_column_to_table()`.
     - `_update_row_hash(data, h, idx=None)` → `self.repository.update_row_hash(data, h, self.config, idx)`.
     - `_remove_rows_by_hash(hashes)` → `self.repository.remove_rows_by_hash(hashes)`.
     - `_process_single_row(row, ...)` → use `CSVDataSource.process_single_row`.
     - `_populate_existing_hashes()` – iterate CSV rows and update.
     - `_full_reload()` – call `self.kb.load(recreate=True)` and summarize.
     - `smart_load(force_recreate=False)` – retain param and route to current strategy.
     - `get_database_stats()` – call `analyze_changes()` and shape result keys expected by tests.

4) BusinessUnitFilter patchability during init
   - Update constructor to use module-local `load_global_knowledge_config()` so tests can patch `lib.knowledge.filters.business_unit_filter.load_global_knowledge_config` effectively.

5) Keep single canonical knowledge factory
   - Ensure `lib/knowledge/knowledge_factory.py` re‑exports from `lib.knowledge.factories.knowledge_factory` (present) and remove any direct imports to the shim in app code to prevent drift.

6) Rerun knowledge suites until green
   - `uv run pytest tests/lib/knowledge -q`
   - `uv run pytest tests/integration/knowledge -q`

7) Optional (future): add new tests for deletion semantics under hot‑reload when `contents_db` is available to prove C3 audit behavior.

## Commands Executed (key)
- `uv run python -c "import agno; print(agno.__version__)"` → 2.0.8
- `uv run pytest tests/integration/knowledge -q` → 2 failed
- `uv run pytest tests/lib/knowledge -q` → 162 failed, 258 passed, 2 skipped

## Verdict
HOLD — Group C does not meet wish acceptance criteria. Integration regressions were introduced in hot‑reload constructor usage, and substantial unit API drift exists in CSVDataSource and SmartIncrementalLoader. Apply the remediations above to restore test parity (RED→GREEN) while preserving v2 semantics.
