"""Pytest configuration for AI workflows tests."""

from unittest.mock import patch

import pytest


@pytest.fixture
def mock_workflows_dir(tmp_path):
    """Create a temporary workflows directory for testing."""
    workflows_dir = tmp_path / "ai" / "workflows"
    workflows_dir.mkdir(parents=True)
    return workflows_dir


@pytest.fixture
def mock_resolve_ai_root(tmp_path):
    """Mock resolve_ai_root to return a test directory."""
    ai_root = tmp_path / "ai"
    ai_root.mkdir(parents=True, exist_ok=True)

    with patch("ai.workflows.registry.resolve_ai_root") as mock:
        mock.return_value = ai_root
        yield mock
