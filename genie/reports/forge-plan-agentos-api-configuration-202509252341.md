# Forge Plan • AgentOS API Configuration

**Wish:** @genie/wishes/agentos-api-configuration-wish.md  
**Status:** Planning Approved (human confirmation received)

## Discovery Notes
- Agno v2 migration completed but platform still lacks AgentOS configuration surface.  
- Wish mandates YAML + typed configuration support, new service facade, protected FastAPI endpoint, optional CLI command, and full test/docs coverage.  
- Critical constraints: retain API key protection, avoid pyproject edits, leverage `uv` tooling, and keep AgentOS logic isolated under `lib/agentos/`.

## Proposed Task Groups

### Group 1 – config-foundation
- **Scope:** Implement AgentOS config models & YAML loader utilities, expose settings hooks (`hive_agentos_config_path`, `hive_agentos_enable_defaults`). Establish default YAML artifact.  
- **Agent:** `hive-coder`
- **Dependencies:** None.  
- **Key Outputs:** `lib/agentos/config_models.py`, `lib/agentos/config_loader.py`, default YAML, settings validations.  
- **Evidence:** Death Testament summarizing loaders + Pydantic validation; targeted unit scaffolds (if any) noted for Group 3 tests.

### Group 2 – runtime-services
- **Scope:** Build `AgentOSService`, integrate loader, aggregate registry metadata (agents, teams, workflows, databases), and register in service exports.  
- **Agent:** `hive-coder`
- **Dependencies:** Group 1.  
- **Key Outputs:** `lib/services/agentos_service.py`, updates to `lib/services/__init__.py`, caching logic, quick prompt normalization helpers.  
- **Evidence:** Death Testament with service usage example + manual serialization snippet; readiness notes for API wiring.

### Group 3 – api-cli-integration
- **Scope:** Add FastAPI dependency provider + router (`/api/v1/agentos/config`), wire router in `api/main.py` / `api/routes/v1_router.py`, add optional CLI inspection command and any startup touchpoints.  
- **Agent:** `hive-coder`
- **Dependencies:** Groups 1 & 2.  
- **Key Outputs:** `api/dependencies/agentos.py`, `api/routes/agentos_router.py`, CLI command updates, startup orchestration adjustments, docstring & logging.  
- **Evidence:** Endpoint smoke snippet, CLI invocation notes, confirmation of API key protection.

### Group 4 – validation-and-docs
- **Scope:** Create pytest coverage for loaders/service/API/CLI; update README or ops docs with configuration + inspection instructions.  
- **Agent:** `hive-tests`
- **Dependencies:** Groups 1–3.  
- **Key Outputs:** `tests/lib/services/test_agentos_service.py`, `tests/api/test_agentos_config.py`, `tests/cli/test_agentos_command.py`, documentation updates.  
- **Evidence:** Death Testament citing `uv run pytest` commands, doc diff summary, confirmation of API auth guard behaviour.

## Approval Tracking
- _Pending human decision._


- Approval: Human confirmed plan (Option 1) at 2025-09-25 23:45 UTC

## Execution Log
- Group 1 (config-foundation): Task `feat: agentos config foundation` → ID f2ed7c6e-3875-4006-aaa4-ecb874f7993e, branch `feat/agentos-config-foundation` (status: todo).
- Group 2 (runtime-services): Task `feat: agentos service runtime` → ID e5693393-4a0f-4e96-8bbd-c86a76a4ea27, branch `feat/agentos-service-runtime` (status: todo).
- Group 3 (api-cli-integration): Task `feat: agentos api cli integration` → ID 1ee928ed-3a47-4eb7-b131-ad2432d5177e, branch `feat/agentos-api-cli` (status: todo).
- Group 4 (validation-and-docs): Task `test: agentos validation and docs` → ID 51b12afc-0bc2-4a8b-b9d3-4a33b3484144, branch `test/agentos-validation-docs` (status: todo).
