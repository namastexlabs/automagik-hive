"""Pytest configuration for API tests."""

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest


@dataclass
class MockComponentRegistries:
    """Mock ComponentRegistries with proper dict attributes."""

    agents: dict[str, Any]
    teams: dict[str, Any]
    workflows: dict[str, Any]


@dataclass
class MockStartupServices:
    """Mock StartupServices with proper service attributes."""

    auth_service: Any
    metrics_service: Any


@dataclass
class MockStartupResults:
    """Mock StartupResults with proper structure."""

    registries: MockComponentRegistries
    services: MockStartupServices
    sync_results: dict[str, Any]
    startup_display: Any


@pytest.fixture
def mock_startup_results():
    """Mock orchestrated_startup results with proper structure for API tests."""
    # Create mock agent
    mock_agent = MagicMock()
    mock_agent.name = "Test Agent"
    mock_agent.agent_id = "test-agent"

    # Create mock auth service
    mock_auth_service = MagicMock()
    mock_auth_service.is_auth_enabled.return_value = False
    mock_auth_service.get_current_key.return_value = "test-key"

    # Create mock metrics service
    mock_metrics_service = MagicMock()

    # Create proper dataclass instances
    registries = MockComponentRegistries(
        agents={"test-agent": mock_agent}, teams={"test-team": MagicMock()}, workflows={"test-workflow": MagicMock()}
    )

    services = MockStartupServices(auth_service=mock_auth_service, metrics_service=mock_metrics_service)

    results = MockStartupResults(registries=registries, services=services, sync_results={}, startup_display=MagicMock())

    return results


def create_mock_startup_results():
    """Helper function to create properly structured mock startup results.

    Use this in tests instead of creating MagicMock() directly.
    """
    # Create mock agent
    mock_agent = MagicMock()
    mock_agent.name = "Test Agent"
    mock_agent.agent_id = "test-agent"

    # Create mock auth service
    mock_auth_service = MagicMock()
    mock_auth_service.is_auth_enabled.return_value = False
    mock_auth_service.get_current_key.return_value = "test-key"

    # Create mock metrics service
    mock_metrics_service = MagicMock()

    # Create proper dataclass instances
    registries = MockComponentRegistries(
        agents={"test-agent": mock_agent}, teams={"test-team": MagicMock()}, workflows={"test-workflow": MagicMock()}
    )

    services = MockStartupServices(auth_service=mock_auth_service, metrics_service=mock_metrics_service)

    results = MockStartupResults(registries=registries, services=services, sync_results={}, startup_display=MagicMock())

    return results


# Removed autouse fixture to avoid conflicts with per-test mocking
# Tests should use create_mock_startup_results() helper directly
