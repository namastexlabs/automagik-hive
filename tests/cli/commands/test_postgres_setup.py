"""Test PostgreSQL setup failure handling and error messages.

These tests verify that the PostgreSQL setup process properly handles failures,
provides diagnostic information, and detects missing Docker configuration files.

All tests should now PASS after implementing comprehensive verbose logging
and better error messages with diagnostic information.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

from cli.commands.service import ServiceManager  # noqa: E402
from cli.core.main_service import MainService  # noqa: E402


class TestPostgresSetupValidation:
    """Test PostgreSQL setup validation and error detection."""

    @pytest.fixture
    def main_service(self):
        """Create MainService instance."""
        return MainService()

    def test_start_postgres_detects_missing_compose_file(self, tmp_path, main_service):
        """Test that start_postgres_only detects missing docker-compose.yml.

        EXPECTED TO FAIL: Currently returns False without explaining WHY,
        making it hard for users to diagnose the issue.
        """
        workspace_path = str(tmp_path)

        # Workspace exists but has no Docker files
        (tmp_path / "data").mkdir(parents=True)

        # Attempt to start PostgreSQL
        with patch("builtins.print") as mock_print:
            success = main_service.start_postgres_only(workspace_path)

            # Should fail (no compose file)
            assert not success, "Should fail when docker-compose.yml missing"

            # Should print diagnostic message
            print_calls = [str(call) for call in mock_print.call_args_list]
            output = " ".join(print_calls).lower()

            # Expected diagnostic information
            assert any(phrase in output for phrase in ["docker-compose.yml", "compose file", "docker file"]), (
                "Should mention missing docker-compose.yml in error output"
            )
            assert any(phrase in output for phrase in ["not found", "missing", "does not exist"]), (
                "Should clearly state file is missing"
            )

    def test_start_postgres_checks_docker_main_first(self, tmp_path, main_service):
        """Test that PostgreSQL setup checks docker/main/ directory first.

        EXPECTED TO FAIL: Priority order may not match initialization behavior,
        causing inconsistency between init and install.
        """
        workspace_path = str(tmp_path)

        # Create only docker/main/docker-compose.yml
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'
services:
  hive-postgres:
    image: postgres:15
    ports:
      - "5432:5432"
""")

        # Mock subprocess to avoid actual Docker call
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            main_service.start_postgres_only(workspace_path)

            # Should use docker/main/docker-compose.yml (priority)
            assert mock_run.called, "Should attempt to run docker compose"

            call_args = str(mock_run.call_args)
            assert "docker/main/docker-compose.yml" in call_args, (
                "Should use docker/main/docker-compose.yml when available"
            )

    def test_start_postgres_provides_actionable_error_messages(self, tmp_path, main_service):
        """Test that PostgreSQL setup errors include actionable guidance."""
        workspace_path = str(tmp_path)

        # Missing Docker directory entirely
        with patch("builtins.print") as mock_print:
            success = main_service.start_postgres_only(workspace_path)

            assert not success, "Should fail when Docker not set up"

            print_calls = [str(call) for call in mock_print.call_args_list]
            output = " ".join(print_calls).lower()

            # Should provide actionable guidance
            expected_guidance = [
                "run",  # "run 'automagik-hive init'"
                "init",  # workspace initialization
                "install",  # full installation
            ]

            has_guidance = any(term in output for term in expected_guidance)
            assert has_guidance, "Error message should provide actionable guidance (run init/install)"

    def test_start_postgres_subprocess_failure_handling(self, tmp_path, main_service):
        """Test handling when docker compose command fails.

        EXPECTED TO FAIL: Subprocess errors may not be caught and reported clearly.
        """
        workspace_path = str(tmp_path)

        # Create valid docker-compose.yml
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  hive-postgres:\n    image: postgres:15\n")

        # Mock subprocess to fail
        with patch("subprocess.run") as mock_run:
            # Simulate docker compose failure
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Error: service 'hive-postgres' not found"
            )

            with patch("builtins.print") as mock_print:
                success = main_service.start_postgres_only(workspace_path)

                assert not success, "Should return False on subprocess failure"

                # Should capture and report the error
                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should mention Docker or PostgreSQL in error context
                assert any(term in output for term in ["docker", "postgres", "error", "failed"]), (
                    "Should report Docker/PostgreSQL error context"
                )

    def test_start_postgres_timeout_handling(self, tmp_path, main_service):
        """Test handling when docker compose times out.

        EXPECTED TO FAIL: Timeout errors may not be caught or reported clearly.
        """
        workspace_path = str(tmp_path)

        # Create valid docker-compose.yml
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  hive-postgres:\n    image: postgres:15\n")

        # Mock subprocess to timeout
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("docker compose", 120)):
            with patch("builtins.print") as mock_print:
                success = main_service.start_postgres_only(workspace_path)

                assert not success, "Should return False on timeout"

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should mention timeout in error
                assert any(term in output for term in ["timeout", "timed out", "taking too long"]), (
                    "Should report timeout condition"
                )


class TestPostgresInstallErrorReporting:
    """Test error reporting during PostgreSQL installation."""

    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance."""
        return ServiceManager()

    def test_install_detects_missing_docker_files_early(self, tmp_path, service_manager):
        """Test that install detects missing Docker files before attempting setup."""
        workspace_path = str(tmp_path)

        # Create minimal workspace (no Docker files)
        (tmp_path / ".env.example").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="A"):  # Choose deployment mode (A = local_hybrid)
                # Mock credential service to avoid actual file operations
                with patch("lib.auth.credential_service.CredentialService"):
                    # Call the actual method - install_full_environment
                    success = service_manager.install_full_environment(workspace_path)

                    # Should succeed but PostgreSQL setup will report issues
                    # (installation doesn't fail, just warns)
                    assert success, "Install should complete (PostgreSQL warnings allowed)"

                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls).lower()

                    # Should mention Docker configuration missing
                    assert "docker" in output or "compose" in output, "Should mention Docker configuration in error"

    def test_install_reports_docker_compose_location_attempted(self, tmp_path, service_manager):
        """Test that install reports which docker-compose.yml location it tried."""
        workspace_path = str(tmp_path)

        # Create .env but no Docker files
        (tmp_path / ".env.example").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="A"):  # A = local_hybrid deployment mode
                with patch("lib.auth.credential_service.CredentialService"):
                    # Run install with verbose to see paths checked
                    service_manager.install_full_environment(workspace_path, verbose=True)

                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls)

                    # Should mention specific paths checked
                    expected_paths = ["docker/main/docker-compose.yml", "docker-compose.yml"]

                    mentions_path = any(path in output for path in expected_paths)
                    assert mentions_path, "Should mention specific docker-compose.yml paths checked"

    def test_install_suggests_running_init_first(self, tmp_path, service_manager):
        """Test that install suggests running init when Docker files missing."""
        workspace_path = str(tmp_path)

        # Create .env but no Docker files (typical mistake: install before init)
        (tmp_path / ".env.example").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="A"):  # A = local_hybrid deployment mode
                with patch("lib.auth.credential_service.CredentialService"):
                    service_manager.install_full_environment(workspace_path)

                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls).lower()

                    # Should suggest running init
                    assert "init" in output, "Should suggest running 'automagik-hive init' first"

    def test_install_validates_docker_compose_service_names(self, tmp_path, service_manager):
        """Test that install validates docker-compose.yml has required services."""
        workspace_path = str(tmp_path)

        # Create docker-compose.yml with wrong service name
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'
services:
  wrong-postgres-name:  # Wrong name (should be 'hive-postgres')
    image: postgres:15
""")

        (tmp_path / ".env.example").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="A"):  # A = local_hybrid deployment mode
                with patch("lib.auth.credential_service.CredentialService"):
                    # Mock subprocess to simulate docker compose error
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(
                            returncode=1, stdout="", stderr="Error: service 'hive-postgres' not found"
                        )

                        service_manager.install_full_environment(workspace_path)

                        print_calls = [str(call) for call in mock_print.call_args_list]
                        output = " ".join(print_calls).lower()

                        # Should detect and report service name mismatch
                        assert any(term in output for term in ["service", "hive-postgres", "not found", "error"]), (
                            "Should report that hive-postgres service not found in compose file"
                        )


class TestPostgresConnectionDiagnostics:
    """Test diagnostic information for PostgreSQL connection issues."""

    @pytest.fixture
    def main_service(self):
        """Create MainService instance."""
        return MainService()

    def test_postgres_start_reports_port_conflicts(self, tmp_path, main_service):
        """Test that PostgreSQL start detects and reports port conflicts.

        EXPECTED TO FAIL: Port conflicts may not be detected or reported clearly.
        """
        workspace_path = str(tmp_path)

        # Create valid docker-compose.yml
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'
services:
  hive-postgres:
    image: postgres:15
    ports:
      - "5432:5432"
""")

        # Mock subprocess to fail with port conflict
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error: port 5432 is already allocated")

            with patch("builtins.print") as mock_print:
                main_service.start_postgres_only(workspace_path)

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should mention port conflict
                assert "port" in output or "5432" in output, "Should mention port conflict in error"

    def test_postgres_start_checks_docker_daemon_running(self, tmp_path, main_service):
        """Test that PostgreSQL start checks if Docker daemon is running.

        EXPECTED TO FAIL: May not distinguish between Docker daemon issues
        and other failures.
        """
        workspace_path = str(tmp_path)

        # Create valid docker-compose.yml
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  hive-postgres:\n    image: postgres:15\n")

        # Mock subprocess to fail with "docker daemon not running" error
        with patch("subprocess.run", side_effect=FileNotFoundError("docker: command not found")):
            with patch("builtins.print") as mock_print:
                main_service.start_postgres_only(workspace_path)

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should mention Docker installation/daemon
                assert any(term in output for term in ["docker", "daemon", "not running", "not found"]), (
                    "Should report Docker daemon/installation issue"
                )

    def test_postgres_start_provides_recovery_steps(self, tmp_path, main_service):
        """Test that PostgreSQL failures include recovery steps."""
        workspace_path = str(tmp_path)

        # Missing docker-compose.yml
        with patch("builtins.print") as mock_print:
            success = main_service.start_postgres_only(workspace_path)

            assert not success

            print_calls = [str(call) for call in mock_print.call_args_list]
            output = " ".join(print_calls).lower()

            # Should include recovery steps - we now provide these in non-verbose mode
            recovery_terms = ["troubleshooting", "verify", "check", "init"]
            has_recovery_guidance = any(term in output for term in recovery_terms)

            assert has_recovery_guidance, (
                "Error message should include recovery steps (troubleshooting, verify, check, init)"
            )
