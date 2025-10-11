# Forge Plan – Credential Service Env Split

## Discovery Recap
- Wish: `genie/wishes/credential-service-env-split-wish.md` (status: DESIGN APPROVED – PREP FOR FORGE)
- Goal: Extract `.env` lifecycle responsibilities from `CredentialService` into a dedicated manager while preserving alias reuse, installer flows, and docker orchestration.
- Constraints: Maintain `.env`/`.env.master` parity, avoid breaking CLI/docker mocks, keep UV-only tooling, and leave MCP sync behavior intact.
- Risks: legacy alias-only installs, docker compose bootstrap relying on `install_all_modes()`, `save_credentials_to_env` overload used by docker manager, and widespread `CredentialService` patching in tests.

## Planning (Pending Approval)

### Group 1 – env-manager-implementation
- **Agent:** `hive-coder`
- **Scope:**
  - Introduce `EnvFileManager` (module under `lib/auth` or `lib/env`) handling env path resolution, template hydration, alias sync, read/write, and extraction helpers.
  - Refactor `CredentialService` to compose the manager (optional injection) while delegating env IO, preserving public API (`install_all_modes`, `save_credentials_to_env`, etc.).
  - Update MCP sync and docker/postgres helpers to use the new manager APIs without altering behavior.
- **Dependencies:** Discovery complete; no blocking tasks.
- **Evidence Expectations:**
  - Death Testament with command log.
  - `uv run pytest tests/lib/auth/test_credential_service.py -q`
  - `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`
  - Smoke: `uv run automagik-hive install --help`

### Group 2 – env-manager-tests
- **Agent:** `hive-tests`
- **Scope:**
  - Add focused tests for `EnvFileManager` covering alias-first reads, template fallback, error handling, and base port extraction.
  - Adjust existing CLI/docker/credential tests to accommodate dependency injection or new seams without weakening assertions.
  - Ensure mocks patch either the manager or `CredentialService` wrappers appropriately.
- **Dependencies:** Requires Group 1 branch/artifacts.
- **Evidence Expectations:**
  - Death Testament with executed pytest commands.
  - `uv run pytest tests/lib/auth/test_credential_service.py -q`
  - `uv run pytest tests/cli/test_docker_manager.py -q`
  - `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`

### Group 3 – env-manager-docs (Optional)
- **Agent:** `hive-coder`
- **Scope:** Update `lib/auth/CREDENTIAL_INTEGRATION.md`, wish doc, and any onboarding notes to describe the new manager contract and injection expectations.
- **Dependencies:** After Groups 1 & 2.
- **Evidence Expectations:**
  - Death Testament referencing updated docs and validation of links/anchors.

### Group 4 – env-manager-docker-alignment
- **Agent:** `hive-coder`
- **Scope:**
  - Reconcile `cli/docker_manager.py` behaviour with `tests/cli/test_docker_manager.py` expectations (Dockerfile paths, compose files, port mappings, data directory ownership, concurrent safety).
  - Decide with product owners whether to restore multi-component (agent/genie) support or update tests to new workspace-only direction; document rationale in Death Testament.
  - Ensure follow-up adjustments keep EnvFileManager integration intact and retain alias-first semantics.
- **Dependencies:** Groups 1 & 2 completed; coordinates with docs group if API changes.
- **Evidence Expectations:**
  - Death Testament summarizing behavioural decision.
  - `uv run pytest tests/cli/test_docker_manager.py -q`
  - Regression sweeps: `uv run pytest tests/lib/auth/test_credential_service.py -q`, `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`.

## Approval Log
- 2025-09-24T17:54Z – Approved by human (chat confirmation)

## Execution Log
- 2025-09-24T17:55Z – Created forge task for env-manager-implementation (agent: hive-coder) → Task `c3a72043-c24a-42cf-ade8-0a29dfc68ab4`, branch `forge/credential-service-env-split/env-manager-implementation`
- 2025-09-24T17:55Z – Created forge task for env-manager-tests (agent: hive-tests) → Task `10027d2f-63dc-4204-9412-2ec356522fe0`, branch `forge/credential-service-env-split/env-manager-tests`
- 2025-09-24T17:55Z – Created forge task for env-manager-docs (agent: hive-coder) → Task `46ef53f1-7318-44d9-9765-984e6eeab53c`, branch `forge/credential-service-env-split/env-manager-docs`
- 2025-09-24T19:11Z – Env manager tests completed. Death Testament: @genie/reports/hive-tests-env-manager-tests-202509241911.md
- 2025-09-24T19:19Z – Env manager docs completed. Death Testament: @genie/reports/hive-coder-credential-service-env-manager-docs-202509241919.md
- 2025-09-24T17:58Z – Created forge task for env-manager-docker-alignment (agent: hive-coder) → Task `7022f49e-227a-42da-a045-7be24e36977d`, branch `forge/credential-service-env-split/env-manager-docker-alignment`
