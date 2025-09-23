# Forge Planning – Agno v2 Migration Wish
- Wish: `genie/wishes/agno-v2-migration-wish.md`
- Status at planning: APPROVED / READY_FOR_EXECUTION
- Created (UTC): 2025-09-23 22:10
- Orchestrator: GENIE (human-coordinated)

## Discovery Highlights
- Objective: migrate Automagik Hive from Agno v1 to v2 while preserving agent behaviours and ensuring db/knowledge/metrics compatibility.
- Key constraints: follow UV-only tooling, protect existing memory/knowledge data, maintain TDD (Red→Green→Refactor), store evidence + Death Testaments per subagent.
- Risks: dependency pin ripple effects across factories, knowledge table migrations risking data loss, metrics schema drift, broad YAML/config churn affecting agents/tests.

## Planning (Pending Human Approval)
| Group | Scope Snapshot | Primary Agent | Dependencies | Expected Evidence |
| --- | --- | --- | --- | --- |
| foundation-upgrade | Execute A1-A4: pin Agno 2.0.8 via `uv`, adapt imports, refresh Db/memory factories, shift proxies to `dependencies`/`db`. | `hive-coder` (+ coordination with `hive-tests` for focused regression) | none | Death Testament covering dependency pin + factory/proxy diffs; `uv run python -c "import agno"` version proof; targeted `uv run pytest tests/lib/memory/test_memory_factory.py tests/lib/utils/test_proxy_agents.py` logs. |
| runtime-surface-sync | Deliver B2-B3: update startup orchestration & CLI runtime bridging to consume v2 helpers without AgentOS rollout. | `hive-coder` | foundation-upgrade | Death Testament with CLI smoke outputs; `uv run pytest tests/cli -k service --maxfail=1`; startup logs showing v2 dependency wiring. |
| knowledge-stack-modernization | Complete C1-C3: port knowledge layer to `Knowledge`, adjust factories, refresh hot reload repo for v2 APIs. | `hive-coder` (paired validation from `hive-tests` as needed) | foundation-upgrade | Death Testament plus `uv run pytest tests/lib/knowledge/test_row_based_csv_knowledge.py tests/integration/knowledge -q`; migration notes confirming vector persistence. |
| persistence-metrics-migration | Deliver D1-D3 (script wrapper, metrics schema shift, settings surfacing). Includes importing upstream migration script safely. | `hive-coder` with `hive-tests` support for migration dry-run harness | foundation-upgrade, knowledge-stack-modernization (for db schemas) | Death Testament including dry-run logs from `uv run python scripts/agno_db_migrate_v2.py --dry-run`; updated metrics unit tests `uv run pytest tests/lib/metrics -q`; settings snapshot. |
| agent-assets-refresh | Address E1-E4: update agents/teams/workflows/YAML + fixtures to v2 semantics. | `hive-coder` (coordinate with `hive-tests` for config assertions) | runtime-surface-sync, persistence-metrics-migration | Death Testament referencing config diffs; `uv run pytest tests/ai/agents/template-agent/test_template_agent.py tests/lib/utils/test_proxy_agents.py`; sample agent run logs. |
| validation-docs-sweep | Execute F1-F3: refresh remaining tests, documentation, and capture final evidence/Death Testaments. | `hive-tests` (lead for regression) + `hive-coder` for docs polish | agent-assets-refresh | Death Testament summarizing full-suite `uv run pytest`, lint outputs, documentation diff, wish evidence appendix. |

## Approval Record
- Status: Pending human approval (no forge tasks created yet).
- To record approval: include timestamp, approver initials, and summary before any `forge-master` invocation.

## Execution Log (populated post-approval)
- _No entries yet._

### Approval Record
- 2025-09-23 22:17 UTC – Approved by Human (Option 1)

## Execution
- Group foundation-upgrade → Task `feat: agno v2 foundation migration` (ID da3a9643-b7f8-412b-9523-f1db4377e6aa, branch guidance: feat/agno-v2-foundation-migration).
- Group runtime-surface-sync → Task `feat: align runtime surfaces with agno v2` (ID abbf5044-3389-4988-87c9-6d3b74d76ce9, branch feat/runtime-surface-sync).
- Group knowledge-stack-modernization → Task `feat: modernize knowledge stack for agno v2` (ID 9c02bb7d-2532-4a9b-a4fa-bb8c9a329e19, branch feat/knowledge-stack-v2).
- Group persistence-metrics-migration → Task `feat: migrate persistence and metrics to agno v2` (ID 8d4060c2-a6e9-4fb3-bf64-5e88ff51369b, branch feat/persistence-metrics-v2).
- Group agent-assets-refresh → Task `feat: refresh agent assets for agno v2` (ID 6538fb96-bee4-43fd-902e-a304b09aec03, branch feat/agent-assets-v2).
- Group validation-docs-sweep → Task `chore: finalize agno v2 validation and docs` (ID acc4165f-ef93-44a9-9051-1003fc578338, branch chore/agno-v2-validation-docs).
