"""
Shared fixtures and utilities for testing lib/utils, lib/knowledge, lib/metrics, lib/logging.

This module provides common test utilities, fixtures, and helpers for all utility
component tests to ensure consistency and reduce duplication.
"""

import os
import shutil
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import yaml

# Settings import removed - using mock instead


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create and cleanup a temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file() -> Generator[Path, None, None]:
    """Create and cleanup a temporary file for tests."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_path = Path(tmp.name)
    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)


@pytest.fixture
def sample_yaml_config() -> dict[str, Any]:
    """Sample YAML configuration for testing."""
    return {
        "agent": {"name": "Test Agent", "agent_id": "test-agent", "version": "1.0.0"},
        "model": {
            "provider": "anthropic",
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.7,
        },
        "instructions": "Test instructions",
        "tools": ["test_tool"],
    }


@pytest.fixture
def yaml_config_file(temp_dir: Path, sample_yaml_config: dict[str, Any]) -> Path:
    """Create a temporary YAML config file."""
    config_file = temp_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_yaml_config, f)
    return config_file


@pytest.fixture
def mock_settings() -> Mock:
    """Mock Settings object with common configurations."""
    mock = Mock()
    mock.database_url = "sqlite:///test.db"
    mock.metrics_batch_size = 50
    mock.metrics_flush_interval = 10.0
    mock.csv_hot_reload_interval = 5
    mock.log_level = "INFO"
    mock.log_format = "json"
    mock.runtime_env = "dev"
    return mock


@pytest.fixture
def mock_logger() -> Mock:
    """Mock logger for testing logging calls."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_csv_content() -> str:
    """Sample CSV content for knowledge base testing."""
    return """id,title,content,category,business_unit
1,Test Knowledge 1,This is test content 1,testing,unit1
2,Test Knowledge 2,This is test content 2,development,unit2
3,Test Knowledge 3,This is test content 3,testing,unit1
"""


@pytest.fixture
def csv_file(temp_dir: Path, sample_csv_content: str) -> Path:
    """Create a temporary CSV file with sample content."""
    csv_file = temp_dir / "test_knowledge.csv"
    with open(csv_file, "w") as f:
        f.write(sample_csv_content)
    return csv_file


@pytest.fixture
def env_vars() -> Generator[dict[str, str], None, None]:
    """Clean environment variables fixture."""
    original_env = os.environ.copy()
    test_env = {
        "HIVE_DATABASE_URL": "sqlite:///test.db",
        "ANTHROPIC_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key",
        "RUNTIME_ENV": "dev",
    }
    os.environ.update(test_env)
    try:
        yield test_env
    finally:
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def mock_path_exists():
    """Mock pathlib.Path.exists method."""
    with patch("pathlib.Path.exists") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_path_is_file():
    """Mock pathlib.Path.is_file method."""
    with patch("pathlib.Path.is_file") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_path_is_dir():
    """Mock pathlib.Path.is_dir method."""
    with patch("pathlib.Path.is_dir") as mock:
        mock.return_value = True
        yield mock


class MockAgentResponse:
    """Mock agent response for testing."""

    def __init__(self, content: str = "Test response", model: str = "test-model"):
        self.content = content
        self.model = model
        self.usage = MockUsage()


class MockUsage:
    """Mock usage information for agent responses."""

    def __init__(self, input_tokens: int = 100, output_tokens: int = 50):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens


@pytest.fixture
def mock_agent_response() -> MockAgentResponse:
    """Mock agent response for testing."""
    return MockAgentResponse()


def create_test_config(config_data: dict[str, Any], temp_dir: Path) -> Path:
    """Helper to create test configuration files."""
    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return config_file


def assert_file_contains(file_path: Path, content: str) -> bool:
    """Helper to assert file contains specific content."""
    if not file_path.exists():
        return False
    with open(file_path) as f:
        return content in f.read()


def assert_yaml_valid(file_path: Path) -> bool:
    """Helper to assert YAML file is valid."""
    try:
        with open(file_path) as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError:
        return False


class PerformanceTestHelper:
    """Helper class for performance testing utilities."""

    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def assert_performance_threshold(execution_time: float, threshold: float):
        """Assert execution time is below threshold."""
        assert execution_time < threshold, (
            f"Execution time {execution_time:.4f}s exceeded threshold {threshold}s"
        )


@pytest.fixture
def performance_helper() -> PerformanceTestHelper:
    """Performance testing helper fixture."""
    return PerformanceTestHelper()
