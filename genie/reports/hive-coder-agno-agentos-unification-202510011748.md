# Death Testament – Agno AgentOS Unification Runtime

## Scope
- Surface Genie wish catalog through a protected `/api/v1/wishes` endpoint.
- Align production (`api/serve.py`) and development (`api/main.py`) apps with the shared router stack.
- Respect the `hive_embed_playground` toggle while mounting Agno Playground routes.

## Files Touched
- `api/dependencies/wish.py`
- `api/routes/wish_router.py`
- `api/routes/v1_router.py`
- `api/main.py`
- `api/serve.py`
- `tests/api/routes/test_wish_router.py`

## Validation
- `uv run pytest tests/api/routes/test_wish_router.py -q`
- `uv run pytest tests/api/routes/test_v1_router.py -q`
- `uv run pytest tests/api/test_main.py -q`
- Manual smoke: `uv run python -c "…"` (FastAPI `TestClient` proving `/api/v1/wishes` listing under patched auth)

All executed commands succeeded; coverage emitted long-standing warnings about optional `coverage` parsing and pydantic deprecations.

## Evidence Highlights
- `/api/v1/wishes` now returns parsed metadata (`id`, `title`, `status`, `path`) from `genie/wishes/*.md` when auth dependency is satisfied.
- Requests without `x-api-key` receive `401` via the shared `require_api_key` dependency.
- `hive_embed_playground = False` now skips router inclusion with an explicit log message.
- Development app (`api/main.py`) consumes the same `wish_router`, ensuring parity with production mounts.

## Risks & Follow-ups
- `tests/api/test_serve.py` still depends on the external `agno` distribution; running the suite without those stubs raises `ModuleNotFoundError`. Recommendation: retain existing module patching or extend it to cover `agno.os.config` when that suite is re-enabled.
- Genie wish parsing currently reads files eagerly on each request; caching or pagination may be required once catalog size grows.
- Downstream consumers should verify that the Control Pane honours the authenticated `/api/v1/wishes` endpoint.

## Handoff Notes
- No schema changes required; API docs will reflect the new route automatically when docs are enabled.
- Consider backfilling integration coverage for Playground endpoints once Agno v2 migrations stabilize.
