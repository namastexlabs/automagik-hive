# Forge Plan – Credential Service Master Env Alignment

## Discovery
- **Wish:** `genie/wishes/credential-service-master-env-alignment-wish.md`
- **Status:** APPROVED
- **Goal:** Restore credential installation so `.env` creation/reuse works post-refactor, eliminating AttributeError during `make install`.
- **Key Constraints:** No reintroduction of multimode scaffolding; updates confined to credential service and minimal installer/test touch points; must use `uv run` for validation.
- **Risks:** Regression in credential file handling, missing coverage allowing future refactor to break alias again.

## Planning (Pending Approval)

### Group 1 – credential-fixes
- **Agent:** `hive-coder`
- **Scope:** Implement constructor alias, restore base port defaults, add credential payload normalization, and ensure `install_all_modes()` uses it. Touch `lib/auth/credential_service.py` plus any minimal callers needed for compatibility.
- **Dependencies:** None
- **Evidence Expectations:**
  - Death Testament documenting code changes and commands executed.
  - `uv run automagik-hive install --help` or equivalent smoke showing credential path loads.

### Group 2 – credential-tests
- **Agent:** `hive-tests`
- **Scope:** Extend unit and integration tests to cover alias, default port fallback, install reuse, and force regeneration scenarios (`tests/lib/auth/test_credential_service.py`, `tests/integration/auth/test_single_credential_integration.py`).
- **Dependencies:** Group 1
- **Evidence Expectations:**
  - Death Testament with executed pytest commands.
  - `uv run pytest tests/lib/auth/test_credential_service.py -q`
  - `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`

## Approval Log
- 2025-09-24T14:44Z – Approved by Human reviewer (chat confirmation)

## Execution Log
- 2025-09-24T15:20Z – Created forge task for credential-fixes (agent: hive-coder) → Task `df0897ae-18de-433e-93b6-a90029c3672c`, branch `forge/credential-service-master-env-alignment/credential-fixes`
- 2025-09-24T15:20Z – Created forge task for credential-tests (agent: hive-tests) → Task `ee9d4fa1-4fb5-4606-a775-b25d4cbf5c2b`, branch `forge/credential-service-master-env-alignment/credential-tests`
