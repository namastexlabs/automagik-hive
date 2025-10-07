## Forge Plan • knowledge-agno-pgvector-alignment-wish (2025-09-24 01:35 UTC)

Context Source: `genie/wishes/knowledge-agno-pgvector-alignment-wish.md`
Origin Branch: `wish/agno-v2-migration`

### Discovery (Summary)
- Goal: Align Agno v2 knowledge objects with the existing pgvector-backed incremental pipeline without breaking legacy contracts.
- Constraints: Preserve pgvector table naming/shape, restore SmartIncrementalLoader facade methods, avoid constructor API drift, assign `contents_db` post-construction, keep logging/QA compatibility. No direct pyproject edits; use `uv` tooling only.
- Success: Knowledge unit + integration suites pass, plus Ruff/Mypy clean for `lib/knowledge/**`. Death Testaments and validation logs captured.

### Planning – Proposed Groups (one forge task per group)

- Group A1 – knowledge-signature-bridge (agent: hive-coder)
  - Scope: Restore `RowBasedCSVKnowledgeBase` helpers (`build_document_from_row`, `get_signature`, `add_document`) that wrap Agno v2 `Knowledge`; share signature logic with service helpers.
  - Evidence: Death Testament; tests: `tests/lib/knowledge/test_row_based_csv_knowledge_coverage_boost.py`, `tests/integration/knowledge/test_row_based_csv_knowledge_comprehensive.py` green.
  - Dependencies: none

- Group A2 – hash-manager-bwc (agent: hive-coder)
  - Scope: Reintroduce legacy `_HashManager.hash_row(row)` and SmartIncrementalLoader helpers delegating to new internals; keep call signatures stable.
  - Evidence: Death Testament; tests: `tests/lib/knowledge/datasources/test_csv_datasource.py`, `tests/lib/knowledge/test_smart_incremental_loader.py` green.
  - Dependencies: none

- Group A3 – factory-repository-sync (agent: hive-coder)
  - Scope: Factory returns pgvector-backed knowledge with optional `contents_db` assigned post-construction; keep repository removals in sync with `Knowledge.remove_content_by_id`.
  - Evidence: Death Testament; tests: `tests/lib/knowledge/test_knowledge_factory_real_coverage.py`, `tests/lib/knowledge/test_hash_fix.py` green.
  - Dependencies: none

- Group B1 – hot-reload-contract (agent: hive-coder)
  - Scope: Maintain constructor expectations (`RowBasedCSVKnowledgeBase(csv_path, vector_db)`), inject contents DB post-instantiation, call SmartIncrementalLoader via restored API; retain debounce/watcher behaviour.
  - Evidence: Death Testament; tests: `tests/integration/knowledge/test_csv_hot_reload_comprehensive.py` (+ coverage) green.
  - Dependencies: A1, A2, A3

- Group B2 – config-filter-compat (agent: hive-coder)
  - Scope: Route config loads through patchable helpers; surface business-unit metadata from new signatures; log diagnostics.
  - Evidence: Death Testament; tests: `tests/lib/knowledge/test_business_unit_filter.py` green.
  - Dependencies: A1

- Group B3 – services-alignment (agent: hive-coder)
  - Scope: Delegate service helpers to SmartIncrementalLoader facade while keeping public signatures unchanged; ensure change analyzer reports contents DB removals.
  - Evidence: Death Testament; tests: `tests/lib/knowledge/services/test_change_analyzer.py`, `tests/lib/knowledge/services/test_hash_manager.py` green.
  - Dependencies: A2

- Group C1 – status-snapshots (agent: hive-coder)
  - Scope: Provide structured status payloads (`new_rows`, `potential_removals`, contents DB warnings) with Agno v2 metadata.
  - Evidence: Death Testament; tests: `tests/lib/knowledge/test_change_analyzer.py::TestChangeAnalyzerStatus` green.
  - Dependencies: A1, A3

- Group C2 – maintenance-hooks (agent: hive-tests)
  - Scope: Ensure maintenance flows (full reload, forced embeddings) exercise adapters without manual mocks; update fixtures if required.
  - Evidence: Death Testament; integration tests updated/green in `tests/integration/knowledge/test_comprehensive_knowledge.py`.
  - Dependencies: A1, A3, B1

- Group C3 – observability-logging (agent: hive-coder)
  - Scope: Normalize log keys for knowledge load/update events so QA scripts remain compatible and capture Agno instrumentation.
  - Evidence: Death Testament; logging assertions in knowledge integration suites remain valid.
  - Dependencies: A1

- Group D1 – smart-loader-wiring (agent: hive-coder)
  - Scope: Ensure factory, hot reload manager, and SmartIncrementalLoader share a single knowledge context (vector_db + optional contents_db); DI ready for CLI workers.
  - Evidence: Death Testament; manual smoke `SmartIncrementalLoader(csv_path).smart_load()` produces strategy summaries without errors.
  - Dependencies: B1, C1

- Group D2 – rollback-safety (agent: hive-coder)
  - Scope: Guard DB ops with transactional removal + Knowledge cleanup; capture audit logs; allow safe dry runs.
  - Evidence: Death Testament; repository tests for removal/update/log assertions green.
  - Dependencies: A3, B3

- Group D3 – configuration-parity (agent: hive-coder)
  - Scope: Ensure global config exposes legacy + Agno v2 keys (hash columns, contents_db toggles) so YAML-referencing tests pass.
  - Evidence: Death Testament; `tests/lib/knowledge/test_knowledge_factory_coverage_boost.py` green.
  - Dependencies: A1, A3

- Group E1 – test-suite-refresh (agent: hive-tests)
  - Scope: Adjust fixtures/mocks to restored interfaces; add regression tests for contents DB hand-off; document assumptions in test helpers.
  - Evidence: Death Testament; full knowledge suites pass under Agno v2 with pgvector.
  - Dependencies: D1

- Group E2 – static-analysis (agent: hive-quality)
  - Scope: Run `uv run ruff check lib/knowledge` and `uv run mypy lib/knowledge`; fix issues without editing `pyproject.toml`.
  - Evidence: Death Testament; Ruff + mypy clean for knowledge modules.
  - Dependencies: A–D complete

- Group E3 – wish-evidence (agent: hive-self-learn)
  - Scope: Append validation evidence, commands, and Death Testament references to the wish; advance status to COMPLETED after human sign-off.
  - Evidence: Death Testament; wish updated with logs and links.
  - Dependencies: E1, E2

### Proposed Branch Template
`wish/agno-v2-migration/<group-slug>` (no pushes; isolated worktrees referencing origin branch)

### Expected Evidence for All Groups
- Subagent Death Testament under `genie/reports/<agent>-<slug>-<YYYYMMDDHHmm>.md`.
- Passing tests per group scope; command outputs captured via `uv run pytest …`.
- Any linter/type fixes executed via `uv run ruff` / `uv run mypy` (no `pyproject.toml` edits).

### Approval
- 2025-09-24 01:38 UTC – Human approved all phases (A–E) for task creation. Proceed to forge-master calls per group.
  - Suggested phase sequencing: Phase 1 = A1–A3; Phase 2 = B1–B3; Phase 3 = C1–C3; Phase 4 = D1–D3; Phase 5 = E1–E3.

### Execution
- Group A foundation – Task ID `a3df7420-0aa5-465d-8afc-77732170666f` – Branch `wish/agno-v2-migration/group-a-foundation` – Agent: hive-coder. Focus on A1–A3 scopes; gather tests listed in plan and produce Death Testament with uv command outputs.
- Group B runtime-surfaces – Task ID `ea062e76-ba93-4bff-b0bd-cafe62886f56` – Branch `wish/agno-v2-migration/group-b-runtime-surfaces` – Agent: hive-coder. Depends on Group A completion; ensure hot reload/contracts/tests/logging captured.
- Group C knowledge-services – Task ID `3117c74d-2af5-4167-98eb-2c0f846ccccd` – Branch `wish/agno-v2-migration/group-c-knowledge-services` – Agent: hive-coder. Depends on Groups A & B; document logging evidence and status payload outputs.
- Group D integration – Task ID `8ebd0b2a-2207-442f-8194-1160505c38a0` – Branch `wish/agno-v2-migration/group-d-integration` – Agent: hive-coder. Requires Groups B & C; include manual smoke evidence and repository rollback proof.
- Group E validation – Task ID `9aede55f-dee2-45d9-ab40-b29a9eba9d0e` – Branch `wish/agno-v2-migration/group-e-validation` – Agent: hive-tests (tests) + hive-quality (lint/type) + hive-self-learn (wish evidence). Depends on Group D; finalizes wish documentation and verification.


