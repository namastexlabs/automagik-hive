# Hive Coder Death Testament — Agno v2 Migration D3

## Scope
- normalised metrics extraction to Agno v2 schema (`input_tokens`, `output_tokens`, `duration`, provider metrics) and refreshed async service docstrings.
- surfaced new Agno migration settings (v1/v2 tables + toggle) and startup/version-sync logging hooks.
- delivered operational wrapper script `scripts/agno_db_migrate_v2.py` with pymongo stubs, dry-run logging, and JSON transcript emission under `genie/reports/`.

## Files touched
- `lib/config/settings.py`
- `lib/metrics/agno_metrics_bridge.py`
- `lib/metrics/async_metrics_service.py`
- `lib/metrics/__init__.py`
- `lib/services/version_sync_service.py`
- `lib/utils/startup_orchestration.py`
- `scripts/agno_db_migrate_v2.py`
- `tests/lib/metrics/test_agno_metrics_bridge.py`
- `tests/lib/metrics/test_async_metrics_service.py`

## Commands
- `uv run pytest tests/lib/metrics -q`
  - ✅ pass (warnings about missing pydantic env fields already known)
- `uv run python scripts/agno_db_migrate_v2.py --dry-run`
  - ✅ pass; fell back to in-memory settings due to absent env vars and wrote log `genie/reports/agno-v2-migration-dry-run-20250925153106.log`

## Evidence
- Dry-run transcript: `genie/reports/agno-v2-migration-dry-run-20250925153106.log`
- Metrics tests cover provider metrics remapping and async queue normalisation.

## Risks & TODOs
- Real migration run still requires valid `HIVE_DATABASE_URL` plus env settings; script logs missing configuration but exits cleanly.
- Follow-up: populate env + rerun script in non-dry mode once staging database available.
- Downstream components (proxy factories) should adopt new Agno v2 settings/fields in subsequent groups.
