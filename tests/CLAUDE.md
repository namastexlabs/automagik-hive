# CLAUDE.md - Testing

## Context & Scope

[CONTEXT]
- Defines pytest-based coverage for agents, teams, workflows, API, and integrations.
- Emphasizes async patterns, mocking, and performance/security validation.
- Coordinate with `/CLAUDE.md` and component-specific guides before writing tests.

[CONTEXT MAP]
@tests/
@tests/ai/agents/
@tests/ai/teams/
@tests/ai/workflows/
@tests/ai/tools/
@tests/api/
@tests/integration/

[SUCCESS CRITERIA]
✅ `uv run pytest` passes across unit + integration layers with coverage flags.
✅ Async tests use `@pytest.mark.asyncio` and await semantics.
✅ External services (MCP, DB, HTTP) mocked or sandboxed.
✅ Death Testament / wish logs contain evidence of test execution.

[NEVER DO]
❌ Run pytest without `uv run`.
❌ Leave external calls unmocked (breaks reproducibility).
❌ Skip negative-path testing (auth failures, timeouts, bad data).
❌ Ignore coverage for new features.

## Task Decomposition
```
<task_breakdown>
1. [Discovery] Identify coverage gaps
   - Map feature code paths to existing tests.
   - Review fixtures, mocks, and async utilities.
   - Note missing negative/performance cases.

2. [Implementation] Write or adjust tests
   - Use pytest fixtures, async patterns, and dependency overrides.
   - Add coverage for happy + failure paths.
   - Update docs/README snippets if commands change.

3. [Verification] Run suites and report
   - Execute `uv run pytest` with coverage where applicable.
   - Capture logs/results in wish or Forge artifact.
   - Address flaky tests before completion.
</task_breakdown>
```

## Purpose

Comprehensive testing framework for multi-agent systems with UV-based execution, fixtures for shared utilities, and multi-level test organization. Includes async patterns, mocking strategies, and performance validation.

## Test Structure

**Directory Organization**:
```
tests/
├── fixtures/                  # Shared test utilities
│   ├── config_fixtures.py     # Mock env vars & configs
│   ├── auth_fixtures.py       # Auth mocks
│   ├── service_fixtures.py    # Service mocks
│   └── utility_fixtures.py    # General utilities
├── ai/                        # AI component tests
│   ├── agents/                # Agent registry tests
│   ├── teams/                 # Team coordination
│   └── workflows/             # Workflow orchestration
├── integration/               # Multi-component tests
│   ├── e2e/                   # End-to-end scenarios
│   ├── api/                   # API integration
│   ├── security/              # Auth & security
│   └── config/                # Configuration tests
├── api/                       # API unit tests
└── lib/                       # Library tests
```

## Quick Start

**Run tests with UV**:
```bash
uv run pytest tests/                    # All tests
uv run pytest tests/ai/agents/         # Agent tests
uv run pytest tests/integration/       # Integration tests
uv run pytest -v --cov=lib --cov=api  # With coverage
uv run pytest -m "not slow"            # Skip slow tests
```

**Path setup pattern**:
```python
# Standard path fix for imports (used in all test files)
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Then import project modules
from ai.agents.registry import get_agent
```

**Async test pattern**:
```python
@pytest.mark.asyncio
async def test_agent_creation(mock_env_vars):
    agent = await get_agent("test-agent")
    assert agent is not None
    assert agent.agent_id == "test-agent"
```

## Test Categories

**Unit Tests**: Individual component validation
- Location: `tests/ai/`, `tests/api/`, `tests/lib/`
- Focus: Single function/class behavior
- Speed: Fast (<100ms per test)

**Integration Tests**: Multi-component interaction
- Location: `tests/integration/`
- Focus: Component integration, database operations
- Speed: Medium (100ms-1s per test)

**E2E Tests**: Full system workflows
- Location: `tests/integration/e2e/`
- Focus: Complete user scenarios, API flows
- Speed: Slow (>1s per test)

**Security Tests**: Auth and access control
- Location: `tests/integration/security/`
- Focus: API auth, database security, credential management
- Speed: Medium

**Performance Tests**: Load and metrics
- Location: `tests/integration/e2e/test_metrics_performance.py`
- Focus: Response times, concurrency, resource usage
- Speed: Variable

## Core Patterns

**Async testing**:
```python
@pytest.mark.asyncio  
async def test_agent_workflow():
    agent = await get_agent("test-agent")
    response = await agent.arun("test message")
    assert response.content
```

## Fixture Patterns

**Environment mocking**:
```python
@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_API_PORT": "8888",
        "HIVE_DATABASE_URL": "sqlite:///test.db",
        "ANTHROPIC_API_KEY": "test-key",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars
```

**MCP tools mocking**:
```python
@pytest.fixture
def mock_mcp_tools():
    with patch('lib.mcp.get_mcp_tools') as mock:
        mock.return_value.__aenter__.return_value.call_tool = AsyncMock(
            return_value="success"
        )
        yield mock
```

**Singleton reset**:
```python
@pytest.fixture
def clean_singleton():
    """Reset singleton instances between tests."""
    from lib.config.server_config import ServerConfig
    original = ServerConfig._instance
    ServerConfig._instance = None
    yield
    ServerConfig._instance = original
```
## Critical Rules

- **UV Required**: Always use `uv run pytest` for test execution
- **Path Setup**: Add project root to sys.path in every test file
- **Async Marking**: Use @pytest.mark.asyncio for all async tests
- **Mock External**: Always mock MCP, databases, external APIs
- **Fixture Usage**: Use shared fixtures from `tests/fixtures/`
- **Isolation**: Reset singletons and clean state between tests
- **Real Configs**: Test with actual YAML configs when possible
- **Error Coverage**: Include failure scenarios and edge cases

## Test Markers

**Common pytest markers**:
```python
@pytest.mark.slow  # Tests taking >1 second
@pytest.mark.integration  # Integration tests
@pytest.mark.security  # Security-focused tests
@pytest.mark.performance  # Performance tests
@pytest.mark.asyncio  # Async test functions
@pytest.mark.parametrize  # Parameterized tests
```

## Integration

- **Agents**: Unit tests for individual agent behavior and configuration
- **Teams**: Multi-agent coordination and routing validation  
- **Workflows**: Step-based process testing with state management
- **API**: FastAPI endpoint testing with authentication
- **Knowledge**: CSV loading, search, and filtering validation
- **MCP**: External service integration and fallback testing

## Special Test Types

**Isolation Tests**:
- `test_isolation_validation.py` - Validates component isolation
- `test_global_isolation_enforcement.py` - Global boundary checks
- `test_pollution_detection_demo.py` - Test pollution detection

**Hook Validation**:
- `test_hook_validation.py` - Validates Claude hooks
- `hooks/test_boundary_enforcer_validation.py` - Boundary enforcement

**Coverage Requirements**:
```bash
# Run with coverage report
uv run pytest --cov=ai --cov=api --cov=lib \
              --cov-report=term-missing \
              --cov-report=html

# Coverage targets
# - ai/: >80% coverage
# - api/: >75% coverage
# - lib/: >85% coverage
```

## Debugging Tips

**Verbose output**:
```bash
uv run pytest -vv tests/  # Very verbose
uv run pytest -s tests/   # Show print statements
uv run pytest --tb=short  # Short traceback
```

**Run specific tests**:
```bash
uv run pytest tests/ai/agents/test_registry.py::TestAgentRegistry
uv run pytest -k "test_discover_agents"  # Match test names
```

Navigate to [AI System](../ai/CLAUDE.md) for component-specific testing or [API](../api/CLAUDE.md) for endpoint testing.
