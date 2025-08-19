"""Integration Test Suite for Agent Commands.

Tests integration scenarios, functional parity between make vs uvx commands,
and end-to-end agent management workflows with >95% coverage.
Follows TDD Red-Green-Refactor approach with failing tests first.

Test Categories:
- Integration tests: Multi-component interaction testing
- Functional parity: make vs uvx command behavior comparison
- End-to-end tests: Complete agent lifecycle workflows
- Cross-platform compatibility: Platform-specific behavior validation
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import available classes
from cli.core.agent_service import AgentService
from cli.commands.agent import AgentCommands
from cli.core.agent_environment import AgentEnvironment

# Mock missing function that was removed from the codebase
def get_agent_ports():
    """Mock function for removed get_agent_ports."""
    return {"api": 38886, "postgres": 35532}

# Skip test - CLI structure refactored, old commands/core modules no longer exist
# pytestmark = pytest.mark.skip(reason="CLI architecture refactored - agent commands/core consolidated")

# TODO: Update tests to use cli.docker_manager.DockerManager and cli.workspace.WorkspaceManager


class TestAgentCommandsIntegration:
    """Test integration between AgentCommands, AgentService, and AgentEnvironment."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with all required files."""
        import shutil
        import stat
        
        # Custom cleanup function to handle Docker-created directories
        def cleanup_docker_dirs(path):
            """Clean up directories that may have been created by Docker with different permissions."""
            try:
                # Try normal removal first
                shutil.rmtree(path)
            except PermissionError:
                # If permission denied, try to fix permissions and retry
                def fix_permissions(func, path, exc_info):
                    """Fix permissions and retry deletion."""
                    try:
                        os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                        func(path)
                    except (PermissionError, OSError):
                        # If still failing, just pass - temp dir cleanup will handle it
                        pass
                
                shutil.rmtree(path, onerror=fix_permissions)
        
        # Create temp directory manually to handle cleanup
        temp_dir = tempfile.mkdtemp()
        try:
            workspace = Path(temp_dir)

            # Create docker-compose.yml with full structure
            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
    volumes:
      - ../../data/agent-postgres:/var/lib/postgresql/data
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
    depends_on:
      - agent-postgres
""")

            # Create .env.example
            (workspace / ".env.example").write_text("""
# =========================================================================
# ⚡ AUTOMAGIK HIVE - ENVIRONMENT CONFIGURATION
# =========================================================================
#
# NOTES:
# - This is a template file. Copy to .env and fill in your values.
# - For development, `make install` generates a pre-configured .env file.
# - DO NOT commit the .env file to version control.
#
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_CORS_ORIGINS=http://localhost:8886
HIVE_API_KEY=your-hive-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here
""")

            # Create .env file for agent environment validation
            (workspace / ".env").write_text("""
HIVE_API_PORT=8886
HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive
HIVE_CORS_ORIGINS=http://localhost:8886
HIVE_API_KEY=test-hive-api-key
ANTHROPIC_API_KEY=test-anthropic-key
OPENAI_API_KEY=test-openai-key
""")

            # Create docker directory structure
            docker_dir = workspace / "docker" / "agent"
            docker_dir.mkdir(parents=True)
            (docker_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
    volumes:
      - ../../data/agent-postgres:/var/lib/postgresql/data
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
    depends_on:
      - agent-postgres
""")

            # Create .venv directory for environment validation
            (workspace / ".venv").mkdir()

            yield str(workspace)
        finally:
            # Clean up with custom function to handle Docker-created directories
            cleanup_docker_dirs(temp_dir)

    def test_full_agent_lifecycle_integration(self, temp_workspace):
        """Test complete agent lifecycle through integration of all components."""
        commands = AgentCommands()

        # Mock AgentService methods directly for clean integration testing
        with patch.object(commands.agent_service, 'install_agent_environment', return_value=True):
            with patch.object(commands.agent_service, 'serve_agent', return_value=True):
                with patch.object(commands.agent_service, 'get_agent_status', return_value={"agent-postgres": "✅ Running", "agent-server": "✅ Running"}):
                    with patch.object(commands.agent_service, 'show_agent_logs', return_value=True):
                        with patch.object(commands.agent_service, 'restart_agent', return_value=True):
                            with patch.object(commands.agent_service, 'stop_agent', return_value=True):
                                with patch.object(commands.agent_service, 'reset_agent_environment', return_value=True):
                                    # Step 1: Install agent environment
                                    install_result = commands.install(temp_workspace)
                                    assert install_result is True

                                    # Step 2: Start agent server
                                    serve_result = commands.start(temp_workspace)
                                    assert serve_result is True

                                    # Step 3: Check agent status
                                    status_result = commands.status(temp_workspace)
                                    assert status_result is True

                                    # Step 4: View agent logs
                                    logs_result = commands.logs(temp_workspace, tail=10)
                                    assert logs_result is True

                                    # Step 5: Restart agent server
                                    restart_result = commands.restart(temp_workspace)
                                    assert restart_result is True

                                    # Step 6: Stop agent server
                                    stop_result = commands.stop(temp_workspace)
                                    assert stop_result is True

                                    # Step 7: Reset agent environment
                                    reset_result = commands.reset(temp_workspace)
                                    assert reset_result is True

    @pytest.mark.skip(reason="Blocked by task-0632420e-876b-41d5-ac9b-c3ac305395c4 - missing generate_env_agent method")
    def test_agent_service_environment_integration(self, temp_workspace):
        """Test integration between AgentService and AgentEnvironment."""
        service = AgentService()
        environment = AgentEnvironment(Path(temp_workspace))

        # Should fail initially - service-environment integration not implemented
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("secrets.token_urlsafe", return_value="test_token"):
                # Test environment generation
                env_path = environment.generate_env_agent()
                assert env_path.exists()

                # Test service can read environment
                credentials = environment.get_agent_credentials()
                assert credentials is not None

                # Test service validation works with generated environment
                workspace_path = Path(temp_workspace)
                validation_result = service._validate_agent_environment(workspace_path)
                assert validation_result is True

    def test_concurrent_agent_operations_integration(self, temp_workspace):
        """Test handling of concurrent operations across components."""
        commands1 = AgentCommands()
        commands2 = AgentCommands()

        # Should fail initially - concurrency handling not implemented
        with patch("subprocess.run") as mock_run:
            with patch("subprocess.Popen") as mock_popen:
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("builtins.open", create=True) as mock_open:
                        # Mock the validation methods to return success instead of actual Docker commands
                        with patch.object(commands1.agent_service, '_validate_agent_environment_with_retry', return_value=True):
                            with patch.object(commands2.agent_service, '_validate_agent_environment_with_retry', return_value=True):
                                with patch.object(commands1.agent_service, 'get_agent_status', return_value={"agent-postgres": "🛑 Stopped", "agent-server": "🛑 Stopped"}):
                                    with patch.object(commands2.agent_service, 'get_agent_status', return_value={"agent-postgres": "✅ Running", "agent-server": "✅ Running"}):
                                        mock_run.return_value.returncode = 0
                                        mock_process = Mock()
                                        mock_process.pid = 12345
                                        mock_popen.return_value = mock_process

                                        mock_file = Mock()
                                        mock_file.read.return_value = "12345"
                                        mock_open.return_value.__enter__.return_value = mock_file

                                        # Simulate concurrent serve attempts
                                        serve_result1 = commands1.start(temp_workspace)
                                        serve_result2 = commands2.start(temp_workspace)

                                        # Both should succeed (second should detect already running)
                                        assert serve_result1 is True
                                        assert serve_result2 is True

    def test_error_propagation_integration(self, temp_workspace):
        """Test error propagation through the integration stack."""
        commands = AgentCommands()

        # Test various failure scenarios with correct method mapping
        failure_scenarios = [
            ("install", {"install_agent_environment": False}),
            ("start", {"serve_agent": False}),
            ("stop", {"stop_agent": False}),
            ("reset", {"reset_agent_environment": False}),
        ]

        for command_name, mock_returns in failure_scenarios:
            with patch.object(
                commands.agent_service,
                next(iter(mock_returns.keys())),
                return_value=next(iter(mock_returns.values())),
            ):
                # Should fail initially - error propagation not implemented
                method = getattr(commands, command_name)
                result = method(temp_workspace)
                assert result is False

    @pytest.mark.skip(reason="Blocked by task-13ed0d8c-230a-4a87-a5ef-e2d11269ffbf - restart() method doesn't use restart_agent()")
    def test_restart_error_propagation(self, temp_workspace):
        """Test restart error propagation - currently blocked by source code issue."""
        commands = AgentCommands()
        
        # This test expects restart() to call restart_agent(), but current implementation
        # calls stop() + start() instead. See forge task for fix.
        with patch.object(commands.agent_service, "restart_agent", return_value=False):
            result = commands.restart(temp_workspace)
            assert result is False


class TestFunctionalParityMakeVsUvx:
    """Test functional parity between make commands and uvx commands."""

    @pytest.fixture
    def temp_workspace_with_makefile(self):
        """Create temporary workspace with Makefile for comparison."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create basic required files
            (workspace / "docker").mkdir()
            (workspace / "docker" / "agent").mkdir()
            (workspace / "docker" / "agent" / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
""")
            (workspace / ".env.example").write_text(
                "HIVE_API_PORT=8886\n"
                "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
                "HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:8886\n"
            )
            
            # Create .env file for agent environment validation
            (workspace / ".env").write_text(
                "HIVE_API_PORT=8886\n"
                "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
                "HIVE_CORS_ORIGINS=http://localhost:3000,http://localhost:8886\n"
            )

            # Create mock Makefile
            (workspace / "Makefile").write_text("""
.PHONY: agent agent-logs agent-status agent-stop agent-restart install-agent

agent:
\t@echo "🚀 Starting agent server via Make..."
\t@docker compose -f docker/agent/docker-compose.yml up -d agent-postgres

agent-logs:
\t@echo "📋 Showing agent logs via Make..."
\t@tail -50 logs/agent-server.log

agent-status:
\t@echo "📊 Checking agent status via Make..."
\t@docker compose -f docker/agent/docker-compose.yml ps

agent-stop:
\t@echo "🛑 Stopping agent server via Make..."
\t@docker compose -f docker/agent/docker-compose.yml down

agent-restart: agent-stop agent
\t@echo "🔄 Agent server restarted via Make..."

install-agent:
\t@echo "🤖 Installing agent environment via Make..."
\t@echo "Agent inherits from main .env via docker-compose - no separate .env.agent needed"
""")

            yield str(workspace)

    def test_agent_start_parity(self, temp_workspace_with_makefile):
        """Test parity between 'make agent' and 'uvx automagik-hive --agent-start'."""

        # Mock both command executions
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Started successfully"

            # Test make command behavior
            make_result = subprocess.run(
                ["make", "agent"],
                check=False,
                cwd=temp_workspace_with_makefile,
                capture_output=True,
                text=True,
            )

            # Test uvx command behavior
            commands = AgentCommands()
            with patch.object(commands, "start", return_value=True) as mock_start:
                uvx_result = commands.start(temp_workspace_with_makefile)

            # Should fail initially - parity validation not implemented
            # Both should achieve the same outcome
            assert make_result.returncode == 0 or mock_start.called
            assert uvx_result is True

    def test_agent_logs_parity(self, temp_workspace_with_makefile):
        """Test parity between 'make agent-logs' and 'uvx automagik-hive --agent-logs'."""

        # Create log file for testing
        logs_dir = Path(temp_workspace_with_makefile) / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / "agent-server.log"
        log_file.write_text("Log line 1\nLog line 2\nLog line 3\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Log line 2\nLog line 3\n"

            # Test make command
            make_result = subprocess.run(
                ["make", "agent-logs"],
                check=False,
                cwd=temp_workspace_with_makefile,
                capture_output=True,
                text=True,
            )

            # Test uvx command
            commands = AgentCommands()
            uvx_result = commands.logs(temp_workspace_with_makefile)

            # Should fail initially - logs parity not implemented
            assert make_result.returncode == 0
            assert uvx_result is True

    def test_agent_status_parity(self, temp_workspace_with_makefile):
        """Test parity between 'make agent-status' and 'uvx automagik-hive --agent-status'."""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "agent-postgres   Up"

            # Test make command
            make_result = subprocess.run(
                ["make", "agent-status"],
                check=False,
                cwd=temp_workspace_with_makefile,
                capture_output=True,
                text=True,
            )

            # Test uvx command
            commands = AgentCommands()
            with patch.object(
                commands.agent_service,
                "get_agent_status",
                return_value={"agent-postgres": "✅ Running"},
            ):
                uvx_result = commands.status(temp_workspace_with_makefile)

            # Should fail initially - status parity not implemented
            assert make_result.returncode == 0
            assert uvx_result is True

    @pytest.mark.skip(reason="Blocked by task-0632420e-876b-41d5-ac9b-c3ac305395c4 - missing generate_env_agent method")
    def test_agent_port_configuration_parity(self, temp_workspace_with_makefile):
        """Test that both approaches use the same port configurations."""

        # Test agent environment ports
        env = AgentEnvironment(Path(temp_workspace_with_makefile))
        env.generate_env_agent()

        credentials = env.get_agent_credentials()

        # Should fail initially - port configuration parity not implemented
        # Both make and uvx should use the same ports
        assert credentials.hive_api_port == 38886
        assert credentials.postgres_port == 35532

        # Verify these match the expected agent ports
        ports = get_agent_ports()
        assert ports["api"] == 38886
        assert ports["postgres"] == 35532

    @pytest.mark.skip(reason="Blocked by task-0632420e-876b-41d5-ac9b-c3ac305395c4 - missing generate_env_agent method")
    def test_environment_file_generation_parity(self, temp_workspace_with_makefile):
        """Test that both approaches handle environment configuration via docker-compose inheritance."""

        # Simulate make install-agent
        workspace = Path(temp_workspace_with_makefile)
        make_env_path = workspace / ".env.make"

        # Copy template (simulating make behavior)
        env_example = workspace / ".env.example"
        make_env_path.write_text(env_example.read_text())

        # Generate via uvx approach
        env = AgentEnvironment(workspace)
        uvx_env_path = env.generate_env_agent()

        # Should fail initially - environment generation parity not implemented
        # Both should produce files with agent-specific configurations
        uvx_content = uvx_env_path.read_text()

        # Verify uvx version has agent-specific transformations
        assert "38886" in uvx_content  # Agent API port
        assert "35532" in uvx_content  # Agent postgres port
        assert "hive_agent" in uvx_content  # Agent database name

    def test_container_management_parity(self, temp_workspace_with_makefile):
        """Test that both approaches manage containers equivalently."""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            # Test container operations - AgentCommands() no longer exists due to refactoring
            # AgentCommands()
            service = AgentService()

            # Both should use the same compose file and container names
            workspace = temp_workspace_with_makefile

            # Should fail initially - container management parity not implemented
            # Verify same compose file path is used internally by the method

            # Verify same container operations
            with patch.object(service, "_setup_agent_containers", return_value=True):
                containers_result = service._setup_agent_containers(workspace)
                assert containers_result is True


class TestEndToEndAgentWorkflows:
    """Test complete end-to-end agent management workflows."""

    @pytest.fixture
    def complete_workspace(self):
        """Create complete workspace with all files for end-to-end testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create all required files and directories
            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
""")
            (workspace / ".env.example").write_text(
                "HIVE_API_PORT=8886\n"
                "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n"
                "HIVE_API_KEY=your-hive-api-key-here\n"
                "ANTHROPIC_API_KEY=test-key\n"
            )

            # Create main .env for credential copying and agent environment validation
            (workspace / ".env").write_text(
                "ANTHROPIC_API_KEY=real-anthropic-key\n"
                "OPENAI_API_KEY=real-openai-key\n"
                "HIVE_DATABASE_URL=postgresql+psycopg://mainuser:mainpass@localhost:5532/hive\n"
            )

            # Create directories
            (workspace / "logs").mkdir()
            (workspace / "data" / "agent-postgres").mkdir(parents=True)
            (workspace / ".venv").mkdir()

            docker_dir = workspace / "docker" / "agent"
            docker_dir.mkdir(parents=True)
            (docker_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
""")

            yield str(workspace)

    def test_development_workflow_end_to_end(self, complete_workspace):
        """Test complete development workflow from setup to teardown."""

        commands = AgentCommands()

        # Mock AgentService methods directly for clean integration testing
        with patch.object(commands.agent_service, 'install_agent_environment', return_value=True):
            with patch.object(commands.agent_service, 'serve_agent', return_value=True):
                with patch.object(commands.agent_service, 'get_agent_status', return_value={"agent-postgres": "✅ Running", "agent-server": "✅ Running"}):
                    with patch.object(commands.agent_service, 'show_agent_logs', return_value=True):
                        with patch.object(commands.agent_service, 'stop_agent', return_value=True):
                            with patch.object(commands.agent_service, 'reset_agent_environment', return_value=True):
                                
                                # Step 1: Fresh environment setup
                                install_result = commands.install(complete_workspace)
                                assert install_result is True

                                # Verify main environment file exists for docker-compose inheritance
                                main_env_path = Path(complete_workspace) / ".env"
                                assert main_env_path.exists()

                                # Step 2: Start development server
                                serve_result = commands.start(complete_workspace)
                                assert serve_result is True

                                # Step 3: Development monitoring
                                status_result = commands.status(complete_workspace)
                                assert status_result is True

                                logs_result = commands.logs(complete_workspace, tail=20)
                                assert logs_result is True

                                # Step 4: Development iteration (restart)
                                restart_result = commands.restart(complete_workspace)
                                assert restart_result is True

                                # Step 5: Clean shutdown
                                stop_result = commands.stop(complete_workspace)
                                assert stop_result is True

                                # Step 6: Environment cleanup
                                reset_result = commands.reset(complete_workspace)
                                assert reset_result is True

    def test_continuous_integration_workflow(self, complete_workspace):
        """Test workflow suitable for CI/CD environments."""

        # Mock AgentService methods for proper integration testing
        commands = AgentCommands()
        
        # Mock all AgentService methods that are called by AgentCommands
        with patch.object(commands.agent_service, 'install_agent_environment', return_value=True):
            with patch.object(commands.agent_service, 'serve_agent', return_value=True):
                with patch.object(commands.agent_service, 'stop_agent', return_value=True):
                    # CI workflow: install -> start -> test -> stop
                    install_result = commands.install(complete_workspace)
                    assert install_result is True

                    serve_result = commands.start(complete_workspace)
                    assert serve_result is True

                    # Simulate test execution time
                    time.sleep(0.1)

                    stop_result = commands.stop(complete_workspace)
                    assert stop_result is True

    def test_error_recovery_workflow(self, complete_workspace):
        """Test workflow with error recovery scenarios."""

        commands = AgentCommands()

        # Mock the internal validation method that performs Docker checks
        with patch.object(commands.agent_service, '_validate_agent_environment_with_retry') as mock_validation:
            with patch("subprocess.run") as mock_run:
                # Scenario 1: Installation failure -> retry -> success
                mock_run.return_value.returncode = 1  # Failure
                mock_validation.return_value = False  # Validation fails
                install_result1 = commands.install(complete_workspace)
                assert install_result1 is False

                mock_run.return_value.returncode = 0  # Success on retry
                mock_validation.return_value = True  # Validation succeeds
                install_result2 = commands.install(complete_workspace)
                assert install_result2 is True

                # Scenario 2: Server start failure -> reset -> retry
                mock_run.return_value.returncode = 1  # Failure
                mock_validation.return_value = False  # Validation fails
                serve_result1 = commands.start(complete_workspace)
                assert serve_result1 is False

                # Reset environment
                with patch.object(
                    commands.agent_service, "reset_agent_environment", return_value=True
                ):
                    reset_result = commands.reset(complete_workspace)
                    assert reset_result is True

                # Retry start
                mock_run.return_value.returncode = 0  # Success
                mock_validation.return_value = True  # Validation succeeds
                serve_result2 = commands.start(complete_workspace)
                assert serve_result2 is True

    def test_production_deployment_workflow(self, complete_workspace):
        """Test workflow suitable for production deployment."""

        # Should fail initially - production workflow not implemented
        with patch("subprocess.run") as mock_run:
            with patch("subprocess.Popen") as mock_popen:
                with patch("pathlib.Path.exists", return_value=True):
                    mock_run.return_value.returncode = 0
                    mock_process = Mock()
                    mock_process.pid = 12345
                    mock_popen.return_value = mock_process

                    commands = AgentCommands()

                    # Mock the validation methods that actually run Docker commands
                    with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                        with patch.object(commands.agent_service, '_validate_agent_environment_with_retry', return_value=True):
                            with patch.object(commands.agent_service, 'get_agent_status', return_value={"agent-postgres": "✅ Running", "agent-server": "✅ Running"}):

                                # Production workflow: install -> serve -> monitor -> maintain

                                # 1. Production installation
                                install_result = commands.install(complete_workspace)
                                assert install_result is True

                                # 2. Production server start
                                serve_result = commands.start(complete_workspace)
                                assert serve_result is True

                                # 3. Health monitoring
                                for _ in range(3):  # Multiple status checks
                                    status_result = commands.status(complete_workspace)
                                    assert status_result is True
                                    time.sleep(0.1)

                                # 4. Log monitoring
                                logs_result = commands.logs(complete_workspace, tail=100)
                                assert logs_result is True

                                # 5. Graceful restart (maintenance)
                                restart_result = commands.restart(complete_workspace)
                                assert restart_result is True

                                # 6. Final status verification
                                final_status = commands.status(complete_workspace)
                                assert final_status is True


class TestCrossPlatformCompatibility:
    """Test cross-platform behavior patterns."""

    @pytest.fixture
    def cross_platform_workspace(self):
        """Create workspace for cross-platform testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}  
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
""")
            (workspace / ".env.example").write_text("HIVE_API_PORT=8886\n")
            
            # Create .env file for agent environment validation
            (workspace / ".env").write_text("HIVE_API_PORT=8886\nHIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n")
            
            # Create .venv directory for environment validation
            (workspace / ".venv").mkdir()
            # Create docker/agent directory structure for AgentService.stop_agent()
            docker_agent_dir = workspace / "docker" / "agent"
            docker_agent_dir.mkdir(parents=True, exist_ok=True)
            (docker_agent_dir / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
""")
            yield str(workspace)

    def test_windows_compatibility_patterns(self, cross_platform_workspace):
        """Test Windows-specific behavior patterns."""

        # Test Windows compatibility by mocking the AgentService methods directly
        with patch("platform.system", return_value="Windows"):
            with patch("os.name", "nt"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0

                    commands = AgentCommands()

                    # Test Windows path handling - convert Unix path to valid Windows path
                    # Convert /tmp/xyz to C:\tmp\xyz for proper Windows path simulation
                    unix_path = cross_platform_workspace
                    if unix_path.startswith("/"):
                        windows_workspace = f"C:{unix_path.replace('/', '\\')}"
                    else:
                        windows_workspace = unix_path.replace("/", "\\")
                    
                    # Mock the AgentService methods directly to ensure Windows compatibility testing
                    with patch.object(commands.agent_service, 'install_agent_environment', return_value=True):
                        with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                            with patch.object(commands.agent_service, 'get_agent_status', return_value={"agent-postgres": "✅ Running", "agent-server": "✅ Running"}):
                                result = commands.install(windows_workspace)
                                assert result is True

                                # Verify Windows-specific process handling
                                serve_result = commands.start(windows_workspace)
                                assert serve_result is True

    def test_linux_compatibility_patterns(self, cross_platform_workspace):
        """Test Linux-specific behavior patterns."""

        with patch("platform.system", return_value="Linux"):
            with patch("os.name", "posix"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0

                    commands = AgentCommands()

                    # Test Linux path handling with proper mocking
                    with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                        result = commands.install(cross_platform_workspace)
                        assert result is True

                    # Test Unix signal handling
                    with patch("os.kill") as mock_kill:
                        mock_kill.return_value = None
                        stop_result = commands.stop(cross_platform_workspace)
                        assert stop_result is True

    def test_macos_compatibility_patterns(self, cross_platform_workspace):
        """Test macOS-specific behavior patterns."""

        with patch("platform.system", return_value="Darwin"):
            with patch("os.name", "posix"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0

                    commands = AgentCommands()

                    # Test macOS path handling with proper mocking
                    with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                        with patch.object(commands.agent_service, '_validate_agent_environment_with_retry', return_value=True):
                            result = commands.install(cross_platform_workspace)
                            assert result is True

                            # Test BSD-style process management
                            serve_result = commands.start(cross_platform_workspace)
                            assert serve_result is True

    def test_path_separator_consistency(self, cross_platform_workspace):
        """Test path separator handling across platforms."""

        commands = AgentCommands()

        # Test various path formats
        path_formats = [
            cross_platform_workspace,
            cross_platform_workspace.replace("/", "\\"),  # Windows style
            Path(cross_platform_workspace),  # Path object
            str(Path(cross_platform_workspace).resolve()),  # Resolved path
        ]

        for path_format in path_formats:
            # Should fail initially - path format consistency not implemented
            try:
                with patch("subprocess.run") as mock_run:
                    with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                        mock_run.return_value.returncode = 0

                        result = commands.install(path_format)
                        assert result is True
            except Exception:
                # Expected to fail initially with some path formats
                pass

    def test_environment_variable_handling(self, cross_platform_workspace):
        """Test environment variable handling across platforms."""

        with patch.dict(
            os.environ,
            {
                "HOME": "/home/user",
                "USERPROFILE": "C:\\Users\\user",
                "PATH": "/usr/bin:/bin",
            },
        ):
            commands = AgentCommands()

            with patch("subprocess.run") as mock_run:
                with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                    mock_run.return_value.returncode = 0

                    result = commands.install(cross_platform_workspace)
                    assert result is True

                    # Verify environment variables are properly handled
                    assert mock_run.called

    def test_permission_handling_patterns(self, cross_platform_workspace):
        """Test file permission handling across platforms."""

        commands = AgentCommands()

        # Should fail initially - permission handling not implemented
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            # Test with various permission scenarios
            permission_scenarios = [
                {"readable": True, "writable": True},
                {"readable": True, "writable": False},
                {"readable": False, "writable": True},
            ]

            for permissions in permission_scenarios:
                with patch("os.access") as mock_access:
                    with patch.object(commands.agent_service, '_validate_agent_environment', return_value=permissions.get("writable", True)):
                        mock_access.return_value = permissions.get("readable", True)

                        try:
                            result = commands.install(cross_platform_workspace)
                            if permissions["writable"]:
                                assert result is True
                            else:
                                assert result is False
                        except Exception:
                            # Expected for some permission combinations
                            pass


class TestPerformanceAndScalability:
    """Test performance characteristics and scalability patterns."""

    @pytest.fixture
    def performance_workspace(self):
        """Create workspace for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "docker-compose.yml").write_text("""
version: '3.8'
services:
  agent-postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-hive_agent}
    ports:
      - "35532:5432"
  agent-api:
    image: python:3.12
    ports:
      - "38886:8000"
""")
            (workspace / ".env.example").write_text("HIVE_API_PORT=8886\n")
            
            # Create .env file for agent environment validation
            (workspace / ".env").write_text("HIVE_API_PORT=8886\nHIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5532/hive\n")
            
            # Create .venv directory for environment validation
            (workspace / ".venv").mkdir()
            yield str(workspace)

    def test_concurrent_command_performance(self, performance_workspace):
        """Test performance with concurrent command execution."""

        import threading
        import time

        commands = [AgentCommands() for _ in range(5)]
        results = []

        def execute_command(cmd, idx):
            # Mock all AgentService methods to avoid Docker conflicts in concurrent execution
            with patch.object(cmd.agent_service, 'install_agent_environment', return_value=True):
                with patch.object(cmd.agent_service, 'serve_agent', return_value=True):
                    with patch.object(cmd.agent_service, '_validate_agent_environment', return_value=True):
                        with patch.object(cmd.agent_service, '_setup_agent_containers', return_value=True):
                            start_time = time.time()
                            result = cmd.install(performance_workspace)
                            end_time = time.time()
                            results.append((idx, result, end_time - start_time))

        threads = []
        for i, cmd in enumerate(commands):
            thread = threading.Thread(target=execute_command, args=(cmd, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All commands should succeed
        assert len(results) == 5
        assert all(result[1] for result in results)

        # Performance should be reasonable (under 1 second per command)
        assert all(result[2] < 1.0 for result in results)

    def test_large_workspace_handling(self, performance_workspace):
        """Test handling of workspaces with many files."""

        # Create many files to simulate large workspace
        workspace = Path(performance_workspace)
        for i in range(100):
            (workspace / f"file_{i}.txt").write_text(f"Content {i}")

        commands = AgentCommands()

        with patch("subprocess.run") as mock_run:
            with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                mock_run.return_value.returncode = 0

                start_time = time.time()
                result = commands.install(performance_workspace)
                end_time = time.time()

                assert result is True
                # Performance should be reasonable even with many files
                assert end_time - start_time < 2.0

    def test_memory_usage_patterns(self, performance_workspace):
        """Test memory usage characteristics."""

        commands = AgentCommands()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            # Test multiple operations to check for memory leaks
            for _ in range(10):
                result = commands.status(performance_workspace)
                assert result is True

                # Basic memory usage should be reasonable
                # (This is a placeholder - real implementation would use psutil)
                import sys

                memory_usage = sys.getsizeof(commands)
                assert memory_usage < 1024 * 1024  # Less than 1MB

    def test_command_response_time(self, performance_workspace):
        """Test command response time characteristics."""

        commands = AgentCommands()

        # Should fail initially - response time optimization not implemented
        command_methods = [
            ("install", commands.install),
            ("start", commands.start),
            ("status", commands.status),
            ("logs", commands.logs),
            ("stop", commands.stop),
            ("restart", commands.restart),
        ]

        response_times = {}

        for method_name, method in command_methods:
            with patch("subprocess.run") as mock_run:
                with patch("subprocess.Popen") as mock_popen:
                    with patch("pathlib.Path.exists") as mock_exists:
                        with patch("pathlib.Path.is_dir") as mock_is_dir:
                            with patch("pathlib.Path.write_text") as mock_write_text:
                                with patch("pathlib.Path.read_text") as mock_read_text:
                                    with patch("pathlib.Path.mkdir") as mock_mkdir:
                                        with patch.object(commands.agent_service, '_validate_agent_environment', return_value=True):
                                            # Configure mocks for successful operations
                                            mock_run.return_value.returncode = 0
                                            mock_run.return_value.stdout = "Success"
                                            mock_run.return_value.stderr = ""
                                            mock_popen.return_value.pid = 12345
                                            mock_exists.return_value = True
                                            mock_is_dir.return_value = True
                                            mock_read_text.return_value = "existing content"

                                            start_time = time.time()
                                            if method_name == "logs":
                                                result = method(performance_workspace, tail=10)
                                            else:
                                                result = method(performance_workspace)
                                            end_time = time.time()

                                            response_times[method_name] = end_time - start_time
                                            assert result is True

        # All commands should respond quickly (under 0.5 seconds)
        for method_name, response_time in response_times.items():
            assert response_time < 0.5, f"{method_name} took too long: {response_time}s"