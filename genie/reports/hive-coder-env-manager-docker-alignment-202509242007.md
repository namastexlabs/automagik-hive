# Death Testament – env-manager-docker-alignment (hive-coder)

## Scope
- Align `DockerManager` with the post-split `EnvFileManager` contract now that `CredentialService.install_all_modes()` only provisions the workspace stack.
- Prune dormant agent/genie behaviours, refresh CLI workspace flows, and realign the docker manager test suite with the single-component product direction.

## Decision & Rationale
- Chose **Option B**: enforce single-component (workspace) behaviour. Evidence: `lib/auth/credential_service.py::install_all_modes` returns only a `"workspace"` entry, confirming multi-mode support was intentionally removed during the EnvFileManager split.
- Restored clarity by hardening unsupported component paths (explicit error messaging) instead of silently falling back to stale agent/genie metadata.

## Code Changes
- Introduced explicit workspace-only container metadata (`DockerManager.CONTAINERS`) and a helper to read the postgres image from compose files while defaulting safely when templates are absent.
- Simplified install flow: `--install all` now aliases to workspace, unsupported targets emit actionable errors, and interactive install removes agent/genie prompts while retaining database reuse safeguards.
- Tightened compose/data directory helpers to guard unsupported components and keep sudo fallback for workspace data ownership.

## Test Updates
- Reworked `tests/cli/test_docker_manager.py` to reflect the new contract: removed agent/genie scenarios, refreshed parametrisations, and updated concurrency expectations to include both workspace containers.
- Added coverage for docker-compose image fallback via `_get_postgres_image` and strengthened installation assertions for the `--install all` pathway.

## Validation Evidence
- Observed pre-change failure:
  - `uv run pytest tests/cli/test_docker_manager.py -q`
    - ❌ 10 failures (agent Dockerfile/compose expectations, port parametrisations, concurrency mismatch).
- Post-change verification:
  1. `uv run pytest tests/cli/test_docker_manager.py -q`
     - ✅ 82 passed, 1 skipped.
  2. `uv run pytest tests/lib/auth/test_credential_service.py -q`
     - ✅ 54 passed, 2 skipped.
  3. `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`
     - ✅ 3 passed.
- Coverage warnings about legacy utility modules persisted (pre-existing condition noted).

## Risks & Follow-ups
- Docs (`README.md`, installer guidance) still reference optional agent/genie setups; coordinate with env-manager-docs group to update messaging for workspace-only installs.
- If multi-component support returns, reintroduce dedicated compose templates + container names to avoid recreating the removed assumptions.
- Custom database flow remains manual; consider future enhancement to automate non-container installs or document explicit manual steps.

## Human Checklist
- ✅ Workspace install path validated via unit/integration suites.
- 🔁 Engage documentation owners to sync messaging on single-component Docker support.

