# 🧞 MCP LAZY CONNECTION WISH

**Status:** DRAFT

## Executive Summary
Ensure MCP-backed tools reconnect on demand so agents can reliably execute remote documentation searches without event-loop failures.

## Current State Analysis
**What exists:** `lib/utils/proxy_agents.py` eagerly connects every MCP server during agent fabrication and keeps the session object on the toolkit.
**Gap identified:** When the underlying loop restarts (uvicorn, CLI runs, etc.) those pre-opened sessions become invalid, leading to `RuntimeError: Event loop is closed` once a tool is actually invoked.
**Solution approach:** Store connection parameters at creation time, defer the real connection until tool-call execution, and guarantee clean teardown plus informative error propagation.

## Change Isolation Strategy
- **Isolation principle:** Encapsulate all lifecycle updates inside `lib/utils/proxy_agents.py` and supporting MCP helpers so higher layers only see a sturdier toolkit surface.
- **Extension pattern:** Add reconnection helpers that wrap existing include/exclude filtering rather than rewriting registries or catalog loading.
- **Stability assurance:** Preserve today’s YAML parsing outputs and tool-list metadata so previously working MCP servers keep functioning unchanged.

## Success Criteria
✅ Template agent lists MCP tools and successfully calls `resolve-library-id` even after multiple runs in the same process.
✅ First-time failures report actionable HTTP or transport details instead of hanging or returning generic loop errors.
✅ Calling code no longer opens persistent MCP sessions during agent boot, avoiding unnecessary resource usage.
✅ Unit and integration tests cover both healthy and failing MCP responses with deterministic behaviour.

## Never Do (Protection Boundaries)
❌ Modify `.mcp.json` defaults or rename existing MCP server entries.
❌ Strip out granular tool filtering (`include_tools` semantics) when refactoring wrappers.
❌ Introduce direct subprocess calls for reconnection that bypass the existing MCP client API.

## Technical Architecture

### Component Structure
- `lib/utils/proxy_agents.py` — central orchestrator that produces Agno agents and merges MCP toolkits.
- `lib/mcp/connection_manager.py` — catalog-aware connection helper for MCP servers (read-only context reference).
- `lib/mcp/catalog.py` — supplies server configuration (no behavioural changes expected beyond read access).
- `tests/lib/utils/test_proxy_agents_coverage.py` — regression harness ensuring proxy behaviour remains consistent.
- `tests/integration/test_agents_real_execution.py` — smoke suite that exercises real agent execution using MCP tooling.

### Naming Conventions
- Helper methods follow `_spawn_<thing>` / `_shutdown_<thing>` verbs inside `AgnoAgentProxy`.
- Stored metadata attributes on toolkits use `_automagik_*` prefix to avoid clashing with upstream Agno fields.
- New tests should live under `tests/lib/utils/test_mcp_proxy_lazy_connection.py` (snake_case file names).

## Task Decomposition

### Dependency Graph
```
A[Capture Connection Metadata] --> B[Lazy Connection Wrapper]
B --> C[Resource Lifecycle]
B --> C
C --> D[Testing]
```

### Group A: Capture Connection Metadata (Parallel)
Dependencies: None

**A1-store-params** – @lib/utils/proxy_agents.py#L927  
Record server name, include/exclude filters, and transport parameters on each `MCPTools` instance (e.g., `_automagik_params`).  
Success: Subsequent helpers can reconstruct equivalent toolkits without re-parsing YAML.

**A2-doc-assumptions** – @genie/wishes/mcp-lazy-connection-wish.md  
Document new lifecycle assumptions inside the wish (this file) so future tasks understand stored metadata usage.  
Success: Wish updated with rationale (fulfilled here).

### Group B: Lazy Connection Wrapper (After A)
Dependencies: A1-store-params

**B1-wrap-entrypoints** – @lib/utils/proxy_agents.py#L362  
Replace direct entrypoint invocation with wrappers that spawn a fresh toolkit using stored parameters, reconnect, execute, then hand back results.  
Success: `SearchAgno` tool calls succeed even after event loop restarts.

**B2-error-normalization** – @lib/utils/proxy_agents.py#L383  
Enhance error formatting to translate transport exceptions (HTTP status, cancelled scope, etc.) into clear `AgentRunException` messages.  
Success: Failure surfaces as concise “MCP HTTP 500 …” responses without stack traces leaking to the user.

### Group C: Resource Lifecycle & Cleanup (After B)
Dependencies: B1-wrap-entrypoints, B2-error-normalization

**C1-shutdown-helpers** – @lib/utils/proxy_agents.py#L456  
Create async/sync `_shutdown_mcp_tool` helpers that close sessions quietly after each call to avoid file-descriptor leaks.  
Success: No orphaned MCP sessions remain after repeated tool usage.

**C2-sync-guardrails** – @lib/utils/proxy_agents.py#L429  
Handle synchronous wrappers by either creating/awaiting fresh sessions via `asyncio.run` or raising informative errors if code attempts sync execution within a running loop.  
Success: Sync tool consumers fail fast with guidance instead of cryptic loop-state errors.

### Group D: Testing & Validation (After C)
Dependencies: All tasks above

**D1-unit-tests** – @tests/lib/utils/test_proxy_agents_coverage.py  
Add targeted tests mocking MCP responses to assert metadata capture, lazy connection, and error normalization.  
Success: `uv run pytest tests/lib/utils/test_proxy_agents_coverage.py -k mcp_lazy` passes.

**D2-integration-tests** – @tests/integration/test_agents_real_execution.py  
Extend real agent run tests to call MCP tools twice sequentially, verifying second call reconnects successfully.  
Success: Integration suite green with new assertions.

**D3-death-testament** – @genie/reports  
Ensure subsequent Forge agent run captures proof (logs showing reconnection, failing server message).  
Success: Death Testament attached during execution phase (tracked later).

## Implementation Examples

### Lazy Wrapper Sketch
```python
# lib/utils/proxy_agents.py
async def _spawn_fresh_mcp_tool(self, template: MCPTools) -> MCPTools:
    params = copy.deepcopy(getattr(template, "_automagik_params", {}))
    fresh = MCPTools(**params)
    await fresh.connect()
    return fresh
```

### Error Normalization Snippet
```python
def _format_httpx_error(error: httpx.HTTPStatusError) -> str:
    request = error.request
    response = error.response
    detail = response.text or response.reason_phrase
    return f"MCP HTTP {response.status_code} from {request.url}: {detail}".strip()
```

### Post-call Cleanup
```python
async def _shutdown_mcp_tool(self, tool: MCPTools | None) -> None:
    if not tool or not hasattr(tool, "close"):
        return
    try:
        await tool.close()
    except Exception:  # logged upstream
        logger.debug("🌐 Ignored MCP shutdown error", exc_info=True)
```

## Testing Protocol
```bash
# Focused unit coverage for proxy helpers
uv run pytest tests/lib/utils/test_proxy_agents_coverage.py -k "mcp_lazy" -q

# Agent execution smoke test (ensures reconnection works twice)
uv run pytest tests/integration/test_agents_real_execution.py -k "template_agent and mcp"

# Static checks
uv run ruff check lib/utils/proxy_agents.py
uv run mypy lib/utils/proxy_agents.py
```

## Validation Checklist
- [ ] Reconnection helpers only trigger during tool execution.
- [ ] Include/exclude filters persist across lazy connections.
- [ ] Errors expose HTTP status or transport detail to the agent response.
- [ ] MCP sessions close after each tool invocation without leaking handles.
- [ ] Unit and integration suites updated with the new lifecycle expectations.
- [ ] Documentation (this wish) reflects all architectural changes.
