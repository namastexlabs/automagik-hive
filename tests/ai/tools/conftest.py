"""Pytest configuration for AI tools tests."""

from unittest.mock import patch

import pytest


@pytest.fixture
def mock_tools_dir(tmp_path):
    """Create a temporary tools directory for testing."""
    tools_dir = tmp_path / "ai" / "tools"
    tools_dir.mkdir(parents=True)
    return tools_dir


@pytest.fixture
def mock_resolve_ai_root(tmp_path):
    """Mock resolve_ai_root to return a test directory."""
    ai_root = tmp_path / "ai"
    ai_root.mkdir(parents=True, exist_ok=True)

    with patch("ai.tools.registry.resolve_ai_root") as mock:
        mock.return_value = ai_root
        yield mock
