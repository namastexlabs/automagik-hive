# Hive Coder Death Testament

## Scope
- Align `CredentialService` master env handling to restore compatibility with installer payloads and master `.env` updates.

## Implementation Notes
- Reintroduced `DEFAULT_BASE_PORTS` and re-aligned `master_env_file` alias to the primary `.env` path for legacy compatibility.
- Added `_normalize_master_credentials_payload` helper and routed `install_all_modes()`+`_save_master_credentials()` through it to bridge new credential payload keys to the legacy schema.
- Ensured normalized data feeds credential persistence and outward compatibility with installer consumers.

## Files Touched
- `lib/auth/credential_service.py`

## Commands & Evidence
1. `uv run pytest tests/lib/auth/test_service.py`
   - Result: **Failed** (pre-existing). Missing `CredentialService.get_deployment_ports()` implementation causes `AttributeError`; `calculate_ports` test expects multi-mode support removed upstream.
2. `uv run automagik-hive install --help`
   - Result: **Passed**. CLI help renders without raising `AttributeError`, confirming credential service import/initialization succeeds after normalization changes.

## Risks & Follow-Ups
- Recommend routing to `credential-tests` group to resurrect/retire `get_deployment_ports` expectations or adjust coverage suites.
- No additional code refactors performed; multi-mode scaffolding remains deprecated per scope.

## Handoff
- Await direction on whether to patch legacy tests or document deprecation in wish plan before closing.
