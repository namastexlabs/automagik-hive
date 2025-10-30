"""Shared fixtures for service testing."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import psycopg
import pytest
from psycopg_pool import AsyncConnectionPool


@pytest.fixture
def mock_database_pool():
    """
    Mock database connection pool with assertion helpers.

    Use mock.assert_* methods to verify database operations:
    - mocks['pool'].assert_connection_opened(): Verify connection was acquired
    - mocks['cursor'].assert_query_executed(expected_sql): Verify SQL was executed
    - mocks['cursor'].assert_fetchone_called(): Verify fetchone was called
    - mocks['cursor'].assert_fetchall_called(): Verify fetchall was called
    - mocks['connection'].assert_transaction_used(): Verify transaction was used
    - mocks.reset_assertions(): Reset all call counts
    """
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

    # Setup transaction context manager - transaction() should return a mock that supports async management
    class MockTransactionAsyncContext:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    # Make transaction() method a Mock that returns the async context manager
    mock_connection.transaction = MagicMock(return_value=MockTransactionAsyncContext())

    # Add assertion helpers to pool
    def assert_connection_opened():
        """Assert that pool.connection() was called."""
        mock_pool.connection.assert_called()

    # Add assertion helpers to cursor
    def assert_query_executed(expected_sql=None):
        """Assert execute was called, optionally with specific SQL."""
        mock_cursor.execute.assert_called()
        if expected_sql is not None:
            # Check if any call matches the expected SQL
            calls = [str(call[0][0]) if call[0] else "" for call in mock_cursor.execute.call_args_list]
            assert any(expected_sql in call for call in calls), (
                f"Expected SQL '{expected_sql}' not found in calls: {calls}"
            )

    def assert_fetchone_called():
        """Assert fetchone was called."""
        mock_cursor.fetchone.assert_called()

    def assert_fetchall_called():
        """Assert fetchall was called."""
        mock_cursor.fetchall.assert_called()

    # Add assertion helpers to connection
    def assert_transaction_used():
        """Assert transaction() was called."""
        mock_connection.transaction.assert_called()

    # Global reset
    def reset_assertions():
        """Reset all mock call counts."""
        mock_pool.connection.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchone.reset_mock()
        mock_cursor.fetchall.reset_mock()
        mock_connection.transaction.reset_mock()

    mock_pool.assert_connection_opened = assert_connection_opened
    mock_cursor.assert_query_executed = assert_query_executed
    mock_cursor.assert_fetchone_called = assert_fetchone_called
    mock_cursor.assert_fetchall_called = assert_fetchall_called
    mock_connection.assert_transaction_used = assert_transaction_used

    mocks = {"pool": mock_pool, "connection": mock_connection, "cursor": mock_cursor}
    mocks["reset_assertions"] = reset_assertions

    return mocks


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
    """
    Mock database operations for version service with assertion helpers.

    Use mock_ops assertion helpers:
    - mock_ops['fetch_one'].assert_called(): Verify single fetch
    - mock_ops['fetch_all'].assert_called(): Verify multi fetch
    - mock_ops['execute'].assert_called(): Verify execute
    - mock_ops['execute_transaction'].assert_called(): Verify transaction
    - mock_ops.assert_version_fetched(): Verify version query
    """
    mock_ops = {
        "fetch_one": AsyncMock(),
        "fetch_all": AsyncMock(),
        "execute": AsyncMock(),
        "execute_transaction": AsyncMock(),
    }

    # Add assertion helper
    def assert_version_fetched():
        """Assert that fetch_one or fetch_all was called."""
        assert mock_ops["fetch_one"].called or mock_ops["fetch_all"].called, (
            "Expected fetch_one or fetch_all to be called"
        )

    def reset_assertions():
        """Reset all db operation mocks."""
        for mock_op in mock_ops.values():
            if hasattr(mock_op, "reset_mock"):
                mock_op.reset_mock()

    mock_ops["assert_version_fetched"] = assert_version_fetched
    mock_ops["reset_assertions"] = reset_assertions

    with patch("lib.services.component_version_service.get_db_service") as mock_get_db:
        mock_db = AsyncMock()
        for op_name, mock_op in mock_ops.items():
            if not callable(mock_op):  # Skip our helper functions
                continue
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
    """
    Mock metrics queue operations with assertion helpers.

    Use mock.assert_* methods to verify queue operations:
    - mock.assert_metric_added(): Verify put was called
    - mock.assert_metric_retrieved(): Verify get was called
    - mock.assert_queue_size_checked(): Verify qsize was called
    - mock.assert_put_count(expected_count): Verify specific number of puts
    """
    mock_queue = AsyncMock()
    mock_queue.put = AsyncMock()
    mock_queue.get = AsyncMock()
    mock_queue.empty.return_value = False
    mock_queue.qsize.return_value = 5

    # Add assertion helpers
    def assert_metric_added():
        """Assert that put was called to add a metric."""
        mock_queue.put.assert_called()

    def assert_metric_retrieved():
        """Assert that get was called to retrieve a metric."""
        mock_queue.get.assert_called()

    def assert_queue_size_checked():
        """Assert that qsize was called."""
        mock_queue.qsize.assert_called()

    def assert_put_count(expected_count):
        """Assert put was called exactly N times."""
        assert mock_queue.put.call_count == expected_count

    def reset_assertions():
        """Reset all queue mock call counts."""
        mock_queue.put.reset_mock()
        mock_queue.get.reset_mock()
        mock_queue.qsize.reset_mock()
        mock_queue.empty.reset_mock()

    mock_queue.assert_metric_added = assert_metric_added
    mock_queue.assert_metric_retrieved = assert_metric_retrieved
    mock_queue.assert_queue_size_checked = assert_queue_size_checked
    mock_queue.assert_put_count = assert_put_count
    mock_queue.reset_assertions = reset_assertions

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
    """
    Mock LangWatch client with assertion helpers.

    Use mock.assert_* methods to verify telemetry:
    - mock.assert_trace_created(): Verify trace was called
    - mock.assert_span_created(): Verify span was called
    - mock.assert_telemetry_count(expected_count): Verify trace call count
    """
    mock_client = AsyncMock()
    mock_client.trace = AsyncMock()
    mock_client.span = AsyncMock()

    # Add assertion helpers
    def assert_trace_created():
        """Assert that trace was called."""
        mock_client.trace.assert_called()

    def assert_span_created():
        """Assert that span was called."""
        mock_client.span.assert_called()

    def assert_telemetry_count(expected_count):
        """Assert trace was called exactly N times."""
        assert mock_client.trace.call_count == expected_count

    def reset_assertions():
        """Reset all LangWatch call counts."""
        mock_client.trace.reset_mock()
        mock_client.span.reset_mock()

    mock_client.assert_trace_created = assert_trace_created
    mock_client.assert_span_created = assert_span_created
    mock_client.assert_telemetry_count = assert_telemetry_count
    mock_client.reset_assertions = reset_assertions

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


@pytest.fixture
def mock_startup_results():
    """Mock orchestrated_startup results with proper structure for API tests."""
    # Create mock agent
    mock_agent = MagicMock()
    mock_agent.name = "Test Agent"
    mock_agent.agent_id = "test-agent"

    # Create mock auth service
    mock_auth_service = MagicMock()
    mock_auth_service.is_auth_enabled.return_value = False
    mock_auth_service.get_current_key.return_value = "test-key"

    # Create mock metrics service
    mock_metrics_service = MagicMock()

    # Create mock registries
    mock_registries = MagicMock()
    # IMPORTANT: Set as dict, not MagicMock, so `bool(available_agents)` works correctly
    mock_registries.agents = {"test-agent": mock_agent}
    mock_registries.teams = {}
    mock_registries.workflows = {}

    # Create mock services
    mock_services = MagicMock()
    mock_services.auth_service = mock_auth_service
    mock_services.metrics_service = mock_metrics_service

    # Create startup results
    mock_results = MagicMock()
    mock_results.registries = mock_registries
    mock_results.services = mock_services
    mock_results.sync_results = {}
    mock_results.startup_display = MagicMock()

    return mock_results
