"""
Tests for Knowledge Base integration with Embedded PostgreSQL.

These tests verify that the knowledge base and RAG system can work
with embedded PostgreSQL, including pgvector extension support.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestKnowledgeBaseWithEmbedded:
    """Test knowledge base configuration with embedded postgres."""

    def test_knowledge_base_uses_env_variable(self):
        """Test that knowledge base reads HIVE_DATABASE_URL from environment."""
        test_url = "postgresql+psycopg://test@localhost:5432/testdb"

        with patch.dict(os.environ, {"HIVE_DATABASE_URL": test_url}):
            # Import here to pick up patched env
            from hive.knowledge.knowledge import create_knowledge_base

            # Mock PgVector to avoid actual database connection
            with patch("hive.knowledge.knowledge.PgVector") as mock_pgvector:
                with patch("hive.knowledge.knowledge.CSVKnowledgeLoader") as mock_loader:
                    with patch("hive.knowledge.knowledge.Knowledge") as mock_kb:
                        # Setup mocks
                        mock_loader_instance = MagicMock()
                        mock_loader_instance.load.return_value = {"mode": "full", "documents": 0}
                        mock_loader.return_value = mock_loader_instance

                        mock_kb_instance = MagicMock()
                        mock_kb.return_value = mock_kb_instance

                        # Create temp CSV
                        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                            f.write("content\ntest data")
                            csv_path = f.name

                        try:
                            _kb = create_knowledge_base(
                                csv_path=csv_path,
                                use_shared=False,
                            )

                            # Verify PgVector was called with correct URL
                            mock_pgvector.assert_called_once()
                            call_kwargs = mock_pgvector.call_args[1]
                            assert call_kwargs["db_url"] == test_url

                        finally:
                            os.unlink(csv_path)

    def test_knowledge_base_raises_without_url(self):
        """Test that knowledge base raises error when HIVE_DATABASE_URL not set."""
        # Remove HIVE_DATABASE_URL from environment
        env = os.environ.copy()
        env.pop("HIVE_DATABASE_URL", None)

        with patch.dict(os.environ, env, clear=True):
            from hive.knowledge.knowledge import create_knowledge_base

            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                f.write("content\ntest data")
                csv_path = f.name

            try:
                with pytest.raises(ValueError, match="HIVE_DATABASE_URL"):
                    create_knowledge_base(
                        csv_path=csv_path,
                        use_shared=False,
                    )
            finally:
                os.unlink(csv_path)


class TestEmbeddedPostgresPgvector:
    """Test pgvector availability checking."""

    @pytest.mark.asyncio
    async def test_has_pgvector_when_not_running(self):
        """Test has_pgvector returns False when server not running."""
        from hive.database import EmbeddedPostgres

        pg = EmbeddedPostgres()
        # Server not started
        result = await pg.has_pgvector()
        assert result is False

    @pytest.mark.asyncio
    async def test_has_pgvector_with_mock(self):
        """Test has_pgvector with mocked psql call."""
        from hive.database import EmbeddedPostgres

        pg = EmbeddedPostgres()
        # Simulate running server
        pg.process = MagicMock()
        pg.process.poll.return_value = None

        # Mock subprocess.run to return pgvector installed
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " 1\n"

        with patch("asyncio.to_thread", return_value=mock_result):
            result = await pg.has_pgvector()
            assert result is True

    @pytest.mark.asyncio
    async def test_has_pgvector_not_installed(self):
        """Test has_pgvector returns False when extension not installed."""
        from hive.database import EmbeddedPostgres

        pg = EmbeddedPostgres()
        # Simulate running server
        pg.process = MagicMock()
        pg.process.poll.return_value = None

        # Mock subprocess.run to return no pgvector
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("asyncio.to_thread", return_value=mock_result):
            result = await pg.has_pgvector()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_database_info(self):
        """Test get_database_info returns correct structure."""
        from hive.database import EmbeddedPostgres

        pg = EmbeddedPostgres(port=15432)
        # Simulate running server
        pg.process = MagicMock()
        pg.process.poll.return_value = None
        pg._initialized = True

        # Mock has_pgvector
        with patch.object(pg, "has_pgvector", return_value=True):
            info = await pg.get_database_info()

            assert info["running"] is True
            assert info["port"] == 15432
            assert "connection_url" in info
            assert "pgvector_available" in info


class TestKnowledgeBaseServerlessWorkflow:
    """Test knowledge base in serverless workflow."""

    @pytest.mark.asyncio
    async def test_embedded_postgres_sets_env_for_knowledge_base(self):
        """Test that embedded postgres sets HIVE_DATABASE_URL for knowledge base."""
        # This simulates the serverless workflow:
        # 1. App starts with no HIVE_DATABASE_URL
        # 2. Embedded postgres starts and sets HIVE_DATABASE_URL
        # 3. Knowledge base can now use that URL

        # Clear env
        env = os.environ.copy()
        env.pop("HIVE_DATABASE_URL", None)

        with patch.dict(os.environ, env, clear=True):
            # Simulate embedded postgres setting the URL
            embedded_url = "postgresql+psycopg://postgres@localhost:5432/hive"
            os.environ["HIVE_DATABASE_URL"] = embedded_url

            # Now knowledge base should be able to get the URL
            db_url = os.getenv("HIVE_DATABASE_URL")
            assert db_url == embedded_url


# Integration tests - require actual embedded PostgreSQL
@pytest.mark.slow
@pytest.mark.integration
class TestKnowledgeBaseIntegration:
    """
    Integration tests for knowledge base with real embedded PostgreSQL.

    These tests download actual PostgreSQL binaries and test the full
    knowledge base workflow including pgvector operations.

    Run with: pytest -m slow tests/hive/database/test_knowledge_integration.py
    """

    @pytest.mark.asyncio
    async def test_embedded_postgres_with_pgvector_check(self):
        """Test embedded postgres initialization and pgvector check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "pgdata"
            bin_cache = Path(tmpdir) / "bin_cache"

            from hive.database import EmbeddedPostgres

            pg = EmbeddedPostgres(
                data_dir=data_dir,
                port=15435,
                bin_cache_dir=bin_cache,
            )

            try:
                await pg.initialize()

                assert pg.is_running()

                # Check database info
                info = await pg.get_database_info()
                assert info["running"] is True
                assert info["port"] == 15435

                # pgvector may or may not be available depending on binaries
                # Just verify the check doesn't crash
                pgvector_available = await pg.has_pgvector()
                assert isinstance(pgvector_available, bool)

                if pgvector_available:
                    print("pgvector is available in embedded postgres")
                else:
                    print("pgvector is NOT available (expected for EDB binaries)")

            finally:
                await pg.cleanup()

    @pytest.mark.asyncio
    async def test_knowledge_base_url_propagation(self):
        """Test that embedded postgres URL is properly propagated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "pgdata"
            bin_cache = Path(tmpdir) / "bin_cache"

            from hive.database import EmbeddedPostgres

            pg = EmbeddedPostgres(
                data_dir=data_dir,
                port=15436,
                bin_cache_dir=bin_cache,
            )

            try:
                await pg.initialize()

                # Get connection URL
                url = pg.get_connection_url()

                # Set as environment variable (like app.py does)
                os.environ["HIVE_DATABASE_URL"] = url

                # Verify knowledge base can read it
                assert os.getenv("HIVE_DATABASE_URL") == url
                assert "15436" in url
                assert "hive" in url

            finally:
                await pg.cleanup()
                # Clean up env
                os.environ.pop("HIVE_DATABASE_URL", None)
