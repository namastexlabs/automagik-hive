# Comprehensive Tests Directory Structure & Organization

**Project Root:** `/home/cezar/automagik/automagik-hive`
**Total Test Files:** 155 test_*.py files + conftest.py files throughout hierarchy

---

## 1. DIRECTORY TREE ORGANIZATION

```
tests/
├── conftest.py                           # Root-level pytest configuration
├── __init__.py                           # Package marker
├── fixtures/                             # Shared fixtures across all tests
│   ├── __init__.py
│   ├── config_fixtures.py               # Configuration & environment mocks
│   ├── auth_fixtures.py                 # Authentication & security mocks
│   ├── service_fixtures.py              # Service layer mocks (DB, metrics)
│   ├── shared_fixtures.py               # General utilities
│   └── utility_fixtures.py              # Various utility fixtures
│
├── ai/                                   # AI system component tests
│   ├── __init__.py
│   ├── agents/                          # Agent registry & factory tests
│   │   ├── conftest.py                 # Agent-specific fixtures
│   │   ├── test_registry.py            # Agent discovery & loading
│   │   ├── test_registry_ext.py        # Extended registry tests
│   │   ├── test_template_agent_factory.py
│   │   ├── test_template_agent_manual_loading.py
│   │   ├── template-agent/              # Template agent tests
│   │   │   └── test_template_agent.py
│   │   ├── tools/                       # Agent tools tests
│   │   │   └── test_code_understanding_toolkit.py
│   │   └── genie-*/ directories         # Special agent test directories
│   │
│   ├── teams/                           # Team coordination tests
│   │   ├── conftest.py                 # Team-specific fixtures
│   │   ├── test_registry.py            # Team discovery & routing
│   │   └── template-team/               # Template team tests
│   │       └── test_team.py
│   │
│   ├── tools/                           # AI tools system tests
│   │   ├── conftest.py                 # Tool-specific fixtures
│   │   ├── test_base_tool.py           # Base tool functionality
│   │   ├── test_registry.py            # Tool registry & discovery
│   │   ├── test_registry_execution.py  # Tool execution patterns
│   │   ├── test_template_tool.py       # Template tool tests
│   │   └── template-tool/               # Template tool tests
│   │       └── test_tool.py
│   │
│   └── workflows/                       # Workflow orchestration tests
│       ├── conftest.py                 # Workflow-specific fixtures
│       └── test_registry.py            # Workflow discovery
│
├── api/                                  # API layer tests
│   ├── conftest.py                      # API test fixtures & FastAPI app
│   ├── __init__.py
│   ├── test_settings.py                 # API settings validation
│   ├── test_playground_unification.py   # Playground integration
│   ├── test_agentos_config.py           # AgentOS configuration
│   ├── routes/                          # API route tests
│   │   ├── __init__.py
│   │   ├── test_health.py              # Health check endpoints
│   │   ├── test_v1_router.py           # Main API v1 endpoints
│   │   ├── test_mcp_router.py          # MCP integration routes
│   │   ├── test_version_router.py      # Version management routes
│   │   └── test_agentos_router.py      # Legacy AgentOS routes
│   └── dependencies/                    # API dependency tests
│       └── test_message_validation.py  # Message validation
│
├── lib/                                  # Library layer tests (extensive)
│   ├── __init__.py
│   ├── auth/                            # Authentication & security
│   │   ├── test_service.py
│   │   ├── test_auth_service_enhanced.py
│   │   ├── test_init_service.py
│   │   ├── test_credentials_service.py
│   │   ├── test_dependencies.py
│   │   ├── test_cli.py
│   │   └── test_env_file_manager.py
│   │
│   ├── config/                          # Configuration management
│   │   ├── test_settings.py
│   │   ├── test_server_config.py
│   │   ├── test_models.py
│   │   ├── test_provider_registry.py
│   │   ├── test_schemas.py
│   │   └── test_yaml_parser.py
│   │
│   ├── database/                        # Database layer
│   │   ├── test_backend_factory.py
│   │   ├── test___init__.py
│   │   └── providers/                   # Database provider tests
│   │       ├── test_base.py
│   │       ├── test_postgresql.py
│   │       ├── test_sqlite.py
│   │       └── test___init__.py
│   │
│   ├── knowledge/                       # Knowledge/RAG system
│   │   ├── test_config_aware_filter.py
│   │   ├── test_config_aware_filter_source_execution.py
│   │   ├── test_csv_hot_reload.py
│   │   ├── test_knowledge_factory.py
│   │   ├── test_hash_fix.py
│   │   ├── test_metadata_csv_reader.py
│   │   ├── test_sqlite_warning_suppression.py
│   │   ├── datasources/
│   │   │   ├── test_csv_datasource.py
│   │   │   └── test_row_based_csv.py
│   │   └── services/
│   │       ├── test_change_analyzer.py
│   │       └── test_hash_manager.py
│   │
│   ├── logging/                         # Logging system
│   │   ├── test_batch_logger.py
│   │   ├── test_config.py
│   │   ├── test_level_enforcement.py
│   │   ├── test_progress.py
│   │   └── test_session_logger.py
│   │
│   ├── mcp/                             # Model Context Protocol
│   │   ├── test_catalog.py
│   │   ├── test_config.py
│   │   └── test_exceptions.py
│   │
│   ├── memory/                          # Memory system
│   │   ├── test_memory_factory.py
│   │   └── test_memory_init.py
│   │
│   ├── metrics/                         # Metrics & monitoring
│   │   └── (test files in this area)
│   │
│   ├── models/                          # Data models
│   │   ├── test_base.py
│   │   ├── test_agent_metrics.py
│   │   ├── test_component_versions.py
│   │   └── test_version_history.py
│   │
│   ├── services/                        # Service layer
│   │   ├── test_database_service.py
│   │   ├── test_database_service_error_handling.py
│   │   ├── test_database_service_exception_path.py
│   │   ├── test_metrics_service.py
│   │   ├── test_agentos_service.py
│   │   ├── test_version_sync_service_focused.py
│   │   └── notifications/
│   │       ├── test_notifications.py
│   │       └── test_startup_notifications.py
│   │
│   ├── tools/                           # Tool utilities
│   │   ├── test_tools_registry.py
│   │   ├── test_mcp_integration.py
│   │   └── shared/
│   │       └── test_shell_toolkit.py
│   │
│   ├── utils/                           # Utility functions (extensive)
│   │   ├── test_agno_proxy.py
│   │   ├── test_agno_storage_utils.py
│   │   ├── test_config_validator.py
│   │   ├── test_db_migration.py
│   │   ├── test_db_migration_sqlite_suppression.py
│   │   ├── test_dynamic_model_resolver.py
│   │   ├── test_emoji_loader.py
│   │   ├── test_message_validation.py
│   │   ├── test_proxy_agents_model_fix.py
│   │   ├── test_proxy_workflows.py
│   │   ├── test_proxy_workflows_final.py
│   │   ├── test_startup_display.py
│   │   ├── test_startup_orchestration.py
│   │   ├── test_shutdown_progress.py
│   │   ├── test_team_utils.py
│   │   ├── test_team_utils_execution.py
│   │   ├── test_user_context_helper.py
│   │   ├── test_version_factory.py
│   │   ├── test_version_reader.py
│   │   ├── test_yaml_cache.py
│   │   └── test_ai_root.py
│   │
│   ├── versioning/                      # Version management
│   │   ├── test_agno_version_service.py
│   │   ├── test_agno_version_service_edge_cases.py
│   │   ├── test_bidirectional_sync.py
│   │   ├── test_dev_mode.py
│   │   ├── test_file_sync_tracker.py
│   │   └── test_version_lifecycle_integration.py
│   │
│   └── test_exceptions.py               # General exception handling
│
└── integration/                          # Integration tests (multi-component)
    ├── __init__.py
    ├── test_agentos_control_plane.py
    ├── test_agents_real_execution.py
    ├── test_model_config_regression.py
    ├── test_model_config_regression_simple.py
    ├── test_tools_real_execution.py
    ├── api/                             # API integration tests
    │   ├── test_api_dependencies.py
    │   ├── test_e2e_integration.py
    │   └── test_performance.py
    │
    ├── auth/                            # Authentication integration
    │   ├── test_credential_service_mcp_sync.py
    │   ├── test_credential_service_mcp_sync_edge_cases.py
    │   ├── test_credential_service_mcp_sync_integration.py
    │   ├── test_credential_service_mcp_sync_specification.py
    │   └── test_single_credential_integration.py
    │
    ├── config/                          # Configuration integration
    │   ├── conftest.py
    │   ├── test_config_settings.py
    │   ├── test_database.py
    │   ├── test_server_config.py
    │   └── test_settings_simple.py
    │
    ├── database/                        # Database integration
    │   ├── test_backend_integration.py
    │   ├── test_backend_migration.py
    │   ├── test_backend_performance.py
    │   └── test_backend_selection.py
    │
    ├── knowledge/                       # Knowledge system integration
    │   ├── test_comprehensive_knowledge.py
    │   ├── test_csv_hot_reload_comprehensive.py
    │   └── test_row_based_csv_knowledge_comprehensive.py
    │
    ├── e2e/                             # End-to-end tests
    │   ├── test_langwatch_integration.py
    │   ├── test_mcp_integration.py
    │   ├── test_metrics_input_validation.py
    │   ├── test_metrics_performance.py
    │   ├── test_sync_integration_clean.py
    │   └── test_yaml_database_sync_clean.py
    │
    ├── lib/                             # Library integration tests
    │   ├── test_comprehensive_utils.py
    │   ├── test_models_compatibility_layer.py
    │   ├── test_models_comprehensive.py
    │   └── test_production_code_analysis.py
    │
    ├── security/                        # Security & auth integration
    │   ├── test_api_routes_security.py
    │   ├── test_api_routes_unit.py
    │   ├── test_auth_dependencies.py
    │   ├── test_auth_init_service.py
    │   ├── test_auth_service.py
    │   ├── test_database_service.py
    │   └── test_database_service_unit.py
    │
    └── workflows/                       # Workflow integration tests
        └── (test files for workflow integration)
```

---

## 2. TEST FILE COUNT BREAKDOWN

| Location | Test Files | Type | Purpose |
|----------|------------|------|---------|
| **tests/fixtures/** | 5 | Fixture modules | Config, auth, service mocks |
| **tests/ai/agents/** | 4 | Unit tests | Agent registry, discovery, templates |
| **tests/ai/teams/** | 1 | Unit tests | Team registry & routing |
| **tests/ai/tools/** | 4 | Unit tests | Tool registry, base, templates |
| **tests/ai/workflows/** | 1 | Unit tests | Workflow registry |
| **tests/api/** | 4 | Unit tests | Settings, playground, routes |
| **tests/api/routes/** | 5 | Unit tests | Health, v1, MCP, version, AgentOS |
| **tests/api/dependencies/** | 1 | Unit tests | Message validation |
| **tests/lib/auth/** | 7 | Unit tests | Auth service, credentials, init |
| **tests/lib/config/** | 6 | Unit tests | Settings, server config, schemas |
| **tests/lib/database/** | 5 | Unit tests | Backend factory, providers |
| **tests/lib/knowledge/** | 9 | Unit tests | CSV, RAG, filters, hot reload |
| **tests/lib/logging/** | 5 | Unit tests | Batch logger, config, levels |
| **tests/lib/mcp/** | 3 | Unit tests | MCP catalog, config, exceptions |
| **tests/lib/models/** | 4 | Unit tests | Data models, metrics, versions |
| **tests/lib/services/** | 7 | Unit tests | DB, metrics, version sync |
| **tests/lib/tools/** | 3 | Unit tests | Shell toolkit, MCP, registry |
| **tests/lib/utils/** | 21 | Unit tests | Proxy, migration, emoji, validation |
| **tests/lib/versioning/** | 6 | Unit tests | Version service, sync, lifecycle |
| **tests/integration/api/** | 3 | Integration | E2E, dependencies, performance |
| **tests/integration/auth/** | 5 | Integration | Credential sync, MCP integration |
| **tests/integration/config/** | 4 | Integration | Settings, database, server config |
| **tests/integration/database/** | 4 | Integration | Backend selection, migration, perf |
| **tests/integration/knowledge/** | 3 | Integration | CSV, hot reload, comprehensive |
| **tests/integration/e2e/** | 6 | E2E | MCP, metrics, sync, LangWatch |
| **tests/integration/lib/** | 4 | Integration | Utils, models, production code |
| **tests/integration/security/** | 7 | Security | Auth, routes, database |
| **tests/integration/** (root) | 5 | Integration | AgentOS, real execution |
| **TOTAL** | **155** | Mixed | All test types |

---

## 3. CONFTEST.PY HIERARCHY & FIXTURE CASCADE

```
tests/conftest.py (ROOT)
├── Markers: integration, postgres, safe, slow, unit
├── Global Fixtures:
│   ├── enforce_global_test_isolation()      [autouse] - Prevent file pollution
│   ├── isolated_workspace()                  - Temp working directory
│   ├── preserve_builtin_input()              [session] - Prevent KeyboardInterrupt
│   ├── event_loop()                          [session] - Async event loop
│   ├── setup_test_environment()              [autouse] - Set test env vars
│   ├── mock_external_dependencies()          [autouse] - Mock non-test code
│   ├── mock_auth_service()
│   ├── mock_database()
│   ├── mock_component_registries()
│   ├── mock_mcp_catalog()
│   ├── mock_mcp_tools()
│   ├── mock_version_service()
│   ├── mock_startup_orchestration()
│   ├── simple_fastapi_app()
│   ├── test_client()                        - FastAPI sync client
│   ├── async_client()                       - FastAPI async client
│   ├── sample_version_request()
│   ├── sample_execution_request()
│   ├── api_headers()
│   └── mock_file_system_ops()
│
├── Plugin Imports:
│   ├── pytest_mock
│   ├── tests.fixtures.config_fixtures
│   └── tests.fixtures.service_fixtures
│
tests/fixtures/config_fixtures.py
├── temp_project_dir()
├── mock_env_vars()                         - Full test env setup
├── mock_invalid_env_vars()
├── clean_singleton()
├── sample_agent_config()
├── sample_team_config()
├── sample_workflow_config()
├── mock_yaml_operations()
├── mock_database_url() / mock_sqlite_url()
└── configuration_test_matrix()

tests/fixtures/auth_fixtures.py
├── clean_auth_environment()
├── mock_auth_service()
├── mock_auth_service_disabled()
├── mock_auth_service_failing()
├── mock_auth_init_service()
├── valid_api_key()
├── invalid_api_key()
├── auth_headers()
├── invalid_auth_headers()
├── no_auth_headers()
├── AuthTestHelpers (class)
├── auth_helpers()
├── security_test_patterns()
└── auth_test_scenarios()

tests/fixtures/service_fixtures.py
├── mock_database_pool()
├── mock_psycopg_operations()
├── sample_database_rows()
├── mock_version_service_db()
├── mock_migration_operations()
├── mock_metrics_queue()
├── sample_metrics_data()
├── mock_langwatch_client()
├── component_version_test_data()
├── mock_file_system_ops()
├── database_error_scenarios()
├── async_test_timeout()
├── service_cleanup()
├── mock_component_discovery()
└── mock_startup_results()

tests/ai/agents/conftest.py
├── mock_database_layer()                   [autouse] - Mock DB for registry
└── setup_test_environment()

tests/ai/tools/conftest.py
├── mock_tools_dir()
└── mock_resolve_ai_root()

tests/ai/workflows/conftest.py
├── mock_workflows_dir()
└── mock_resolve_ai_root()

tests/api/conftest.py
├── MockComponentRegistries (dataclass)
├── MockStartupServices (dataclass)
├── MockStartupResults (dataclass)
├── mock_startup_results()
└── create_mock_startup_results()

tests/integration/config/conftest.py
└── (Config-specific fixtures)
```

---

## 4. FIXTURE USAGE PATTERNS

### **A. Import Pattern (Standard)**
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
```

### **B. Common Fixture Combinations**

**For Agent Tests:**
```python
def test_agent_registry(mock_database_layer, mock_file_system_ops, sample_agent_config):
    # Database layer auto-mocked
    # Filesystem mocked for path operations
    # Config sample provided
```

**For API Tests:**
```python
def test_api_endpoint(test_client, mock_auth_service, mock_version_service):
    # FastAPI test client
    # Auth pre-mocked
    # Version service ready
```

**For Integration Tests:**
```python
@pytest.mark.asyncio
async def test_integration(async_client, mock_startup_results, mock_mcp_tools):
    # Async HTTP client
    # Full startup mock
    # MCP integration ready
```

**For Security Tests:**
```python
def test_auth_security(auth_helpers, security_test_patterns, invalid_api_key):
    # Helper methods for assertions
    # Injection payloads pre-built
    # Invalid key for testing
```

### **C. Fixture Scope Summary**

| Scope | Count | Usage |
|-------|-------|-------|
| `session` | 2 | `event_loop`, `preserve_builtin_input` |
| `module` | ~3 | conftest fixtures in subdirs |
| `function` | ~150+ | Most test fixtures |
| `autouse` | 4 | Global enforcement fixtures |

---

## 5. KEY FIXTURE CAPABILITIES

### **Global Test Isolation**
- `enforce_global_test_isolation()` - Monitors file creation, prevents pollution
- `isolated_workspace()` - Changes working directory to temp space
- Auto-applied to all tests via `autouse=True`

### **Environment Setup**
- `mock_env_vars()` - Complete test environment
- `setup_test_environment()` - Auto-applied to all tests
- Environment cleanup on fixture teardown

### **Database Mocking**
- `mock_database_pool()` - Async connection pools
- `mock_psycopg_operations()` - PostgreSQL operations
- `mock_version_service_db()` - Version service DB layer
- Supports async context managers properly

### **API Testing**
- `simple_fastapi_app()` - Minimal test FastAPI app
- `test_client()` - Synchronous HTTP client
- `async_client()` - Asynchronous HTTP client
- Pre-configured routes and mocks

### **Authentication**
- `mock_auth_service()` - Enabled auth
- `mock_auth_service_disabled()` - Disabled auth
- `mock_auth_service_failing()` - Rejection scenarios
- Security test patterns for injection attacks

### **Component Mocking**
- `mock_component_registries()` - Agent/team/workflow stubs
- `mock_startup_orchestration()` - Full startup simulation
- `mock_mcp_catalog()` & `mock_mcp_tools()` - MCP integration

---

## 6. IMPORT PATTERNS & DEPENDENCIES

### **Standard Import Order** (in all test files)
1. System imports (sys, pathlib, datetime)
2. Temporary/file operations (tempfile, os)
3. Testing imports (pytest, unittest.mock)
4. Third-party async (pytest_asyncio, httpx)
5. Project-root path setup
6. Project imports (after path setup)

### **Common Modules Imported in Tests**
```python
# Core testing
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# API testing
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Project modules (after path setup)
from ai.agents.registry import AgentRegistry
from api.routes.v1_router import v1_router
from lib.auth.service import AuthService
from lib.config.settings import HiveSettings
from lib.knowledge.knowledge_factory import get_knowledge_base
```

### **Patch Target Patterns**
```python
# Database services
"lib.services.database_service.*"
"lib.utils.db_migration.*"

# Version management
"lib.versioning.agno_version_service.*"
"lib.services.component_version_service.*"

# API layer
"api.routes.*"
"api.serve.*"

# Knowledge/RAG
"lib.knowledge.*"
"lib.knowledge.csv_hot_reload.*"

# MCP Integration
"lib.mcp.get_mcp_tools"
"api.routes.mcp_router.MCPCatalog"

# Logging
"lib.logging.initialize_logging"
```

---

## 7. ASYNC TESTING PATTERNS

### **Async Test Marking**
```python
@pytest.mark.asyncio
async def test_async_operation(mock_database_pool):
    # AsyncMock objects auto-await
    result = await some_async_function()
    assert result is not None
```

### **Async Fixtures**
```python
@pytest_asyncio.fixture
async def async_client(simple_fastapi_app):
    async with AsyncClient(...) as client:
        yield client
```

### **Event Loop Management**
- Session-scoped event loop created in conftest
- Proper cleanup of pending tasks
- KeyboardInterrupt handling during mock cleanup

---

## 8. SECURITY & AUTHENTICATION TESTING

### **Security Test Patterns** (from auth_fixtures.py)
```python
security_test_patterns = {
    "sql_injection": [...],
    "xss_payloads": [...],
    "path_traversal": [...],
    "injection_attempts": [...]
}

auth_test_scenarios = {
    "valid_scenarios": [...],
    "invalid_scenarios": [...],
    "attack_scenarios": [...]
}
```

### **Common Attack Vectors Tested**
- SQL injection (multiple variants)
- XSS (script tags, image tags, javascript:)
- Path traversal (../, \\, encoded)
- Template injection (Velocity, Angular)
- Log4j injection (jndi:ldap://)
- Null byte injection

---

## 9. PERFORMANCE & CONFIGURATION TESTING

### **Configuration Test Matrix** (from config_fixtures.py)
```python
configuration_test_matrix = {
    "environments": ["development", "staging", "production"],
    "ports": [8886, 3000, 80, 443],
    "worker_counts": [1, 2, 4, 8],
    "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
    "batch_sizes": [1, 50, 100, 1000, 10000],
    "flush_intervals": [0.1, 1.0, 5.0, 60.0, 3600.0],
    "queue_sizes": [10, 100, 1000, 10000, 100000]
}
```

### **Performance Test Categories**
- E2E integration tests
- Database backend performance
- Metrics collection performance
- API response time validation

---

## 10. SPECIAL TEST DIRECTORIES

### **Template Test Directories**
These mirror the main component structure:
```
tests/ai/agents/template-agent/     - Template agent test example
tests/ai/teams/template-team/       - Template team test example
tests/ai/tools/template-tool/       - Template tool test example
```

### **Special Agent Directories**
```
tests/ai/agents/genie-debug/        - Genie debug agent tests
tests/ai/agents/genie-dev/          - Genie dev agent tests
tests/ai/agents/genie-testing/      - Genie testing agent tests
tests/ai/agents/genie-quality/      - Genie quality agent tests
```

---

## 11. CRITICAL PYTEST CONFIGURATION

### **pytest.ini Equivalent** (from conftest.py)
```
Markers registered:
- integration
- postgres
- safe
- slow
- unit
```

### **Plugins Loaded**
```
pytest_mock        # Provides mocker fixture
config_fixtures    # Configuration test fixtures
service_fixtures   # Service layer mocks
```

### **Keyboard Interrupt Handling**
- Custom hook catches KeyboardInterrupt from mock cleanup
- Distinguishes user Ctrl+C from mock side effects
- Allows test session to continue instead of abort

---

## 12. FIXTURE DEPENDENCY GRAPH

```
┌─────────────────────────────────────────────────────┐
│          conftest.py (ROOT LEVEL)                   │
│  ├─ enforce_global_test_isolation [autouse]        │
│  ├─ setup_test_environment [autouse]               │
│  ├─ mock_external_dependencies [autouse]           │
│  └─ event_loop [session]                           │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┴───────────┬─────────────────────┐
    │                    │                     │
    v                    v                     v
┌──────────┐     ┌──────────────┐     ┌────────────────┐
│ fixtures │     │ ai/conftest  │     │ api/conftest   │
│ directory│     │   & routes   │     │   & routes     │
└──────────┘     └──────────────┘     └────────────────┘
    │                 │                       │
    ├─────────────────┼─────────────────────┬─┴─────────┐
    │                 │                     │           │
    v                 v                     v           v
config_     service_      mock_database   mock_auth   mock_version
fixtures    fixtures      _layer          _service    _service
```

---

## 13. TEST EXECUTION WORKFLOW

### **Typical Test Run**
```bash
# Full test suite
uv run pytest tests/

# With coverage
uv run pytest --cov=ai --cov=api --cov=lib

# Specific directory
uv run pytest tests/ai/agents/

# By marker
uv run pytest -m integration
uv run pytest -m "not slow"

# Specific test
uv run pytest tests/api/routes/test_health.py::test_health_check
```

### **Pre-Test Setup Order** (for each test)
1. Global isolation enforcement activated
2. Environment variables set up
3. External dependencies mocked
4. Test-specific fixtures instantiated
5. Conftest fixtures at module level applied
6. Test runs with all mocks active
7. Fixtures torn down in reverse order
8. Environment restored

---

## 14. KEY DESIGN PATTERNS IN TESTS

### **Path Setup Pattern** (Every file)
```python
# Always added to every test file
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

### **Mock Database Layer Pattern** (Registry tests)
```python
@pytest.fixture(autouse=True)
def mock_database_layer():
    # Create all mocks needed for database operations
    # Patch multiple modules at once
    # Return dict of mocks for test access
```

### **Async Context Manager Pattern** (MCP, database)
```python
class MockConnectionAsyncContext:
    async def __aenter__(self):
        return mock_connection
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None
```

### **Parametrized Test Data**
```python
# Via fixtures
configuration_test_matrix = {...}
security_test_patterns = {...}
auth_test_scenarios = {...}
```

---

## 15. CRITICAL FIXTURE NOTES

### **DO Use These Fixtures:**
- `enforce_global_test_isolation()` - Always active
- `mock_auth_service()` - For API tests
- `mock_database_layer()` - For registry tests
- `test_client()` / `async_client()` - For API tests
- `mock_env_vars()` - For config tests
- `isolated_workspace()` - When creating files

### **NEVER DO:**
- Run pytest without `uv run` prefix
- Import project modules before path setup
- Skip path setup in new test files
- Use real database/API calls in unit tests
- Disable global isolation enforcement
- Mix mock and real operations

---

## Summary Statistics

- **Total Test Files:** 155 test_*.py
- **Conftest Files:** 8 (1 root + 7 subdirectories)
- **Fixture Modules:** 5 (config, auth, service, shared, utility)
- **Total Fixtures:** 100+
- **Test Markers:** 5 (integration, postgres, safe, slow, unit)
- **Directory Depth:** 4-6 levels
- **Async Tests:** ~40+ marked with @pytest.mark.asyncio
- **Mock Targets:** 50+ unique patch locations
- **Environment Variables:** 20+ for testing
