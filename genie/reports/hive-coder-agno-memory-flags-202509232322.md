# Hive Coder Death Testament – Restore legacy memory flags in Agno v2 proxies

## Context
- Wish: `genie/wishes/agno-v2-migration-wish.md` (Group A1–A4 foundation scope)
- Review finding: `@genie/reports/hive-reviewer-agno-migration-foundation-review-202509232312.md`
- Commit under review: 805b5d72

## Scope
Reconnect legacy Agno v1 memory flags defined in YAML configs with the Agno 2.0.8 agent/team constructors so behaviour stays consistent post-migration.

## Implementation Summary
- `lib/utils/proxy_agents.py:20` added `_LEGACY_MEMORY_KEY_MAP` and translate legacy keys inside `_handle_memory_config`, while expanding the fallback parameter set to include v2 flag names.
- `lib/utils/proxy_teams.py:28` mirrored the legacy mapping for teams, ensured `_process_config` iterates on a stable copy, updated fallback parameters (including `memory_manager`), and reused the new key names.
- `tests/lib/utils/test_proxy_agents.py:502` and `tests/lib/utils/test_proxy_teams.py:548` now assert that legacy YAML flags surface as `*_to_context` parameters and that the deprecated names are excluded.
- Updated team integration tests to patch the new Agno storage import path `agno.db.postgres.PostgresDb` so mocks align with the v2 storage resolver.

## Validation
- `uv run pytest tests/lib/utils/test_proxy_agents.py tests/lib/utils/test_proxy_teams.py`
  - RED excerpt (pre-fix): `KeyError: 'add_history_to_context'` raised by `TestCustomParameterHandlers::test_handle_memory_config_enabled` once legacy-only flags were asserted.
- `uv run pytest tests/lib/utils/test_proxy_agents.py tests/lib/utils/test_proxy_teams.py`
  - GREEN: 118 passed, legacy flags mapped to their v2 equivalents.

## Risks & Mitigations
- **Risk**: Other legacy parameters might need translation in future. *Mitigation*: centralise the mapping dictionaries so extending coverage is straightforward.
- **Risk**: `_process_config` now copies `config.items()` which adds minor overhead. *Mitigation*: documented change and constrained to teams where mutation occurs during iteration.

## Follow-ups / TODOs
- None. Coverage for agent/team proxies now exercises legacy YAML paths.

## Notes for Humans
Behaviour parity verified only for targeted suites; broader regression pass left to existing pipelines.
