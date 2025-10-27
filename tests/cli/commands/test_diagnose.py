"""Test diagnose command for installation troubleshooting.

Tests the comprehensive diagnostic tool that helps users troubleshoot:
- Workspace structure validation
- Docker configuration checks
- PostgreSQL container status
- Environment configuration
- API keys validation
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

from cli.commands.diagnose import DiagnoseCommands  # noqa: E402


class TestDiagnoseCommands:
    """Test diagnostic command functionality."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance with temp workspace."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_diagnose_commands_initialization(self, tmp_path):
        """Test DiagnoseCommands initializes correctly."""
        cmd = DiagnoseCommands(workspace_path=tmp_path)
        assert cmd.workspace_path == tmp_path

    def test_diagnose_commands_uses_current_dir_by_default(self):
        """Test DiagnoseCommands defaults to current directory."""
        cmd = DiagnoseCommands()
        assert cmd.workspace_path == Path()


class TestWorkspaceStructureCheck:
    """Test workspace structure validation."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_check_workspace_structure_passes_with_complete_structure(self, diagnose_commands, tmp_path):
        """Test workspace structure check passes when all directories exist."""
        # Create required directories
        (tmp_path / "ai" / "agents").mkdir(parents=True)
        (tmp_path / "ai" / "teams").mkdir(parents=True)
        (tmp_path / "ai" / "workflows").mkdir(parents=True)
        (tmp_path / "knowledge").mkdir(parents=True)

        check_name, passed, issues = diagnose_commands._check_workspace_structure()

        assert check_name == "Workspace Structure"
        assert passed is True
        assert len(issues) == 0

    def test_check_workspace_structure_fails_with_missing_directories(self, diagnose_commands):
        """Test workspace structure check fails when directories missing."""
        check_name, passed, issues = diagnose_commands._check_workspace_structure()

        assert check_name == "Workspace Structure"
        assert passed is False
        assert any("Missing directory: ai/agents" in issue for issue in issues)
        assert any("init" in issue.lower() for issue in issues)

    def test_check_workspace_structure_lists_all_missing_dirs(self, diagnose_commands, tmp_path):
        """Test workspace structure check lists all missing directories."""
        # Create only one directory
        (tmp_path / "ai" / "agents").mkdir(parents=True)

        check_name, passed, issues = diagnose_commands._check_workspace_structure()

        assert passed is False
        # Should report multiple missing directories
        missing_count = sum(1 for issue in issues if "Missing directory:" in issue)
        assert missing_count >= 2  # At least teams, workflows, knowledge


class TestDockerFilesCheck:
    """Test Docker configuration validation."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_check_docker_files_passes_with_complete_config(self, diagnose_commands, tmp_path):
        """Test Docker files check passes when all files exist."""
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)

        # Create required files
        (docker_main / "docker-compose.yml").write_text("""
version: '3.8'
services:
  hive-postgres:
    image: postgres:15
""")
        (docker_main / "Dockerfile").write_text("FROM python:3.12")

        check_name, passed, issues = diagnose_commands._check_docker_files()

        assert check_name == "Docker Configuration"
        assert passed is True
        assert len(issues) == 0

    def test_check_docker_files_fails_with_missing_compose(self, diagnose_commands):
        """Test Docker files check fails when compose file missing."""
        check_name, passed, issues = diagnose_commands._check_docker_files()

        assert passed is False
        assert any("docker-compose.yml" in issue for issue in issues)

    def test_check_docker_files_validates_postgres_service(self, diagnose_commands, tmp_path):
        """Test Docker files check validates hive-postgres service exists."""
        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)

        # Create compose file without hive-postgres service
        (docker_main / "docker-compose.yml").write_text("""
version: '3.8'
services:
  other-service:
    image: nginx
""")
        (docker_main / "Dockerfile").write_text("FROM python:3.12")

        check_name, passed, issues = diagnose_commands._check_docker_files()

        assert passed is False
        assert any("hive-postgres" in issue for issue in issues)


class TestDockerDaemonCheck:
    """Test Docker daemon availability."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_check_docker_daemon_passes_when_running(self, diagnose_commands):
        """Test Docker daemon check passes when Docker is running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            check_name, passed, issues = diagnose_commands._check_docker_daemon()

            assert check_name == "Docker Daemon"
            assert passed is True
            assert len(issues) == 0

    def test_check_docker_daemon_fails_when_not_running(self, diagnose_commands):
        """Test Docker daemon check fails when Docker not running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            check_name, passed, issues = diagnose_commands._check_docker_daemon()

            assert passed is False
            assert any("not responding" in issue for issue in issues)
            assert any("systemctl" in issue or "Docker Desktop" in issue for issue in issues)

    def test_check_docker_daemon_handles_not_installed(self, diagnose_commands):
        """Test Docker daemon check handles Docker not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            check_name, passed, issues = diagnose_commands._check_docker_daemon()

            assert passed is False
            assert any("not installed" in issue for issue in issues)
            assert any("docker.com" in issue for issue in issues)


class TestPostgresStatusCheck:
    """Test PostgreSQL container status validation."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_check_postgres_status_passes_when_running(self, diagnose_commands):
        """Test PostgreSQL status check passes when container running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Up 5 minutes", text=True)

            check_name, passed, issues = diagnose_commands._check_postgres_status()

            assert check_name == "PostgreSQL Status"
            assert passed is True
            assert len(issues) == 0

    def test_check_postgres_status_fails_when_not_running(self, diagnose_commands):
        """Test PostgreSQL status check fails when container not running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Exited (0) 2 minutes ago", text=True)

            check_name, passed, issues = diagnose_commands._check_postgres_status()

            assert passed is False
            assert any("not running" in issue for issue in issues)
            assert any("postgres-start" in issue for issue in issues)

    def test_check_postgres_status_fails_when_not_found(self, diagnose_commands):
        """Test PostgreSQL status check fails when container not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", text=True)

            check_name, passed, issues = diagnose_commands._check_postgres_status()

            assert passed is False
            assert any("not found" in issue for issue in issues)
            assert any("install" in issue for issue in issues)


class TestEnvironmentConfigCheck:
    """Test environment configuration validation."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_check_environment_config_passes_with_valid_env(self, diagnose_commands, tmp_path):
        """Test environment config check passes with valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/db
HIVE_API_KEY=hive_1234567890abcdef1234567890abcdef
""")

        check_name, passed, issues = diagnose_commands._check_environment_config()

        assert check_name == "Environment Config"
        assert passed is True
        assert len(issues) == 0

    def test_check_environment_config_fails_without_env_file(self, diagnose_commands):
        """Test environment config check fails when .env missing."""
        check_name, passed, issues = diagnose_commands._check_environment_config()

        assert passed is False
        assert any(".env file not found" in issue for issue in issues)
        assert any("cp .env.example .env" in issue for issue in issues)

    def test_check_environment_config_detects_missing_keys(self, diagnose_commands, tmp_path):
        """Test environment config check detects missing required keys."""
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_ENVIRONMENT=development\n")

        check_name, passed, issues = diagnose_commands._check_environment_config()

        assert passed is False
        assert any("HIVE_API_PORT" in issue for issue in issues)
        assert any("HIVE_DATABASE_URL" in issue for issue in issues)
        assert any("HIVE_API_KEY" in issue for issue in issues)

    def test_check_environment_config_detects_placeholder_values(self, diagnose_commands, tmp_path):
        """Test environment config check detects placeholder values."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8886
HIVE_DATABASE_URL=your-database-url-here
HIVE_API_KEY=your-api-key-here
""")

        check_name, passed, issues = diagnose_commands._check_environment_config()

        assert passed is False
        assert any("placeholder" in issue.lower() for issue in issues)


class TestAPIKeysCheck:
    """Test API keys validation."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_check_api_keys_passes_with_valid_key(self, diagnose_commands):
        """Test API keys check passes when valid key configured."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-api03-abcdef1234567890"}):
            check_name, passed, issues = diagnose_commands._check_api_keys()

            assert check_name == "API Keys"
            assert passed is True
            # Should have warning about found keys
            assert any("ANTHROPIC_API_KEY" in issue for issue in issues)

    def test_check_api_keys_fails_without_any_keys(self, diagnose_commands):
        """Test API keys check fails when no keys configured."""
        with patch.dict("os.environ", {}, clear=True):
            check_name, passed, issues = diagnose_commands._check_api_keys()

            assert passed is False
            assert any("No AI provider API keys" in issue for issue in issues)

    def test_check_api_keys_ignores_placeholder_values(self, diagnose_commands):
        """Test API keys check ignores placeholder values."""
        # Save original values
        provider_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"]
        original_values = {key: os.environ.get(key) for key in provider_keys}

        try:
            # Clear all keys and set only placeholder
            for key in provider_keys:
                if key in os.environ:
                    del os.environ[key]
            os.environ["ANTHROPIC_API_KEY"] = "your-key-here"

            check_name, passed, issues = diagnose_commands._check_api_keys()
            assert passed is False
        finally:
            # Restore original values
            for key in provider_keys:
                if key in os.environ:
                    del os.environ[key]
                if original_values[key] is not None:
                    os.environ[key] = original_values[key]


class TestDiagnoseInstallation:
    """Test comprehensive diagnose_installation method."""

    @pytest.fixture
    def diagnose_commands(self, tmp_path):
        """Create DiagnoseCommands instance."""
        return DiagnoseCommands(workspace_path=tmp_path)

    def test_diagnose_installation_returns_true_when_all_pass(self, diagnose_commands, tmp_path):
        """Test diagnose_installation returns True when all checks pass."""
        # Setup complete valid workspace
        (tmp_path / "ai" / "agents").mkdir(parents=True)
        (tmp_path / "ai" / "teams").mkdir(parents=True)
        (tmp_path / "ai" / "workflows").mkdir(parents=True)
        (tmp_path / "knowledge").mkdir(parents=True)

        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        (docker_main / "docker-compose.yml").write_text("""
version: '3.8'
services:
  hive-postgres:
    image: postgres:15
""")
        (docker_main / "Dockerfile").write_text("FROM python:3.12")

        (tmp_path / ".env").write_text("""
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/db
HIVE_API_KEY=hive_1234567890abcdef1234567890abcdef
""")

        # Mock Docker and PostgreSQL checks
        with patch("subprocess.run") as mock_run:

            def docker_side_effect(*args, **kwargs):
                command = args[0] if args else []
                if "ps" in command and "--filter" in command:
                    return MagicMock(returncode=0, stdout="Up 5 minutes", text=True)
                return MagicMock(returncode=0)

            mock_run.side_effect = docker_side_effect

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-valid-key"}):
                result = diagnose_commands.diagnose_installation()

        assert result is True

    def test_diagnose_installation_returns_false_with_failures(self, diagnose_commands):
        """Test diagnose_installation returns False when checks fail."""
        result = diagnose_commands.diagnose_installation()
        assert result is False

    def test_diagnose_installation_shows_all_issues(self, diagnose_commands):
        """Test diagnose_installation shows all issues, not just first."""
        with patch("builtins.print") as mock_print:
            diagnose_commands.diagnose_installation()

            print_calls = [str(call) for call in mock_print.call_args_list]
            output = " ".join(print_calls)

            # Should show multiple check categories
            assert "Workspace Structure" in output
            assert "Docker Configuration" in output
            assert "Environment Config" in output

    def test_diagnose_installation_provides_next_steps_on_success(self, diagnose_commands, tmp_path):
        """Test diagnose_installation provides next steps when successful."""
        # Setup complete workspace
        (tmp_path / "ai" / "agents").mkdir(parents=True)
        (tmp_path / "ai" / "teams").mkdir(parents=True)
        (tmp_path / "ai" / "workflows").mkdir(parents=True)
        (tmp_path / "knowledge").mkdir(parents=True)

        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        (docker_main / "docker-compose.yml").write_text("""
version: '3.8'
services:
  hive-postgres:
    image: postgres:15
""")
        (docker_main / "Dockerfile").write_text("FROM python:3.12")

        (tmp_path / ".env").write_text("""
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/db
HIVE_API_KEY=hive_1234567890abcdef1234567890abcdef
""")

        with patch("subprocess.run") as mock_run:

            def docker_side_effect(*args, **kwargs):
                command = args[0] if args else []
                if "ps" in command and "--filter" in command:
                    return MagicMock(returncode=0, stdout="Up 5 minutes", text=True)
                return MagicMock(returncode=0)

            mock_run.side_effect = docker_side_effect

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-valid"}):
                with patch("builtins.print") as mock_print:
                    diagnose_commands.diagnose_installation()

                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls)

                    assert "Next steps" in output
                    assert "automagik-hive dev" in output

    def test_diagnose_installation_verbose_shows_warnings(self, diagnose_commands, tmp_path):
        """Test diagnose_installation verbose mode shows warnings."""
        # Setup valid workspace
        (tmp_path / "ai" / "agents").mkdir(parents=True)
        (tmp_path / "ai" / "teams").mkdir(parents=True)
        (tmp_path / "ai" / "workflows").mkdir(parents=True)
        (tmp_path / "knowledge").mkdir(parents=True)

        docker_main = tmp_path / "docker" / "main"
        docker_main.mkdir(parents=True)
        (docker_main / "docker-compose.yml").write_text("""
version: '3.8'
services:
  hive-postgres:
    image: postgres:15
""")
        (docker_main / "Dockerfile").write_text("FROM python:3.12")

        (tmp_path / ".env").write_text("""
HIVE_ENVIRONMENT=development
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/db
HIVE_API_KEY=hive_1234567890abcdef1234567890abcdef
""")

        with patch("subprocess.run") as mock_run:

            def docker_side_effect(*args, **kwargs):
                command = args[0] if args else []
                if "ps" in command and "--filter" in command:
                    return MagicMock(returncode=0, stdout="Up 5 minutes", text=True)
                return MagicMock(returncode=0)

            mock_run.side_effect = docker_side_effect

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-valid"}):
                with patch("builtins.print") as mock_print:
                    diagnose_commands.diagnose_installation(verbose=True)

                    print_calls = [str(call) for call in mock_print.call_args_list]
                    output = " ".join(print_calls)

                    # Verbose should show API key info
                    assert "ℹ️" in output or "ANTHROPIC_API_KEY" in output
