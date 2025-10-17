# Death Testament – Agno AgentOS Foundation Settings

## Scope
- Extend Hive runtime settings with playground embedding and Control Pane metadata (`lib/config/settings.py`).
- Mirror the new toggles in the server singleton to expose derived URLs (`lib/config/server_config.py`).
- Surface Playground and AgentOS availability within startup summaries (`lib/utils/startup_orchestration.py`, `lib/utils/startup_display.py`).
- Refresh Docker guidance to position Hive as the authoritative Playground/Control Pane host (`docker/README.md`, `docker/main/docker-compose.yml`).

## Change Log
- Added `hive_embed_playground`, `hive_playground_mount_path`, and `hive_control_pane_base_url` fields with defaults that preserve existing behaviour.
- Provided `ServerConfig` helpers for playground/control pane URLs, validation for override schemes, and normalized mount paths.
- Populated startup displays with surface tables and enriched runtime summaries with surface metadata for downstream consumers.
- Documented the new environment variables and clarified that compose stacks should proxy the Hive API instead of exposing a standalone Playground port.

## Validation
- `uv run uvicorn api.serve:app --help`
  - ✅ Command executes with the updated configuration helpers; help text renders without errors after environment evaluation.

## Risks & Follow-ups
- `HIVE_PLAYGROUND_MOUNT_PATH` currently informs URLs and documentation; the Agno Playground router still controls its internal prefix until later phases adjust mounting.
- Filesystem checks for `HIVE_AGENTOS_CONFIG_PATH` assume local accessibility; remote loaders may need a future abstraction layer.
- Compose documentation referenced in the wish (`agent-infra-docker/README.md`) was absent in the workspace; adjusted existing Docker docs instead and flagged for follow-up alignment if the legacy path resurfaces.

## Handoff Notes
- No tests were added; future phases should extend coverage once the Control Pane integration lands.
- Startup output now includes a "Runtime Surfaces" table—update any log parsers or dashboards that consume the banner.
