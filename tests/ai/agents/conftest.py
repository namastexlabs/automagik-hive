"""Configuration and fixtures for registry tests."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to Python path to fix module import issues
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest

# Re-export the specific fixtures needed for registry tests
from tests.fixtures.config_fixtures import sample_agent_config
from tests.fixtures.service_fixtures import mock_file_system_ops


@pytest.fixture(autouse=True)
def mock_database_layer():
    """Mock the entire database layer to prevent real connections."""

    # Mock version service with proper async methods
    mock_version_service = AsyncMock()
    mock_version_service.get_version = AsyncMock()
    mock_version_service.create_version = AsyncMock()
    mock_version_service.get_component_versions = AsyncMock(return_value=[])

    # Mock component version service
    mock_component_service = AsyncMock()
    mock_component_service.get_component_version = AsyncMock()
    mock_component_service.create_component_version = AsyncMock()
    mock_component_service.list_component_versions = AsyncMock(return_value=[])

    # Mock database service
    mock_db_service = AsyncMock()
    mock_db_service.fetch_one = AsyncMock()
    mock_db_service.fetch_all = AsyncMock(return_value=[])
    mock_db_service.execute = AsyncMock()

    # Mock version factory
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value="Test response")
    mock_agent.metadata = {}

    patches = [
        # Mock version services
        patch(
            "lib.versioning.agno_version_service.AgnoVersionService",
            return_value=mock_version_service,
        ),
        patch(
            "lib.services.component_version_service.ComponentVersionService",
            return_value=mock_component_service,
        ),
        patch(
            "lib.services.database_service.get_db_service", return_value=mock_db_service
        ),
        # Mock version factory - These need to be AsyncMock since they are async functions
        patch(
            "lib.utils.version_factory.create_agent",
            new_callable=AsyncMock,
            return_value=mock_agent,
        ),
        patch(
            "lib.utils.version_factory.VersionFactory.create_versioned_component",
            new_callable=AsyncMock,
            return_value=mock_agent,
        ),
        # Mock database migrations and connections
        patch("lib.utils.db_migration.check_and_run_migrations", return_value=False),
        patch("lib.services.database_service.DatabaseService"),
        # Mock Agno framework dependencies
        patch("agno.agent.Agent", return_value=mock_agent),
        patch("agno.team.Team", return_value=mock_agent),
    ]

    for p in patches:
        p.start()

    yield {
        "version_service": mock_version_service,
        "component_service": mock_component_service,
        "db_service": mock_db_service,
        "agent": mock_agent,
    }

    for p in patches:
        try:
            p.stop()
        except Exception:
            # Ignore cleanup errors to prevent test failures
            pass


@pytest.fixture
def setup_test_environment():
    """Setup clean test environment for registry tests."""
    # This fixture runs after the auto mock_database_layer
    return
