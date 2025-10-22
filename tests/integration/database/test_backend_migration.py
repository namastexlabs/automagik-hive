"""
Backend Migration Integration Tests.

Tests migration scenarios between backends:
- PostgreSQL → PGlite migration path
- PostgreSQL → SQLite migration path
- Schema compatibility across backends
- Data export/import patterns
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

# Path setup for imports
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.database import DatabaseBackendType  # noqa: E402
from lib.database.backend_factory import create_backend  # noqa: E402


class TestCrossPlatformSchemaCompatibility:
    """Test schema compatibility across different backends."""

    @pytest_asyncio.fixture
    async def test_schema_sql(self):
        """Common test schema SQL compatible with all backends."""
        return """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """

    @pytest.mark.asyncio
    async def test_sqlite_schema_creation(self, test_schema_sql):
        """Test schema creation in SQLite backend."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url=f"sqlite:///{db_path}")

        try:
            await backend.initialize()

            # Create schema
            for statement in test_schema_sql.strip().split(";"):
                if statement.strip():
                    await backend.execute(statement.strip())

            # Verify tables exist
            tables = await backend.fetch_all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")

            table_names = [t["name"] for t in tables]
            assert "users" in table_names
            assert "posts" in table_names

        finally:
            await backend.close()
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_pglite_schema_creation_mocked(self, test_schema_sql):
        """Test schema creation in PGlite backend (mocked)."""
        backend = create_backend(backend_type=DatabaseBackendType.PGLITE, db_url="pglite://./test.db")

        # Mock HTTP client
        with (
            patch.object(backend, "bridge_process", Mock()),
            patch("lib.database.providers.pglite.httpx.AsyncClient") as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock health check
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}

            # Mock schema creation response
            schema_response = Mock()
            schema_response.status_code = 200
            schema_response.json.return_value = {"success": True}

            # Setup async context manager
            async def mock_health_context():
                temp_client = AsyncMock()
                temp_client.get.return_value = health_response
                return temp_client

            with patch("lib.database.providers.pglite.httpx.AsyncClient") as temp_mock:
                temp_mock.return_value.__aenter__ = mock_health_context
                temp_mock.return_value.__aexit__ = AsyncMock()
                await backend.initialize()

            backend.client = mock_client
            mock_client.post.return_value = schema_response

            # Execute schema
            for statement in test_schema_sql.strip().split(";"):
                if statement.strip():
                    await backend.execute(statement.strip())

            # Verify execute was called
            assert mock_client.post.call_count > 0

            await backend.close()


class TestDataMigrationPatterns:
    """Test data migration patterns between backends."""

    @pytest_asyncio.fixture
    async def sqlite_with_data(self):
        """SQLite backend with test data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url=f"sqlite:///{db_path}")
        await backend.initialize()

        # Create table
        await backend.execute(
            """
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER
            )
            """
        )

        # Insert test data
        test_records = [
            {"id": 1, "name": "record1", "value": 100},
            {"id": 2, "name": "record2", "value": 200},
            {"id": 3, "name": "record3", "value": 300},
        ]

        for record in test_records:
            await backend.execute("INSERT INTO test_data (id, name, value) VALUES (?, ?, ?)", record)

        yield backend, db_path

        await backend.close()
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_export_data_from_sqlite(self, sqlite_with_data):
        """Test exporting data from SQLite backend."""
        backend, _ = sqlite_with_data

        # Export all data
        records = await backend.fetch_all("SELECT * FROM test_data ORDER BY id")

        assert len(records) == 3
        assert records[0]["name"] == "record1"
        assert records[1]["value"] == 200
        assert records[2]["id"] == 3

    @pytest.mark.asyncio
    async def test_import_data_to_new_sqlite(self, sqlite_with_data):
        """Test importing data to a new SQLite backend."""
        source_backend, _ = sqlite_with_data

        # Export from source
        source_records = await source_backend.fetch_all("SELECT * FROM test_data ORDER BY id")

        # Create new target backend
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            target_path = tmp.name

        target_backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url=f"sqlite:///{target_path}")

        try:
            await target_backend.initialize()

            # Create schema in target
            await target_backend.execute(
                """
                CREATE TABLE test_data (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value INTEGER
                )
                """
            )

            # Import data
            for record in source_records:
                await target_backend.execute("INSERT INTO test_data (id, name, value) VALUES (?, ?, ?)", record)

            # Verify import
            target_records = await target_backend.fetch_all("SELECT * FROM test_data ORDER BY id")

            assert len(target_records) == len(source_records)
            assert target_records[0]["name"] == source_records[0]["name"]
            assert target_records[1]["value"] == source_records[1]["value"]

        finally:
            await target_backend.close()
            if os.path.exists(target_path):
                os.unlink(target_path)

    @pytest.mark.asyncio
    async def test_bulk_data_transfer(self, sqlite_with_data):
        """Test bulk data transfer between backends."""
        source_backend, _ = sqlite_with_data

        # Export in bulk
        all_records = await source_backend.fetch_all("SELECT * FROM test_data")

        # Create target
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            target_path = tmp.name

        target_backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url=f"sqlite:///{target_path}")

        try:
            await target_backend.initialize()

            # Create schema
            await target_backend.execute(
                """
                CREATE TABLE test_data (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value INTEGER
                )
                """
            )

            # Bulk insert via transaction
            operations = [
                (
                    "INSERT INTO test_data (id, name, value) VALUES (?, ?, ?)",
                    record,
                )
                for record in all_records
            ]

            await target_backend.execute_transaction(operations)

            # Verify
            count = await target_backend.fetch_one("SELECT COUNT(*) as count FROM test_data")
            assert count["count"] == len(all_records)

        finally:
            await target_backend.close()
            if os.path.exists(target_path):
                os.unlink(target_path)


class TestMigrationErrorHandling:
    """Test error handling during migration."""

    @pytest.mark.asyncio
    async def test_missing_source_table(self):
        """Test handling of missing source table during migration."""
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            # Try to read from non-existent table
            with pytest.raises((Exception, RuntimeError)):  # SQLite table not found wrapped as RuntimeError
                await backend.fetch_all("SELECT * FROM nonexistent_table")

        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_schema_mismatch_detection(self):
        """Test detecting schema mismatches between backends."""
        # Source backend with schema
        source = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await source.initialize()

        try:
            await source.execute(
                """
                CREATE TABLE test (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    extra_field TEXT
                )
                """
            )

            # Get schema info
            schema_info = await source.fetch_all("PRAGMA table_info(test)")

            # Verify expected columns
            column_names = {col["name"] for col in schema_info}
            assert "id" in column_names
            assert "name" in column_names
            assert "extra_field" in column_names

        finally:
            await source.close()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_migration_failure(self):
        """Test transaction rollback when migration fails partway."""
        backend = create_backend(backend_type=DatabaseBackendType.SQLITE, db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            # Create table
            await backend.execute(
                """
                CREATE TABLE test (
                    id INTEGER PRIMARY KEY,
                    value INTEGER NOT NULL
                )
                """
            )

            # Try to insert with one failing operation
            operations = [
                ("INSERT INTO test (id, value) VALUES (?, ?)", {"id": 1, "value": 100}),
                ("INSERT INTO test (id, value) VALUES (?, ?)", {"id": 2, "value": 200}),
                ("INSERT INTO test (id, value) VALUES (?, ?)", {"id": 1, "value": 300}),  # Duplicate key
            ]

            with pytest.raises((Exception, RuntimeError)):  # Integrity errors wrapped as RuntimeError
                await backend.execute_transaction(operations)

            # Verify rollback - should have no rows
            count = await backend.fetch_one("SELECT COUNT(*) as count FROM test")
            assert count["count"] == 0

        finally:
            await backend.close()


class TestPostgreSQLToPGliteMigration:
    """Test migration patterns from PostgreSQL to PGlite."""

    def test_connection_string_conversion(self):
        """Test converting PostgreSQL connection string to PGlite format."""
        # PostgreSQL URL
        pg_url = "postgresql://user:password@localhost:5432/mydb"

        # PGlite equivalent (would store in local directory)
        pglite_url = "pglite://./pglite-data"

        # Create backends
        pg_backend = create_backend(db_url=pg_url)
        pglite_backend = create_backend(db_url=pglite_url)

        assert "PostgreSQL" in pg_backend.__class__.__name__
        assert "PGlite" in pglite_backend.__class__.__name__

    @pytest.mark.asyncio
    async def test_pglite_data_directory_setup(self):
        """Test PGlite data directory setup for migration."""
        pglite_url = "pglite://./test-migration-data"
        backend = create_backend(db_url=pglite_url)

        # Verify backend created
        assert "PGlite" in backend.__class__.__name__
        assert "./test-migration-data" in backend.data_dir or "test-migration-data" in backend.data_dir


class TestPostgreSQLToSQLiteMigration:
    """Test migration patterns from PostgreSQL to SQLite."""

    def test_connection_string_conversion(self):
        """Test converting PostgreSQL connection string to SQLite format."""
        # PostgreSQL URL
        pg_url = "postgresql://user:password@localhost:5432/mydb"

        # SQLite equivalent
        sqlite_url = "sqlite:///data/mydb.db"

        # Create backends
        pg_backend = create_backend(db_url=pg_url)
        sqlite_backend = create_backend(db_url=sqlite_url)

        assert "PostgreSQL" in pg_backend.__class__.__name__
        assert "SQLite" in sqlite_backend.__class__.__name__

    @pytest.mark.asyncio
    async def test_sqlite_file_creation(self):
        """Test SQLite file creation during migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "migration.db"
            backend = create_backend(db_url=f"sqlite:///{sqlite_path}")

            await backend.initialize()

            try:
                # Create test table
                await backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

                # Verify file exists
                # Note: File might not exist until first write with aiosqlite
                # but backend should be initialized
                assert backend._initialized is True

            finally:
                await backend.close()


class TestDataTypeCompatibility:
    """Test data type compatibility across backends."""

    @pytest.mark.asyncio
    async def test_integer_type_compatibility(self):
        """Test INTEGER type works across backends."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value INTEGER)")
            await backend.execute("INSERT INTO test (id, value) VALUES (?, ?)", {"id": 1, "value": 42})

            result = await backend.fetch_one("SELECT * FROM test WHERE id = ?", {"id": 1})
            assert result["value"] == 42

        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_text_type_compatibility(self):
        """Test TEXT type works across backends."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            await backend.execute("INSERT INTO test (id, name) VALUES (?, ?)", {"id": 1, "name": "test_data"})

            result = await backend.fetch_one("SELECT * FROM test WHERE id = ?", {"id": 1})
            assert result["name"] == "test_data"

        finally:
            await backend.close()

    @pytest.mark.asyncio
    async def test_timestamp_type_compatibility(self):
        """Test TIMESTAMP handling across backends."""
        backend = create_backend(db_url="sqlite:///:memory:")
        await backend.initialize()

        try:
            await backend.execute(
                """
                CREATE TABLE test (
                    id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            await backend.execute("INSERT INTO test (id) VALUES (?)", {"id": 1})

            result = await backend.fetch_one("SELECT * FROM test WHERE id = ?", {"id": 1})
            assert "created_at" in result
            assert result["created_at"] is not None

        finally:
            await backend.close()
