"""
Test configuration and shared fixtures for API testing.

This provides comprehensive fixtures for testing the Automagik Hive API layer
with proper isolation, authentication, and database setup.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment before importing API modules
os.environ["HIVE_ENVIRONMENT"] = "development"
os.environ["HIVE_DATABASE_URL"] = "sqlite:///test.db"
os.environ["HIVE_API_PORT"] = "8887"
os.environ["HIVE_LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests
os.environ["AGNO_LOG_LEVEL"] = "ERROR"

# Mock external dependencies to avoid real API calls
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    with patch("lib.auth.dependencies.get_auth_service") as mock:
        auth_service = Mock()
        auth_service.is_auth_enabled.return_value = False
        auth_service.get_current_key.return_value = "test-api-key"
        auth_service.validate_api_key.return_value = True
        mock.return_value = auth_service
        yield auth_service


@pytest.fixture
def mock_database():
    """Mock database operations to avoid real database setup."""
    with patch("lib.utils.db_migration.check_and_run_migrations") as mock_migration:
        mock_migration.return_value = False  # No migrations needed
        yield mock_migration


@pytest.fixture
def mock_component_registries():
    """Mock component registries to avoid loading real agents/teams/workflows."""
    mock_agents = {
        "test-agent": {
            "name": "Test Agent",
            "version": "1.0.0",
            "config": {"test": True}
        }
    }
    
    mock_teams = {
        "test-team": {
            "name": "Test Team",
            "version": "1.0.0",
            "config": {"test": True}
        }
    }
    
    mock_workflows = {
        "test-workflow": {
            "name": "Test Workflow", 
            "version": "1.0.0",
            "config": {"test": True}
        }
    }
    
    patches = [
        patch("ai.agents.registry.AgentRegistry.list_available_agents", return_value=list(mock_agents.keys())),
        patch("ai.teams.registry.list_available_teams", return_value=list(mock_teams.keys())),
        patch("ai.workflows.registry.list_available_workflows", return_value=list(mock_workflows.keys())),
        patch("lib.utils.version_factory.create_agent", return_value=Mock()),
        patch("lib.utils.version_factory.create_team", return_value=Mock()),
        patch("ai.workflows.registry.get_workflow", return_value=Mock()),
    ]
    
    for p in patches:
        p.start()
    
    yield {
        "agents": mock_agents,
        "teams": mock_teams, 
        "workflows": mock_workflows
    }
    
    for p in patches:
        p.stop()


@pytest.fixture
def mock_mcp_catalog():
    """Mock MCP catalog for testing MCP endpoints."""
    with patch("lib.mcp.MCPCatalog") as mock_catalog_class:
        mock_catalog = Mock()
        mock_catalog.list_servers.return_value = ["test-server", "another-server"]
        mock_catalog.get_server_info.return_value = {
            "type": "command",
            "is_sse_server": False,
            "is_command_server": True,
            "url": None,
            "command": "test-command"
        }
        mock_catalog_class.return_value = mock_catalog
        yield mock_catalog


@pytest.fixture
def mock_mcp_tools():
    """Mock MCP tools for connection testing."""
    async def mock_get_mcp_tools(server_name: str):
        mock_tools = AsyncMock()
        mock_tools.list_tools.return_value = ["test-tool-1", "test-tool-2"]
        
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_tools
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return AsyncContextManager()
    
    with patch("lib.mcp.get_mcp_tools", side_effect=mock_get_mcp_tools):
        yield


@pytest.fixture
def mock_version_service():
    """Mock version service for version router testing."""
    with patch("api.routes.version_router.get_version_service") as mock:
        service = Mock()
        
        # Mock version info
        mock_version = Mock()
        mock_version.component_id = "test-component"
        mock_version.version = 1
        mock_version.component_type = "agent"
        mock_version.config = {"test": True}
        mock_version.created_at = "2024-01-01T00:00:00"
        mock_version.is_active = True
        mock_version.description = "Test component for API testing"
        
        # Mock history entry
        mock_history = Mock()
        mock_history.version = 1
        mock_history.action = "created"
        mock_history.timestamp = "2024-01-01T00:00:00"
        mock_history.changed_by = "test"
        mock_history.reason = "Initial version"
        
        # Configure service methods
        service.get_version.return_value = mock_version
        service.create_version.return_value = mock_version
        service.update_config.return_value = mock_version
        service.activate_version.return_value = mock_version
        service.delete_version.return_value = True
        service.list_versions.return_value = [mock_version]
        service.get_history.return_value = [mock_history]
        service.get_all_components.return_value = ["test-component"]
        service.get_active_version.return_value = mock_version
        # Configure get_components_by_type to return empty list for invalid types
        def mock_get_components_by_type(component_type):
            if component_type in ["agent", "team", "workflow"]:
                return ["test-component"]
            return []
        
        service.get_components_by_type.side_effect = mock_get_components_by_type
        
        mock.return_value = service
        yield service


@pytest.fixture
def mock_startup_orchestration():
    """Mock startup orchestration to avoid loading real components."""
    mock_results = Mock()
    mock_results.registries = Mock()
    mock_results.registries.agents = {"test-agent": Mock()}
    mock_results.registries.workflows = {"test-workflow": Mock()}
    mock_results.registries.teams = {"test-team": Mock()}
    mock_results.services = Mock()
    mock_results.services.auth_service = Mock()
    mock_results.services.auth_service.is_auth_enabled.return_value = False
    mock_results.services.auth_service.get_current_key.return_value = "test-key"
    mock_results.sync_results = {}
    
    with patch("lib.utils.startup_orchestration.orchestrated_startup", return_value=mock_results):
        with patch("lib.utils.startup_orchestration.get_startup_display_with_results") as mock_display:
            mock_display.return_value = Mock()
            mock_display.return_value.teams = []
            mock_display.return_value.agents = []
            mock_display.return_value.workflows = []
            mock_display.return_value.display_summary = Mock()
            yield mock_results


@pytest.fixture
def simple_fastapi_app(
    mock_auth_service,
    mock_database,
    mock_component_registries,
    mock_mcp_catalog,
    mock_version_service
):
    """Create a simple FastAPI app for testing without complex initialization."""
    from fastapi import FastAPI
    from api.routes.health import health_check_router
    from api.routes.version_router import version_router
    from api.routes.mcp_router import router as mcp_router
    from starlette.middleware.cors import CORSMiddleware
    
    # Create a simple test app with just the routes we need
    app = FastAPI(
        title="Test Automagik Hive Multi-Agent System", 
        version="2.0",
        description="Test Multi-Agent System"
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
    
    yield app


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
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def api_headers():
    """Standard API headers for testing."""
    return {
        "Content-Type": "application/json",
        "x-api-key": "test-api-key"
    }


@pytest.fixture
def sample_version_request():
    """Sample request data for version endpoints."""
    return {
        "component_type": "agent",
        "version": 1,
        "config": {"test": True, "name": "Test Component"},
        "description": "Test component for API testing",
        "is_active": True
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
        "user_id": "test-user"
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
    
    # Set test environment variables
    test_env = {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_DATABASE_URL": "sqlite:///test.db",
        "HIVE_API_PORT": "8887",
        "HIVE_LOG_LEVEL": "ERROR",
        "AGNO_LOG_LEVEL": "ERROR",
        "ANTHROPIC_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key",
        "DISABLE_RELOAD": "true"
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
    ]
    
    for p in patches:
        p.start()
    
    yield
    
    for p in patches:
        p.stop()