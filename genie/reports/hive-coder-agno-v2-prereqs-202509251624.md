# Hive Coder Death Testament – Agno v2 Config Prereqs

## Phase Log
- **Phase 0 – Discovery**: Parsed `genie/reports/hive-reviewer-agno-v2-audit-202509251548.md` and the Group E requirements in `genie/wishes/agno-v2-migration-wish.md# Group E`, confirming blockers were limited to lingering `storage`/`context` usage in configs, proxies, and tests.
- **Phase 1 – Red**: No new tests were added; instead, existing schema assertions were updated to expect Agno v2 semantics (`tests/lib/utils/test_proxy_agents.py`, `tests/lib/utils/test_proxy_workflows_*`, `tests/lib/utils/test_proxy_teams*.py`). The original suites failed until configuration fixtures and proxy handlers were migrated off `storage`.
- **Phase 2 – Green**:
  - Introduced `_handle_db_config` across `lib/utils/proxy_agents.py:471`, `lib/utils/proxy_teams.py:385`, `lib/utils/proxy_workflows.py:231`, delegating legacy `storage` calls through a warning shim while merging user-provided `dependencies` with generated ones.
  - Updated template assets (`ai/agents/template-agent/config.yaml:16`, `ai/teams/template-team/config.yaml:23`, `ai/workflows/template-workflow/config.yaml:19`, `ai/templates/standard-team.yaml:23`, `ai/templates/standard-team-member.yaml:9`) to declare `db` + `dependencies`, removing the deprecated `context` sections and stray `mode` default per wish guidance.
  - Adjusted workflow proxy imports to `from agno.workflow import Workflow` and pushed `id` instead of `workflow_id`, while metadata still records `workflow_id` for external consumers.
- **Phase 3 – Refine & Report**: Normalised test fixtures/mocks to the new schema, ensured top-level dependency merges were idempotent, documented follow-ups below, and captured evidence.

## Implementation Highlights
- **Proxy orchestration**: Shared DB builder now validates dict input, ensures bad types are ignored, and merges dependencies so callers can inject mocks without losing the generated DB handle.
- **Backward compatibility**: Retained `storage` handlers with explicit warnings, allowing downstream YAML to be migrated incrementally without breaking runtime.
- **Schema alignment**: All template YAML files now express Agno v2 `db` semantics, giving Group E a clean baseline for refreshing agent assets.
- **Testing updates**: Expectations now check for `.db` attributes and `id`-centric workflow parameters. Validation coverage thresholds in `tests/lib/utils/test_proxy_*` were recalculated to reflect the supported parameter sets.

## Evidence
```bash
$ uv run pytest tests/ai/agents/template-agent/test_template_agent.py
============================= test session starts ==============================
platform darwin -- Python 3.12.11, pytest-8.4.1, pluggy-1.6.0
...
tests/ai/agents/template-agent/test_template_agent.py ............
======================== 14 passed, 2 warnings in 1.90s =======================
```

```bash
$ uv run pytest tests/lib/utils/test_proxy_workflows_final.py \
    tests/lib/utils/test_proxy_workflows_boost.py \
    tests/lib/utils/test_proxy_workflows_coverage.py
...
======================== 91 passed, 2 warnings in 1.75s =======================
```

```bash
$ uv run pytest tests/lib/utils/test_proxy_agents.py \
    tests/lib/utils/test_proxy_teams.py \
    tests/lib/utils/test_proxy_teams_coverage.py \
    tests/lib/config/test_yaml_parser_execution_suite.py
...
======================= 162 passed, 2 warnings in 2.29s =======================
```

_Note_: Coverage emits longstanding warnings for `lib/utils/error_handlers.py` and `lib/utils/fallback_model.py`; no behavioural changes were introduced in these modules.

## Risks / Follow-ups
- Remaining non-template agent/team/workflow configs should be migrated to the new schema to eliminate the temporary `storage` shim.
- Consider tasking `hive-quality` with removing the legacy coverage warnings once the upstream files are reformatted.
- Monitor downstream agents/teams for reliance on `workflow_id` constructor kwargs; update callers if any rely on the deprecated signature.

## Handoff
- Group E prerequisites around config/schema alignment are satisfied; assets and proxy loaders now speak Agno v2. Ready for human review and subsequent Group E execution.
