# Hive QA Testament — Agno Migration Readiness
Date (UTC): 2025-09-25T20:29Z
Wish: `genie/wishes/agno-v2-migration-wish.md`
Role: Hive QA Tester • Validation Scout

## Phase 0 – Plan
- Reviewed wish success criteria, validation checklist, and prior hive reports linked from the wish.
- Prioritized verification of Agno version pin, proxy/knowledge factories, API surface tests, and smoke script referenced in the wish.
- Targeted uv-only command execution per tooling guardrails.

## Phase 1 – Execute
1. **Agno version pin (PASS)**
   - `uv run python -c "import agno; assert agno.__version__ == '2.0.8'; print(agno.__version__)"`
   - Output: `2.0.8` (virt env `.venv`, CPython 3.12.11).

2. **Proxy suite sanity (PASS with coverage warnings)**
   - `uv run pytest -q tests/lib/utils/test_proxy_agents.py tests/lib/utils/test_proxy_teams.py`
   - 118 tests passed. Coverage emitted parse warnings for `lib/utils/error_handlers.py` and `lib/utils/fallback_model.py` (existing known issue).

3. **Memory factory regression (PASS with coverage warnings)**
   - `uv run pytest -q tests/lib/memory/test_memory_factory.py`
   - 3 tests passed; same coverage parse warnings.

4. **Knowledge factory regression (PASS with coverage warnings)**
   - `uv run pytest -q tests/lib/knowledge/test_knowledge_factory.py`
   - 6 tests passed; same coverage parse warnings.

5. **Knowledge datasource coverage (PASS)**
   - `uv run pytest -q tests/lib/knowledge/datasources/test_row_based_csv.py`
   - 15 tests passed; coverage warnings identical to above.

6. **Agent lifecycle smoke (PASS)**
   - `uv run pytest -q tests/ai/agents/test_registry_ext.py::TestIntegrationScenarios::test_full_agent_lifecycle`
   - Scenario passed; verifies `dependencies` + `db` wiring.

7. **API routers & dependencies (PASS with warnings)**
   - Executed individually due to full-suite timeout:
     - `uv run pytest -q tests/api/routes/test_health.py`
     - `uv run pytest -q tests/api/routes/test_version_router.py`
     - `uv run pytest -q tests/api/routes/test_mcp_router.py`
     - `uv run pytest -q tests/api/routes/test_v1_router.py`
     - `uv run pytest -q tests/api/dependencies/test_message_validation.py`
     - `uv run pytest -q tests/api/test_main.py`
   - All passed. `test_mcp_router` triggered runtime warnings (`api/routes/mcp_router.py:90` coroutine not awaited) indicating async cleanup gap.

8. **API settings validation (FAIL — 4 regressions)**
   - `uv run pytest -q tests/api/test_settings.py`
   - Failures: `test_default_settings_development`, `test_development_cors_origins`, `test_set_cors_origin_list_development`, `test_settings_isolation`.
   - Actual `cors_origin_list` returned `['http://localhost:3000', 'http://localhost:8080']`; tests expect wildcard `['*']` in development. Root cause: `tests/conftest.py:186` seeds `HIVE_CORS_ORIGINS`, so new ApiSettings logic no longer aligns with test expectations. Needs code/test reconciliation before release.

9. **Proxy smoke script from wish (FAIL)**
   - `uv run python -c "from lib.utils.agno_proxy import create_sample_agent; agent = create_sample_agent(); ..."`
   - Raised `ImportError: cannot import name 'create_sample_agent'`. Wish still references removed helper; documentation requires update or replacement command.

10. **Wish-listed proxy test command (DOC GAP)**
    - Initial wish command `uv run pytest -q tests/lib/test_proxy_agents.py tests/lib/test_proxy_teams.py` fails (`file or directory not found`). Actual paths live under `tests/lib/utils/`. Wish instructions should be corrected.

## Phase 2 – Report

### Summary
- Core lib + knowledge + agent lifecycle tests pass under uv tooling with existing coverage warnings.
- API surface tests pass individually; asynchronous tool failure warning surfaced in MCP router mocks.
- API settings suite reveals four failing cases around development CORS defaults — current behaviour diverges from documented expectation and blocks completion.
- Wish smoke command references deprecated helper; needs replacement to keep validation checklist actionable.
- Validation checklist in wish remains unchecked (`- [ ]` items) despite evidence; requires author review before marking production-ready.

### Bugs & Coverage Gaps
1. **Dev CORS expectations out of sync** (`tests/api/test_settings.py`, `api/settings.py`). Development should default to `['*']` per tests/wish; current behaviour honours env list seeded in `tests/conftest.py`. Decide whether code or tests need update; track via follow-up Forge task.
2. **Legacy helper removal** (`lib/utils/agno_proxy.py`). Wish’s smoke instructions fail because `create_sample_agent` no longer exists. Update wish/docs with new sample path.
3. **Async warning in MCP router** (`api/routes/mcp_router.py:90`). Unawaited coroutine during error-path tests; investigate to avoid resource leaks in production.
4. **Wish checklist left unchecked** (`genie/wishes/agno-v2-migration-wish.md`). Confirm each criterion, mark appropriately to prevent confusion post-QA.

### Evidence Attachments
- Pytest output snippets stored in terminal history (see above commands).
- Coverage warnings consistent across runs pointing to existing parsing issue (not new to migration but noted).

### Recommended Next Actions
1. Align ApiSettings dev CORS behaviour with test expectations or update tests + wish narrative; re-run `tests/api/test_settings.py` post-fix (focus on `cors_origin_list`).
2. Replace/remove `create_sample_agent` smoke step in wish; provide verified alternative command.
3. Address async warning in MCP router mocks; ensure coroutine context managers handle failures cleanly (add regression test if missing).
4. Update wish validation checklist to `[x]` / `[ ]` based on verified outcomes once above issues resolved; rerun QA sweep to capture fresh evidence.

