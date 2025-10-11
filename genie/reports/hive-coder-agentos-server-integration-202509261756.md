# Hive Coder Death Testament — AgentOS Server Integration Fix

## Scope
- Resolve startup regression called out in `genie/reports/hive-reviewer-agentos-server-startup-202509261752.md` by removing the circular import between `lib.utils.version_factory` and `lib.services.agentos_service`.
- Maintain wish requirements (AgentOS service still re-exported from `lib/services/__init__.py`) while restoring server launch with Agno v2 + AgentOS wiring.

## Timeline & Evidence
1. **Reproduction (RED)**
   - `uv run python -c "import api.serve"`
   - Result: ImportError due to partial initialization of `lib.utils.version_factory` triggered via `AgentOSService` ➜ `AgentRegistry` ➜ `version_factory`.
2. **Implementation (GREEN)**
   - Deferred registry imports inside `lib/services/agentos_service.py` using helper accessors `_list_available_agents/teams/workflows()` to avoid module-level dependencies.
3. **Validation (GREEN)**
   - `uv run python -c "import api.serve"`
     - ✅ succeeds; logging initializes without traceback.
   - `HIVE_AUTH_DISABLED=false uv run pytest tests/api/routes/test_agentos_router.py tests/cli/commands/test_agentos_cli_command.py tests/lib/services/test_agentos_service.py`
     - ✅ 13 tests passed (warnings unchanged legacy noise).

## Files Touched
- `lib/services/agentos_service.py`
  - Introduced lazy import helpers and guarded type-checking block to break cycle while preserving behaviour.

## Risks & Follow-Ups
- Lazy imports add minor runtime overhead when first resolving registry lists; acceptable given significant reduction in startup risk.
- Coverage warnings from unrelated legacy modules persist; no new warnings introduced.
- Recommendation: future refactor could centralize registry metadata access to avoid repeated dynamic imports.

## Handoff Notes
- Server startup validated; Genie may re-run end-to-end orchestration scripts if desired.
- No documentation changes required; tests already cover API/CLI/service flows.
