"""Tests for lib.utils.config_validator module.

Tests the simplified config validator with inheritance system removed.
"""

import pytest
from unittest.mock import Mock

from lib.utils.config_validator import AGNOConfigValidator, ValidationResult


class TestAGNOConfigValidator:
    """Test AGNOConfigValidator simplified implementation."""

    def test_init(self):
        """Test AGNOConfigValidator initialization."""
        validator = AGNOConfigValidator()
        assert validator is not None

    def test_validate_inheritance_compliance_disabled(self):
        """Test inheritance validation is disabled."""
        validator = AGNOConfigValidator()
        
        result = validator._validate_inheritance_compliance(
            "test-team", {}, {}
        )
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []