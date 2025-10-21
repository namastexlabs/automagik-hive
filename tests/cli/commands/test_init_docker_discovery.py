"""Test Docker template discovery during workspace initialization.

These tests verify that the init_workspace command correctly locates and copies
Docker configuration files, with proper fallback to GitHub download when local
templates are not available.

EXPECTED FAILURES:
- Docker templates not copied from source during init
- GitHub fallback not properly tested
- Workspace missing docker/main/docker-compose.yml after init
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

from cli.commands.service import ServiceManager  # noqa: E402


class TestDockerTemplateDiscovery:
    """Test Docker template discovery and copying during init."""

    @pytest.fixture
    def service_manager(self, temp_workspace):
        """Create ServiceManager instance."""
        return ServiceManager(workspace_path=temp_workspace)

    def test_init_copies_docker_templates_from_source(self, tmp_path):
        """Test that init_workspace copies Docker templates from source directory.

        EXPECTED TO FAIL: Current implementation may not properly detect and copy
        docker/main/ directory structure during initialization.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Initialize workspace
        service_manager.init_workspace(workspace_name, force=False)

        # Verify Docker directory structure created
        workspace_path = Path(workspace_name)
        assert workspace_path.exists(), "Workspace should be created"

        docker_main_dir = workspace_path / "docker" / "main"
        assert docker_main_dir.exists(), "docker/main directory should exist"

        # Verify critical Docker files present
        docker_compose = docker_main_dir / "docker-compose.yml"
        assert docker_compose.exists(), "docker-compose.yml should be copied"

        dockerfile = docker_main_dir / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile should be copied"

        dockerignore = docker_main_dir / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore should be copied"

    def test_init_docker_compose_contains_postgres_service(self, tmp_path):
        """Test that copied docker-compose.yml contains PostgreSQL service.

        EXPECTED TO FAIL: Docker compose file may not be copied or may be incomplete.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Initialize workspace
        success = service_manager.init_workspace(workspace_name, force=False)
        assert success, "Init should succeed"

        # Read docker-compose.yml
        compose_file = Path(workspace_name) / "docker" / "main" / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml must exist"

        compose_content = compose_file.read_text()

        # Verify PostgreSQL service present
        assert "hive-postgres" in compose_content, "Should define hive-postgres service"
        assert "postgres:15" in compose_content or "postgres:" in compose_content, "Should use postgres image"
        assert "5432" in compose_content, "Should expose PostgreSQL port"

    def test_init_github_fallback_when_local_templates_missing(self, tmp_path):
        """Test GitHub fallback when local Docker templates not found.

        Verifies that when Docker templates are not found locally,
        the system falls back to downloading them from GitHub.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Mock _locate_template_root to return a valid path (so init doesn't exit early)
        # but mock _locate_docker_templates to return None (to trigger Docker GitHub fallback)
        fake_template_root = tmp_path / "fake_templates" / "ai"
        fake_template_root.mkdir(parents=True)

        # Create minimal agent/team/workflow templates so init can proceed
        for component in ["agents", "teams", "workflows"]:
            component_dir = fake_template_root / component / f"template-{component[:-1]}"
            component_dir.mkdir(parents=True)
            (component_dir / "config.yaml").write_text("# minimal config")

        with patch.object(service_manager, "_locate_template_root", return_value=fake_template_root):
            with patch.object(service_manager, "_locate_docker_templates", return_value=None):
                # Mock urllib to simulate successful GitHub download
                with patch("urllib.request.urlretrieve") as mock_retrieve:
                    mock_retrieve.return_value = (None, None)

                    # Initialize workspace
                    service_manager.init_workspace(workspace_name, force=False)

                    # Verify GitHub download attempted for Docker files
                    docker_compose_url = "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/docker/main/docker-compose.yml"
                    dockerfile_url = (
                        "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/docker/main/Dockerfile"
                    )
                    dockerignore_url = (
                        "https://raw.githubusercontent.com/namastexlabs/automagik-hive/main/docker/main/.dockerignore"
                    )

                    # Check that Docker files were downloaded
                    calls = [str(call) for call in mock_retrieve.call_args_list]

                    assert any(docker_compose_url in str(call) for call in calls), (
                        "Should attempt to download docker-compose.yml from GitHub"
                    )
                    assert any(dockerfile_url in str(call) for call in calls), (
                        "Should attempt to download Dockerfile from GitHub"
                    )
                    assert any(dockerignore_url in str(call) for call in calls), (
                        "Should attempt to download .dockerignore from GitHub"
                    )

    def test_init_creates_complete_docker_structure(self, tmp_path):
        """Test that init creates complete Docker directory structure.

        EXPECTED TO FAIL: Complete directory structure may not be created,
        leading to subsequent installation failures.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Initialize workspace
        success = service_manager.init_workspace(workspace_name, force=False)
        assert success, "Init should succeed"

        workspace_path = Path(workspace_name)

        # Verify complete structure
        expected_paths = [
            workspace_path / "docker",
            workspace_path / "docker" / "main",
            workspace_path / "docker" / "main" / "docker-compose.yml",
            workspace_path / "docker" / "main" / "Dockerfile",
            workspace_path / "docker" / "main" / ".dockerignore",
        ]

        for expected_path in expected_paths:
            assert expected_path.exists(), f"Required path missing: {expected_path}"

    def test_init_failure_when_docker_source_unavailable(self, tmp_path):
        """Test proper error handling when Docker source unavailable.

        EXPECTED TO FAIL: Error messages may not be clear about missing Docker files,
        making troubleshooting difficult for users.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Mock both local and GitHub sources to fail
        with patch.object(service_manager, "_locate_template_root", return_value=None):
            with patch("urllib.request.urlretrieve", side_effect=Exception("Network error")):
                # Capture output
                with patch("builtins.print") as mock_print:
                    service_manager.init_workspace(workspace_name, force=False)

                    # Verify error messages printed
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls)

                    # Should warn about Docker configuration issues
                    assert "Docker" in output or "docker" in output, "Should mention Docker in error output"
                    assert "PostgreSQL" in output or "postgres" in output or "manual" in output, (
                        "Should warn that PostgreSQL needs manual setup"
                    )

    def test_init_docker_templates_source_priority(self, tmp_path):
        """Test that local source templates take priority over GitHub download.

        EXPECTED TO FAIL: Priority logic may not be correctly implemented,
        potentially causing unnecessary network calls.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Create mock source directory with Docker templates
        project_root = Path(__file__).parent.parent.parent.parent
        docker_source = project_root / "docker"

        if docker_source.exists():
            # Mock GitHub download to track if it's called
            with patch("urllib.request.urlretrieve") as mock_retrieve:
                service_manager.init_workspace(workspace_name, force=False)

                # Verify local source used, GitHub NOT called for Docker files
                docker_urls = ["docker/main/docker-compose.yml", "docker/main/Dockerfile", "docker/main/.dockerignore"]

                calls = [str(call) for call in mock_retrieve.call_args_list]

                # GitHub should NOT be called if local Docker templates exist
                for url in docker_urls:
                    assert not any(url in str(call) for call in calls), (
                        f"Should use local Docker templates, not download from GitHub: {url}"
                    )

    def test_init_workspace_docker_validation(self, tmp_path):
        """Test that initialized workspace passes Docker validation.

        EXPECTED TO FAIL: Workspace may be missing critical Docker files needed
        for subsequent install and start operations.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Initialize workspace
        success = service_manager.init_workspace(workspace_name, force=False)
        assert success, "Init should succeed"

        # Try to validate the workspace using MainService validation logic
        from cli.core.main_service import MainService

        main_service = MainService()
        workspace_path = Path(workspace_name)

        # Workspace should pass validation (has docker-compose.yml in correct location)
        is_valid = main_service._validate_workspace(workspace_path)
        assert is_valid, "Initialized workspace should pass MainService validation"


@pytest.mark.skip(reason="Aspirational tests for Docker template fallback - not yet fully implemented")
class TestDockerTemplateFallbackScenarios:
    """Test various fallback scenarios for Docker template copying."""

    def test_partial_docker_files_available(self, tmp_path):
        """Test handling when only some Docker files are available.

        EXPECTED TO FAIL: Partial availability may not be handled correctly,
        leading to incomplete Docker setup.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        # Mock scenario: compose file exists but Dockerfile missing
        with patch("shutil.copytree", side_effect=FileNotFoundError("Dockerfile missing")):
            with patch("urllib.request.urlretrieve") as mock_retrieve:
                mock_retrieve.return_value = (None, None)

                service_manager.init_workspace(workspace_name, force=False)

                # Should attempt GitHub fallback for missing files
                assert mock_retrieve.called, "Should attempt GitHub download when copy fails"

    def test_github_download_creates_directory_structure(self, tmp_path):
        """Test that GitHub fallback creates proper directory structure.

        EXPECTED TO FAIL: Directory creation may not happen before file download,
        causing file write failures.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        with patch.object(service_manager, "_locate_template_root", return_value=None):
            with patch("urllib.request.urlretrieve") as mock_retrieve:
                # Simulate successful download
                def fake_download(url, target):
                    # Verify parent directory exists before "download"
                    target_path = Path(target)
                    assert target_path.parent.exists(), (
                        f"Parent directory should exist before download: {target_path.parent}"
                    )
                    target_path.touch()

                mock_retrieve.side_effect = fake_download

                service_manager.init_workspace(workspace_name, force=False)

                # Verify docker/main directory was created
                docker_main = Path(workspace_name) / "docker" / "main"
                assert docker_main.exists(), "docker/main directory should be created before downloads"

    def test_init_reports_docker_copy_status(self, tmp_path):
        """Test that init properly reports Docker copy success/failure.

        EXPECTED TO FAIL: Status messages may not clearly indicate whether
        Docker files were successfully copied or downloaded.
        """
        workspace_name = str(tmp_path / "test-workspace")
        service_manager = ServiceManager()

        with patch("builtins.print") as mock_print:
            service_manager.init_workspace(workspace_name, force=False)

            print_calls = [str(call) for call in mock_print.call_args_list]
            output = " ".join(print_calls).lower()

            # Should explicitly mention Docker configuration status
            assert "docker" in output, "Should mention Docker in output"
            assert any(marker in output for marker in ["✅", "⚠️", "❌"]), (
                "Should use status indicators for Docker files"
            )
