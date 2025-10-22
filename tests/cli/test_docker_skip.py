"""Tests for Docker validation bypass based on backend selection.

Tests that PGlite and SQLite backends skip Docker checks while
PostgreSQL backend requires Docker validation. Includes tests
for error messages and fallback behavior.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.docker_manager import DockerManager  # noqa: E402


class TestDockerSkipLogic:
    """Test Docker validation bypass for different backends."""

    def test_pglite_skips_docker_check(self):
        """Test PGlite backend skips Docker availability check."""
        manager = DockerManager()

        # Set environment to PGlite
        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "pglite"}, clear=False):
            # Docker check should return True without checking Docker
            with patch("subprocess.run") as mock_run:
                result = manager._check_docker()

                # Should return True (skip check)
                assert result is True

                # Docker commands should NOT be called
                mock_run.assert_not_called()

    def test_sqlite_skips_docker_check(self):
        """Test SQLite backend skips Docker availability check."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "sqlite"}, clear=False):
            with patch("subprocess.run") as mock_run:
                result = manager._check_docker()

                assert result is True
                mock_run.assert_not_called()

    def test_postgresql_requires_docker_check(self):
        """Test PostgreSQL backend performs Docker availability check."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "postgresql"}, clear=False):
            # Mock Docker available
            with patch.object(manager, "_run_command") as mock_run:
                mock_run.return_value = "Docker version 20.10.0"

                result = manager._check_docker()

                # Should return True (Docker available)
                assert result is True

                # Docker commands SHOULD be called
                assert mock_run.call_count >= 1

    def test_postgresql_docker_not_installed(self, capsys):
        """Test PostgreSQL backend fails when Docker not installed."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "postgresql"}, clear=False):
            # Mock Docker not available
            with patch.object(manager, "_run_command", return_value=None):
                result = manager._check_docker()

                assert result is False

                # Verify error message
                captured = capsys.readouterr()
                assert "Docker not found" in captured.out
                assert "PGlite or SQLite" in captured.out

    def test_postgresql_docker_daemon_not_running(self, capsys):
        """Test PostgreSQL backend fails when Docker daemon not running."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "postgresql"}, clear=False):
            # Mock Docker installed but daemon not running
            def mock_run_command(cmd, capture_output=False):
                if "--version" in cmd:
                    return "Docker version 20.10.0"
                elif "ps" in cmd:
                    return None  # Docker ps fails
                return None

            with patch.object(manager, "_run_command", side_effect=mock_run_command):
                result = manager._check_docker()

                assert result is False

                # Verify error message
                captured = capsys.readouterr()
                assert "Docker daemon not running" in captured.out
                assert "PGlite or SQLite" in captured.out

    def test_pglite_url_detection_skips_docker(self):
        """Test URL-based PGlite detection skips Docker check."""
        manager = DockerManager()

        # No explicit backend but URL indicates PGlite
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "pglite://./data/db.db"},
            clear=True,
        ):
            with patch("subprocess.run") as mock_run:
                result = manager._check_docker()

                assert result is True
                mock_run.assert_not_called()

    def test_sqlite_url_detection_skips_docker(self):
        """Test URL-based SQLite detection skips Docker check."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "sqlite:///./data/db.db"},
            clear=True,
        ):
            with patch("subprocess.run") as mock_run:
                result = manager._check_docker()

                assert result is True
                mock_run.assert_not_called()

    def test_postgresql_url_detection_requires_docker(self):
        """Test URL-based PostgreSQL detection requires Docker check."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "postgresql://localhost/db"},
            clear=True,
        ):
            with patch.object(manager, "_run_command") as mock_run:
                mock_run.return_value = "Docker version 20.10.0"

                _ = manager._check_docker()  # Result intentionally unused

                # Should perform Docker check
                assert mock_run.call_count >= 1

    def test_backend_aware_error_messages_pglite(self, capsys):
        """Test error messages mention PGlite as alternative."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "postgresql"}, clear=False):
            with patch.object(manager, "_run_command", return_value=None):
                manager._check_docker()

                captured = capsys.readouterr()
                assert "PGlite" in captured.out

    def test_backend_aware_error_messages_sqlite(self, capsys):
        """Test error messages mention SQLite as alternative."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "postgresql"}, clear=False):
            with patch.object(manager, "_run_command", return_value=None):
                manager._check_docker()

                captured = capsys.readouterr()
                assert "SQLite" in captured.out

    def test_install_with_pglite_no_docker_required(self):
        """Test install command with PGlite doesn't require Docker."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "pglite"}, clear=False):
            # Mock Docker not available
            with patch("subprocess.run", side_effect=FileNotFoundError):
                # _check_docker should still return True for PGlite
                result = manager._check_docker()
                assert result is True

    def test_install_with_sqlite_no_docker_required(self):
        """Test install command with SQLite doesn't require Docker."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "sqlite"}, clear=False):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                result = manager._check_docker()
                assert result is True

    def test_detect_backend_from_env_explicit_setting(self):
        """Test backend detection prioritizes explicit HIVE_DATABASE_BACKEND."""
        manager = DockerManager()

        # Explicit backend setting
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_BACKEND": "pglite",
                # Conflicting URL should be ignored
                "HIVE_DATABASE_URL": "postgresql://localhost/db",
            },
            clear=False,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "pglite"

    def test_detect_backend_from_env_url_fallback(self):
        """Test backend detection falls back to URL parsing."""
        manager = DockerManager()

        # No explicit backend, use URL
        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "sqlite:///test.db"},
            clear=True,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "sqlite"

    def test_detect_backend_from_env_pglite_url(self):
        """Test PGlite URL detection."""
        manager = DockerManager()

        with patch.dict(
            os.environ,
            {"HIVE_DATABASE_URL": "pglite://./data/db.db"},
            clear=True,
        ):
            backend = manager._detect_backend_from_env()
            assert backend == "pglite"

    def test_detect_backend_from_env_postgresql_url(self):
        """Test PostgreSQL URL detection."""
        manager = DockerManager()

        url_variants = [
            "postgresql://localhost/db",
            "postgresql+psycopg://localhost/db",
            "postgres://localhost/db",
        ]

        for url in url_variants:
            with patch.dict(
                os.environ,
                {"HIVE_DATABASE_URL": url},
                clear=True,
            ):
                backend = manager._detect_backend_from_env()
                assert backend == "postgresql", f"Failed for URL: {url}"

    def test_detect_backend_from_env_default_postgresql(self):
        """Test default backend is PostgreSQL for backward compatibility."""
        manager = DockerManager()

        # No backend or URL set
        with patch.dict(os.environ, {}, clear=True):
            backend = manager._detect_backend_from_env()
            assert backend == "postgresql"

    def test_docker_check_with_case_variations(self):
        """Test backend detection is case-insensitive."""
        manager = DockerManager()

        backend_values = ["PGLITE", "PgLite", "pglite", "SQLITE", "SQLite", "sqlite"]

        for backend in backend_values:
            with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": backend}, clear=False):
                with patch("subprocess.run") as mock_run:
                    result = manager._check_docker()

                    # All variations should skip Docker check
                    if backend.lower() in ("pglite", "sqlite"):
                        assert result is True
                        mock_run.assert_not_called()

    def test_service_manager_docker_skip_integration(self):
        """Test ServiceManager integrates with Docker skip logic."""
        from cli.commands.service import ServiceManager

        service_manager = ServiceManager()

        # Test backend detection in serve_local
        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "pglite"}, clear=False):
            # Mock the actual server startup
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                # Backend detection should happen
                backend = service_manager._detect_backend_from_env()
                assert backend == "pglite"

                # PostgreSQL dependency check should be skipped for PGlite
                with patch.object(service_manager, "_ensure_postgres_dependency") as mock_ensure:
                    try:
                        service_manager.serve_local()
                    except Exception:  # noqa: S110
                        pass  # Intentionally ignoring execution errors - testing flow control only

                    # PostgreSQL dependency should NOT be checked for PGlite
                    mock_ensure.assert_not_called()

    def test_docker_unavailable_helpful_message(self, capsys):
        """Test Docker unavailable shows helpful message with alternatives."""
        manager = DockerManager()

        with patch.dict(os.environ, {"HIVE_DATABASE_BACKEND": "postgresql"}, clear=False):
            with patch.object(manager, "_run_command", return_value=None):
                result = manager._check_docker()

                assert result is False

                captured = capsys.readouterr()

                # Verify helpful message content
                assert "Docker not found" in captured.out
                assert "Tip" in captured.out or "💡" in captured.out
                assert "PGlite" in captured.out
                assert "SQLite" in captured.out
                assert "without Docker" in captured.out
