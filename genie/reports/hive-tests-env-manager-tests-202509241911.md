# Hive Tests • Env Manager Tests

- Scope: Backfill unit tests for `EnvFileManager`; align suites for injected manager; validate installer regressions.
- Group: env-manager-tests • Branch: `forge/credential-service-env-split/env-manager-tests`

## Tests Added
- `tests/lib/auth/test_env_file_manager.py`
  - Alias-first reads and hydration from alias
  - Template fallback when `.env.example` missing (uses default template)
  - Base port extraction overrides (`HIVE_DATABASE_URL`, `HIVE_API_PORT`)
  - Update behavior with and without `create_if_missing`
  - Error handling: read/write failures are logged and non-fatal where designed

## Commands Run (UV-only)
1) uv run pytest tests/lib/auth/test_env_file_manager.py -q
   - Result: PASS (11 passed)

2) uv run pytest tests/lib/auth/test_credential_service.py -q
   - Result: PASS (existing suite green)

3) uv run pytest tests/integration/auth/test_single_credential_integration.py -q
   - Result: PASS (verifies fresh install creates primary and alias)

4) uv run pytest tests/cli/test_docker_manager.py -q
   - Result: FAIL (10 failing, 77 passing, 1 skipped)
   - Key failures (summarized):
     - Dockerfile path expectations for `agent` component vs current single `docker/main/Dockerfile` design
     - Data directory creation sudo-fallback not exercised by current implementation
     - Compose file path for `agent` expects `docker/agent/docker-compose.yml`; current manager maps workspace-only
     - Container set and port mapping parametrizations expect multiple modes; implementation exposes workspace path

## Evidence Excerpts
- Docker Manager failures (headlines):
  - test_get_dockerfile_path_agent: expected `docker/agent/Dockerfile.api`, got `docker/main/Dockerfile`
  - test_create_containers_via_compose_agent: expected agent compose path and service set
  - sudo fallback path: `Path.mkdir` not invoked in code path under test

## Intent and Coverage
- Alias reuse and template fallback validated via `EnvFileManager` tests (RED→GREEN captured above).
- Base port extraction logic validated; regression for installer flows (alias reuse) confirmed via integration test.
- CredentialService suites require no changes for manager injection; existing patches to `cli.docker_manager.CredentialService` remain effective.

## Gaps / Follow-ups
- Docker Manager expectations for multi-component (agent/genie) paths diverge from current code. Two options:
  - Update Docker tests to reflect workspace-only compose in this branch; or
  - Extend DockerManager to support agent paths as previously assumed (requires `hive-coder`).
- Recommendation: Route to `hive-coder` for a decision; avoid weakening test assertions without product alignment.

## Human Revalidation
- Run:
  - `uv run pytest tests/lib/auth/test_env_file_manager.py -q`
  - `uv run pytest tests/lib/auth/test_credential_service.py -q`
  - `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`
  - `uv run pytest tests/cli/test_docker_manager.py -q` (to review remaining deltas)

## Notes
- UV tooling respected throughout; no production code modified.
- All filesystem writes limited to `tests/` and `genie/reports/`.

