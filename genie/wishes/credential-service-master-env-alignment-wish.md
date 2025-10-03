# 🧞 CREDENTIAL SERVICE MASTER ENV ALIGNMENT WISH

**Status:** APPROVED

## Executive Summary
Reinstate the credential service wiring so `make install` and CLI installs recreate/populate `.env` without attribute errors after the single-instance merge.

## Current State Analysis
**What exists:** `lib/auth/credential_service.py` now drives all credential setup, and installers call `CredentialService.install_all_modes()` during `uv run automagik-hive install`.
**Gap identified:** The refactor dropped the `master_env_file` alias, removed `DEFAULT_BASE_PORTS`, and changed the credential payload shape, so `_save_master_credentials()` crashes before `.env` is written.
**Solution approach:** Restore the constructor alias, add a small normalizer so `_save_master_credentials()` can work with the new payload, reintroduce default port constants, and cover the regression with focused tests.

## Change Isolation Strategy
- **Isolation principle:** Touch `lib/auth/credential_service.py` only, plus targeted installer/test adjustments where expectations broke.
- **Extension pattern:** Add a thin normalization helper rather than broad rewrites; keep signatures the same for CLI and Makefile callers.
- **Stability assurance:** Validated by the existing unit/integration suites so installers remain idempotent.

## Success Criteria
✅ `make install` (Makefile line 323) finishes without `AttributeError` and writes a populated `.env` when missing.
✅ Re-running `uv run automagik-hive install` skips regeneration unless `force_regenerate=True`.
✅ `uv run pytest tests/lib/auth/test_credential_service.py -q` passes with assertions on the shared `.env` alias.
✅ `uv run pytest tests/integration/auth/test_single_credential_integration.py -q` verifies end-to-end install and reuse.

## Never Do (Protection Boundaries)
❌ Reintroduce multi-mode credential scaffolding removed by the refactor.
❌ Touch credential files outside CredentialService helpers or bypass uv tooling.
❌ Alter installer prompts/UX beyond regression fixes.

## Technical Architecture
Credential Service:
├── lib/auth/credential_service.py       # Constructor alias, normalization helper, default constants

Install Surfaces:
├── cli/commands/service.py              # Calls `install_all_modes` during CLI install
├── cli/docker_manager.py                # Legacy path still referencing CredentialService
├── Makefile                             # `make install` calling `uv run automagik-hive install`

Tests:
├── tests/lib/auth/test_credential_service.py         # Initialization expectations
├── tests/integration/auth/test_single_credential_integration.py  # Installer E2E

### Naming Conventions
- Helpers stay snake_case (e.g., `_normalize_master_credentials`).
- Environment variables remain uppercase `HIVE_*`.
- Tests use existing `test_credential_service_*` naming.

## Task Decomposition

### Dependency Graph
```
A[Credential Fixes] ---> B[Test Coverage]
```

### Group A: Credential Fixes (Parallel)
Dependencies: None | Execute simultaneously

**A1-master-env-alias**: Restore constructor alias  @lib/auth/credential_service.py:40  Modifies: `__init__` to set `self.master_env_file` and keep `self.env_file` in sync  Success: `CredentialService()` exposes both attributes in all initialization paths.

**A2-port-defaults**: Reintroduce base port constants  @lib/auth/credential_service.py:30  Modifies: Restore `DEFAULT_BASE_PORTS` (or reuse `DEFAULT_PORTS`) so `extract_base_ports_from_env()` no longer raises  Success: Method returns defaults when `.env` missing.

**A3-credential-normalizer**: Align `_save_master_credentials` input  @lib/auth/credential_service.py:732  Modifies: Add helper or branch so install-generated payload is converted to expected keys before saving  Success: Fresh install writes `.env` without KeyError.

### Group B: Test Coverage (After A)
Dependencies: All tasks in Group A

**B1-unit-regression**: Extend unit test coverage  @tests/lib/auth/test_credential_service.py:12  Modifies: Add assertions for `master_env_file` alias, default port fallback, and normalization path  Success: `uv run pytest tests/lib/auth/test_credential_service.py -q` fails on current `dev` and passes post-fix.

**B2-integration-flow**: Verify installer reuse  @tests/integration/auth/test_single_credential_integration.py:49  Modifies: Add scenario covering fresh install + rerun reuse + force regeneration flag  Success: Prevents future regressions in credential install.

## Implementation Examples
```python
# lib/auth/credential_service.py
class CredentialService:
    def __init__(self, project_root: Path | None = None, env_file: Path | None = None) -> None:
        source = env_file if env_file is not None and project_root is None else (project_root or Path.cwd()) / ".env"
        self.project_root = (project_root or source.parent).resolve()
        self.master_env_file = source.resolve()
        self.env_file = self.master_env_file  # legacy alias
```

```python
    def _normalize_master_credentials(self, payload: dict[str, str]) -> dict[str, str]:
        if "postgres_user" in payload:
            return payload
        hive_key = payload["HIVE_API_KEY"]
        return {
            "postgres_user": payload["HIVE_POSTGRES_USER"],
            "postgres_password": payload["HIVE_POSTGRES_PASSWORD"],
            "api_key_base": hive_key[5:] if hive_key.startswith("hive_") else hive_key,
        }
```

## Testing Protocol
```bash
uv run pytest tests/lib/auth/test_credential_service.py -q
uv run pytest tests/integration/auth/test_single_credential_integration.py -q
```

## Validation Checklist
- [ ] `.env` file created/populated on fresh install.
- [ ] Second install detects existing credentials without regeneration.
- [ ] Force regenerate path recreates credentials cleanly.
- [ ] All credential-related pytest suites pass through `uv run`.
