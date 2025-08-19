"""
Configuration test fixtures for lib/config module tests.

Provides specialized fixtures for testing configuration components with proper
isolation, singleton management, and environment variable mocking.
"""

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

# Add project root to Python path to fix module import issues
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create basic project structure
        (temp_path / "data").mkdir(exist_ok=True)
        (temp_path / "logs").mkdir(exist_ok=True)
        (temp_path / "lib" / "config").mkdir(parents=True, exist_ok=True)

        yield temp_path


@pytest.fixture
def clean_singleton() -> Generator[None, None, None]:
    """Clean singleton instances before and after tests."""
    # Import here to avoid circular imports
    from lib.config.settings import HiveSettings
    Settings = HiveSettings  # Alias for compatibility

    # Clear any existing singleton instance before test
    if hasattr(Settings, "_instance"):
        Settings._instance = None

    yield

    # Clear singleton instance after test
    if hasattr(Settings, "_instance"):
        Settings._instance = None


@pytest.fixture
def mock_env_vars() -> dict[str, str]:
    """Mock environment variables for testing."""
    return {
        "HIVE_ENVIRONMENT": "development",
        "HIVE_LOG_LEVEL": "DEBUG",
        "HIVE_MAX_CONVERSATION_TURNS": "10",
        "HIVE_SESSION_TIMEOUT": "600",
        "HIVE_MAX_CONCURRENT_USERS": "50",
        "HIVE_MEMORY_RETENTION_DAYS": "7",
        "HIVE_MAX_MEMORY_ENTRIES": "500",
        "HIVE_ENABLE_METRICS": "false",
        "HIVE_ENABLE_LANGWATCH": "false",
        "HIVE_METRICS_BATCH_SIZE": "25",
        "HIVE_METRICS_FLUSH_INTERVAL": "2.5",
        "HIVE_METRICS_QUEUE_SIZE": "500",
        "HIVE_MAX_REQUEST_SIZE": "5242880",
        "HIVE_RATE_LIMIT_REQUESTS": "50",
        "HIVE_RATE_LIMIT_PERIOD": "30",
        "HIVE_TEAM_ROUTING_TIMEOUT": "15",
        "HIVE_MAX_TEAM_SWITCHES": "2",
        "HIVE_MAX_KNOWLEDGE_RESULTS": "5",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OPENAI_API_KEY": "test-openai-key",
    }


@pytest.fixture
def mock_invalid_env_vars() -> dict[str, str]:
    """Mock invalid environment variables for validation testing."""
    return {
        "HIVE_METRICS_BATCH_SIZE": "999999",  # Too high, should clamp to 10000
        "HIVE_METRICS_FLUSH_INTERVAL": "-1",  # Too low, should clamp to 0.1
        "HIVE_METRICS_QUEUE_SIZE": "5",  # Too low, should clamp to 10
    }


@pytest.fixture
def mock_logger() -> Generator[Mock, None, None]:
    """Mock logger for testing logging operations."""
    with patch("lib.logging.logger") as mock_log:
        logger_mock = Mock()
        logger_mock.warning = Mock()
        logger_mock.error = Mock()
        logger_mock.info = Mock()
        logger_mock.debug = Mock()
        mock_log.return_value = logger_mock
        yield logger_mock


@pytest.fixture
def clean_environment() -> Generator[None, None, None]:
    """Clean environment variables for isolated testing."""
    # Store original environment
    original_env = os.environ.copy()

    # Clear environment variables that might interfere with tests
    config_vars = [
        var
        for var in os.environ
        if var.startswith("HIVE_")
        or var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LANGWATCH_API_KEY"]
    ]

    for var in config_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_settings_file(temp_project_dir: Path) -> Generator[Path, None, None]:
    """Create a mock settings.py file in the temporary project directory."""
    settings_file = temp_project_dir / "lib" / "config" / "settings.py"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.touch()

    with patch("lib.config.settings.__file__", str(settings_file)):
        yield settings_file


@pytest.fixture
def isolated_settings(
    temp_project_dir: Path, clean_singleton: None, mock_settings_file: Path
) -> None:
    """Provide isolated settings environment for testing."""
    # This fixture combines temp directory, clean singleton, and mock settings file
    # for comprehensive settings isolation
    return


# Server Config specific fixtures
@pytest.fixture
def clean_server_singleton() -> Generator[None, None, None]:
    """Clean server config singleton instances before and after tests."""
    try:
        from lib.config.server_config import ServerConfig

        # Clear any existing singleton instance before test
        if hasattr(ServerConfig, "_instance"):
            ServerConfig._instance = None

        yield

        # Clear singleton instance after test
        if hasattr(ServerConfig, "_instance"):
            ServerConfig._instance = None
    except ImportError:
        # If ServerConfig doesn't exist, just yield
        yield


@pytest.fixture
def server_mock_env_vars() -> dict[str, str]:
    """Mock environment variables for server config testing."""
    return {
        "HIVE_HOST": "0.0.0.0",
        "HIVE_PORT": "8888",
        "HIVE_WORKERS": "4",
        "HIVE_ENVIRONMENT": "development",
        "HIVE_LOG_LEVEL": "INFO",
        "HIVE_RELOAD": "true",
        "HIVE_ACCESS_LOG": "true",
    }


@pytest.fixture
def mock_pathlib_file_operations() -> Generator[dict[str, Mock], None, None]:
    """Mock pathlib file operations for testing directory creation."""
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("pathlib.Path.touch") as mock_touch:
                # Configure mocks to simulate successful operations
                mock_mkdir.return_value = None
                mock_exists.return_value = True
                mock_touch.return_value = None

                yield {
                    "mkdir": mock_mkdir,
                    "exists": mock_exists,
                    "touch": mock_touch,
                }
