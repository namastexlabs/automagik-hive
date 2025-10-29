# Tests Directory - Quick Reference Guide

## Overview
- **Total Test Files:** 155 test_*.py files
- **Total Fixture Modules:** 5 shared + 8 conftest files
- **Total Fixtures:** 100+
- **Test Types:** Unit, Integration, E2E, Security

---

## Quick Navigation

### By Component Type

**AI Component Tests** (14 test files)
- `tests/ai/agents/` - Agent registry, discovery, templates (4 files)
- `tests/ai/teams/` - Team routing, coordination (1 file)
- `tests/ai/tools/` - Tool registry, base class (4 files)
- `tests/ai/workflows/` - Workflow orchestration (1 file)

**API Layer Tests** (10 test files)
- `tests/api/` - Settings, playground, config (4 files)
- `tests/api/routes/` - Health, v1, MCP, version endpoints (5 files)
- `tests/api/dependencies/` - Message validation (1 file)

**Library Tests** (78 test files) - LARGEST CATEGORY
- `tests/lib/auth/` - Auth service, credentials (7 files)
- `tests/lib/config/` - Settings, server config (6 files)
- `tests/lib/database/` - DB backends, providers (5 files)
- `tests/lib/knowledge/` - RAG, CSV, hot reload (9 files)
- `tests/lib/logging/` - Logger, batch, levels (5 files)
- `tests/lib/mcp/` - MCP catalog, config (3 files)
- `tests/lib/models/` - Data models, versions (4 files)
- `tests/lib/services/` - DB, metrics, sync (7 files)
- `tests/lib/tools/` - Shell toolkit, registry (3 files)
- `tests/lib/utils/` - LARGEST SUBSECTION - 21 utility tests
- `tests/lib/versioning/` - Version service, sync (6 files)

**Integration Tests** (53 test files) - SECOND LARGEST
- `tests/integration/api/` - E2E, dependencies, performance (3 files)
- `tests/integration/auth/` - Credential sync, MCP integration (5 files)
- `tests/integration/config/` - Config, database, settings (4 files)
- `tests/integration/database/` - Backend selection, migration (4 files)
- `tests/integration/knowledge/` - CSV, hot reload (3 files)
- `tests/integration/e2e/` - MCP, metrics, sync, LangWatch (6 files)
- `tests/integration/lib/` - Utils, models (4 files)
- `tests/integration/security/` - Auth, routes, database (7 files)
- `tests/integration/` (root) - AgentOS, real execution (5 files)

**Fixture Modules** (5 files)
- `tests/fixtures/config_fixtures.py` - Config & env mocks
- `tests/fixtures/auth_fixtures.py` - Auth & security mocks
- `tests/fixtures/service_fixtures.py` - DB, metrics, version mocks
- `tests/fixtures/shared_fixtures.py` - General utilities
- `tests/fixtures/utility_fixtures.py` - Various utilities

---

## Finding Tests for Specific Code

### For `ai/agents/` code:
```
tests/ai/agents/test_registry.py       # Main test
tests/ai/agents/test_registry_ext.py   # Extended tests
tests/ai/agents/conftest.py            # Agent-specific mocks
```

### For `api/routes/` code:
```
tests/api/routes/test_v1_router.py     # Main endpoints
tests/api/routes/test_health.py        # Health check
tests/api/routes/test_mcp_router.py    # MCP routes
tests/api/conftest.py                  # API mocks
```

### For `lib/knowledge/` code:
```
tests/lib/knowledge/test_*.py          # Unit tests (9 files)
tests/integration/knowledge/           # Integration tests (3 files)
tests/lib/knowledge/datasources/       # Datasource tests
tests/lib/knowledge/services/          # Service tests
```

### For `lib/auth/` code:
```
tests/lib/auth/test_*.py               # Unit tests (7 files)
tests/integration/auth/                # Integration tests (5 files)
tests/integration/security/            # Security tests (7 files)
```

---

## Fixture Quick Reference

### Most Important Fixtures

**For All Tests:**
- `enforce_global_test_isolation()` - Auto-applied, prevents file pollution
- `setup_test_environment()` - Auto-applied, sets test env vars
- `mock_external_dependencies()` - Auto-applied, mocks external services

**For Agent Tests:**
- `mock_database_layer()` - Mocks DB for registry tests (autouse)
- `mock_file_system_ops()` - Mocks filesystem operations

**For API Tests:**
- `simple_fastapi_app()` - Minimal FastAPI test app
- `test_client()` - Sync HTTP client for API tests
- `async_client()` - Async HTTP client for API tests
- `mock_auth_service()` - Mock authentication service
- `mock_version_service()` - Mock version management

**For Integration Tests:**
- `mock_startup_results()` - Full startup simulation
- `mock_startup_orchestration()` - Component registration mocks

**For Configuration Tests:**
- `mock_env_vars()` - Complete test environment variables
- `configuration_test_matrix()` - Config test variations

**For Security Tests:**
- `auth_helpers()` - Authentication assertion helpers
- `security_test_patterns()` - SQL injection, XSS, path traversal payloads
- `auth_test_scenarios()` - Valid/invalid/attack scenarios

---

## Standard Import Pattern

Every test file must start with:
```python
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
```

---

## Running Tests

```bash
# All tests
uv run pytest tests/

# Specific module
uv run pytest tests/ai/agents/test_registry.py

# Specific test
uv run pytest tests/api/routes/test_health.py::test_health_check

# With coverage
uv run pytest --cov=ai --cov=api --cov=lib tests/

# Skip slow tests
uv run pytest -m "not slow" tests/

# Integration tests only
uv run pytest -m integration tests/
```

---

## Conftest Hierarchy

```
tests/conftest.py                    # ROOT - Global setup
├── tests/fixtures/config_fixtures.py
├── tests/fixtures/auth_fixtures.py
├── tests/fixtures/service_fixtures.py
└── tests/*/conftest.py              # Local overrides
    ├── tests/ai/agents/conftest.py
    ├── tests/ai/tools/conftest.py
    ├── tests/ai/workflows/conftest.py
    ├── tests/api/conftest.py
    └── tests/integration/config/conftest.py
```

---

## Key Patterns

### AsyncTest Pattern
```python
@pytest.mark.asyncio
async def test_async(async_client, mock_database_pool):
    result = await some_async_func()
    assert result is not None
```

### Mock Database Layer Pattern
```python
def test_with_mocked_db(mock_database_layer, sample_agent_config):
    # Database layer already mocked by fixture
    # mock_database_layer dict contains: version_service, db_service, agent
```

### Security Test Pattern
```python
def test_security(security_test_patterns, auth_helpers):
    for payload in security_test_patterns["sql_injection"]:
        # Test against SQL injection payloads
        pass
```

---

## Common Patch Targets

```python
# Database
"lib.services.database_service.*"
"lib.utils.db_migration.*"

# Version Management
"lib.versioning.agno_version_service.*"
"lib.services.component_version_service.*"

# Knowledge/RAG
"lib.knowledge.*"
"lib.knowledge.csv_hot_reload.*"

# MCP Integration
"lib.mcp.get_mcp_tools"
"api.routes.mcp_router.MCPCatalog"

# API Layer
"api.routes.*"
"api.serve.*"

# Logging
"lib.logging.initialize_logging"
```

---

## Test Markers

```bash
@pytest.mark.integration     # Integration tests
@pytest.mark.postgres        # Requires PostgreSQL
@pytest.mark.safe            # Safe to run anywhere
@pytest.mark.slow            # Slow running tests (>1s)
@pytest.mark.unit            # Unit tests
```

---

## Environment Variables for Testing

All set automatically via `mock_env_vars()` fixture:
```
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8888
HIVE_DATABASE_URL=sqlite:///test.db
HIVE_API_KEY=hive_test_key_...
HIVE_LOG_LEVEL=ERROR        # Reduced log noise
ANTHROPIC_API_KEY=test-key
OPENAI_API_KEY=test-key
```

---

## File Locations - Absolute Paths

**Main fixture module:**
- `/home/cezar/automagik/automagik-hive/tests/conftest.py`

**Fixture implementations:**
- `/home/cezar/automagik/automagik-hive/tests/fixtures/`

**Test organization:**
- `/home/cezar/automagik/automagik-hive/tests/ai/`
- `/home/cezar/automagik/automagik-hive/tests/api/`
- `/home/cezar/automagik/automagik-hive/tests/lib/`
- `/home/cezar/automagik/automagik-hive/tests/integration/`

---

## Troubleshooting

**Module not found errors?**
→ Check path setup is correct in test file

**Fixture not found?**
→ Verify fixture name in conftest.py or fixtures/ directory
→ Check fixture scope matches test scope

**Mock not working?**
→ Patch target before import: `patch("module.before.importing")`
→ Use `AsyncMock` for async functions
→ Use `MagicMock` for context managers

**AsyncMock not awaiting?**
→ Mark test with `@pytest.mark.asyncio`
→ Use `await` when calling async mocks

**Database connection issues?**
→ Fixtures automatically mock DB operations
→ Check mock_database_layer fixture is applied

---

## Full Documentation

See `/home/cezar/automagik/automagik-hive/.genie/tests_structure_mapping.md` for comprehensive guide.
