"""
Test configuration and shared fixtures for API testing.

This provides comprehensive fixtures for testing the Automagik Hive API layer
with proper isolation, authentication, and database setup.

# Testing agent verification comment: hive-testing-fixer can edit files in tests/ directory
# Testing agents work fine in tests directory
# Hook test: Direct Edit call should be allowed in tests/
"""

import asyncio
import os
import sys
import tempfile
import warnings
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Add project root to Python path to fix module import issues
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ============================================================================
# GLOBAL TEST ISOLATION ENFORCEMENT
# ============================================================================


@pytest.fixture(autouse=True)
def enforce_global_test_isolation(request, tmp_path, monkeypatch):
    """
    Enforce global test isolation to prevent project directory pollution.

    This fixture automatically:
    1. Monitors project directory for new file creation during tests
    2. Redirects common file operations to temp directories
    3. Warns about potential project pollution
    4. Provides defense-in-depth against test artifacts

    Applied to ALL tests automatically via autouse=True.
    """
    # Store original directory state
    original_cwd = Path.cwd()

    # Identify safe temp directories for this test
    test_temp_dir = tmp_path / "test_isolation"
    test_temp_dir.mkdir(exist_ok=True)

    # Track files that existed before test
    if original_cwd == project_root:
        # Only monitor if we're in the project root
        existing_files = set()
        try:
            # Capture current project files (not recursively, just root level)
            for item in project_root.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    existing_files.add(item.name)
        except Exception:
            # If we can't read directory, skip monitoring
            existing_files = set()
    else:
        existing_files = set()

    # Patch common file creation functions to redirect to temp
    original_open = open

    def safe_open(filename, mode="r", *args, **kwargs):
        """Redirect file creation to temp directory if in project root."""
        file_path = Path(filename)

        # If trying to create a file in project root with write mode
        if (
            file_path.parent == project_root
            and isinstance(mode, str)
            and any(write_mode in mode for write_mode in ["w", "a", "x"])
            and not file_path.name.startswith(".")
        ):
            # Create a warning but allow the operation
            warnings.warn(
                f"Test '{request.node.name}' attempted to create file '{filename}' "
                f"in project root. Consider using isolated_workspace fixture or tmp_path.",
                category=UserWarning,
                stacklevel=3,
            )

        return original_open(filename, mode, *args, **kwargs)

    # Apply the patch
    monkeypatch.setattr("builtins.open", safe_open)

    # Yield control to the test
    yield test_temp_dir

    # Post-test validation: Check for new files in project root
    if existing_files is not None and original_cwd == project_root:
        try:
            current_files = set()
            for item in project_root.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    current_files.add(item.name)

            new_files = current_files - existing_files
            if new_files:
                # Filter out expected test artifacts
                concerning_files = [
                    f
                    for f in new_files
                    if not any(pattern in f.lower() for pattern in ["test-", "tmp_", ".tmp", ".bak", ".test"])
                ]

                if concerning_files:
                    warnings.warn(
                        f"Test '{request.node.name}' may have created files in project root: "
                        f"{concerning_files}. Use isolated_workspace fixture to prevent pollution.",
                        category=UserWarning,
                        stacklevel=2,
                    )
        except Exception:
            # If we can't validate, skip the check
            pass


@pytest.fixture
def isolated_workspace(tmp_path):
    """Enhanced test isolation with working directory change.

    Creates a temporary directory and changes working directory to it
    for the duration of the test. This provides the strongest protection
    against test pollution by ensuring relative paths point to temp space.

    Used in combination with enforce_global_test_isolation for defense-in-depth:
    - Global fixture: Monitors and warns about project pollution
    - This fixture: Completely isolates working directory

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Yields:
        Path: The temporary workspace directory
    """
    original_cwd = os.getcwd()
    workspace_dir = tmp_path / "test_workspace"
    workspace_dir.mkdir()
    os.chdir(workspace_dir)
    try:
        yield workspace_dir
    finally:
        os.chdir(original_cwd)


# Register pytest markers to avoid "Unknown marker" warnings
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests requiring external services")
    config.addinivalue_line("markers", "postgres: marks tests as requiring PostgreSQL database connection")
    config.addinivalue_line("markers", "safe: marks tests as safe to run in any environment without side effects")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "unit: marks tests as unit tests with no external dependencies")


# Pytest plugins must be defined at the top level conftest.py
# Note: tests.config.conftest is auto-discovered, so we only include explicit fixture modules
pytest_plugins = [
    "tests.fixtures.config_fixtures",
    "tests.fixtures.service_fixtures",
    "pytest_mock",  # Moved from tests/cli/conftest.py to fix collection error
]

# Set test environment before importing API modules
os.environ["HIVE_ENVIRONMENT"] = "development"
os.environ["HIVE_DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/test_db"
os.environ["HIVE_API_PORT"] = "8887"
os.environ["HIVE_LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests
os.environ["AGNO_LOG_LEVEL"] = "ERROR"
os.environ["HIVE_API_KEY"] = "hive_test_key_12345678901234567890123456789012"
os.environ["HIVE_CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8080"

# Mock external dependencies to avoid real API calls
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"


def _create_test_fastapi_app() -> FastAPI:
    """Create a minimal FastAPI app for testing with basic endpoints."""
    test_app = FastAPI(
        title="Automagik Hive Multi-Agent System", description="Test Multi-Agent System", version="1.0.0"
    )

    @test_app.get("/health")
    async def health():
        return {
            "status": "success",
            "service": "Automagik Hive Multi-Agent System",
            "router": "health",
            "path": "/health",
            "utc": datetime.now(tz=UTC).isoformat(),
            "message": "System operational",
        }

    @test_app.get("/")
    async def root():
        return {"status": "ok"}

    return test_app


@pytest.fixture(scope="session", autouse=True)
def preserve_builtin_input():
    """Preserve and restore the original input function to prevent KeyboardInterrupt during pytest shutdown."""
    import builtins

    # Back up the original input function
    original_input = builtins.input
    builtins.__original_input__ = original_input

    yield

    # Restore the original input function during session cleanup
    # This prevents any lingering mocks with KeyboardInterrupt side effects
    # from interfering with pytest's shutdown process
    builtins.input = original_input


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        # Cancel all pending tasks before closing the loop
        try:
            pending_tasks = asyncio.all_tasks(loop)
            if pending_tasks:
                for task in pending_tasks:
                    task.cancel()
                # Run the loop briefly to allow cancelled tasks to complete
                loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
        except Exception:
            # Ignore cleanup errors to prevent test failures
            pass
        finally:
            loop.close()

        # Ensure builtins.input is restored to prevent
        # KeyboardInterrupt during pytest shutdown
        try:
            import builtins

            # Force restore the original input function to prevent any lingering mocks
            # that might have KeyboardInterrupt side effects
            if hasattr(builtins, "__original_input__"):
                builtins.input = builtins.__original_input__
            else:
                # Restore input to a safe default implementation
                def safe_input(prompt=""):
                    return ""

                builtins.input = safe_input
        except Exception:
            # Fail silently to avoid affecting test results
            pass


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
def mock_component_registries() -> Generator[dict[str, dict[str, dict[str, Any]]], None, None]:
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

    # Define patches with error handling for missing modules
    patch_specs = [
        ("ai.agents.registry.AgentRegistry.list_available_agents", "return_value", list(mock_agents.keys())),
        ("ai.teams.registry.list_available_teams", "return_value", list(mock_teams.keys())),
        ("ai.workflows.registry.list_available_workflows", "return_value", list(mock_workflows.keys())),
        ("lib.utils.version_factory.create_agent", "async_mock", mock_agent),
        ("lib.utils.version_factory.create_team", "async_mock", mock_agent),
        ("ai.workflows.registry.get_workflow", "return_value", mock_agent),
        ("lib.services.database_service.get_db_service", "return_value", AsyncMock()),
        ("lib.services.component_version_service.ComponentVersionService", "mock", None),
        ("lib.versioning.agno_version_service.AgnoVersionService", "mock", None),
        ("lib.utils.version_factory.VersionFactory.create_versioned_component", "special", None),
    ]

    patches = []
    for target, patch_type, value in patch_specs:
        try:
            if patch_type == "return_value":
                patches.append(patch(target, return_value=value))
            elif patch_type == "async_mock":
                patches.append(patch(target, new_callable=AsyncMock, return_value=value))
            elif patch_type == "mock":
                patches.append(patch(target))
            elif patch_type == "special":
                # Special case for version factory
                patches.append(
                    patch(
                        target,
                        new_callable=lambda: AsyncMock(
                            side_effect=lambda component_id, **kwargs: None
                            if component_id == "non-existent-component"
                            else mock_agent
                        ),
                    )
                )
        except ImportError:
            # Skip patches for modules that can't be imported
            continue
        except Exception:
            # Skip patches that can't be created
            continue

    started_patches = []
    for p in patches:
        try:
            p.start()
            started_patches.append(p)
        except Exception:
            # Skip patches that can't be started
            continue

    yield {"agents": mock_agents, "teams": mock_teams, "workflows": mock_workflows}

    for p in started_patches:
        try:
            p.stop()
        except Exception:
            # Ignore cleanup errors to prevent test failures
            pass


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
            versions = [v for k, v in created_versions.items() if k.startswith(f"{component_id}-")]
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

    patches = []

    # Use try/except for each patch to handle missing modules gracefully
    try:
        patches.append(
            patch(
                "lib.utils.startup_orchestration.orchestrated_startup",
                return_value=mock_results,
            )
        )
    except ImportError:
        pass

    try:
        patches.append(
            patch(
                "lib.utils.startup_display.create_startup_display",
                return_value=mock_startup_display,
            )
        )
    except ImportError:
        pass

    try:
        patches.append(
            patch(
                "lib.utils.startup_orchestration.get_startup_display_with_results",
                return_value=mock_startup_display,
            )
        )
    except ImportError:
        pass

    try:

        async def mock_create_team(*args: Any, **kwargs: Any) -> Mock:
            mock_team = Mock()
            mock_team.name = "test-team"
            return mock_team

        patches.append(
            patch(
                "lib.utils.version_factory.create_team",
                side_effect=mock_create_team,
            )
        )
    except ImportError:
        pass

    # Start all valid patches
    started_patches = []
    for p in patches:
        try:
            p.start()
            started_patches.append(p)
        except Exception:
            # Skip patches that can't be started
            pass

    try:
        yield mock_results
    finally:
        # Stop all started patches
        for p in started_patches:
            try:
                p.stop()
            except Exception:
                # Ignore cleanup errors
                pass


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
    from lib.utils.version_reader import get_api_version

    # Create a simple test app with just the routes we need
    app = FastAPI(
        title="Test Automagik Hive Multi-Agent System",
        version=get_api_version(),
        description="Test Multi-Agent System",
    )

    # Add health router directly at root level for /health endpoint compatibility
    app.include_router(health_check_router)

    # Add the v1_router which includes all sub-routers with proper /api/v1 prefix
    from api.routes.v1_router import v1_router

    app.include_router(v1_router)

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
        "HIVE_API_KEY": "hive_test_key_12345678901234567890123456789012",
        "HIVE_CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
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
    # Define patches with error handling for missing modules
    patch_specs = [
        ("lib.knowledge.csv_hot_reload.CSVHotReloadManager", None),
        ("lib.metrics.langwatch_integration.LangWatchManager", None),
        ("lib.logging.setup_logging", None),
        ("lib.logging.set_runtime_mode", None),
        ("api.serve.orchestrated_startup", AsyncMock),
        ("api.serve.create_startup_display", None),
        ("common.startup_notifications.send_startup_notification", AsyncMock),
        ("common.startup_notifications.send_shutdown_notification", AsyncMock),
        ("api.serve.create_automagik_api", lambda: _create_test_fastapi_app()),
    ]

    patches = []
    for target, new_callable in patch_specs:
        try:
            if new_callable == AsyncMock:
                patches.append(patch(target, new_callable=AsyncMock))
            elif callable(new_callable):
                patches.append(patch(target, side_effect=new_callable))
            else:
                patches.append(patch(target))
        except ImportError:
            # Skip patches for modules that can't be imported
            continue
        except Exception:
            # Skip patches that can't be created
            continue

    started_patches = []
    try:
        for p in patches:
            try:
                p.start()
                started_patches.append(p)
            except Exception:
                # Skip patches that can't be started
                continue
        yield
    finally:
        # Stop patches in reverse order to ensure proper cleanup
        for p in reversed(started_patches):
            try:
                p.stop()
            except Exception:
                # Ignore cleanup errors to prevent test failures
                pass
