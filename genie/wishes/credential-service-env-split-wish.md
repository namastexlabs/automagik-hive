# 🧞 CREDENTIAL SERVICE ENV SPLIT WISH

**Status:** PHASE 3 – DOCS COMPLETE (awaiting human review)

## Executive Summary
Separate `.env` file management from `CredentialService` so credential generation stays focused on secrets while file orchestration moves into a dedicated collaborator. This reduces side effects, makes alias syncing reusable, and clarifies ownership for installers and future services.

## Current State Analysis
**What exists:** `CredentialService` generates credentials and directly mutates `.env` / `.env.master`, handling template hydration, alias syncing, and reuse detection.
**Pain point:** File lifecycle logic mixes with credential normalization, making the class large, hard to test, and risky to change.
**Opportunity:** Extract environment-file responsibilities into an `EnvFileManager` (or similar) that provides explicit APIs for reading, writing, and alias sync.

## Success Criteria
✅ Clear boundary: `CredentialService` delegates `.env` writes/reads to a new component.
✅ Alias sync and fallback logic fully covered by tests independent of credential generation.
✅ CLI/Makefile installers continue passing without pull-through changes.

## Guardrails
❌ No regression to `.env` + `.env.master` behavior.
❌ Keep UV tooling intact; no direct `python` commands.
❌ Avoid broad refactors beyond splitting responsibilities.

## Initial Thoughts / Questions
- Should the manager live under `lib/env/` or alongside CredentialService?
- Do we need dependency injection for easy testing, or is composition enough?
- How do we stage the split to avoid breaking existing forge tasks for credential fixes/tests?

**Next step:** Discovery plan & forge grouping after human alignment.

## Discovery Findings (Phase 1)
- **Env-touching methods inside CredentialService**:
  - `__init__`, `_refresh_master_env_pointer`, `_active_env_source` manage `.env`/`.env.master` path resolution and alias preference (`lib/auth/credential_service.py:60-102`).
  - `_save_master_credentials`, `_get_base_env_template`, `_create_mode_env_file` perform template hydration, alias mirroring, and per-mode file writes (`lib/auth/credential_service.py:961-1105`).
  - `extract_postgres_credentials_from_env`, `extract_hive_api_key_from_env`, `_extract_existing_master_credentials`, `extract_base_ports_from_env` parse env content for reuse/default logic (`lib/auth/credential_service.py:203-609`, `858-923`).
  - `save_credentials_to_env` writes directly to `.env` and preserves existing keys (`lib/auth/credential_service.py:290-377`).
  - `sync_mcp_config_with_credentials` writes `.mcp.json`; should share the same file manager primitives if we centralize IO (`lib/auth/credential_service.py:378-461`).
  - `install_all_modes`, `setup_complete_credentials`, and legacy CLI helpers call the save/extract paths above; any split must maintain these indirect dependencies (`lib/auth/credential_service.py:786-856`, `520-606`).

- **Primary call sites / stakeholders**:
  - CLI installer path `cli/commands/service.py:126-208` constructs `CredentialService(project_root=workspace)` and relies on `install_all_modes()` for env persistence.
  - `cli/docker_manager.py:65-382` and `docker/lib/postgres_manager.py:20-371` use `CredentialService` for setup/reuse during container operations.
  - Makefile target `make install` shells into `uv run automagik-hive install`, which routes through the CLI code path above.
  - Tests exercising env behavior: `tests/lib/auth/test_credential_service.py`, `tests/integration/auth/test_single_credential_integration.py`, plus CLI/docker integration suites listed in `tests/cli/test_docker_manager.py` and `tests/integration/docker/test_compose_service.py`.
  - Numerous CLI unit suites mock `CredentialService` (`tests/cli/commands/test_service.py`, `tests/cli/test_docker_manager.py`). Injecting a manager must not break patch targets; consider providing a property or setter for the new collaborator.

- **Supporting data structures likely to migrate**:
  - `DEFAULT_PORTS` / `DEFAULT_BASE_PORTS` and alias-aware helpers currently live on `CredentialService` but conceptually belong to the env manager for parsing defaults.
  - Template strings for new env files (`_get_base_env_template`) and alias naming logic (`self.master_env_alias`).

- **Behavioral expectations to preserve**:
  - Alias-first reuse: `.env.master` should remain authoritative when present.
  - Template fallback when neither `.env` nor `.env.master` exists, including logging semantics.
  - MCP sync should continue reading the same env content without duplicating state.

## Target Architecture Sketch (Phase 2)
- **Proposed component**: `EnvFileManager` (working name) living under `lib/auth` or new `lib/env/` namespace.
  - Responsibilities: resolve env/alias paths, load content, apply template hydration, sync alias, expose parsed views (postgres creds, API key, base ports), and surface write helpers accepting normalized payloads.
  - API candidates:
    - `active_env_path() -> Path`
    - `read() -> str` / `write(str) -> None`
    - `ensure_base_template() -> str`
    - `sync_alias() -> None`
    - `extract_postgres_section() -> dict[str, str | None]`
    - `extract_api_key() -> str | None`
    - `update_master_credentials(payload: dict[str, str]) -> None`
  - Construction: `CredentialService` composes an EnvFileManager instance (default) but accepts one via optional parameter for testing/injection.
  - Error flow: manager raises dedicated exceptions (e.g., `EnvFileError`) so CredentialService can translate to user-facing logs without duplicating try/except blocks.
  - Telemetry: low-level logging stays in manager for IO events; CredentialService logs business-level decisions (reuse vs regenerate).

- **Integration outline**:
  - Refactor `CredentialService.__init__` to accept `env_manager: EnvFileManager | None`.
  - Move env parsing/writing helpers into manager; keep credential generation/token logic in CredentialService.
  - Update MCP sync to use manager read/write utilities instead of direct `Path` operations.

## Impact & Risk Assessment
- **Compatibility hazards**:
  - Legacy installs with alias-only files must still reuse credentials; ensure manager chooses `.env.master` when `.env` missing.
  - Docker workflows rely on `install_all_modes()` side effects; regression here blocks `docker compose` bootstrap (`docker/lib/compose_service.py:34-93`).
  - Coverage harness warns about unrelated modules; splitting code should not resurrect the earlier AttributeErrors noted in Death Testaments (`genie/reports/hive-tests-credential-service-master-env-alignment-202509241611.md`).
  - CLI mocks patch `CredentialService` directly; sudden constructor signature changes without defaults will break dozens of tests (`tests/cli/commands/test_service.py`, `tests/cli/test_docker_manager.py`).
  - `save_credentials_to_env` currently accepts a path argument in docker manager code (`docker/lib/postgres_manager.py:356-363`); confirm the new abstraction keeps backward compatibility or adjust callers.

- **Test impact**:
  - Update existing unit/integration suites to use the manager (possibly inject fakes) while keeping assertions intact.
  - Add focused tests for new manager (temp directories verifying alias sync, template fallback, default port extraction).
  - Revisit CLI/docker mocks that patch `CredentialService` to ensure they either stub the manager or bypass it cleanly.
  - New manager should expose seam for tests to simulate I/O failures without monkeypatching `Path.write_text`. Consider fixtures returning stub manager objects.

- **Open questions**:
  - Should non-`.env` artifacts (e.g., `.mcp.json`) also move under the manager or stay in CredentialService?
  - Where should configuration live for alternate env filenames (future multi-tenant scenarios)?

## Execution Strategy & Forge Proposal
- **Phase 1 Forge Task – env-manager-implementation (agent: hive-coder)**
  - Introduce `EnvFileManager` module with read/write/alias-sync/template logic.
  - Refactor `CredentialService` to delegate env IO to the manager without changing public API.
  - Ensure docker/CLI entry points remain untouched apart from constructor wiring.
  - Evidence: branch-level pytest focus (`uv run pytest tests/lib/auth/test_credential_service.py -q`, integration suite), plus smoke `uv run automagik-hive install --help`.

- **Phase 2 Forge Task – env-manager-tests (agent: hive-tests)**
  - Add unit tests for the manager (happy path, alias-only path, template fallback, error handling).
  - Adjust integration tests to use manager-aware assertions where necessary.
  - Evidence: targeted pytest modules, Death Testament referencing new coverage.

- **Optional Phase 3 – docs/knowledge (agent: hive-coder or hive-quality)**
  - Update `lib/auth/CREDENTIAL_INTEGRATION.md` and wish docs to reflect the new component boundary.

- **Validation checklist (across phases)**
  - `uv run pytest tests/lib/auth/test_credential_service.py -q`
  - `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`
  - `uv run pytest tests/cli/test_docker_manager.py -q`
  - Smoke: `uv run automagik-hive install --help`

## Phase 3 Documentation Summary – 2025-09-24
- `lib/auth/CREDENTIAL_INTEGRATION.md` now documents `EnvFileManager` responsibilities, constructor injection patterns, and migration guidance for collaborators relying on credential flows.
- `README.md` onboarding instructions point new contributors to the CLI credential workflows backed by `CredentialService` + `EnvFileManager`.
- Death Testaments on record:
  - Implementation: @genie/reports/hive-coder-credential-service-env-manager-202509241824.md
  - Tests: @genie/reports/hive-tests-env-manager-tests-202509241911.md
  - Documentation: @genie/reports/hive-coder-credential-service-env-manager-docs-202509241919.md

## Wish Review – 2025-09-24
- Manual `/wish-review` audit executed (CLI helper missing); evidence captured in this wish and referenced Death Testaments.
- Validation commands rerun via UV tooling:
  - `uv run pytest tests/lib/auth/test_credential_service.py -q`
  - `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`
  - `uv run pytest tests/cli/test_docker_manager.py -q`
- All suites passed; lingering coverage warnings originate from legacy `lib/utils/*` modules documented in @genie/reports/hive-coder-credential-service-env-manager-202509241824.md.
- Readiness score: **100/100** – implementation, validation, and documentation complete with no residual wish-specific risks.

## Next Actions
- Human review: confirm documentation tone/coverage aligns with onboarding expectations and note any additional knowledge base updates.
- Consider scheduling follow-up wish for Docker manager expectations highlighted in env-manager-tests report if product direction changes.
