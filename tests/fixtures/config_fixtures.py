"""Shared fixtures for configuration testing."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create directory structure
        (temp_path / "data").mkdir()
        (temp_path / "logs").mkdir()
        (temp_path / "ai" / "agents").mkdir(parents=True)
        (temp_path / "ai" / "teams").mkdir(parents=True)
        (temp_path / "ai" / "workflows").mkdir(parents=True)

        yield temp_path


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Mock environment variables for testing."""
    env_vars = {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_API_HOST": "localhost",
        "HIVE_API_PORT": "8888",
        "HIVE_API_WORKERS": "2",
        "HIVE_LOG_LEVEL": "DEBUG",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OPENAI_API_KEY": "test-openai-key",
        "HIVE_DATABASE_URL": "sqlite:///test.db",
        "HIVE_MAX_CONVERSATION_TURNS": "10",
        "HIVE_SESSION_TIMEOUT": "600",
        "HIVE_MAX_CONCURRENT_USERS": "50",
        "HIVE_MEMORY_RETENTION_DAYS": "7",
        "HIVE_MAX_MEMORY_ENTRIES": "500",
        "HIVE_MAX_KNOWLEDGE_RESULTS": "5",
        "HIVE_MAX_REQUEST_SIZE": "5242880",
        "HIVE_RATE_LIMIT_REQUESTS": "50",
        "HIVE_RATE_LIMIT_PERIOD": "30",
        "HIVE_TEAM_ROUTING_TIMEOUT": "15",
        "HIVE_MAX_TEAM_SWITCHES": "2",
        "HIVE_ENABLE_METRICS": "false",
        "HIVE_ENABLE_LANGWATCH": "false",
        "HIVE_METRICS_BATCH_SIZE": "25",
        "HIVE_METRICS_FLUSH_INTERVAL": "2.5",
        "HIVE_METRICS_QUEUE_SIZE": "500",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_invalid_env_vars() -> Generator[dict[str, str], None, None]:
    """Mock invalid environment variables for testing validation."""
    env_vars = {
        "HIVE_API_PORT": "99999",  # Invalid port
        "HIVE_API_WORKERS": "-1",  # Invalid worker count
        "HIVE_ENVIRONMENT": "invalid_env",  # Invalid environment
        "HIVE_LOG_LEVEL": "INVALID",  # Invalid log level
        "HIVE_METRICS_BATCH_SIZE": "999999",  # Too large
        "HIVE_METRICS_FLUSH_INTERVAL": "-1",  # Negative
        "HIVE_METRICS_QUEUE_SIZE": "5",  # Too small
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch("lib.logging.logger") as mock_log:
        yield mock_log


@pytest.fixture
def mock_dotenv():
    """Mock dotenv for testing environment loading."""
    with patch("lib.config.settings.load_dotenv") as mock_load:
        yield mock_load


@pytest.fixture
def clean_singleton():
    """Reset singleton instances between tests."""
    # Store original instances
    from lib.config.server_config import ServerConfig

    original_instance = ServerConfig._instance

    yield

    # Reset singleton
    ServerConfig._instance = original_instance


@pytest.fixture
def mock_pathlib_file_operations():
    """Mock pathlib file operations for testing."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.mkdir") as mock_mkdir,
        patch("pathlib.Path.is_dir") as mock_is_dir,
    ):
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        yield {"exists": mock_exists, "mkdir": mock_mkdir, "is_dir": mock_is_dir}


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "agent": {"name": "Test Agent", "agent_id": "test-agent", "version": "1.0.0"},
        "model": {
            "provider": "anthropic",
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.7,
        },
        "instructions": "Test instructions for the agent.",
    }


@pytest.fixture
def sample_team_config():
    """Sample team configuration for testing."""
    return {
        "team": {"name": "Test Team", "team_id": "test-team", "version": "1.0.0"},
        "mode": "route",
        "agents": ["test-agent-1", "test-agent-2"],
        "routing_logic": "default",
    }


@pytest.fixture
def sample_workflow_config():
    """Sample workflow configuration for testing."""
    return {
        "workflow": {
            "name": "Test Workflow",
            "workflow_id": "test-workflow",
            "version": "1.0.0",
        },
        "steps": [{"name": "step1", "agent": "test-agent", "action": "process"}],
    }


@pytest.fixture
def mock_yaml_operations():
    """Mock YAML operations for testing."""
    with patch("yaml.safe_load") as mock_load, patch("yaml.dump") as mock_dump:
        yield {"load": mock_load, "dump": mock_dump}


@pytest.fixture
def mock_database_url():
    """Mock database URL for testing."""
    return "postgresql+psycopg://test:test@localhost:5432/test_db"


@pytest.fixture
def mock_sqlite_url():
    """Mock SQLite URL for testing."""
    return "sqlite:///test.db"


@pytest.fixture
def configuration_test_matrix():
    """Test matrix for comprehensive configuration testing."""
    return {
        "environments": ["development", "staging", "production"],
        "ports": [8886, 3000, 80, 443],
        "worker_counts": [1, 2, 4, 8],
        "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
        "batch_sizes": [1, 50, 100, 1000, 10000],
        "flush_intervals": [0.1, 1.0, 5.0, 60.0, 3600.0],
        "queue_sizes": [10, 100, 1000, 10000, 100000],
    }
