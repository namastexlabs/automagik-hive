"""
Test configuration and shared fixtures for API testing.

This provides comprehensive fixtures for testing the Automagik Hive API layer
with proper isolation, authentication, and database setup.
"""

import asyncio
import os
import tempfile
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Pytest plugins must be defined at the top level conftest.py
# Note: tests.config.conftest is auto-discovered, so we only include explicit fixture modules
pytest_plugins = [
    "tests.fixtures.config_fixtures",
    "tests.fixtures.service_fixtures",
    "pytest_mock",  # Moved from tests/cli/conftest.py to fix collection error
]

# Set test environment before importing API modules
os.environ["HIVE_ENVIRONMENT"] = "development"
os.environ["HIVE_DATABASE_URL"] = (
    "postgresql+psycopg://test:test@localhost:5432/test_db"
)
os.environ["HIVE_API_PORT"] = "8887"
os.environ["HIVE_LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests
os.environ["AGNO_LOG_LEVEL"] = "ERROR"

# Mock external dependencies to avoid real API calls
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"


def _create_test_fastapi_app() -> FastAPI:
    """Create a minimal FastAPI app for testing with basic endpoints."""
    test_app = FastAPI(title="Automagik Hive Multi-Agent System", description="Test Multi-Agent System", version="1.0.0")
    
    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @test_app.get("/")
    async def root():
        return {"status": "ok"}
    
    return test_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_auth_service() -> Generator[Mock, None, None]:
    """Mock authentication service."""
    with patch("lib.auth.dependencies.get_auth_service") as mock:
        auth_service = Mock()
        auth_service.is_auth_enabled.return_value = False
        auth_service.get_current_key.return_value = "test-api-key"
        auth_service.validate_api_key.return_value = True
        mock.return_value = auth_service
        yield auth_service


@pytest.fixture
def mock_database() -> Generator[Mock, None, None]:
    """Mock database operations to avoid real database setup."""
    with patch("lib.utils.db_migration.check_and_run_migrations") as mock_migration:
        mock_migration.return_value = False  # No migrations needed
        yield mock_migration


@pytest.fixture
def mock_component_registries() -> Generator[
    dict[str, dict[str, dict[str, Any]]], None, None
]:
    """Mock component registries to avoid loading real agents/teams/workflows."""
    mock_agents = {
        "test-agent": {
            "name": "Test Agent",
            "version": "1.0.0",
            "config": {"test": True},
        },
    }

    mock_teams = {
        "test-team": {
            "name": "Test Team",
            "version": "1.0.0",
            "config": {"test": True},
        },
    }

    mock_workflows = {
        "test-workflow": {
            "name": "Test Workflow",
            "version": "1.0.0",
            "config": {"test": True},
        },
    }

    # Mock the component creations to return simple mock agents
    mock_agent = Mock()
    mock_agent.run.return_value = "Test response"
    mock_agent.metadata = {}  # Add metadata as empty dict, not Mock

    patches = [
        patch(
            "ai.agents.registry.AgentRegistry.list_available_agents",
            return_value=list(mock_agents.keys()),
        ),
        patch(
            "ai.teams.registry.list_available_teams",
            return_value=list(mock_teams.keys()),
        ),
        patch(
            "ai.workflows.registry.list_available_workflows",
            return_value=list(mock_workflows.keys()),
        ),
        patch(
            "lib.utils.version_factory.create_agent",
            new_callable=AsyncMock,
            return_value=mock_agent,
        ),
        patch(
            "lib.utils.version_factory.create_team",
            new_callable=AsyncMock,
            return_value=mock_agent,
        ),
        patch("ai.workflows.registry.get_workflow", return_value=mock_agent),
        # Mock the database services to avoid actual database connections
        patch("lib.services.database_service.get_db_service", return_value=AsyncMock()),
        patch("lib.services.component_version_service.ComponentVersionService"),
        patch("lib.versioning.agno_version_service.AgnoVersionService"),
        # Mock the version factory method to return mock agent directly, but fail for non-existent components
        patch(
            "lib.utils.version_factory.VersionFactory.create_versioned_component",
            new_callable=lambda: AsyncMock(
                side_effect=lambda component_id, **kwargs: None
                if component_id == "non-existent-component"
                else mock_agent
            ),
        ),
    ]

    for p in patches:
        p.start()

    yield {"agents": mock_agents, "teams": mock_teams, "workflows": mock_workflows}

    for p in patches:
        p.stop()


@pytest.fixture
def mock_mcp_catalog() -> Generator[Mock, None, None]:
    """Mock MCP catalog for testing MCP endpoints."""
    with patch("api.routes.mcp_router.MCPCatalog") as mock_catalog_class:
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = ["test-server", "another-server"]
        mock_catalog.get_server_info.return_value = {
            "type": "command",
            "is_sse_server": False,
            "is_command_server": True,
            "url": None,
            "command": "test-command",
        }
        mock_catalog_class.return_value = mock_catalog
        yield mock_catalog


@pytest.fixture
def mock_mcp_tools() -> Generator[None, None, None]:
    """Mock MCP tools for connection testing."""

    def mock_get_mcp_tools(server_name: str) -> Any:
        mock_tools = AsyncMock()
        # Make list_tools return the actual list, not a coroutine
        mock_tools.list_tools = Mock(return_value=["test-tool-1", "test-tool-2"])

        class AsyncContextManager:
            async def __aenter__(self) -> AsyncMock:
                return mock_tools

            async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                pass

        return AsyncContextManager()

    with patch("api.routes.mcp_router.get_mcp_tools", side_effect=mock_get_mcp_tools):
        yield


@pytest.fixture
def mock_version_service() -> Generator[AsyncMock, None, None]:
    """Mock version service for version router testing."""
    with patch("api.routes.version_router.get_version_service") as mock:
        service = AsyncMock()

        # Mock version info - dynamic component_id to match requests
        def create_mock_version(component_id="test-component", config=None):
            mock_version = Mock()
            mock_version.component_id = component_id
            mock_version.version = 1
            mock_version.component_type = "agent"
            mock_version.config = config or {"test": True}
            mock_version.created_at = "2024-01-01T00:00:00"
            mock_version.is_active = True
            mock_version.description = "Test component for API testing"
            return mock_version

        # Mock history entry
        mock_history = Mock()
        mock_history.version = 1
        mock_history.action = "created"
        mock_history.timestamp = "2024-01-01T00:00:00"
        mock_history.changed_by = "test"
        mock_history.reason = "Initial version"

        # Track created versions to maintain state consistency
        created_versions = {}

        # Configure async service methods with dynamic responses
        async def mock_get_version(component_id, version_num):
            # Return None for non-existent components to trigger 404 responses
            if component_id in {"non-existent", "non-existent-component"}:
                return None
            # Return stored version if it exists, otherwise create default
            key = f"{component_id}-{version_num}"
            if key in created_versions:
                return created_versions[key]
            return create_mock_version(component_id)

        async def mock_create_version(component_id, config=None, **kwargs):
            # Store the version with the provided config
            version_num = kwargs.get("version", 1)
            key = f"{component_id}-{version_num}"
            mock_version = create_mock_version(component_id, config)
            created_versions[key] = mock_version
            return mock_version

        async def mock_list_versions(component_id):
            # Return all versions for this component
            versions = [
                v
                for k, v in created_versions.items()
                if k.startswith(f"{component_id}-")
            ]
            return versions if versions else [create_mock_version(component_id)]

        async def mock_get_active_version(component_id):
            # Return None for non-existent components
            if component_id in {"non-existent", "non-existent-component"}:
                return None
            # Return the first version for this component
            for k, v in created_versions.items():
                if k.startswith(f"{component_id}-"):
                    return v
            return create_mock_version(component_id)

        service.get_version.side_effect = mock_get_version
        service.create_version.side_effect = mock_create_version
        service.update_config.return_value = create_mock_version()
        service.activate_version.return_value = create_mock_version()
        service.delete_version.return_value = True
        service.list_versions.side_effect = mock_list_versions
        service.get_history.return_value = [mock_history]
        service.get_all_components = AsyncMock(return_value=["test-component"])
        service.get_active_version.side_effect = mock_get_active_version

        # Configure get_components_by_type to return empty list for invalid types
        async def mock_get_components_by_type(component_type: str) -> list[str]:
            if component_type in ["agent", "team", "workflow"]:
                return ["test-component"]
            return []

        service.get_components_by_type = AsyncMock(
            side_effect=mock_get_components_by_type,
        )

        mock.return_value = service
        yield service


@pytest.fixture
def mock_startup_orchestration() -> Generator[Mock, None, None]:
    """Mock startup orchestration to avoid loading real components."""

    # Create dict-like mocks for registries
    class DictLikeMock(dict[str, Any]):
        def __init__(self, items: dict[str, Any] | None = None) -> None:
            super().__init__(items or {})

        def keys(self) -> Any:
            return super().keys()

    # Create list-like mocks for startup display
    class ListLikeMock(list[Any]):
        def __init__(self, items: list[Any] | None = None) -> None:
            super().__init__(items or [])

    mock_results = Mock()
    mock_results.registries = Mock()
    mock_results.registries.agents = DictLikeMock({"test-agent": Mock()})
    mock_results.registries.workflows = DictLikeMock({"test-workflow": Mock()})
    mock_results.registries.teams = DictLikeMock()
    mock_results.services = Mock()
    mock_results.services.auth_service = Mock()
    mock_results.services.auth_service.is_auth_enabled.return_value = False
    mock_results.services.auth_service.get_current_key.return_value = "test-key"
    mock_results.services.metrics_service = Mock()
    mock_results.sync_results = {}

    # Create proper startup display mock
    mock_startup_display = Mock()
    mock_startup_display.teams = ListLikeMock([])
    mock_startup_display.agents = ListLikeMock(["test-agent"])
    mock_startup_display.workflows = ListLikeMock(["test-workflow"])
    mock_startup_display.display_summary = Mock()

    with patch(
        "lib.utils.startup_orchestration.orchestrated_startup",
        return_value=mock_results,
    ):
        # Mock both create_startup_display and get_startup_display_with_results
        with patch(
            "lib.utils.startup_display.create_startup_display",
            return_value=mock_startup_display,
        ):
            with patch(
                "lib.utils.startup_orchestration.get_startup_display_with_results",
                return_value=mock_startup_display,
            ):
                # Mock the team creation function used in serve.py
                async def mock_create_team(*args: Any, **kwargs: Any) -> Mock:
                    mock_team = Mock()
                    mock_team.name = "test-team"
                    return mock_team

                with patch(
                    "lib.utils.version_factory.create_team",
                    side_effect=mock_create_team,
                ):
                    yield mock_results


@pytest.fixture
def simple_fastapi_app(
    mock_auth_service,
    mock_database,
    mock_component_registries,
    mock_mcp_catalog,
    mock_version_service,
):
    """Create a simple FastAPI app for testing without complex initialization."""
    from starlette.middleware.cors import CORSMiddleware

    from api.routes.health import health_check_router
    from api.routes.mcp_router import router as mcp_router
    from api.routes.version_router import version_router
    from lib.utils.version_reader import get_api_version

    # Create a simple test app with just the routes we need
    app = FastAPI(
        title="Test Automagik Hive Multi-Agent System",
        version=get_api_version(),
        description="Test Multi-Agent System",
    )

    # Add routes
    app.include_router(health_check_router)
    app.include_router(version_router)
    app.include_router(mcp_router)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


@pytest.fixture
def test_client(simple_fastapi_app):
    """Create a test client for synchronous testing."""
    with TestClient(simple_fastapi_app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(simple_fastapi_app):
    """Create an async test client for async testing."""
    async with AsyncClient(
        transport=ASGITransport(app=simple_fastapi_app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def api_headers():
    """Standard API headers for testing."""
    return {"Content-Type": "application/json", "x-api-key": "test-api-key"}


@pytest.fixture
def sample_version_request():
    """Sample request data for version endpoints."""
    return {
        "component_type": "agent",
        "version": 1,
        "config": {"test": True, "name": "Test Component"},
        "description": "Test component for API testing",
        "is_active": True,
    }


@pytest.fixture
def sample_execution_request():
    """Sample request data for execution endpoints."""
    return {
        "message": "Test message",
        "component_id": "test-component",
        "version": 1,
        "session_id": "test-session",
        "debug_mode": False,
        "user_id": "test-user",
    }


@pytest.fixture
def temp_db_file():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables and cleanup."""
    # Store original environment
    original_env = os.environ.copy()

    # Clear problematic environment variables
    problematic_vars = [
        "env",
    ]  # The 'env=[object Object]' causes Agno Playground validation errors
    for var in problematic_vars:
        if var in os.environ:
            del os.environ[var]

    # Set test environment variables
    test_env = {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/test_db",
        "HIVE_API_PORT": "8887",
        "HIVE_LOG_LEVEL": "ERROR",
        "AGNO_LOG_LEVEL": "ERROR",
        "ANTHROPIC_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key",
        "DISABLE_RELOAD": "true",
    }

    os.environ.update(test_env)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Mock external dependencies that might cause issues
@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """Mock external dependencies to prevent real network calls."""
    patches = [
        patch("lib.knowledge.csv_hot_reload.CSVHotReloadManager"),
        patch("lib.metrics.langwatch_integration.LangWatchManager"),
        patch("lib.logging.setup_logging"),
        patch("lib.logging.set_runtime_mode"),
        # Mock serve.py startup orchestration to prevent component loading at import
        patch("api.serve.orchestrated_startup", new_callable=AsyncMock),
        patch("api.serve.create_startup_display"),
        # Mock async notification functions in lifespan
        patch("common.startup_notifications.send_startup_notification", new_callable=AsyncMock),
        patch("common.startup_notifications.send_shutdown_notification", new_callable=AsyncMock),
        # Mock the serve.py app creation to return a FastAPI app with basic endpoints
        patch("api.serve.create_automagik_api", side_effect=lambda: _create_test_fastapi_app()),
    ]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()
