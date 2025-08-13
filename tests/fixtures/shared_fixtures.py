"""
Shared test utilities and fixtures for all test suites.

This module provides common fixtures, utilities, and helper functions that can be
reused across all test domains to ensure consistency and reduce duplication.
"""

import contextlib
import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)
    yield temp_path
    # Cleanup
    with contextlib.suppress(OSError):
        os.unlink(temp_path)


@pytest.fixture
def sample_yaml_data():
    """Sample YAML data for testing."""
    return {
        "name": "test_component",
        "version": "1.0.0",
        "config": {"enabled": True, "timeout": 30, "retries": 3},
        "metadata": {"tags": ["test", "sample"], "description": "Sample test data"},
    }


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return [
        ["id", "name", "category", "value"],
        ["1", "Item One", "category_a", "100"],
        ["2", "Item Two", "category_b", "200"],
        ["3", "Item Three", "category_a", "150"],
    ]


@pytest.fixture
def sample_metrics_data():
    """Sample metrics data for testing."""
    return {
        "agent_id": "test_agent_001",
        "execution_time": 1.234,
        "tokens_used": 150,
        "input_tokens": 100,
        "output_tokens": 50,
        "cost": 0.001,
        "success": True,
        "error_count": 0,
        "timestamp": "2023-01-01T12:00:00Z",
        "metadata": {"model": "claude-3", "temperature": 0.7},
    }


class TestFileCreator:
    """Utility class for creating test files."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.created_files = []

    def create_yaml_file(self, filename: str, data: dict[str, Any]) -> str:
        """Create a YAML file with given data."""
        file_path = self.base_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            yaml.dump(data, f)

        self.created_files.append(str(file_path))
        return str(file_path)

    def create_csv_file(self, filename: str, data: list[list[str]]) -> str:
        """Create a CSV file with given data."""
        file_path = self.base_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)

        self.created_files.append(str(file_path))
        return str(file_path)

    def create_json_file(self, filename: str, data: dict[str, Any]) -> str:
        """Create a JSON file with given data."""
        file_path = self.base_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        self.created_files.append(str(file_path))
        return str(file_path)

    def create_text_file(self, filename: str, content: str) -> str:
        """Create a text file with given content."""
        file_path = self.base_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)

        self.created_files.append(str(file_path))
        return str(file_path)

    def cleanup(self):
        """Clean up all created files."""
        for file_path in self.created_files:
            with contextlib.suppress(OSError):
                os.unlink(file_path)
        self.created_files.clear()


@pytest.fixture
def file_creator(temp_directory):
    """Create a TestFileCreator instance."""
    creator = TestFileCreator(temp_directory)
    yield creator
    creator.cleanup()


class MockFactory:
    """Factory for creating consistent mock objects."""

    @staticmethod
    def create_mock_logger():
        """Create a mock logger with common methods."""
        mock_logger = MagicMock()
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.warning = MagicMock()
        mock_logger.error = MagicMock()
        mock_logger.critical = MagicMock()
        return mock_logger

    @staticmethod
    def create_mock_database():
        """Create a mock database with common operations."""
        mock_db = MagicMock()
        mock_db.connect = MagicMock()
        mock_db.execute = MagicMock()
        mock_db.fetchall = MagicMock(return_value=[])
        mock_db.fetchone = MagicMock(return_value=None)
        mock_db.commit = MagicMock()
        mock_db.close = MagicMock()
        return mock_db

    @staticmethod
    def create_mock_async_service():
        """Create a mock async service."""
        mock_service = MagicMock()
        mock_service.start = AsyncMock()
        mock_service.stop = AsyncMock()
        mock_service.process = AsyncMock()
        mock_service.store = AsyncMock()
        return mock_service

    @staticmethod
    def create_mock_config(overrides: dict[str, Any] | None = None):
        """Create a mock configuration object."""
        default_config = {
            "debug": True,
            "batch_size": 100,
            "timeout": 30,
            "retries": 3,
            "enabled": True,
        }

        if overrides:
            default_config.update(overrides)

        mock_config = MagicMock()
        for key, value in default_config.items():
            setattr(mock_config, key, value)

        return mock_config


@pytest.fixture
def mock_factory():
    """Provide MockFactory instance."""
    return MockFactory()


class AssertionHelpers:
    """Helper functions for common test assertions."""

    @staticmethod
    def assert_file_exists(file_path: str):
        """Assert that a file exists."""
        assert os.path.exists(file_path), f"File does not exist: {file_path}"

    @staticmethod
    def assert_file_not_empty(file_path: str):
        """Assert that a file exists and is not empty."""
        AssertionHelpers.assert_file_exists(file_path)
        assert os.path.getsize(file_path) > 0, f"File is empty: {file_path}"

    @staticmethod
    def assert_yaml_valid(file_path: str):
        """Assert that a file contains valid YAML."""
        AssertionHelpers.assert_file_exists(file_path)
        with open(file_path) as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {file_path}: {e}")

    @staticmethod
    def assert_csv_valid(file_path: str):
        """Assert that a file contains valid CSV."""
        AssertionHelpers.assert_file_exists(file_path)
        with open(file_path) as f:
            try:
                reader = csv.reader(f)
                list(reader)  # Try to read all rows
            except csv.Error as e:
                pytest.fail(f"Invalid CSV in {file_path}: {e}")

    @staticmethod
    def assert_json_valid(file_path: str):
        """Assert that a file contains valid JSON."""
        AssertionHelpers.assert_file_exists(file_path)
        with open(file_path) as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {file_path}: {e}")

    @staticmethod
    def assert_dict_contains_keys(data: dict[str, Any], required_keys: list[str]):
        """Assert that a dictionary contains all required keys."""
        missing_keys = [key for key in required_keys if key not in data]
        assert not missing_keys, f"Missing required keys: {missing_keys}"

    @staticmethod
    def assert_list_not_empty(data: list[Any]):
        """Assert that a list is not empty."""
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "List is empty"

    @staticmethod
    def assert_async_function(func):
        """Assert that a function is async."""
        import asyncio

        assert asyncio.iscoroutinefunction(func), (
            f"Function {func.__name__} is not async"
        )


@pytest.fixture
def assert_helpers():
    """Provide AssertionHelpers instance."""
    return AssertionHelpers()


class PerformanceTimer:
    """Utility for timing test operations."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start timing."""
        import time

        self.start_time = time.time()

    def stop(self):
        """Stop timing."""
        import time

        self.end_time = time.time()

    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time is None or self.end_time is None:
            raise ValueError("Timer not properly started/stopped")
        return self.end_time - self.start_time

    def assert_duration_under(self, max_seconds: float):
        """Assert that duration is under specified seconds."""
        duration = self.duration()
        assert duration < max_seconds, (
            f"Operation took {duration}s, expected under {max_seconds}s"
        )


@pytest.fixture
def performance_timer():
    """Provide PerformanceTimer instance."""
    return PerformanceTimer()


class DatabaseTestHelpers:
    """Helpers for database testing."""

    @staticmethod
    def create_mock_sqlalchemy_session():
        """Create a mock SQLAlchemy session."""
        mock_session = MagicMock()
        mock_session.query = MagicMock()
        mock_session.add = MagicMock()
        mock_session.delete = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.rollback = MagicMock()
        mock_session.close = MagicMock()
        return mock_session

    @staticmethod
    def create_sample_db_records(count: int = 5) -> list[dict[str, Any]]:
        """Create sample database records."""
        records = []
        for i in range(count):
            records.append(
                {
                    "id": i + 1,
                    "name": f"Record {i + 1}",
                    "value": (i + 1) * 10,
                    "active": i % 2 == 0,
                    "created_at": "2023-01-01T12:00:00Z",
                },
            )
        return records


@pytest.fixture
def db_helpers():
    """Provide DatabaseTestHelpers instance."""
    return DatabaseTestHelpers()


class ErrorSimulator:
    """Utility for simulating various error conditions."""

    @staticmethod
    def create_file_permission_error():
        """Create a file permission error."""
        return PermissionError("Permission denied")

    @staticmethod
    def create_file_not_found_error():
        """Create a file not found error."""
        return FileNotFoundError("File not found")

    @staticmethod
    def create_yaml_error():
        """Create a YAML parsing error."""
        return yaml.YAMLError("Invalid YAML syntax")

    @staticmethod
    def create_csv_error():
        """Create a CSV parsing error."""
        return csv.Error("Invalid CSV format")

    @staticmethod
    def create_json_error():
        """Create a JSON parsing error."""
        return json.JSONDecodeError("Invalid JSON", "document", 0)

    @staticmethod
    def create_timeout_error():
        """Create a timeout error."""
        return TimeoutError("Operation timed out")

    @staticmethod
    def create_connection_error():
        """Create a connection error."""
        return ConnectionError("Connection failed")


@pytest.fixture
def error_simulator():
    """Provide ErrorSimulator instance."""
    return ErrorSimulator()


# Common test data generators
def generate_test_metrics(count: int = 10) -> list[dict[str, Any]]:
    """Generate test metrics data."""
    import random

    metrics = []

    for i in range(count):
        metrics.append(
            {
                "agent_id": f"test_agent_{i:03d}",
                "execution_time": round(random.uniform(0.1, 5.0), 3),
                "tokens_used": random.randint(50, 500),
                "success": random.choice([True, False]),
                "cost": round(random.uniform(0.001, 0.01), 6),
                "timestamp": f"2023-01-01T{i % 24:02d}:00:00Z",
            },
        )

    return metrics


def generate_test_csv_data(rows: int = 10, columns: int = 4) -> list[list[str]]:
    """Generate test CSV data."""
    import random
    import string

    # Generate header
    headers = [f"column_{i}" for i in range(columns)]
    data = [headers]

    # Generate data rows
    for i in range(rows):
        row = []
        for j in range(columns):
            if j == 0:
                row.append(str(i + 1))  # ID column
            elif j == 1:
                row.append(f"Item {i + 1}")  # Name column
            else:
                # Random data
                row.append(
                    "".join(random.choices(string.ascii_letters + string.digits, k=8)),
                )
        data.append(row)

    return data


def generate_test_yaml_config(component_type: str = "test") -> dict[str, Any]:
    """Generate test YAML configuration."""
    return {
        "name": f"{component_type}_component",
        "version": "1.0.0",
        "enabled": True,
        "config": {"timeout": 30, "retries": 3, "batch_size": 100},
        "metadata": {
            "created_by": "test_suite",
            "tags": ["test", component_type],
            "description": f"Test configuration for {component_type}",
        },
    }


# Export commonly used functions
__all__ = [
    "AssertionHelpers",
    "DatabaseTestHelpers",
    "ErrorSimulator",
    "MockFactory",
    "PerformanceTimer",
    "TestFileCreator",
    "generate_test_csv_data",
    "generate_test_metrics",
    "generate_test_yaml_config",
]
