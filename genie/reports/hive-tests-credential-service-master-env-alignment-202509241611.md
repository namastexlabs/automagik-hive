# Hive Tests Death Testament

## Scope
- Backfilled regression coverage for credential master env aliasing, base port fallback, and normalized payload handling.
- Exercised install flows covering fresh install, alias-based reuse, and force regeneration.

## Commands & Outcomes
1. `uv run pytest tests/lib/auth/test_credential_service.py -q`
   - **Failed**: alias sync test (missing `.env.master`), alias-first base port fallback still honoring stale `.env`, docker detection raising `AttributeError: CONTAINERS`.
2. `uv run pytest tests/integration/auth/test_single_credential_integration.py -q`
   - **Failed**: fresh install lacks alias file; reuse + force regenerate scenarios regenerate unexpectedly without alias support.
3. `uv run pytest tests/lib/auth/test_credential_service.py -k "docker_not_available" -vv`
   - **Failed**: confirmed `CredentialService.detect_existing_containers` still references undefined `CONTAINERS` map.

## Evidence Highlights
- `tests/lib/auth/test_credential_service.py:554` – `.env.master` alias absent after `_save_master_credentials`.
- `tests/lib/auth/test_credential_service.py:575` – `master_env_file` remains `.env`, so base port fallback ignores alias and preserves legacy overrides (db: 6123, api: 9777).
- `tests/integration/auth/test_single_credential_integration.py:25` – fresh install does not materialize alias; downstream reuse/regenerate flows diverge from expected reuse semantics.
- `lib/auth/credential_service.py:689` – `detect_existing_containers` still relies on `CONTAINERS` constant removed in credential-fixes scope.

## Follow-Up Recommendations
1. `credential-fixes` implementation should:
   - Persist `.env.master` alongside `.env` and point `master_env_file` to the alias when present.
   - Update base port extraction to prioritize the alias and fall back to `DEFAULT_BASE_PORTS` when alias omits ports.
   - Restore or replace the `CONTAINERS` map to keep docker detection coverage green.
2. After fixes land, rerun both pytest commands above to capture passing evidence and refresh this report.
3. Update `genie/reports/forge-plan-credential-service-master-env-alignment-202509241443.md` execution log with Death Testament link once the plan report is restored in the branch workspace.

## Residual Risks
- Reuse logic currently depends solely on `.env`; alias-only environments (legacy installers) will unintentionally rotate credentials.
- Force regeneration does not recreate alias; downstream automation referencing `.env.master` will miss updated secrets.
- Docker detection remains broken until the missing container metadata is reinstated.
