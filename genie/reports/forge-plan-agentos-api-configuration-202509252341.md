# Forge Plan • AgentOS API Configuration

**Wish:** @genie/wishes/agentos-api-configuration-wish.md  
**Status:** Planning Approved (human confirmation received)

## Discovery Notes
- Agno v2 migration completed but platform still lacks AgentOS configuration surface.  
- Wish mandates YAML + typed configuration support, new service facade, protected FastAPI endpoint, optional CLI command, and full test/docs coverage.  
- Registry audit shows only filesystem YAML provides agent/team/workflow IDs; no quick prompt corpus exists yet for AgentOS chat configuration.  
- Automagik-specific memory and knowledge tables live in `HiveSettings`/factory modules and must be surfaced without modifying `pyproject.toml`.  
- Critical constraints: retain API key protection, avoid pyproject edits, leverage `uv` tooling, and keep AgentOS logic isolated under `lib/agentos/`.

## Proposed Task Groups

### Group 1 – config-foundation
- **Scope:** Implement AgentOS config models & YAML loader utilities, expose settings hooks (`hive_agentos_config_path`, `hive_agentos_enable_defaults`). Establish default YAML artifact that supplies quick prompts, display names, and DB IDs sourced from `HiveSettings`, `lib/memory/config.yaml`, and `lib/knowledge/config.yaml`.  
- **Agent:** `hive-coder`
- **Dependencies:** None.  
- **Key Outputs:** `lib/agentos/config_models.py`, `lib/agentos/config_loader.py`, default YAML, settings validations.  
- **Evidence:** Death Testament summarizing loaders + Pydantic validation, including confirmation that default quick prompts and database references align with current registries; targeted unit scaffolds (if any) noted for Group 3 tests.

### Group 2 – runtime-services
- **Scope:** Build `AgentOSService`, integrate loader, aggregate registry metadata (agents, teams, workflows, databases) using lightweight `list_*` calls (no deferred instantiation), map DB identifiers from `HiveSettings`/factory helpers, and register in service exports.  
- **Agent:** `hive-coder`
- **Dependencies:** Group 1.  
- **Key Outputs:** `lib/services/agentos_service.py`, updates to `lib/services/__init__.py`, caching logic, quick prompt normalization helpers.  
- **Evidence:** Death Testament with service usage example + manual serialization snippet that demonstrates agent/team/workflow listings and resolved DB metadata; readiness notes for API wiring.

### Group 3 – api-cli-integration
- **Scope:** Add FastAPI dependency provider + router (`/api/v1/agentos/config`), wire router in `api/main.py` / `api/routes/v1_router.py`, add optional CLI inspection command and any startup touchpoints, and expose a `/config` alias if the Agno control plane still expects the legacy path.  
- **Agent:** `hive-coder`
- **Dependencies:** Groups 1 & 2.  
- **Key Outputs:** `api/dependencies/agentos.py`, `api/routes/agentos_router.py`, CLI command updates, startup orchestration adjustments, docstring & logging.  
- **Evidence:** Endpoint smoke snippet, CLI invocation notes, confirmation of API key protection, and compatibility note for the `/config` alias.

### Group 4 – validation-and-docs
- **Scope:** Create pytest coverage for loaders/service/API/CLI; update README or ops docs with configuration + inspection instructions, and cover both `/api/v1/agentos/config` and legacy `/config` alias responses.  
- **Agent:** `hive-tests`
- **Dependencies:** Groups 1–3.  
- **Key Outputs:** `tests/lib/services/test_agentos_service.py`, `tests/api/test_agentos_config.py`, `tests/cli/test_agentos_command.py`, documentation updates.  
- **Evidence:** Death Testament citing `uv run pytest` commands, doc diff summary, confirmation of API auth guard behaviour, and compatibility validation for both route paths plus quick prompt coverage.

## Approval Tracking
- _Pending human decision._


- Approval: Human confirmed plan (Option 1) at 2025-09-25 23:45 UTC

## Execution Log
- Group 1 (config-foundation): Task `feat: agentos config foundation` → ID 9f6996b4-c1d9-4421-bec6-1dd304bdee66, branch `feat/agentos-config-foundation` (status: todo).
- Group 2 (runtime-services): Task `feat: agentos service runtime` → ID d5caf8a3-e698-4230-b9af-a6a746710914, branch `feat/agentos-service-runtime` (status: todo).
- Group 3 (api-cli-integration): Task `feat: agentos api cli integration` → ID 1ae46ef0-dc13-4bbb-a7db-fe2db4939de7, branch `feat/agentos-api-cli` (status: todo).
- Group 4 (validation-and-docs): Task `test: agentos validation and docs` → ID 62281056-5a22-4355-bfbe-23d536238d0f, branch `test/agentos-validation-docs` (status: todo).
