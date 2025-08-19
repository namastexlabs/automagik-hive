"""Integration test suite for current CLI health system.

Tests the current health system based on AgentEnvironment and HealthChecker
from the cli.commands.health and cli.core.agent_environment modules.
"""

import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

from cli.commands.health import HealthChecker
from cli.core.agent_environment import AgentEnvironment, ServiceHealth


class TestServiceHealth:
    """Test ServiceHealth dataclass functionality."""

    def test_service_health_creation(self):
        """Test basic ServiceHealth creation and fields."""
        health = ServiceHealth(
            name="test-service",
            running=True,
            healthy=True,
            container_id="container_123",
        )

        assert health.name == "test-service"
        assert health.running is True
        assert health.healthy is True
        assert health.container_id == "container_123"

    def test_service_health_defaults(self):
        """Test ServiceHealth with default values."""
        health = ServiceHealth(
            name="test-service",
            running=False,
            healthy=False,
        )

        assert health.name == "test-service"
        assert health.running is False
        assert health.healthy is False
        assert health.container_id is None


class TestHealthChecker:
    """Tests for current HealthChecker class."""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance for testing."""
        return HealthChecker()

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create temporary workspace for testing."""
        return tmp_path

    def test_health_checker_initialization(self, health_checker):
        """Test HealthChecker initialization."""
        assert health_checker.workspace_path is not None
        assert hasattr(health_checker, 'check_health')
        assert hasattr(health_checker, 'execute')
        assert hasattr(health_checker, 'status')

    def test_health_checker_initialization_with_workspace(self, temp_workspace):
        """Test HealthChecker initialization with workspace path."""
        health_checker = HealthChecker(workspace_path=temp_workspace)
        assert health_checker.workspace_path == temp_workspace

    def test_check_health_default(self, health_checker):
        """Test check_health with no component specified."""
        result = health_checker.check_health()
        assert isinstance(result, bool)

    def test_check_health_with_component(self, health_checker):
        """Test check_health with specific component."""
        result = health_checker.check_health("agent")
        assert isinstance(result, bool)

    def test_execute_method(self, health_checker):
        """Test execute method delegation."""
        result = health_checker.execute()
        assert isinstance(result, bool)

    def test_status_method(self, health_checker):
        """Test status method returns proper format."""
        status = health_checker.status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "healthy" in status


class TestAgentEnvironment:
    """Tests for AgentEnvironment class."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create temporary workspace for testing."""
        return tmp_path

    @pytest.fixture
    def agent_env(self, temp_workspace):
        """Create AgentEnvironment instance for testing."""
        return AgentEnvironment(workspace_path=temp_workspace)

    def test_agent_environment_initialization(self, agent_env, temp_workspace):
        """Test AgentEnvironment initialization."""
        assert agent_env.workspace_path == temp_workspace
        assert agent_env.env_example_path == temp_workspace / ".env.example"
        assert agent_env.main_env_path == temp_workspace / ".env"

    def test_ensure_main_env_from_example(self, agent_env, temp_workspace):
        """Test ensure_main_env creates from example."""
        # Create .env.example
        example_content = "TEST_VAR=example_value\n"
        agent_env.env_example_path.write_text(example_content)
        
        # Ensure main env gets created
        result = agent_env.ensure_main_env()
        
        assert result is True
        assert agent_env.main_env_path.exists()
        assert agent_env.main_env_path.read_text() == example_content

    def test_ensure_main_env_already_exists(self, agent_env):
        """Test ensure_main_env when main env already exists."""
        # Create main .env
        main_content = "EXISTING_VAR=existing_value\n"
        agent_env.main_env_path.write_text(main_content)
        
        result = agent_env.ensure_main_env()
        
        assert result is True
        assert agent_env.main_env_path.read_text() == main_content

    @patch("subprocess.run")
    def test_validate_environment_missing_env(self, mock_subprocess, agent_env):
        """Test validate_environment when .env file is missing."""
        result = agent_env.validate_environment()
        
        assert result["valid"] is False
        assert any("not found" in error for error in result["errors"])

    @patch("subprocess.run")
    def test_validate_environment_valid_setup(self, mock_subprocess, agent_env):
        """Test validate_environment with valid setup."""
        # Create valid .env file
        env_content = "HIVE_API_KEY=test_key\nHIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/test\n"
        agent_env.main_env_path.write_text(env_content)
        
        # Create docker-compose.yml
        compose_dir = agent_env.workspace_path / "docker" / "agent"
        compose_dir.mkdir(parents=True)
        compose_file = compose_dir / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  agent-postgres:\n    image: postgres\n")
        
        # Mock container health checks
        mock_subprocess.return_value = Mock(returncode=0, stdout="container123")
        
        result = agent_env.validate_environment()
        
        assert result["valid"] is True
        assert "HIVE_API_KEY" in result["config"]

    @patch("subprocess.run")
    def test_get_service_health(self, mock_subprocess, agent_env):
        """Test get_service_health method."""
        # Create docker-compose.yml
        compose_dir = agent_env.workspace_path / "docker" / "agent"
        compose_dir.mkdir(parents=True)
        compose_file = compose_dir / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  agent-postgres:\n    image: postgres\n")
        
        # Mock container health checks
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="container123"),  # ps call
            Mock(returncode=0, stdout="true"),          # inspect call
            Mock(returncode=0, stdout="container456"),  # ps call
            Mock(returncode=0, stdout="true"),          # inspect call
        ]
        
        health = agent_env.get_service_health()
        
        assert isinstance(health, dict)
        assert "agent-postgres" in health
        assert "agent-api" in health
        
        for service_health in health.values():
            assert isinstance(service_health, ServiceHealth)

    @patch("subprocess.run")
    def test_container_operations(self, mock_subprocess, agent_env):
        """Test container start/stop/restart operations."""
        # Create docker-compose.yml
        compose_dir = agent_env.workspace_path / "docker" / "agent"
        compose_dir.mkdir(parents=True)
        compose_file = compose_dir / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\nservices:\n  agent-postgres:\n    image: postgres\n")
        
        # Mock successful operations
        mock_subprocess.return_value = Mock(returncode=0)
        
        # Test start
        assert agent_env.start_containers() is True
        
        # Test stop
        assert agent_env.stop_containers() is True
        
        # Test restart
        assert agent_env.restart_containers() is True

    def test_update_environment(self, agent_env):
        """Test update_environment method."""
        # Create initial .env file
        initial_content = "EXISTING_VAR=old_value\nKEEP_VAR=keep_value\n"
        agent_env.main_env_path.write_text(initial_content)
        
        # Update with new values
        updates = {
            "EXISTING_VAR": "new_value",
            "NEW_VAR": "new_value"
        }
        
        result = agent_env.update_environment(updates)
        
        assert result is True
        
        # Check updated content
        updated_content = agent_env.main_env_path.read_text()
        assert "EXISTING_VAR=new_value" in updated_content
        assert "KEEP_VAR=keep_value" in updated_content
        assert "NEW_VAR=new_value" in updated_content


class TestHealthSystemIntegration:
    """Integration tests for health system components."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create temporary workspace for testing."""
        return tmp_path

    def test_health_checker_agent_environment_integration(self, temp_workspace):
        """Test integration between HealthChecker and AgentEnvironment."""
        # Create health checker with workspace
        health_checker = HealthChecker(workspace_path=temp_workspace)
        
        # Create agent environment with same workspace
        agent_env = AgentEnvironment(workspace_path=temp_workspace)
        
        # Both should use the same workspace
        assert health_checker.workspace_path == agent_env.workspace_path

    def test_health_check_with_missing_environment(self, temp_workspace):
        """Test health check behavior when environment is not set up."""
        health_checker = HealthChecker(workspace_path=temp_workspace)
        
        # Health check should handle missing environment gracefully
        result = health_checker.check_health("agent")
        assert isinstance(result, bool)

    def test_end_to_end_health_workflow(self, temp_workspace):
        """Test complete health check workflow."""
        # Set up environment
        agent_env = AgentEnvironment(workspace_path=temp_workspace)
        
        # Create .env.example
        example_content = "HIVE_API_KEY=test_key\nHIVE_DATABASE_URL=postgresql://test:test@localhost:5432/test\n"
        agent_env.env_example_path.write_text(example_content)
        
        # Ensure main env
        agent_env.ensure_main_env()
        
        # Run health check
        health_checker = HealthChecker(workspace_path=temp_workspace)
        result = health_checker.check_health()
        
        # Should complete without error
        assert isinstance(result, bool)