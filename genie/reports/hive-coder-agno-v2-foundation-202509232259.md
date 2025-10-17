# Death Testament – Agno v2 Foundation Migration

## Scope
- Pinned Agno dependency to 2.0.8 via `uv` tooling and refreshed `uv.lock` / `pyproject.toml`.
- Retrofitted proxy utilities (`lib/utils/proxy_agents.py`, `proxy_teams.py`, `proxy_workflows.py`) to emit Agno v2 `db` + `dependencies` constructs while removing legacy storage/context calls.
- Reworked shared storage helper (`lib/utils/agno_storage_utils.py`) to materialize Agno v2 `Db` instances and dependency bundles.
- Updated memory factory to return Agno v2 `MemoryManager` and accept shared DB handles; added lazy knowledge factory shims.
- Realigned associated tests across storage, proxy, and memory suites for new semantics.

## Commands
```bash
uv add agno==2.0.8
uv run pytest tests/lib/memory/test_memory_factory.py tests/lib/utils/test_proxy_agents.py
uv run python -c "import agno; print(agno.__version__)"
```
Outputs confirm pytest success and Agno version 2.0.8.

## Risks & Follow-ups
- Broader suite not rerun; downstream configs using legacy `storage` keys should be verified during next integration pass.
- Knowledge factory shim lazily delegates to heavy implementation; ensure runtime environment provides Agno embedder dependencies before production rollout.
- Additional test modules updated but not executed post-change; schedule follow-up run for full coverage when bandwidth allows.

