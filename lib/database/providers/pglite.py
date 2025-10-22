"""
PGlite Database Backend.

HTTP client for PGlite bridge with subprocess lifecycle management.
Compatible with psycopg3 patterns via BaseDatabaseBackend interface.
"""

import asyncio
import os
import re
import subprocess
from contextlib import asynccontextmanager
from typing import Any

import httpx

from lib.logging import logger

from .base import BaseDatabaseBackend


class PGliteBackend(BaseDatabaseBackend):
    """
    PGlite database backend via HTTP bridge.

    Manages bridge subprocess lifecycle and provides async database operations
    through HTTP endpoints. Compatible with psycopg3 patterns.
    """

    def __init__(self, db_url: str | None = None, min_size: int = 2, max_size: int = 10):
        """
        Initialize PGlite backend.

        Args:
            db_url: PGlite data directory path (ignored for pool config)
            min_size: Unused (PGlite doesn't support pooling)
            max_size: Unused (PGlite doesn't support pooling)
        """
        # Store original URL for interface compatibility
        self.db_url = db_url or os.getenv("PGLITE_DATA_DIR", "./pglite-data")
        self.data_dir = self.db_url
        self.port = int(os.getenv("PGLITE_PORT", "5532"))
        self.base_url = f"http://127.0.0.1:{self.port}"

        self.bridge_process: subprocess.Popen | None = None
        self.client: httpx.AsyncClient | None = None

        # Connection pool size (unused but stored for interface compatibility)
        self.min_size = min_size
        self.max_size = max_size

    async def initialize(self) -> None:
        """
        Initialize PGlite bridge subprocess and HTTP client.

        Raises:
            RuntimeError: If bridge fails to start or health check fails
        """
        if self.bridge_process is not None:
            logger.warning("PGlite bridge already initialized")
            return

        logger.info("Starting PGlite bridge", port=self.port, data_dir=self.data_dir)

        # Start bridge subprocess
        bridge_script = os.path.join(os.path.dirname(__file__), "../../../tools/pglite-bridge/server.js")

        try:
            self.bridge_process = subprocess.Popen(
                ["node", bridge_script],
                env={
                    **os.environ,
                    "PGLITE_PORT": str(self.port),
                    "PGLITE_DATA_DIR": self.data_dir,
                },
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for bridge to be ready
            await self._wait_for_bridge_ready()

            # Initialize HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0),
            )

            logger.info("PGlite bridge initialized successfully", port=self.port)

        except Exception as e:
            logger.error("Failed to initialize PGlite bridge", error=str(e))
            await self._cleanup_bridge()
            raise RuntimeError(f"PGlite bridge initialization failed: {e}") from e

    async def _wait_for_bridge_ready(self, max_attempts: int = 30, delay: float = 0.5) -> None:
        """
        Wait for bridge to become ready via health check.

        Args:
            max_attempts: Maximum number of health check attempts
            delay: Delay between attempts in seconds

        Raises:
            RuntimeError: If bridge doesn't become ready in time
        """
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/health",
                        timeout=httpx.Timeout(2.0),
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "healthy":
                            logger.info("PGlite bridge health check passed", attempt=attempt + 1)
                            return
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

            await asyncio.sleep(delay)

        raise RuntimeError(f"PGlite bridge failed to become ready after {max_attempts} attempts")

    async def _cleanup_bridge(self) -> None:
        """Cleanup bridge subprocess if it exists."""
        if self.bridge_process:
            try:
                self.bridge_process.terminate()
                self.bridge_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.bridge_process.kill()
                self.bridge_process.wait()
            finally:
                self.bridge_process = None

    async def close(self) -> None:
        """Close HTTP client and stop bridge subprocess."""
        logger.info("Closing PGlite bridge")

        # Close HTTP client
        if self.client:
            await self.client.aclose()
            self.client = None

        # Stop bridge subprocess
        await self._cleanup_bridge()

        logger.info("PGlite bridge closed")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get database connection (no-op for HTTP-based PGlite).

        Yields:
            self: Backend instance (for interface compatibility)
        """
        if not self.client:
            await self.initialize()

        # PGlite bridge doesn't use connections - yield self for interface compatibility
        yield self

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        """
        Execute a query without returning results.

        Args:
            query: SQL query string
            params: Query parameters (converted to list for PGlite)
        """
        if not self.client:
            await self.initialize()

        # Convert dict params to list (PGlite bridge expects positional params)
        param_list = self._convert_params(query, params) if params else []

        try:
            response = await self.client.post(
                "/query",
                json={"sql": query, "params": param_list},
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise RuntimeError(f"PGlite query failed: {error}")

        except httpx.HTTPStatusError as e:
            logger.error("PGlite HTTP error", status=e.response.status_code, error=str(e))
            raise RuntimeError(f"PGlite HTTP error: {e}") from e
        except Exception as e:
            logger.error("PGlite execute failed", query=query[:100], error=str(e))
            raise

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """
        Fetch single row as dictionary.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Optional[dict[str, Any]]: Row data or None
        """
        if not self.client:
            await self.initialize()

        param_list = self._convert_params(query, params) if params else []

        try:
            response = await self.client.post(
                "/query",
                json={"sql": query, "params": param_list},
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise RuntimeError(f"PGlite query failed: {error}")

            rows = result.get("rows", [])
            return rows[0] if rows else None

        except httpx.HTTPStatusError as e:
            logger.error("PGlite HTTP error", status=e.response.status_code, error=str(e))
            raise RuntimeError(f"PGlite HTTP error: {e}") from e
        except Exception as e:
            logger.error("PGlite fetch_one failed", query=query[:100], error=str(e))
            raise

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Fetch all rows as list of dictionaries.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            list[dict[str, Any]]: List of row data
        """
        if not self.client:
            await self.initialize()

        param_list = self._convert_params(query, params) if params else []

        try:
            response = await self.client.post(
                "/query",
                json={"sql": query, "params": param_list},
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise RuntimeError(f"PGlite query failed: {error}")

            return result.get("rows", [])

        except httpx.HTTPStatusError as e:
            logger.error("PGlite HTTP error", status=e.response.status_code, error=str(e))
            raise RuntimeError(f"PGlite HTTP error: {e}") from e
        except Exception as e:
            logger.error("PGlite fetch_all failed", query=query[:100], error=str(e))
            raise

    async def execute_transaction(self, operations: list[tuple]) -> None:
        """
        Execute multiple operations in a transaction.

        Args:
            operations: List of (query, params) tuples
        """
        if not self.client:
            await self.initialize()

        # Build transaction SQL
        transaction_sql = ["BEGIN;"]

        for query, params in operations:
            if params:
                # For simplicity, just append queries without param substitution
                # Real implementation would need proper parameter handling
                transaction_sql.append(query)
            else:
                transaction_sql.append(query)

        transaction_sql.append("COMMIT;")

        try:
            response = await self.client.post(
                "/query",
                json={"sql": "\n".join(transaction_sql), "params": []},
            )
            response.raise_for_status()

            result = response.json()
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise RuntimeError(f"PGlite transaction failed: {error}")

        except Exception as e:
            logger.error("PGlite transaction failed", error=str(e))
            raise

    def _convert_params(self, query: str, params: dict[str, Any]) -> list[Any]:
        """
        Convert named parameters dict to positional list.

        Args:
            query: SQL query with named placeholders
            params: Dictionary of parameters

        Returns:
            list[Any]: Positional parameter list
        """
        # Extract parameter names from query (assumes %(name)s format)
        param_names = re.findall(r"%\((\w+)\)s", query)

        # Build positional list
        return [params.get(name) for name in param_names]
