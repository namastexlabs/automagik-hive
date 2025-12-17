"""
Embedded PostgreSQL for Serverless Hive.

Manages Postgres lifecycle within application process.
Zero changes to existing DatabaseService code.

Usage:
    # Automatic (recommended)
    pg = await get_embedded_postgres()
    db_url = pg.get_connection_url()

    # Manual lifecycle
    pg = EmbeddedPostgres(data_dir="/tmp/pgdata")
    await pg.initialize()
    db_url = pg.get_connection_url()
    # ... use database ...
    await pg.stop()
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import uuid
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)


class EmbeddedPostgresError(Exception):
    """Base exception for embedded postgres errors."""

    pass


class BinaryDownloadError(EmbeddedPostgresError):
    """Failed to download PostgreSQL binaries."""

    pass


class InitializationError(EmbeddedPostgresError):
    """Failed to initialize PostgreSQL cluster."""

    pass


class StartupError(EmbeddedPostgresError):
    """Failed to start PostgreSQL server."""

    pass


class EmbeddedPostgres:
    """
    Self-contained Postgres manager for serverless deployments.

    Features:
    - Downloads platform-specific Postgres binaries (cached)
    - Initializes isolated cluster (initdb)
    - Starts/stops postgres process
    - Installs pgvector extension
    - Provides connection URL for DatabaseService

    Attributes:
        data_dir: Path to PostgreSQL data directory
        port: Port number for PostgreSQL server
        postgres_version: PostgreSQL version to use
        process: Running PostgreSQL process (if started)
    """

    # PostgreSQL binary download URLs by platform
    # Using self-contained binaries from theseus-rs/postgresql-binaries (GitHub)
    # These binaries include all dependencies (no ICU issues on macOS)
    BINARY_BASE_URL = "https://github.com/theseus-rs/postgresql-binaries/releases/download/{version}/postgresql-{version}-{target}.tar.gz"

    # Target triples for each platform
    PLATFORM_TARGETS = {
        ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
        ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
        ("darwin", "x86_64"): "x86_64-apple-darwin",
        ("darwin", "arm64"): "aarch64-apple-darwin",
    }

    # Default PostgreSQL version (theseus-rs release version)
    DEFAULT_VERSION = "16.6.0"

    # Connection settings
    DEFAULT_USER = "postgres"
    DEFAULT_DATABASE = "hive"

    def __init__(
        self,
        data_dir: Path | None = None,
        port: int = 5432,
        postgres_version: str = DEFAULT_VERSION,
        bin_cache_dir: Path | None = None,
    ):
        """
        Initialize EmbeddedPostgres manager.

        Args:
            data_dir: Path for PostgreSQL data. If None, uses /tmp/pgdata-{uuid}
            port: Port for PostgreSQL server (default: 5432)
            postgres_version: PostgreSQL version to download (default: 16.3)
            bin_cache_dir: Directory to cache PostgreSQL binaries
        """
        # Unique data dir per instance (serverless isolation)
        if data_dir is None:
            instance_id = str(uuid.uuid4())[:8]
            data_dir = Path(tempfile.gettempdir()) / f"pgdata-{instance_id}"

        self.data_dir = Path(data_dir)
        self.port = port
        self.postgres_version = postgres_version
        self.process: subprocess.Popen | None = None
        self._initialized = False

        # Binary cache (shared across warm starts)
        if bin_cache_dir is None:
            bin_cache_dir = Path(tempfile.gettempdir()) / "postgres-binaries"
        self.bin_cache = Path(bin_cache_dir)

        # Detect platform
        self._system = platform.system().lower()
        self._machine = platform.machine().lower()

        # Normalize machine architecture
        if self._machine in ("amd64", "x86_64"):
            self._machine = "x86_64"
        elif self._machine in ("arm64", "aarch64"):
            self._machine = "arm64" if self._system == "darwin" else "aarch64"

        # Compute target triple for binary paths
        platform_key = (self._system, self._machine)
        self._target = self.PLATFORM_TARGETS.get(platform_key, "")

    @property
    def _pg_base_dir(self) -> Path:
        """Base directory for PostgreSQL binaries."""
        # theseus-rs structure: postgresql-{version}-{target}/bin/
        return self.bin_cache / f"postgresql-{self.postgres_version}-{self._target}"

    @property
    def postgres_bin(self) -> Path:
        """Path to postgres binary."""
        return self._pg_base_dir / "bin" / "postgres"

    @property
    def initdb_bin(self) -> Path:
        """Path to initdb binary."""
        return self._pg_base_dir / "bin" / "initdb"

    @property
    def psql_bin(self) -> Path:
        """Path to psql binary."""
        return self._pg_base_dir / "bin" / "psql"

    @property
    def pg_isready_bin(self) -> Path:
        """Path to pg_isready binary."""
        return self._pg_base_dir / "bin" / "pg_isready"

    async def initialize(self) -> None:
        """
        Initialize and start embedded Postgres.

        This method:
        1. Downloads PostgreSQL binaries (if not cached)
        2. Initializes the database cluster (if new)
        3. Starts the PostgreSQL server
        4. Creates the hive database
        5. Installs pgvector extension

        Raises:
            BinaryDownloadError: Failed to download binaries
            InitializationError: Failed to initialize cluster
            StartupError: Failed to start server
        """
        if self._initialized:
            logger.debug("EmbeddedPostgres already initialized")
            return

        logger.info(
            f"Initializing embedded Postgres {self.postgres_version}",
            extra={"port": self.port, "data_dir": str(self.data_dir)},
        )

        # 1. Ensure binaries are available
        await self._ensure_binaries()

        # 2. Initialize cluster if needed
        if not (self.data_dir / "PG_VERSION").exists():
            await self._init_cluster()

        # 3. Start server
        await self._start_server()

        # 4. Setup database and extensions
        await self._setup_database()

        self._initialized = True
        logger.info(
            f"Embedded Postgres ready on port {self.port}",
            extra={"connection_url": self.get_connection_url()},
        )

    async def _ensure_binaries(self) -> None:
        """Download and cache PostgreSQL binaries if needed."""
        if self.postgres_bin.exists():
            logger.debug(f"Postgres binaries cached at {self.bin_cache}")
            return

        logger.info("Downloading PostgreSQL binaries (first run only)...")

        # Get target triple for platform
        platform_key = (self._system, self._machine)
        if platform_key not in self.PLATFORM_TARGETS:
            raise BinaryDownloadError(
                f"Unsupported platform: {self._system}-{self._machine}. Supported: {list(self.PLATFORM_TARGETS.keys())}"
            )

        target = self.PLATFORM_TARGETS[platform_key]
        download_url = self.BINARY_BASE_URL.format(
            version=self.postgres_version,
            target=target,
        )

        # Create cache directory
        self.bin_cache.mkdir(parents=True, exist_ok=True)

        # Download archive (theseus-rs always uses .tar.gz)
        archive_path = self.bin_cache / f"postgres-{self.postgres_version}.tar.gz"

        try:
            logger.debug(f"Downloading from {download_url}")
            await asyncio.to_thread(urlretrieve, download_url, archive_path, self._download_progress)
        except Exception as e:
            raise BinaryDownloadError(f"Failed to download PostgreSQL: {e}") from e

        # Extract archive
        try:
            logger.debug(f"Extracting to {self.bin_cache}")
            await asyncio.to_thread(self._extract_archive, archive_path)
        except Exception as e:
            raise BinaryDownloadError(f"Failed to extract PostgreSQL: {e}") from e
        finally:
            # Cleanup archive
            if archive_path.exists():
                archive_path.unlink()

        # Make binaries executable
        bin_dir = self._pg_base_dir / "bin"
        if bin_dir.exists():
            for binary in bin_dir.glob("*"):
                if binary.is_file():
                    binary.chmod(0o755)

        logger.info(f"PostgreSQL binaries cached at {self._pg_base_dir}")

    def _download_progress(self, block_num: int, block_size: int, total_size: int) -> None:
        """Report download progress."""
        if total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, (downloaded * 100) // total_size)
            if block_num % 100 == 0:  # Log every 100 blocks
                logger.debug(f"Download progress: {percent}%")

    def _extract_archive(self, archive_path: Path) -> None:
        """Extract downloaded archive."""
        # S202: extractall is safe here - we download from trusted source (GitHub releases)
        if archive_path.suffix == ".zip" or str(archive_path).endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(self.bin_cache)  # noqa: S202
        else:
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(self.bin_cache)  # noqa: S202

    async def _init_cluster(self) -> None:
        """Initialize PostgreSQL cluster with initdb."""
        logger.info(f"Initializing cluster at {self.data_dir}")

        self.data_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.initdb_bin),
            "-D",
            str(self.data_dir),
            "-U",
            self.DEFAULT_USER,
            "--auth=trust",
            "--encoding=UTF8",
            "--locale=C",
            "--no-instructions",
        ]

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise InitializationError(f"initdb failed: {result.stderr}")

        # Configure postgresql.conf for embedded use
        await self._configure_postgres()

        logger.info("Cluster initialized successfully")

    async def _configure_postgres(self) -> None:
        """Configure PostgreSQL for embedded/serverless use."""
        conf_path = self.data_dir / "postgresql.conf"

        # Optimizations for embedded use
        config_additions = f"""
# Embedded Postgres Configuration
listen_addresses = 'localhost'
port = {self.port}

# Logging (minimal)
log_statement = 'none'
log_min_messages = warning
logging_collector = off

# Performance tuning for embedded
shared_buffers = 128MB
work_mem = 4MB
maintenance_work_mem = 64MB
effective_cache_size = 256MB

# Connection settings
max_connections = 20

# WAL settings (faster but less durable - OK for embedded)
fsync = off
synchronous_commit = off
full_page_writes = off

# Checkpoints
checkpoint_timeout = 30min
max_wal_size = 256MB
"""

        # Append to existing config
        with open(conf_path, "a") as f:
            f.write(config_additions)

        # Configure pg_hba.conf for trust authentication
        hba_path = self.data_dir / "pg_hba.conf"
        hba_content = """
# Trust local connections
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
"""
        with open(hba_path, "w") as f:
            f.write(hba_content)

    async def _start_server(self) -> None:
        """Start PostgreSQL server process."""
        if self.process and self.process.poll() is None:
            logger.debug("Postgres server already running")
            return

        logger.info(f"Starting Postgres server on port {self.port}")

        # Set library path for dynamic libraries
        env = os.environ.copy()
        lib_dir = self._pg_base_dir / "lib"
        if self._system == "darwin":
            env["DYLD_LIBRARY_PATH"] = str(lib_dir)
        else:
            env["LD_LIBRARY_PATH"] = str(lib_dir)

        cmd = [
            str(self.postgres_bin),
            "-D",
            str(self.data_dir),
            "-p",
            str(self.port),
            "-h",
            "localhost",
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        # Wait for server to be ready
        try:
            await self._wait_for_ready()
        except TimeoutError as e:
            # Capture stderr for debugging
            if self.process:
                self.process.terminate()
                _, stderr = self.process.communicate(timeout=5)
                raise StartupError(f"Postgres failed to start: {stderr.decode()}") from e
            raise

        logger.info(f"Postgres started (PID: {self.process.pid})")

    async def _wait_for_ready(self, timeout: int = 30) -> None:
        """Wait for PostgreSQL to accept connections."""
        env = os.environ.copy()
        lib_dir = self._pg_base_dir / "lib"
        if self._system == "darwin":
            env["DYLD_LIBRARY_PATH"] = str(lib_dir)
        else:
            env["LD_LIBRARY_PATH"] = str(lib_dir)

        cmd = [
            str(self.pg_isready_bin),
            "-h",
            "localhost",
            "-p",
            str(self.port),
            "-U",
            self.DEFAULT_USER,
        ]

        for _ in range(timeout * 2):  # Poll every 0.5s
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                env=env,
            )

            if result.returncode == 0:
                return

            # Check if process died
            if self.process and self.process.poll() is not None:
                raise StartupError("Postgres process terminated unexpectedly")

            await asyncio.sleep(0.5)

        raise TimeoutError(f"Postgres did not become ready within {timeout}s")

    async def _setup_database(self) -> None:
        """Create hive database and install extensions."""
        env = os.environ.copy()
        lib_dir = self._pg_base_dir / "lib"
        if self._system == "darwin":
            env["DYLD_LIBRARY_PATH"] = str(lib_dir)
        else:
            env["LD_LIBRARY_PATH"] = str(lib_dir)

        # Create hive database
        create_db_cmd = [
            str(self.psql_bin),
            "-h",
            "localhost",
            "-p",
            str(self.port),
            "-U",
            self.DEFAULT_USER,
            "-d",
            "postgres",
            "-c",
            f"CREATE DATABASE {self.DEFAULT_DATABASE}",
        ]

        result = await asyncio.to_thread(
            subprocess.run,
            create_db_cmd,
            capture_output=True,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            if "already exists" not in result.stderr:
                logger.warning(f"Database creation warning: {result.stderr}")
            else:
                logger.debug(f"Database '{self.DEFAULT_DATABASE}' already exists")
        else:
            logger.info(f"Database '{self.DEFAULT_DATABASE}' created")

        # Install pgvector extension
        await self._install_pgvector(env)

    async def _install_pgvector(self, env: dict) -> None:
        """Install pgvector extension if available."""
        # Check if pgvector is available in the PostgreSQL distribution
        share_dir = self._pg_base_dir / "share" / "extension"
        vector_control = share_dir / "vector.control"

        if not vector_control.exists():
            logger.warning(
                "pgvector extension not found in PostgreSQL distribution. "
                "Vector operations will not be available. "
                "Consider using external PostgreSQL with pgvector for production."
            )
            return

        create_ext_cmd = [
            str(self.psql_bin),
            "-h",
            "localhost",
            "-p",
            str(self.port),
            "-U",
            self.DEFAULT_USER,
            "-d",
            self.DEFAULT_DATABASE,
            "-c",
            "CREATE EXTENSION IF NOT EXISTS vector",
        ]

        result = await asyncio.to_thread(
            subprocess.run,
            create_ext_cmd,
            capture_output=True,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            logger.warning(f"pgvector installation warning: {result.stderr}")
        else:
            logger.info("pgvector extension installed")

    async def stop(self) -> None:
        """Stop PostgreSQL server gracefully."""
        if not self.process:
            return

        if self.process.poll() is not None:
            logger.debug("Postgres process already stopped")
            self.process = None
            return

        logger.info(f"Stopping Postgres (PID: {self.process.pid})")

        # Try graceful shutdown first
        self.process.terminate()

        try:
            await asyncio.to_thread(self.process.wait, timeout=10)
            logger.info("Postgres stopped gracefully")
        except subprocess.TimeoutExpired:
            logger.warning("Force killing Postgres")
            self.process.kill()
            await asyncio.to_thread(self.process.wait, timeout=5)

        self.process = None
        self._initialized = False

    async def cleanup(self) -> None:
        """Stop server and remove data directory."""
        await self.stop()

        if self.data_dir.exists():
            logger.info(f"Removing data directory: {self.data_dir}")
            shutil.rmtree(self.data_dir)

    def get_connection_url(self, dialect: str = "postgresql+psycopg") -> str:
        """
        Get database connection URL.

        Args:
            dialect: SQLAlchemy dialect (default: postgresql+psycopg for psycopg3)

        Returns:
            Connection URL string compatible with SQLAlchemy/psycopg3
        """
        return f"{dialect}://{self.DEFAULT_USER}@localhost:{self.port}/{self.DEFAULT_DATABASE}"

    def get_asyncpg_url(self) -> str:
        """Get connection URL for asyncpg."""
        return f"postgresql://{self.DEFAULT_USER}@localhost:{self.port}/{self.DEFAULT_DATABASE}"

    def is_running(self) -> bool:
        """Check if PostgreSQL server is running."""
        return self.process is not None and self.process.poll() is None

    async def has_pgvector(self) -> bool:
        """
        Check if pgvector extension is available and installed.

        Returns:
            True if pgvector is available and can be used
        """
        if not self.is_running():
            return False

        env = os.environ.copy()
        lib_dir = self._pg_base_dir / "lib"
        if self._system == "darwin":
            env["DYLD_LIBRARY_PATH"] = str(lib_dir)
        else:
            env["LD_LIBRARY_PATH"] = str(lib_dir)

        cmd = [
            str(self.psql_bin),
            "-h",
            "localhost",
            "-p",
            str(self.port),
            "-U",
            self.DEFAULT_USER,
            "-d",
            self.DEFAULT_DATABASE,
            "-t",
            "-c",
            "SELECT 1 FROM pg_extension WHERE extname = 'vector'",
        ]

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            env=env,
        )

        return result.returncode == 0 and "1" in result.stdout

    async def get_database_info(self) -> dict:
        """
        Get information about the embedded database.

        Returns:
            Dictionary with database information
        """
        info = {
            "running": self.is_running(),
            "port": self.port,
            "data_dir": str(self.data_dir),
            "version": self.postgres_version,
            "connection_url": self.get_connection_url() if self.is_running() else None,
            "pgvector_available": await self.has_pgvector() if self.is_running() else False,
        }
        return info

    def __repr__(self) -> str:
        status = "running" if self.is_running() else "stopped"
        return f"EmbeddedPostgres(port={self.port}, status={status})"


# Global singleton for serverless warm starts
_embedded_pg: EmbeddedPostgres | None = None
_embedded_pg_lock = asyncio.Lock()


async def get_embedded_postgres(**kwargs) -> EmbeddedPostgres:
    """
    Get or create global embedded Postgres instance.

    This function implements a singleton pattern suitable for serverless
    environments where warm starts should reuse the existing Postgres instance.

    Args:
        **kwargs: Arguments passed to EmbeddedPostgres constructor (only used on first call)

    Returns:
        Initialized EmbeddedPostgres instance
    """
    global _embedded_pg

    async with _embedded_pg_lock:
        if _embedded_pg is None:
            _embedded_pg = EmbeddedPostgres(**kwargs)
            await _embedded_pg.initialize()
        elif not _embedded_pg.is_running():
            # Restart if stopped
            await _embedded_pg.initialize()

    return _embedded_pg


async def stop_embedded_postgres() -> None:
    """Stop global embedded Postgres instance."""
    global _embedded_pg

    async with _embedded_pg_lock:
        if _embedded_pg:
            await _embedded_pg.stop()
            _embedded_pg = None


async def cleanup_embedded_postgres() -> None:
    """Stop and cleanup global embedded Postgres instance (removes data)."""
    global _embedded_pg

    async with _embedded_pg_lock:
        if _embedded_pg:
            await _embedded_pg.cleanup()
            _embedded_pg = None
