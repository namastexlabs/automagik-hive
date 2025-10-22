#!/usr/bin/env python3
"""Test CLI integration with single credential system."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from cli.docker_manager import DockerManager


# Test enabled - credential service database port bug has been fixed
def test_cli_install_uses_single_credential_system():
    """Test that CLI install command uses single credential system."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Mock all Docker operations so we can test credential generation
        with patch("cli.docker_manager.DockerManager._check_docker", return_value=True):
            with patch("cli.docker_manager.DockerManager._create_network"):
                with patch("cli.docker_manager.DockerManager._container_exists", return_value=False):
                    with patch("cli.docker_manager.DockerManager._container_running", return_value=False):
                        with patch(
                            "cli.docker_manager.DockerManager._create_containers_via_compose", return_value=True
                        ):
                            with patch("time.sleep"):  # Skip sleep delays in tests
                                # Create DockerManager with temp directory
                                docker_manager = DockerManager()
                                docker_manager.project_root = temp_path
                                # Also update the credential service to use the temp path
                                docker_manager.credential_service.project_root = temp_path
                                docker_manager.credential_service.env_manager.project_root = temp_path
                                docker_manager.credential_service.env_manager.primary_env_path = temp_path / ".env"
                                docker_manager.credential_service.env_manager.alias_env_path = temp_path / ".env.master"
                                docker_manager.credential_service._refresh_env_paths()

                                # After refactoring, only workspace mode is supported
                                # Install workspace component
                                result = docker_manager.install("workspace")

                                assert result is True

                                # Check that credentials were generated
                                main_env = temp_path / ".env"

                                assert main_env.exists(), "Main .env file should be created"
                                # After refactoring, single credential system with workspace-only mode

                                # Check main env has workspace credentials
                                main_content = main_env.read_text()
                                assert "HIVE_DATABASE_URL=" in main_content
                                assert "localhost:5532" in main_content  # Workspace uses base port
                                assert "HIVE_API_KEY=" in main_content

                                # After refactoring: single workspace mode, no multi-mode credential system
                                # Main env contains the unified configuration for workspace
                                assert "localhost:5532" in main_content  # Workspace port

                                # Verify workspace configuration is complete
                                main_lines = main_content.splitlines()
                                main_db_url = next(line for line in main_lines if line.startswith("HIVE_DATABASE_URL="))

                                # Extract user/password from main URL
                                main_user = main_db_url.split("://")[1].split(":")[0]
                                main_pass = main_db_url.split(":")[2].split("@")[0]

                                # Unified workspace credentials
                                assert main_user, "Workspace user should be present"
                                assert main_pass, "Workspace password should be present"


if __name__ == "__main__":
    test_cli_install_uses_single_credential_system()
