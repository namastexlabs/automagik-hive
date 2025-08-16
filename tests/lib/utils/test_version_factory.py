"""Tests for lib.utils.version_factory module.

Tests the simplified version factory with inheritance system removed.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from lib.utils.version_factory import VersionFactory


class TestVersionFactory:
    """Test VersionFactory simplified implementation."""

    def test_init(self):
        """Test VersionFactory initialization."""
        factory = VersionFactory()
        assert factory is not None

    @patch('lib.utils.version_factory.logger')
    def test_apply_team_inheritance_passthrough(self, mock_logger):
        """Test team inheritance returns config unchanged."""
        factory = VersionFactory()
        config = {"name": "test", "version": "1.0.0"}
        
        result = factory._apply_team_inheritance("test-agent", config)
        
        assert result == config
        mock_logger.debug.assert_called_once()

    @patch('lib.utils.version_factory.logger')
    def test_validate_team_inheritance_disabled(self, mock_logger):
        """Test team inheritance validation is disabled."""
        factory = VersionFactory()
        config = {"name": "test", "version": "1.0.0"}
        
        result = factory._validate_team_inheritance("test-team", config)
        
        # Should return config unchanged (validation disabled)
        assert result == config
        mock_logger.debug.assert_called_once()