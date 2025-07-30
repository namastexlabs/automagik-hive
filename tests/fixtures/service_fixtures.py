"""Shared fixtures for service testing."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import psycopg
import pytest
from psycopg_pool import AsyncConnectionPool


@pytest.fixture
def mock_database_pool():
    """Mock database connection pool."""
    mock_pool = AsyncMock(spec=AsyncConnectionPool)
    mock_connection = AsyncMock()
    mock_cursor = AsyncMock()

    # Setup connection context manager - pool.connection() should return a mock that supports async context management
    class MockConnectionAsyncContext:
        async def __aenter__(self):
            return mock_connection

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    # Make connection() method a Mock that returns the async context manager
    mock_pool.connection = MagicMock(return_value=MockConnectionAsyncContext())

    # Setup cursor context manager - cursor() should return a mock that supports async context management
    class MockCursorAsyncContext:
        async def __aenter__(self):
            return mock_cursor

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    # Make cursor() method return the async context manager regardless of arguments
    def mock_cursor_factory(*args, **kwargs):
        return MockCursorAsyncContext()

    mock_connection.cursor = mock_cursor_factory

    # Setup transaction context manager - transaction() should return a mock that supports async context management
    class MockTransactionAsyncContext:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    # Make transaction() method a Mock that returns the async context manager
    mock_connection.transaction = MagicMock(return_value=MockTransactionAsyncContext())

    return {"pool": mock_pool, "connection": mock_connection, "cursor": mock_cursor}


@pytest.fixture
def mock_psycopg_operations():
    """Mock psycopg operations."""
    with (
        patch("lib.services.database_service.AsyncConnectionPool") as mock_pool_class,
    ):
        mock_connection = AsyncMock()
        mock_pool = AsyncMock()
        mock_cursor = AsyncMock()

        # Setup connection context manager - pool.connection() should return a mock that supports async context management
        class MockConnectionAsyncContext:
            async def __aenter__(self):
                return mock_connection

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Make connection() method a Mock that returns the async context manager
        mock_pool.connection = MagicMock(return_value=MockConnectionAsyncContext())

        # Setup cursor context manager - cursor() should return a mock that supports async context management
        class MockCursorAsyncContext:
            async def __aenter__(self):
                return mock_cursor

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Make cursor() method return the async context manager regardless of arguments
        def mock_cursor_factory(*args, **kwargs):
            return MockCursorAsyncContext()

        mock_connection.cursor = mock_cursor_factory

        # Setup transaction context manager - transaction() should return a mock that supports async context management
        class MockTransactionAsyncContext:
            async def __aenter__(self):
                return None

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Make transaction() method a Mock that returns the async context manager
        mock_connection.transaction = MagicMock(
            return_value=MockTransactionAsyncContext(),
        )

        # Add open and close methods
        mock_pool.open = AsyncMock()
        mock_pool.close = AsyncMock()

        mock_pool_class.return_value = mock_pool

        yield {
            "pool_class": mock_pool_class,
            "connection": mock_connection,
            "pool": mock_pool,
            "cursor": mock_cursor,
        }


@pytest.fixture
def sample_database_rows():
    """Sample database rows for testing."""
    return [
        {
            "id": 1,
            "component_id": "test-agent",
            "version": 1,
            "is_active": True,
            "config_hash": "abc123",
            "created_at": "2025-01-01T00:00:00Z",
        },
        {
            "id": 2,
            "component_id": "test-team",
            "version": 1,
            "is_active": True,
            "config_hash": "def456",
            "created_at": "2025-01-01T00:00:00Z",
        },
    ]


@pytest.fixture
def mock_version_service_db():
    """Mock database operations for version service."""
    mock_ops = {
        "fetch_one": AsyncMock(),
        "fetch_all": AsyncMock(),
        "execute": AsyncMock(),
        "execute_transaction": AsyncMock(),
    }

    with patch("lib.services.component_version_service.get_db_service") as mock_get_db:
        mock_db = AsyncMock()
        for op_name, mock_op in mock_ops.items():
            setattr(mock_db, op_name, mock_op)

        mock_get_db.return_value = mock_db
        yield mock_ops


@pytest.fixture
def mock_migration_operations():
    """Mock migration operations."""
    with (
        patch("alembic.config.Config") as mock_config,
        patch("alembic.command.upgrade") as mock_upgrade,
        patch("alembic.command.downgrade") as mock_downgrade,
        patch("alembic.command.current") as mock_current,
    ):
        yield {
            "config": mock_config,
            "upgrade": mock_upgrade,
            "downgrade": mock_downgrade,
            "current": mock_current,
        }


@pytest.fixture
def mock_metrics_queue():
    """Mock metrics queue operations."""
    mock_queue = AsyncMock()
    mock_queue.put = AsyncMock()
    mock_queue.get = AsyncMock()
    mock_queue.empty.return_value = False
    mock_queue.qsize.return_value = 5

    with patch("asyncio.Queue", return_value=mock_queue):
        yield mock_queue


@pytest.fixture
def sample_metrics_data():
    """Sample metrics data for testing."""
    return [
        {
            "trace_id": "trace-123",
            "user_id": "user-456",
            "metadata": {"agent": "test-agent"},
            "input": "test input",
            "output": "test output",
            "timestamps": {"started_at": 1640995200, "finished_at": 1640995210},
        },
        {
            "trace_id": "trace-456",
            "user_id": "user-789",
            "metadata": {"team": "test-team"},
            "input": "another input",
            "output": "another output",
            "timestamps": {"started_at": 1640995220, "finished_at": 1640995230},
        },
    ]


@pytest.fixture
def mock_langwatch_client():
    """Mock LangWatch client."""
    mock_client = AsyncMock()
    mock_client.trace = AsyncMock()
    mock_client.span = AsyncMock()

    with patch("langwatch.langwatch.LangWatch", return_value=mock_client):
        yield mock_client


@pytest.fixture
def component_version_test_data():
    """Test data for component versioning."""
    return {
        "agents": [
            {
                "component_id": "agent-1",
                "version": 1,
                "config_hash": "hash1",
                "is_active": True,
            },
            {
                "component_id": "agent-2",
                "version": 2,
                "config_hash": "hash2",
                "is_active": False,
            },
        ],
        "teams": [
            {
                "component_id": "team-1",
                "version": 1,
                "config_hash": "hash3",
                "is_active": True,
            },
        ],
        "workflows": [
            {
                "component_id": "workflow-1",
                "version": 3,
                "config_hash": "hash4",
                "is_active": True,
            },
        ],
    }


@pytest.fixture
def mock_file_system_ops():
    """Mock file system operations for service testing."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_text") as mock_read,
        patch("pathlib.Path.write_text") as mock_write,
        patch("pathlib.Path.iterdir") as mock_iterdir,
    ):
        mock_exists.return_value = True
        mock_read.return_value = "test content"

        yield {
            "exists": mock_exists,
            "read": mock_read,
            "write": mock_write,
            "iterdir": mock_iterdir,
        }


@pytest.fixture
def database_error_scenarios():
    """Database error scenarios for testing."""
    return {
        "connection_error": psycopg.OperationalError("Connection failed"),
        "query_error": psycopg.ProgrammingError("Invalid query"),
        "transaction_error": psycopg.TransactionRollbackError("Transaction failed"),
        "pool_error": Exception("Pool exhausted"),
    }


@pytest.fixture
def async_test_timeout():
    """Timeout for async tests."""
    return 5.0  # 5 seconds


@pytest.fixture
def service_cleanup():
    """Cleanup services after tests."""
    services_to_cleanup = []

    def register_service(service):
        services_to_cleanup.append(service)
        return service

    yield register_service

    # Cleanup registered services
    for service in services_to_cleanup:
        if hasattr(service, "close"):
            if asyncio.iscoroutinefunction(service.close):
                asyncio.run(service.close())
            else:
                service.close()


@pytest.fixture
def mock_component_discovery():
    """Mock component discovery for registry testing."""
    mock_components = {
        "agents": ["agent-1", "agent-2", "agent-3"],
        "teams": ["team-1", "team-2"],
        "workflows": ["workflow-1", "workflow-2", "workflow-3"],
    }

    with (
        patch("pathlib.Path.iterdir"),
        patch("pathlib.Path.is_dir") as mock_is_dir,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_is_dir.return_value = True
        mock_exists.return_value = True

        yield mock_components
