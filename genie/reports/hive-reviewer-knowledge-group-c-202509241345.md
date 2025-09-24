# Death Testament – Forge Task Review: Group C (Knowledge System)

## Scope
- Wish: `genie/wishes/agno-v2-migration-wish.md` — Group C (C1–C3)
- Commits reviewed:
  - 575f83f “feat: modernize knowledge stack for agno v2” (Group C core)
  - 6ca4bc9 “Solve the problems encountered in this task” (Group C remediation)
- Agent artefacts:
  - @genie/reports/hive-coder-knowledge-v2-migration-202509240106.md
  - @genie/reports/hive-coder-knowledge-group-c-remediation-202509241332.md

## Acceptance Criteria (Group C)
- C1-knowledge-core-rewrite: Port to `Knowledge`; tests load/query/delete; vectors migrated.
- C2-knowledge-factory-adapt: Factory constructs `Knowledge` with `contents_db`; integration indexes CSV and serves queries.
- C3-knowledge-watcher-sync: CSV hot reload + repositories use new deletion APIs; hot reload adds/removes with audit logs.

## Evidence Collected
- Agno version (A1 dependency):
  - Command: `uv run python -c "import agno; print(agno.__version__)"`
  - Output: 2.0.8
- Integration tests (Group C focus):
  - Command: `uv run pytest tests/integration/knowledge -q`
  - Result: PASS (all tests green; warnings only)
- Unit tests (knowledge domain breadth):
  - Command: `uv run pytest tests/lib/knowledge -q`
  - Result: 140 failed, 51 errors, 229 passed, 2 skipped
  - First error excerpt (config patch target missing):
    - AttributeError: module `lib.knowledge.filters.business_unit_filter` has no attribute `load_global_knowledge_config`

## Code Observations (traceability to criteria)
- C1 (port to Knowledge, deletion API usage)
  - `lib/knowledge/row_based_csv_knowledge.py` uses Agno v2 `Knowledge` and calls deletion API when upserting:

```423:426:lib/knowledge/row_based_csv_knowledge.py
            try:
                knowledge.remove_content_by_id(signature.content_id)
            except ValueError:
                logger.debug("Knowledge contents DB not configured; skipping content removal")
```

- C2 (factory constructs Knowledge with contents_db)
  - `lib/knowledge/factories/knowledge_factory.py` builds `PostgresDb` and passes `contents_db` into the KB wrapper, satisfying factory wiring for v2.
- C3 (watcher, repositories, deletion paths)
  - Repository invokes v2 deletion with content-id generation:

```239:246:lib/knowledge/repositories/knowledge_repository.py
        for content_hash in hashes:
            if not content_hash:
                continue
            try:
                content_id = generate_id(content_hash)
                self.knowledge.remove_content_by_id(content_id)
            except ValueError:
                logger.debug("Knowledge removal skipped; contents DB unavailable")
```

  - CSV hot reload manager constructs `contents_db` but does not pass it to the KB wrapper, which may impede `remove_content_by_id` behavior at runtime:

```126:133:lib/knowledge/csv_hot_reload.py
            self.knowledge_base = RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path),
                vector_db=vector_db,
            )

            if self.csv_path.exists():
                self.knowledge_base.load(recreate=False, skip_existing=True)
```

- Scope drift note: `lib/knowledge/filters/business_unit_filter.py` added; not explicitly listed under Group C tasks. Tests expect `load_global_knowledge_config` to be directly importable/patchable from this module, but current code sources it indirectly from `config_aware_filter`.
- Potential duplication: both `lib/knowledge/factories/knowledge_factory.py` and `lib/knowledge/knowledge_factory.py` exist, which may cause ambiguous imports in tests/callers.

## Validation vs Criteria
- C1: Partially satisfied
  - Port to `Knowledge` complete; integration tests for row-based KB green. Deletion path present but gated by `contents_db` availability; broader unit tests reveal gaps in related components.
- C2: Largely satisfied
  - Factory adapts to v2 and attempts `contents_db` wiring; integration indexing flows pass. Some broader unit tests still fail, indicating incomplete harmonization.
- C3: Not fully satisfied
  - Repositories use new deletion APIs; integration watcher flows pass. However, unit tests for smart incremental loader and config-aware filter fail extensively. Hot reload does not supply `contents_db` to the KB wrapper, undermining content removal semantics and acceptance around “adds/removes … with audit logs.”

## Risks & Regressions
- High: 140+ unit failures within `tests/lib/knowledge` (not just integration), centered on:
  - Config patchability (`load_global_knowledge_config` symbol exposure) in `business_unit_filter`.
  - Smart incremental loader DB/hash paths (`update_row_hash`, removals, env handling). These directly relate to C3.
- Medium: `contents_db` not passed in hot reload manager likely disables `remove_content_by_id` during reload cycles.
- Medium: Factory module duplication may lead to import drift between tests and runtime code.

## Tooling Guardrails
- No direct `pyproject.toml` edits observed in the Group C commits reviewed. UV tooling used for version verification.

## Verdict
HOLD — Group C integration scenarios pass, but unit-level coverage reveals substantive gaps in config filter and smart loader behaviors required for C3. Hot reload’s omission of `contents_db` also weakens deletion guarantees.

## Required Remediations
1. BusinessUnitFilter patchability: expose `load_global_knowledge_config` in `lib/knowledge/filters/business_unit_filter.py` (simple passthrough) so tests can patch the module-local symbol.
2. SmartIncrementalLoader parity: make unit tests pass end-to-end.
   - Ensure repository methods return values expected by tests; tighten SQL paths and exception handling.
   - Verify env fallbacks and CSV hashing consistency match KB signature logic.
   - Re-run: `uv run pytest tests/lib/knowledge/test_smart_incremental_loader*.py -q` until green.
3. CSVHotReload contents DB: pass `contents_db` into `RowBasedCSVKnowledgeBase` to enable `remove_content_by_id` during reloads; add audit logging assertions.
4. Factory consolidation: choose `lib/knowledge/factories/knowledge_factory.py` as canonical; re-export from `lib/knowledge/knowledge_factory.py` or remove duplicate to avoid ambiguity.
5. Add/confirm tests for deletion semantics: ensure upsert/change paths call `remove_content_by_id` when `contents_db` available; verify through unit mocks and integration traces.
6. Static checks for knowledge domain: `uv run ruff check lib/knowledge` and `uv run mypy lib/knowledge` and address findings.

## Commands Executed (key)
- `uv run python -c "import agno; print(agno.__version__)"` → 2.0.8
- `uv run pytest tests/integration/knowledge -q` → PASS
- `uv run pytest tests/lib/knowledge -q` → 140 failed, 51 errors, 229 passed

## Artefacts
- Wish: @genie/wishes/agno-v2-migration-wish.md
- Agent DTs: @genie/reports/hive-coder-knowledge-v2-migration-202509240106.md, @genie/reports/hive-coder-knowledge-group-c-remediation-202509241332.md
- Commits: 575f83f, 6ca4bc9
