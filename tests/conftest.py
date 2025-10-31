"""
Pytest configuration and shared fixtures for Automagik Hive v2 tests.

This module provides:
- Test database setup
- Temporary directory management
- Mock API keys for safe testing
- Async test support
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """
    Mock environment variables for testing.

    Provides safe defaults that won't hit real APIs or databases.
    """
    test_env = {
        "HIVE_ENVIRONMENT": "test",
        "HIVE_DATABASE_URL": "sqlite:///:memory:",
        "ANTHROPIC_API_KEY": "test-anthropic-key-not-real",
        "OPENAI_API_KEY": "test-openai-key-not-real",
        "HIVE_LOG_LEVEL": "ERROR",  # Quiet during tests
    }

    with patch.dict(os.environ, test_env, clear=False):
        yield test_env


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test projects.

    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory(prefix="hive_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_csv_data() -> str:
    """
    Sample CSV data for RAG testing.

    Small dataset for fast tests.
    """
    return """query,context,conclusion
How do I reset password?,Go to settings > security > reset password,Process
Payment failed,Check card details and try again,Technical
Account locked,Contact support after 3 failed attempts,Security"""


@pytest.fixture
def sample_agent_yaml() -> str:
    """
    Valid agent YAML for testing.

    Minimal but complete agent configuration.
    """
    return """agent:
  name: "Test Agent"
  id: "test-agent"
  version: 1

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a helpful test agent.
  Answer questions concisely.

knowledge:
  enabled: false

storage:
  table_name: "test_agent_sessions"
"""


@pytest.fixture
def sample_team_yaml() -> str:
    """
    Valid team YAML for testing.
    """
    return """team:
  name: "Test Team"
  team_id: "test-team"
  mode: "route"

members:
  - "test-agent-1"
  - "test-agent-2"

instructions: |
  Route questions to appropriate specialist.
"""


@pytest.fixture
def sample_workflow_yaml() -> str:
    """
    Valid workflow YAML for testing.
    """
    return """workflow:
  name: "Test Workflow"
  workflow_id: "test-workflow"

steps:
  - name: "Analysis"
    agent: "analyst-agent"
  - name: "Review"
    agent: "reviewer-agent"
"""


@pytest.fixture
def mock_agno_agent(monkeypatch):
    """
    Mock Agno Agent class to avoid hitting real LLMs in tests.
    """

    class MockAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name", "Mock Agent")
            self.id = kwargs.get("id", "mock-agent")
            self.instructions = kwargs.get("instructions", "Test instructions")

        def run(self, message: str, **kwargs):
            return MockResponse(f"Mock response to: {message}")

        async def arun(self, message: str, **kwargs):
            return MockResponse(f"Mock async response to: {message}")

    class MockResponse:
        def __init__(self, content: str):
            self.content = content

    def mock_agent_factory(*args, **kwargs):
        return MockAgent(**kwargs)

    # Patch Agno's Agent class
    monkeypatch.setattr("agno.agent.Agent", mock_agent_factory)

    return MockAgent


@pytest.fixture
def mock_database():
    """
    Mock database operations for testing without real DB.
    """

    class MockDB:
        def __init__(self):
            self.data = {}

        def store(self, key: str, value: str):
            self.data[key] = value

        def retrieve(self, key: str):
            return self.data.get(key)

        def delete(self, key: str):
            if key in self.data:
                del self.data[key]

    return MockDB()


# Test markers for categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "requires_api_key: marks tests that need real API keys")
