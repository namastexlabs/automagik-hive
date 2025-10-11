# Hive Tests • Agno v2 Migration — Knowledge static gates + AI/Proxy suites

Scope: Validate ruff/mypy for `lib/knowledge/**` are green; run `tests/ai` and proxy suites; confirm targeted assertions for `dependencies` presence.

## Commands (UV only)
```bash
uv sync
uv run ruff check lib/knowledge --output-format concise
uv run mypy lib/knowledge --hide-error-codes --pretty
uv run pytest tests/ai -q
uv run pytest tests/lib/utils/test_proxy_agents.py tests/lib/utils/test_proxy_teams.py -q
```

## Results
- Ruff (lib/knowledge):
  - All checks passed!
- Mypy (lib/knowledge):
  - Success: no issues found in 15 source files
- Pytest (tests/ai):
  - PASS (excerpt)
  - 283 passed, 53 warnings in 6.58s
- Pytest (proxy suites):
  - PASS (excerpt)
  - 118 passed, 8 warnings in 5.72s

Raw excerpts
```text
Ruff: All checks passed!
Mypy: Success: no issues found in 15 source files

Pytest tests/ai -q
... 283 passed, 53 warnings in 6.58s

Pytest proxy suites -q
... 118 passed, 8 warnings in 5.72s
```

## Targeted assertions for `dependencies`
- Already present and passing in proxy tests:
  - `tests/lib/utils/test_proxy_agents.py` lines asserting presence of `dependencies` in processed kwargs and returns (e.g., 381–383, 492, 1244).
  - `tests/lib/utils/test_proxy_teams.py` lines asserting `dependencies` are carried through team config processing (e.g., 365–372, 536–543, 1140–1149).
- AI tests: No additional `dependencies`-specific assertions applicable; existing focus is registry/template agents/tools.

## Notes
- Stubs present: `pandas-stubs`, `types-PyYAML`, `types-tqdm` installed via `uv sync` (already in lock), supporting clean mypy.
- No production edits required for `lib/knowledge/**`; localized `# noqa: S324` already used where legacy MD5 is intentionally preserved.

## Re-run status
- No changes required after validation; re-running suites continues to pass.

## Next
- If any further repos sweep requires `dependencies` checks in AI domain, add assertions alongside concrete fixtures once surfaces expose them; current proxies already cover the presence/injection semantics.
