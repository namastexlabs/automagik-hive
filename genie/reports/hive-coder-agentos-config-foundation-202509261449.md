# Hive Coder Death Testament — AgentOS Config Foundation

## Scope
- Established `lib/agentos/` package with default builders (`config_models.py`) and YAML loader (`config_loader.py`).
- Added fallback assets (`default_agentos.yaml`) plus custom exception plumbing.
- Extended `HiveSettings` with `hive_agentos_config_path` and `hive_agentos_enable_defaults` including path validation + disable guard.

## Files
- `lib/agentos/__init__.py`
- `lib/agentos/config_models.py`
- `lib/agentos/config_loader.py`
- `lib/agentos/default_agentos.yaml`
- `lib/agentos/exceptions.py`
- `lib/config/settings.py`

## Commands
- `uv run python -c "import inspect, agno.os.config as cfg; ..."` — inspected upstream schema (success).
- `uv run python -c "from agno.os.config import AgentOSConfig; ..."` — emitted JSON schema (success).
- `uv run python -c "import inspect, agno.os.router as cfg; ..."` — attempted router introspection (failed: attribute missing, non-blocking).
- `env HIVE_ENVIRONMENT=development ... uv run python -c "from lib.agentos import load_agentos_config; ..."` — validated loader + defaults (success).

## Evidence Notes
- Quick prompt normalization trims whitespace, deduplicates case-insensitively, and caps lists at three entries per Agno rule. Keys follow `component-type:identifier` (`agent:template-agent`, etc.); Group 2 should preserve this scheme when wiring services to avoid collisions.
- Default display names + DB identifiers pull straight from `HiveSettings` (`hive_agno_v2_*`) ensuring registry alignment. Knowledge fallback mirrors PgVector defaults while respecting settings overrides.
- Builder aggregates model IDs from agent/team/workflow YAMLs; Group 2 can extend metadata extraction without disrupting available model ordering (preserved by `_unique_preserving_order`).

## Test Scaffolds for Group 4
- `tests/lib/agentos/test_config_loader.py` (new):
  - RED: simulate missing file with `hive_agentos_enable_defaults=False` expecting `AgentOSConfigError`.
  - RED: patch YAML returning >3 prompts to confirm loader raises via Agno validator.
- `tests/lib/agentos/test_config_models.py` (new):
  - RED: verify `_normalize_prompts` trims, dedupes, and truncates to three entries.
  - RED: ensure `_merge_domain_section` injects `domain_config.display_name` matching settings tables.

## Risks & Follow-Ups
- Need service integration (Group 2) to surface builder + loader through DI.
- No docs updates yet; note for later groups once API wiring lands.
- When environments lack required Hive env vars, defaults raise early — ensure deployment pipeline feeds `HiveSettings` before calling loader.

## Human Validation
- Re-run `env ... uv run python -c "from lib.agentos import load_agentos_config; ..."` with production-like env to confirm resolved paths if an external YAML is provided.
- Review generated quick prompts for tone before exposing to UI; adjust via YAML or overrides as needed.
