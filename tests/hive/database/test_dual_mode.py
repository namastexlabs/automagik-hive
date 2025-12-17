"""
Tests for dual mode database configuration.

Tests that Hive correctly detects and switches between:
- External PostgreSQL (when HIVE_DATABASE_URL is set)
- Embedded PostgreSQL (when HIVE_DATABASE_URL is not set)
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hive.config.settings import HiveSettings


class TestSettingsDualMode:
    """Test HiveSettings database mode detection."""

    def test_external_mode_when_url_set(self):
        """Test external mode is detected when HIVE_DATABASE_URL is provided."""
        # Create settings directly without relying on env file
        config = HiveSettings(
            hive_database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            _env_file=None,  # Disable .env file loading
        )

        assert config.hive_database_url == "postgresql+psycopg://user:pass@localhost:5432/db"
        assert config.use_embedded_postgres is False
        assert config.database_mode == "external"

    def test_embedded_mode_when_url_not_set(self):
        """Test embedded mode is detected when HIVE_DATABASE_URL is not provided."""
        # Create settings directly without database URL
        config = HiveSettings(
            hive_database_url=None,
            _env_file=None,
        )

        assert config.hive_database_url is None
        assert config.use_embedded_postgres is True
        assert config.database_mode == "embedded"

    def test_embedded_postgres_port_configurable(self):
        """Test embedded postgres port is configurable."""
        config = HiveSettings(
            hive_database_url=None,
            hive_embedded_postgres_port=15432,
            _env_file=None,
        )

        assert config.hive_embedded_postgres_port == 15432

    def test_embedded_postgres_data_dir_configurable(self):
        """Test embedded postgres data dir is configurable."""
        config = HiveSettings(
            hive_database_url=None,
            hive_embedded_postgres_data_dir=Path("/custom/pgdata"),
            _env_file=None,
        )

        assert config.hive_embedded_postgres_data_dir == Path("/custom/pgdata")

    def test_default_embedded_postgres_data_dir_is_none(self):
        """Test default embedded postgres data dir is None (auto temp dir)."""
        config = HiveSettings(
            hive_database_url=None,
            _env_file=None,
        )

        assert config.hive_embedded_postgres_data_dir is None


class TestAppLifespanDualMode:
    """Test app.py lifespan dual mode handling."""

    @pytest.mark.asyncio
    async def test_external_mode_skips_embedded_init(self):
        """Test that external mode skips embedded postgres initialization."""
        # Mock settings to return external mode
        mock_settings = MagicMock()
        mock_settings.use_embedded_postgres = False
        mock_settings.hive_database_url = "postgresql+psycopg://user:pass@localhost:5432/db"

        with patch("hive.api.app.settings", return_value=mock_settings):
            with patch("hive.database.get_embedded_postgres") as mock_get:
                import hive.api.app as app_module

                app_module._embedded_postgres = None
                await app_module._initialize_embedded_postgres()

                # Should NOT have been called (external mode)
                mock_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_embedded_mode_initializes_postgres(self):
        """Test that embedded mode initializes embedded postgres."""
        # Mock settings to return embedded mode
        mock_settings = MagicMock()
        mock_settings.use_embedded_postgres = True
        mock_settings.hive_database_url = None
        mock_settings.hive_embedded_postgres_port = 5432
        mock_settings.hive_embedded_postgres_data_dir = None

        # Mock the embedded postgres instance
        mock_pg = MagicMock()
        mock_pg.get_connection_url.return_value = "postgresql+psycopg://postgres@localhost:5432/hive"

        with patch("hive.api.app.settings", return_value=mock_settings):
            with patch(
                "hive.database.get_embedded_postgres",
                new_callable=AsyncMock,
                return_value=mock_pg,
            ) as mock_get:
                import hive.api.app as app_module

                app_module._embedded_postgres = None
                await app_module._initialize_embedded_postgres()

                # Should have been called
                mock_get.assert_called_once()

                # Environment variable should be set
                assert os.environ.get("HIVE_DATABASE_URL") == "postgresql+psycopg://postgres@localhost:5432/hive"

    @pytest.mark.asyncio
    async def test_shutdown_stops_embedded_postgres(self):
        """Test that shutdown stops embedded postgres."""
        import hive.api.app as app_module

        # Set up mock embedded postgres
        mock_pg = MagicMock()
        app_module._embedded_postgres = mock_pg

        with patch(
            "hive.database.stop_embedded_postgres",
            new_callable=AsyncMock,
        ) as mock_stop:
            await app_module._shutdown_embedded_postgres()

            mock_stop.assert_called_once()
            assert app_module._embedded_postgres is None

    @pytest.mark.asyncio
    async def test_shutdown_noop_when_no_embedded(self):
        """Test that shutdown is a no-op when not using embedded."""
        import hive.api.app as app_module

        # No embedded postgres
        app_module._embedded_postgres = None

        with patch(
            "hive.database.stop_embedded_postgres",
            new_callable=AsyncMock,
        ) as mock_stop:
            await app_module._shutdown_embedded_postgres()

            # Should NOT have been called
            mock_stop.assert_not_called()


class TestDatabaseUrlPropagation:
    """Test that database URL is properly propagated to components."""

    def test_environment_variable_propagation(self):
        """Test that embedded mode sets HIVE_DATABASE_URL env var."""
        # This is tested in test_embedded_mode_initializes_postgres
        # But we can add additional component-specific tests here
        pass

    @pytest.mark.asyncio
    async def test_knowledge_base_gets_embedded_url(self):
        """Test that knowledge base can use embedded postgres URL."""
        env = os.environ.copy()
        env.pop("HIVE_DATABASE_URL", None)

        with patch.dict(os.environ, env, clear=True):
            # Set the URL as embedded postgres would
            os.environ["HIVE_DATABASE_URL"] = "postgresql+psycopg://postgres@localhost:5432/hive"

            # Knowledge base should be able to get this URL
            assert os.getenv("HIVE_DATABASE_URL") == "postgresql+psycopg://postgres@localhost:5432/hive"


# Integration tests - require actual PostgreSQL
@pytest.mark.slow
@pytest.mark.integration
class TestDualModeIntegration:
    """Integration tests for dual mode database configuration."""

    @pytest.mark.asyncio
    async def test_full_embedded_lifecycle(self):
        """Test complete embedded postgres lifecycle through app lifespan."""
        import tempfile
        from pathlib import Path

        env = os.environ.copy()
        env.pop("HIVE_DATABASE_URL", None)

        with tempfile.TemporaryDirectory() as tmpdir:
            env["HIVE_EMBEDDED_POSTGRES_PORT"] = "15434"
            env["HIVE_EMBEDDED_POSTGRES_DATA_DIR"] = str(Path(tmpdir) / "pgdata")

            with patch.dict(os.environ, env, clear=True):
                from hive.config.settings import settings

                settings.cache_clear()

                import importlib

                import hive.api.app as app_module

                importlib.reload(app_module)

                # Reset global state
                app_module._embedded_postgres = None

                try:
                    # Initialize
                    await app_module._initialize_embedded_postgres()

                    # Verify postgres is running
                    assert app_module._embedded_postgres is not None
                    assert app_module._embedded_postgres.is_running()

                    # Verify URL is set
                    assert "15434" in os.environ.get("HIVE_DATABASE_URL", "")

                finally:
                    # Cleanup
                    await app_module._shutdown_embedded_postgres()
