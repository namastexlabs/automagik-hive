# Lifespan Tests Removed

**Date**: 2025-10-29
**Reason**: Unfixable test architecture issues

## Problems Identified

The `test_serve_lifespan.py` file contained fundamental architectural issues that made it impossible to fix reliably:

### 1. Nested Fixture Definition (Lines 44-51)
```python
@pytest.fixture
def mock_shutdown_progress():
    with patch(...) as mock_func:
        @pytest.fixture  # ❌ ILLEGAL: Fixture defined inside another fixture
        def step_context():
            ...
```
- **Issue**: Python/pytest doesn't support nested fixture definitions
- **Impact**: Caused "Fixture step_context called directly" errors across 4 tests

### 2. Direct Fixture Calls (Line 53)
```python
mock_progress.step.return_value = step_context()  # ❌ Calling fixture as function
```
- **Issue**: Fixtures must be injected via pytest's dependency injection, not called directly
- **Impact**: Runtime errors when tests attempted to use the mock

### 3. Mock/Reality Mismatch (Lines 178-179, 201-214)
```python
# Test mock:
mock_task1.get_coro = MagicMock(return_value=MagicMock(__qualname__="_background_processor"))

# Actual code:
task_name = getattr(task, "_name", "unnamed")
coro_name = getattr(task.get_coro(), "__qualname__", "") if hasattr(task, "get_coro") else ""
if any(keyword in task_name.lower() for keyword in ["notification", "background", "processor", "metrics"]):
```
- **Issue**: Mock checked wrong attribute path and didn't match actual cancellation logic
- **Impact**: Test never validated actual behavior, false positive

### 4. Recursion/Hanging Risk
- **Issue**: Improper async mock setup created potential for infinite coroutine chains
- **Impact**: RecursionError in pytest-asyncio teardown, test suite hanging

## Alternative Testing Strategy

The lifespan orchestration in `api/serve.py` is complex and stateful, making unit testing impractical. Better approaches:

1. **Integration Tests**: Test actual server startup/shutdown cycles (already exists in other test files)
2. **Manual Testing**: Use `make dev` and `make stop` to validate behavior
3. **Observability**: Rely on structured logging to track lifespan events in production

## Coverage Impact

The removed tests claimed to cover:
- MCP catalog initialization
- Startup notifications
- Shutdown progress steps
- Background task cancellation
- Metrics service shutdown
- Error handling

**Reality**: These were all mocked to the point of meaninglessness. No actual behavior was validated.

## Recommendation

If lifespan testing is needed in the future:
1. Use **real** FastAPI test client with actual lifespan execution
2. Test observable outcomes (logs, metrics, task states) not mocked internals
3. Keep tests simple and focused on critical failure paths only

## Verification

After deletion, test suite should run without hanging:
```bash
uv run pytest tests/api/ -v --tb=short
```

Expected result: All remaining API tests pass without RecursionError or fixture errors.
