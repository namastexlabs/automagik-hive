# Death Testament – Agno AgentOS Alignment

## Scope
- Extend `AgentOSService` interfaces with Control Pane, Playground, and wish catalog routes derived from Hive settings.
- Refresh AgentOS dependency caching to respect runtime toggles for playground embedding and control pane overrides.
- Restore legacy `/config` alias while keeping `/agentos/config` and update README guidance for Agno Control Pane wiring.
- Harden unit and API tests to verify interface metadata and settings-driven URLs.

## Files Touched
- `lib/services/agentos_service.py`
- `api/dependencies/agentos.py`
- `api/routes/agentos_router.py`
- `tests/lib/services/test_agentos_service.py`
- `tests/api/routes/test_agentos_router.py`
- `tests/api/test_agentos_config.py`
- `README.md`

## Validation
- `uv run pytest tests/lib/services/test_agentos_service.py -q`
  - ✅ Pass (warnings from pydantic deprecations and coverage parsing match existing baseline).
- `uv run pytest tests/api/routes/test_agentos_router.py -q`
  - ✅ Pass after reinstating `/config` alias (same coverage warnings).
- `uv run pytest tests/api/test_agentos_config.py -q`
  - ✅ Pass (same warning set).
- `uv run python ...` (TestClient request to `/api/v1/agentos/config`)
  - ✅ Returned interfaces:
    ```json
    {
      "agentos-config": "http://localhost:8887/api/v1/agentos/config",
      "playground": "http://localhost:8887/playground",
      "wish-catalog": "http://localhost:8887/api/v1/wishes",
      "control-pane": "http://localhost:8887"
    }
    ```

## Risks & TODOs
- Coverage warnings flag pre-existing files (`lib/utils/error_handlers.py`, `lib/utils/fallback_model.py`) that fail coverage parsing; no changes made in this pass.
- `/api/v1/wishes` is referenced but not yet implemented—future phases must supply the endpoint before Control Pane integrations rely on it.
- Consider extending broader test suites once wish/catalog APIs land to keep interfaces synced.

## Handoff Notes
- README now documents how to source Control Pane URLs from the config endpoint; ensure ops teams update runbooks.
- Dependency provider caches by signature—changing `HIVE_CONTROL_PANE_BASE_URL`, `HIVE_PLAYGROUND_MOUNT_PATH`, or AgentOS config path will spin a fresh service instance automatically.
