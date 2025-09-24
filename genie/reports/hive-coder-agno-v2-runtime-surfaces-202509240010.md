# Death Testament – Runtime Surface Sync

## Scope
- Align startup orchestration summaries with Agno v2 dependency helpers (`lib/utils/startup_orchestration.py`, `lib/utils/startup_display.py`).
- Route CLI status surfaces through the v2 startup helpers (`cli/commands/service.py`) while keeping Docker/simple sync flow intact (`api/serve.py`).
- Strip legacy context injection from the version factory and rely on session state/dependency metadata (`lib/utils/version_factory.py`).
- Extend targeted unit coverage for the new pathways (`tests/lib/utils/test_startup_orchestration.py`, `tests/lib/utils/test_version_factory.py`, `tests/cli/commands/test_service.py`).

## Change Log
- Added dependency profile extraction + runtime summary builder and exposed optional knobs to skip watchers/services for lightweight snapshots (`lib/utils/startup_orchestration.py`).
- Enriched startup display rows with db labels + dependency metadata and surfaced totals in the footer (`lib/utils/startup_display.py`).
- Swapped legacy `context` wiring for session-state generation via `create_user_context_state` and stored runtime keys in agent metadata (`lib/utils/version_factory.py`).
- Introduced `_gather_runtime_snapshot` for CLI status, defaulted `HIVE_DEV_GRACEFUL` to opt-in, and surfaced runtime summary in `ServiceManager.status` (`cli/commands/service.py`).
- Updated the simplified API startup banner to pass placeholder dependency data and refreshed tests to validate the new semantics (`api/serve.py`, test modules).

## Validation
- `uv run pytest tests/lib/utils/test_version_factory.py tests/lib/utils/test_startup_orchestration.py::TestGetStartupDisplayWithResults::test_get_startup_display_with_results tests/lib/utils/test_startup_orchestration.py::TestRuntimeSummary::test_build_runtime_summary_includes_dependencies tests/cli/commands/test_service.py::TestServiceManagerInitialization::test_status tests/cli/commands/test_service.py::TestServiceManagerInitialization::test_runtime_snapshot_success tests/cli/commands/test_service.py::TestServiceManagerInitialization::test_runtime_snapshot_failure`
  - ✅ 9 tests passed; coverage plugin still emits parse warnings for pre-existing stub files.
- `uv run pytest --no-cov tests/cli -k service --maxfail=1 -q`
  - ✅ 19 tests reported as passed before teardown; pytest repeatedly raises a trailing `KeyboardInterrupt` from `unittest.mock` on exit even with coverage disabled. Results reflect a fully green run despite the noisy termination.

## Risks & Follow-ups
- Changing the default for `HIVE_DEV_GRACEFUL` to opt-in keeps the historical CLI test path, but environments that relied on implicit graceful shutdown must now export `HIVE_DEV_GRACEFUL=1`.
- The CLI runtime snapshot deliberately skips service initialization; if future call sites expect metrics/auth objects, we may need an enriched mode.
- KeyboardInterrupt noise from pytest exit remains unresolved; consider investigating upstream coverage/mock interaction to restore a clean exit code.

## Handoff Notes
- No docs were touched; if the CLI graceful mode change should be documented, queue a follow-up.
- Startup summary now includes db labels—downstream tooling that parses stdout should tolerate the extra column.
