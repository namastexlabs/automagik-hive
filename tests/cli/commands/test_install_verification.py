"""Test post-installation verification and validation.

These tests verify that the installation process properly validates the workspace
after setup, detects missing components, and provides actionable error messages.

EXPECTED FAILURES:
- Post-install verification doesn't detect missing Docker files
- Verification doesn't provide actionable error messages
- Installation passes even when critical components missing
"""

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


@pytest.mark.skip(reason="Aspirational tests for unimplemented install_environment() method")
class TestPostInstallVerification:
    """Test post-installation verification checks."""

    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance."""
        return ServiceManager()

    @pytest.fixture
    def main_service(self):
        """Create MainService instance."""
        return MainService()

    def test_install_verifies_docker_files_present(self, tmp_path, service_manager):
        """Test that install verifies Docker files are present after completion.

        EXPECTED TO FAIL: Install may succeed even when docker-compose.yml
        is missing or incomplete.
        """
        workspace_path = str(tmp_path)

        # Create minimal .env
        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        # Mock subprocess to simulate successful docker commands
        # but don't actually create Docker files
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("builtins.input", return_value="y"):
                success = service_manager.install_environment(workspace_path)

                if success:
                    # If install claims success, verify Docker files exist
                    docker_main_compose = tmp_path / "docker" / "main" / "docker-compose.yml"
                    docker_root_compose = tmp_path / "docker-compose.yml"

                    has_docker_compose = docker_main_compose.exists() or docker_root_compose.exists()
                    assert has_docker_compose, "Install should not succeed without docker-compose.yml"

    def test_install_verifies_postgres_service_defined(self, tmp_path, service_manager):
        """Test that install verifies PostgreSQL service is defined in compose file.

        EXPECTED TO FAIL: Install may not validate compose file contents,
        leading to runtime failures when trying to start PostgreSQL.
        """
        workspace_path = str(tmp_path)

        # Create docker-compose.yml WITHOUT postgres service
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'
services:
  some-other-service:  # No hive-postgres service
    image: nginx:latest
""")

        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="y"):
                success = service_manager.install_environment(workspace_path)

                # Should fail or warn about missing hive-postgres service
                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                if success:
                    # If it succeeded, should have warned about missing service
                    assert "postgres" in output or "hive-postgres" in output, (
                        "Should validate that hive-postgres service is defined"
                    )

    def test_install_checks_docker_file_syntax(self, tmp_path, service_manager):
        """Test that install validates docker-compose.yml syntax.

        EXPECTED TO FAIL: Install may not validate YAML syntax before
        attempting to use the compose file.
        """
        workspace_path = str(tmp_path)

        # Create invalid docker-compose.yml
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("invalid: yaml: syntax: [[[")

        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="y"):
                success = service_manager.install_environment(workspace_path)

                # Should fail due to invalid YAML
                assert not success, "Install should fail with invalid docker-compose.yml syntax"

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should mention YAML or syntax error
                assert any(term in output for term in ["yaml", "syntax", "invalid", "parse"]), (
                    "Should report YAML syntax error"
                )

    def test_install_validates_postgres_image_specified(self, tmp_path, service_manager):
        """Test that install validates PostgreSQL image is specified.

        EXPECTED TO FAIL: Install may not check that postgres image is
        properly defined in the service configuration.
        """
        workspace_path = str(tmp_path)

        # Create docker-compose.yml with hive-postgres but no image
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("""
version: '3.8'
services:
  hive-postgres:
    # Missing 'image:' field
    ports:
      - "5432:5432"
""")

        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="y"):
                # Mock subprocess to simulate docker compose validation error
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=1, stderr="Error: service 'hive-postgres' has no 'image' or 'build' key"
                    )

                    service_manager.install_environment(workspace_path)

                    # Should detect and report the issue
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls).lower()

                    assert "image" in output or "postgres" in output, (
                        "Should report missing postgres image specification"
                    )


@pytest.mark.skip(reason="Aspirational tests for unimplemented install_environment() method")
class TestInstallVerificationMessages:
    """Test verification error messages are actionable."""

    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance."""
        return ServiceManager()

    def test_verification_provides_fix_for_missing_docker_files(self, tmp_path, service_manager):
        """Test that verification provides fix steps for missing Docker files.

        EXPECTED TO FAIL: Error messages may not tell users how to fix
        missing Docker configuration.
        """
        workspace_path = str(tmp_path)

        # Minimal workspace (no Docker files)
        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="y"):
                service_manager.install_environment(workspace_path)

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should provide fix steps
                fix_terms = [
                    "init",  # Run automagik-hive init
                    "copy",  # Copy Docker files
                    "download",  # Download from GitHub
                    "create",  # Create the files
                ]

                has_fix_guidance = any(term in output for term in fix_terms)
                assert has_fix_guidance, "Should provide guidance on how to fix missing Docker files"

    def test_verification_lists_all_missing_components(self, tmp_path, service_manager):
        """Test that verification lists ALL missing components, not just first.

        EXPECTED TO FAIL: May only report first missing component,
        requiring multiple fix iterations.
        """
        workspace_path = str(tmp_path)

        # Empty workspace (missing multiple components)
        # No .env, no Docker files, no data directories

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="y"):
                service_manager.install_environment(workspace_path)

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should mention multiple missing components
                components = [".env", "docker", "compose"]
                mentioned_count = sum(1 for comp in components if comp in output)

                assert mentioned_count >= 2, "Should list multiple missing components in one error message"

    def test_verification_distinguishes_init_vs_install_errors(self, tmp_path, service_manager):
        """Test that verification distinguishes between init and install issues.

        EXPECTED TO FAIL: May not clearly distinguish whether user needs to
        run init first vs having an install configuration issue.
        """
        workspace_path = str(tmp_path)

        # Workspace that looks like init was never run (no ai/ directory)
        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        with patch("builtins.print") as mock_print:
            with patch("builtins.input", return_value="y"):
                service_manager.install_environment(workspace_path)

                print_calls = [str(call) for call in mock_print.call_args_list]
                output = " ".join(print_calls).lower()

                # Should suggest running init first
                assert "init" in output, "Should suggest running 'automagik-hive init' when workspace not initialized"


@pytest.mark.skip(reason="Aspirational tests for unimplemented install_environment() method")
class TestInstallHealthChecks:
    """Test that install performs health checks after setup."""

    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance."""
        return ServiceManager()

    def test_install_verifies_postgres_container_started(self, tmp_path, service_manager):
        """Test that install verifies PostgreSQL container actually started.

        EXPECTED TO FAIL: Install may succeed even if container failed to start.
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

        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        # Mock docker compose to succeed but container not actually running
        with patch("subprocess.run") as mock_run:

            def mock_docker_command(*args, **kwargs):
                command = args[0]
                if "up -d" in " ".join(command):
                    # Docker compose succeeds
                    return MagicMock(returncode=0, stdout="Container started")
                elif "ps" in " ".join(command) or "inspect" in " ".join(command):
                    # But container not actually running
                    return MagicMock(returncode=1, stdout="")
                return MagicMock(returncode=0)

            mock_run.side_effect = mock_docker_command

            with patch("builtins.input", return_value="y"):
                with patch("builtins.print") as mock_print:
                    success = service_manager.install_environment(workspace_path)

                    # Should verify container actually running
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls).lower()

                    if success:
                        # If install claims success, should have verified container running
                        assert "running" in output or "started" in output, (
                            "Should verify PostgreSQL container is running after install"
                        )

    def test_install_checks_postgres_port_accessible(self, tmp_path, service_manager):
        """Test that install checks PostgreSQL port is accessible.

        EXPECTED TO FAIL: Install may not verify port accessibility,
        leading to connection issues later.
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

        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        # Mock successful docker start
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("builtins.input", return_value="y"):
                with patch("builtins.print") as mock_print:
                    success = service_manager.install_environment(workspace_path)

                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls).lower()

                    if success:
                        # Should mention port or accessibility check
                        assert "port" in output or "5432" in output or "accessible" in output, (
                            "Should verify PostgreSQL port is accessible"
                        )

    def test_install_provides_verification_summary(self, tmp_path, service_manager):
        """Test that install provides summary of what was verified.

        EXPECTED TO FAIL: Install may not summarize what was checked,
        making it unclear what succeeded vs what was skipped.
        """
        workspace_path = str(tmp_path)

        # Create complete valid workspace
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

        (tmp_path / ".env").write_text("POSTGRES_PASSWORD=fake-test-password-not-real\n")

        # Mock successful installation
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("builtins.input", return_value="y"):
                with patch("builtins.print") as mock_print:
                    success = service_manager.install_environment(workspace_path)

                    if success:
                        print_calls = [str(call) for call in mock_print.call_args_list]
                        output = " ".join(print_calls).lower()

                        # Should provide verification summary
                        verification_terms = ["verified", "checked", "validated", "confirmed"]

                        has_verification_summary = any(term in output for term in verification_terms)
                        assert has_verification_summary, "Should provide summary of verification checks performed"


@pytest.mark.skip(reason="Aspirational tests - validation features not fully implemented yet")
class TestWorkspaceConsistencyChecks:
    """Test that verification ensures workspace consistency."""

    @pytest.fixture
    def main_service(self):
        """Create MainService instance."""
        return MainService()

    def test_workspace_validation_matches_install_expectations(self, tmp_path, main_service):
        """Test that workspace validation uses same paths as install.

        EXPECTED TO FAIL: Validation logic may check different paths than
        install uses, causing inconsistencies.
        """
        workspace_path = tmp_path

        # Create compose file in docker/main/
        docker_main = workspace_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  hive-postgres:\n    image: postgres:15\n")

        # Validation should find this file
        is_valid = main_service._validate_workspace(workspace_path)
        assert is_valid, "Workspace validation should find docker/main/docker-compose.yml (same as install)"

    def test_validation_rejects_incomplete_workspace(self, tmp_path, main_service):
        """Test that validation rejects workspace missing critical components.

        EXPECTED TO FAIL: Validation may be too lenient, accepting workspaces
        that will fail during actual operations.
        """
        workspace_path = tmp_path

        # Create only directory structure, no actual files
        (workspace_path / "docker" / "main").mkdir(parents=True)

        # Should fail validation (no compose file)
        is_valid = main_service._validate_workspace(workspace_path)
        assert not is_valid, "Validation should reject workspace without docker-compose.yml"

    def test_validation_checks_compose_file_readability(self, tmp_path, main_service):
        """Test that validation checks compose file is readable.

        EXPECTED TO FAIL: May only check existence, not readability.
        """
        workspace_path = tmp_path

        # Create docker-compose.yml
        docker_main = workspace_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        compose_file = docker_main / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  hive-postgres:\n    image: postgres:15\n")

        # Make it unreadable (permission test)
        import os
        import stat

        try:
            os.chmod(compose_file, 0o000)  # Remove all permissions

            is_valid = main_service._validate_workspace(workspace_path)

            # Should fail validation (file not readable)
            assert not is_valid, "Validation should reject workspace with unreadable docker-compose.yml"

        finally:
            # Restore permissions for cleanup
            os.chmod(compose_file, stat.S_IRUSR | stat.S_IWUSR)
