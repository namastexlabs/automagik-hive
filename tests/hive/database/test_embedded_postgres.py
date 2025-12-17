"""
Tests for EmbeddedPostgres module.

Unit tests use mocks to avoid downloading PostgreSQL binaries.
Integration tests (marked @pytest.mark.slow) test the full lifecycle.
"""

import platform
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hive.database.embedded_postgres import (
    BinaryDownloadError,
    EmbeddedPostgres,
    EmbeddedPostgresError,
    InitializationError,
    StartupError,
    cleanup_embedded_postgres,
    get_embedded_postgres,
    stop_embedded_postgres,
)


class TestEmbeddedPostgresInit:
    """Test EmbeddedPostgres initialization."""

    def test_default_initialization(self):
        """Test default constructor values."""
        pg = EmbeddedPostgres()

        assert pg.port == 5432
        assert pg.postgres_version == "16.6.0"
        assert pg.process is None
        assert pg._initialized is False
        assert "pgdata-" in str(pg.data_dir)

    def test_custom_initialization(self):
        """Test custom constructor values."""
        data_dir = Path("/tmp/custom-pgdata")  # noqa: S108
        pg = EmbeddedPostgres(
            data_dir=data_dir,
            port=5433,
            postgres_version="15.4",
        )

        assert pg.data_dir == data_dir
        assert pg.port == 5433
        assert pg.postgres_version == "15.4"

    def test_platform_detection(self):
        """Test platform detection logic."""
        pg = EmbeddedPostgres()

        system = platform.system().lower()
        assert pg._system == system
        assert pg._machine in ("x86_64", "arm64", "aarch64")

    def test_binary_paths(self):
        """Test binary path properties."""
        pg = EmbeddedPostgres()

        assert pg.postgres_bin.name == "postgres"
        assert pg.initdb_bin.name == "initdb"
        assert pg.psql_bin.name == "psql"
        assert pg.pg_isready_bin.name == "pg_isready"


class TestConnectionUrls:
    """Test connection URL generation."""

    def test_default_connection_url(self):
        """Test default SQLAlchemy connection URL."""
        pg = EmbeddedPostgres(port=5432)
        url = pg.get_connection_url()

        assert url == "postgresql+psycopg://postgres@localhost:5432/hive"

    def test_custom_dialect_connection_url(self):
        """Test connection URL with custom dialect."""
        pg = EmbeddedPostgres(port=5433)
        url = pg.get_connection_url(dialect="postgresql")

        assert url == "postgresql://postgres@localhost:5433/hive"

    def test_asyncpg_url(self):
        """Test asyncpg connection URL."""
        pg = EmbeddedPostgres(port=5434)
        url = pg.get_asyncpg_url()

        assert url == "postgresql://postgres@localhost:5434/hive"


class TestPlatformTargets:
    """Test platform target triple mapping."""

    def test_linux_x86_target(self):
        """Test Linux x86_64 target triple."""
        pg = EmbeddedPostgres()

        target = pg.PLATFORM_TARGETS.get(("linux", "x86_64"))
        assert target is not None
        assert target == "x86_64-unknown-linux-gnu"

    def test_linux_arm_target(self):
        """Test Linux ARM64 target triple."""
        pg = EmbeddedPostgres()

        target = pg.PLATFORM_TARGETS.get(("linux", "aarch64"))
        assert target is not None
        assert target == "aarch64-unknown-linux-gnu"

    def test_macos_x86_target(self):
        """Test macOS x86_64 target triple."""
        pg = EmbeddedPostgres()

        target = pg.PLATFORM_TARGETS.get(("darwin", "x86_64"))
        assert target is not None
        assert target == "x86_64-apple-darwin"

    def test_macos_arm_target(self):
        """Test macOS ARM64 target triple."""
        pg = EmbeddedPostgres()

        target = pg.PLATFORM_TARGETS.get(("darwin", "arm64"))
        assert target is not None
        assert target == "aarch64-apple-darwin"


class TestIsRunning:
    """Test is_running() method."""

    def test_not_running_no_process(self):
        """Test is_running when no process exists."""
        pg = EmbeddedPostgres()
        assert pg.is_running() is False

    def test_not_running_terminated_process(self):
        """Test is_running when process has terminated."""
        pg = EmbeddedPostgres()
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process exited
        pg.process = mock_process

        assert pg.is_running() is False

    def test_running_active_process(self):
        """Test is_running when process is active."""
        pg = EmbeddedPostgres()
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        pg.process = mock_process

        assert pg.is_running() is True


class TestRepr:
    """Test string representation."""

    def test_repr_stopped(self):
        """Test repr when stopped."""
        pg = EmbeddedPostgres(port=5432)
        assert "port=5432" in repr(pg)
        assert "stopped" in repr(pg)

    def test_repr_running(self):
        """Test repr when running."""
        pg = EmbeddedPostgres(port=5433)
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        pg.process = mock_process

        assert "port=5433" in repr(pg)
        assert "running" in repr(pg)


class TestEnsureBinaries:
    """Test binary download and caching."""

    @pytest.mark.asyncio
    async def test_binaries_already_cached(self):
        """Test skipping download when binaries are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bin_cache = Path(tmpdir)
            # Create fake cached binary
            postgres_bin = bin_cache / "pgsql" / "bin" / "postgres"
            postgres_bin.parent.mkdir(parents=True)
            postgres_bin.touch()

            pg = EmbeddedPostgres(bin_cache_dir=bin_cache)

            # Should not raise and not download
            await pg._ensure_binaries()

    @pytest.mark.asyncio
    async def test_unsupported_platform_raises(self):
        """Test error on unsupported platform."""
        pg = EmbeddedPostgres()
        pg._system = "windows"  # Not supported
        pg._machine = "x86_64"
        pg._target = ""  # Clear target to ensure platform check is reached

        with pytest.raises(BinaryDownloadError) as exc_info:
            await pg._ensure_binaries()

        assert "Unsupported platform" in str(exc_info.value)


class TestInitCluster:
    """Test cluster initialization."""

    @pytest.mark.asyncio
    async def test_init_cluster_creates_directory(self):
        """Test that init_cluster creates data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bin_cache = Path(tmpdir) / "bin_cache"
            data_dir = Path(tmpdir) / "pgdata"

            # Create fake initdb binary
            initdb_bin = bin_cache / "pgsql" / "bin" / "initdb"
            initdb_bin.parent.mkdir(parents=True)
            initdb_bin.touch()
            initdb_bin.chmod(0o755)

            pg = EmbeddedPostgres(data_dir=data_dir, bin_cache_dir=bin_cache)

            # Mock subprocess.run to succeed
            with patch("asyncio.to_thread") as mock_thread:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stderr = ""
                mock_thread.return_value = mock_result

                # Mock _configure_postgres
                pg._configure_postgres = AsyncMock()

                await pg._init_cluster()

                assert data_dir.exists()

    @pytest.mark.asyncio
    async def test_init_cluster_failure_raises(self):
        """Test InitializationError on initdb failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bin_cache = Path(tmpdir) / "bin_cache"
            data_dir = Path(tmpdir) / "pgdata"

            # Create fake initdb binary
            initdb_bin = bin_cache / "pgsql" / "bin" / "initdb"
            initdb_bin.parent.mkdir(parents=True)
            initdb_bin.touch()
            initdb_bin.chmod(0o755)

            pg = EmbeddedPostgres(data_dir=data_dir, bin_cache_dir=bin_cache)

            # Mock subprocess.run to fail
            with patch("asyncio.to_thread") as mock_thread:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stderr = "initdb: error: directory exists"
                mock_thread.return_value = mock_result

                with pytest.raises(InitializationError) as exc_info:
                    await pg._init_cluster()

                assert "initdb failed" in str(exc_info.value)


class TestStop:
    """Test server shutdown."""

    @pytest.mark.asyncio
    async def test_stop_no_process(self):
        """Test stop when no process exists."""
        pg = EmbeddedPostgres()
        pg.process = None

        # Should not raise
        await pg.stop()
        assert pg.process is None

    @pytest.mark.asyncio
    async def test_stop_already_terminated(self):
        """Test stop when process already terminated."""
        pg = EmbeddedPostgres()
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Already exited
        pg.process = mock_process

        await pg.stop()
        assert pg.process is None

    @pytest.mark.asyncio
    async def test_stop_running_process(self):
        """Test graceful stop of running process."""
        pg = EmbeddedPostgres()
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        pg.process = mock_process
        pg._initialized = True

        with patch("asyncio.to_thread") as mock_thread:
            mock_thread.return_value = None

            await pg.stop()

            mock_process.terminate.assert_called_once()
            assert pg.process is None
            assert pg._initialized is False


class TestCleanup:
    """Test cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_data_dir(self):
        """Test cleanup removes data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "pgdata"
            data_dir.mkdir()
            (data_dir / "test_file").touch()

            pg = EmbeddedPostgres(data_dir=data_dir)
            pg.process = None

            await pg.cleanup()

            assert not data_dir.exists()


class TestSingletonFunctions:
    """Test global singleton functions."""

    @pytest.mark.asyncio
    async def test_get_embedded_postgres_creates_singleton(self):
        """Test singleton creation."""
        # Reset global state
        import hive.database.embedded_postgres as module

        module._embedded_pg = None

        with patch.object(EmbeddedPostgres, "initialize", new_callable=AsyncMock):
            pg = await get_embedded_postgres(port=5555)
            assert pg is not None
            assert pg.port == 5555

            # Second call should return same instance
            pg2 = await get_embedded_postgres(port=5556)  # Different port ignored
            assert pg2 is pg

        # Cleanup
        module._embedded_pg = None

    @pytest.mark.asyncio
    async def test_stop_embedded_postgres(self):
        """Test singleton stop."""
        import hive.database.embedded_postgres as module

        # Setup mock singleton
        mock_pg = MagicMock()
        mock_pg.stop = AsyncMock()
        module._embedded_pg = mock_pg

        await stop_embedded_postgres()

        mock_pg.stop.assert_called_once()
        assert module._embedded_pg is None

    @pytest.mark.asyncio
    async def test_cleanup_embedded_postgres(self):
        """Test singleton cleanup."""
        import hive.database.embedded_postgres as module

        # Setup mock singleton
        mock_pg = MagicMock()
        mock_pg.cleanup = AsyncMock()
        module._embedded_pg = mock_pg

        await cleanup_embedded_postgres()

        mock_pg.cleanup.assert_called_once()
        assert module._embedded_pg is None


class TestExceptions:
    """Test custom exceptions."""

    def test_embedded_postgres_error_hierarchy(self):
        """Test exception inheritance."""
        assert issubclass(BinaryDownloadError, EmbeddedPostgresError)
        assert issubclass(InitializationError, EmbeddedPostgresError)
        assert issubclass(StartupError, EmbeddedPostgresError)

    def test_exception_messages(self):
        """Test exception message preservation."""
        msg = "Test error message"

        exc = BinaryDownloadError(msg)
        assert str(exc) == msg

        exc = InitializationError(msg)
        assert str(exc) == msg

        exc = StartupError(msg)
        assert str(exc) == msg


# Integration tests - require actual PostgreSQL download
# These are slow and should be run separately


@pytest.mark.slow
@pytest.mark.integration
class TestEmbeddedPostgresIntegration:
    """
    Integration tests for EmbeddedPostgres.

    These tests download actual PostgreSQL binaries and test the full lifecycle.
    Run with: pytest -m slow tests/hive/database/test_embedded_postgres.py
    """

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test complete initialize -> use -> stop cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "pgdata"
            bin_cache = Path(tmpdir) / "bin_cache"

            pg = EmbeddedPostgres(
                data_dir=data_dir,
                port=15432,  # Non-standard port to avoid conflicts
                bin_cache_dir=bin_cache,
            )

            try:
                # Initialize (downloads binaries, creates cluster, starts server)
                await pg.initialize()

                assert pg.is_running()
                assert pg._initialized

                # Verify connection URL
                url = pg.get_connection_url()
                assert "15432" in url
                assert "hive" in url

                # Test idempotent initialize
                await pg.initialize()  # Should not raise

            finally:
                await pg.cleanup()

            assert not pg.is_running()
            assert not data_dir.exists()

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test actual database connection."""
        pytest.importorskip("asyncpg")
        import asyncpg

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "pgdata"
            bin_cache = Path(tmpdir) / "bin_cache"

            pg = EmbeddedPostgres(
                data_dir=data_dir,
                port=15433,
                bin_cache_dir=bin_cache,
            )

            try:
                await pg.initialize()

                # Connect with asyncpg
                conn = await asyncpg.connect(pg.get_asyncpg_url())

                try:
                    # Run a simple query
                    result = await conn.fetchval("SELECT 1")
                    assert result == 1

                    # Check database name
                    db_name = await conn.fetchval("SELECT current_database()")
                    assert db_name == "hive"

                finally:
                    await conn.close()

            finally:
                await pg.cleanup()
