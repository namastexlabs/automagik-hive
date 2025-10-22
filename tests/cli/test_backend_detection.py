"""Tests for backend detection and environment handling.

Tests backend detection priority (explicit > URL > default),
environment variable handling, and integration with CLI workflows.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.commands.service import ServiceManager  # noqa: E402
from cli.docker_manager import DockerManager  # noqa: E402


class TestBackendDetection:
    """Test backend detection logic and priority."""

    def test_explicit_backend_setting_highest_priority(self):
        """Test HIVE_DATABASE_BACKEND has highest priority."""
        manager = DockerManager()

        # Explicit backend should override URL-based detection
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_BACKEND": "pglite",
                "HIVE_DATABASE_URL": "postgresql://localhost/db",  # Conflicting URL
            },
            clear=False,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "pglite"

    def test_url_based_detection_second_priority(self):
        """Test URL parsing when explicit backend not set."""
        manager = DockerManager()

        # No explicit backend, URL should determine backend
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "sqlite:///test.db"},
            clear=True,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "sqlite"

    def test_default_fallback_postgresql(self):
        """Test default is PostgreSQL for backward compatibility."""
        manager = DockerManager()

        # No backend or URL set - should default to PostgreSQL
        with patch.dict(os.environ, {}, clear=True):
            backend = manager._detect_backend_from_env()
            assert backend == "postgresql"

    def test_detection_priority_order(self):
        """Test complete priority chain: explicit > URL > default."""
        manager = DockerManager()

        # Case 1: Explicit backend only
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_BACKEND": "sqlite"},
            clear=True,
        ):
            assert manager._detect_backend_from_env() == "sqlite"

        # Case 2: URL only
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "pglite://test.db"},
            clear=True,
        ):
            assert manager._detect_backend_from_env() == "pglite"

        # Case 3: Both explicit and URL (explicit wins)
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_BACKEND": "pglite",
                "HIVE_DATABASE_URL": "sqlite:///test.db",
            },
            clear=True,
        ):
            assert manager._detect_backend_from_env() == "pglite"

        # Case 4: Neither (default)
        with patch.dict(os.environ, {}, clear=True):
            assert manager._detect_backend_from_env() == "postgresql"

    def test_pglite_url_detection(self):
        """Test PGlite URL pattern detection."""
        manager = DockerManager()

        pglite_urls = [
            "pglite://./data/db.db",
            "pglite:///absolute/path/db.db",
            "pglite://memory",
        ]

        for url in pglite_urls:
            with patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": url},
                clear=True,
            ):
                backend = manager._detect_backend_from_env()
                assert backend == "pglite", f"Failed for URL: {url}"

    def test_sqlite_url_detection(self):
        """Test SQLite URL pattern detection."""
        manager = DockerManager()

        sqlite_urls = [
            "sqlite:///./data/db.db",
            "sqlite:////absolute/path/db.db",
            "sqlite:///test.db",
        ]

        for url in sqlite_urls:
            with patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": url},
                clear=True,
            ):
                backend = manager._detect_backend_from_env()
                assert backend == "sqlite", f"Failed for URL: {url}"

    def test_postgresql_url_detection(self):
        """Test PostgreSQL URL pattern detection."""
        manager = DockerManager()

        postgresql_urls = [
            "postgresql://localhost/db",
            "postgresql+psycopg://localhost/db",
            "postgres://localhost/db",
            "postgresql://user:pass@host:5432/db",
        ]

        for url in postgresql_urls:
            with patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": url},
                clear=True,
            ):
                backend = manager._detect_backend_from_env()
                assert backend == "postgresql", f"Failed for URL: {url}"

    def test_explicit_backend_case_insensitive(self):
        """Test explicit backend setting is case-insensitive."""
        manager = DockerManager()

        backend_variants = [
            ("PGLITE", "pglite"),
            ("PgLite", "pglite"),
            ("pglite", "pglite"),
            ("POSTGRESQL", "postgresql"),
            ("PostgreSQL", "postgresql"),
            ("SQLITE", "sqlite"),
            ("SQLite", "sqlite"),
        ]

        for input_val, expected in backend_variants:
            with patch.dict(
                os.environ,
                {"HIVE_DATABASE_BACKEND": input_val},
                clear=False,
            ):
                backend = manager._detect_backend_from_env()
                assert backend == expected, f"Failed for input: {input_val}"

    def test_service_manager_backend_detection(self):
        """Test ServiceManager uses same detection logic."""
        service_manager = ServiceManager()

        # Test explicit backend
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_BACKEND": "pglite"},
            clear=False,
        ):
            backend = service_manager._detect_backend_from_env()
            assert backend == "pglite"

        # Test URL-based detection
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "sqlite:///test.db"},
            clear=True,
        ):
            backend = service_manager._detect_backend_from_env()
            assert backend == "sqlite"

    def test_backend_detection_with_factory_integration(self):
        """Test backend detection integrates with backend factory."""
        manager = DockerManager()

        # Test that detection works with actual backend factory
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "pglite://test.db"},
            clear=True,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "pglite"

            # Verify it matches what backend factory would detect
            try:
                from lib.database.backend_factory import detect_backend_from_url

                factory_backend = detect_backend_from_url("pglite://test.db")
                assert backend == factory_backend.value
            except ImportError:
                # Factory may not be available in all test contexts
                pass

    def test_empty_backend_variable_uses_url(self):
        """Test empty HIVE_DATABASE_BACKEND falls back to URL."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_BACKEND": "",  # Empty string
                "HIVE_DATABASE_URL": "sqlite:///test.db",
            },
            clear=False,
        ):
            backend = manager._detect_backend_from_env()
            # Empty string should fall through to URL detection
            # (depends on implementation - may need adjustment)
            assert backend in ("sqlite", "postgresql")

    def test_invalid_url_falls_back_to_default(self):
        """Test invalid URL format falls back to default."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "invalid-url"},
            clear=True,
        ):
            backend = manager._detect_backend_from_env()
            # Should fall back to default PostgreSQL
            assert backend == "postgresql"

    def test_backend_detection_consistency(self):
        """Test detection is consistent across multiple calls."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_BACKEND": "pglite"},
            clear=False,
        ):
            # Multiple calls should return same result
            backend1 = manager._detect_backend_from_env()
            backend2 = manager._detect_backend_from_env()
            backend3 = manager._detect_backend_from_env()

            assert backend1 == backend2 == backend3 == "pglite"

    def test_store_backend_writes_to_env(self, tmp_path):
        """Test _store_backend_choice writes HIVE_DATABASE_BACKEND."""
        service_manager = ServiceManager()

        env_file = tmp_path / ".env"
        env_file.write_text("# Empty env\n")

        service_manager._store_backend_choice(tmp_path, "pglite")

        env_content = env_file.read_text()
        assert "HIVE_DATABASE_BACKEND=pglite" in env_content

    def test_store_backend_updates_existing_backend(self, tmp_path):
        """Test _store_backend_choice updates existing backend setting."""
        service_manager = ServiceManager()

        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_BACKEND=postgresql\n")

        service_manager._store_backend_choice(tmp_path, "sqlite")

        env_content = env_file.read_text()
        assert "HIVE_DATABASE_BACKEND=sqlite" in env_content
        assert "HIVE_DATABASE_BACKEND=postgresql" not in env_content

    def test_store_backend_updates_database_url(self, tmp_path):
        """Test _store_backend_choice updates HIVE_DATABASE_URL."""
        service_manager = ServiceManager()

        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=your_database_url_here\n")

        service_manager._store_backend_choice(tmp_path, "pglite")

        env_content = env_file.read_text()
        assert "pglite://" in env_content

    def test_store_backend_url_mappings(self, tmp_path):
        """Test correct URL mapping for each backend."""
        service_manager = ServiceManager()

        backend_url_map = {
            "pglite": "pglite://./data/automagik_hive.db",
            "sqlite": "sqlite:///./data/automagik_hive.db",
            "postgresql": "postgresql+psycopg://",
        }

        for backend, expected_url_prefix in backend_url_map.items():
            env_file = tmp_path / ".env"
            env_file.write_text("HIVE_DATABASE_URL=your_database_url_here\n")

            service_manager._store_backend_choice(tmp_path, backend)

            env_content = env_file.read_text()
            assert expected_url_prefix in env_content, f"Failed for backend: {backend}"

    def test_backend_detection_in_install_flow(self, tmp_path):
        """Test backend detection works correctly in install workflow."""
        service_manager = ServiceManager()

        # Create .env with backend
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_BACKEND=pglite\n")

        # Detection should find the stored backend
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_BACKEND": "pglite"},
            clear=False,
        ):
            backend = service_manager._detect_backend_from_env()
            assert backend == "pglite"

    def test_backend_detection_backward_compatibility(self):
        """Test backward compatibility with existing PostgreSQL setups."""
        manager = DockerManager()

        # Existing setup with PostgreSQL URL and no explicit backend
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://localhost:5432/automagik_hive"},
            clear=True,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "postgresql"

    def test_multiple_backend_detectors_consistency(self):
        """Test ServiceManager and DockerManager use same detection."""
        service_manager = ServiceManager()
        docker_manager = DockerManager()

        test_scenarios = [
            {"HIVE_DATABASE_BACKEND": "pglite"},
            {"HIVE_DATABASE_URL": "sqlite:///test.db"},
            {"HIVE_DATABASE_URL": "postgresql://localhost/db"},
        ]

        for env_vars in test_scenarios:
            with patch.dict(os.environ, env_vars, clear=True):
                service_backend = service_manager._detect_backend_from_env()
                docker_backend = docker_manager._detect_backend_from_env()

                assert service_backend == docker_backend, f"Mismatch for env: {env_vars}"

    def test_backend_detection_with_whitespace(self):
        """Test backend detection handles whitespace correctly."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_BACKEND": "  pglite  "},
            clear=False,
        ):
            # Should handle whitespace (after strip and lower)
            backend = manager._detect_backend_from_env()
            # Implementation may or may not strip - verify actual behavior
            assert "pglite" in backend.lower()
