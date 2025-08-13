"""Tests for CLI health commands."""

import pytest
from pathlib import Path
from cli.commands.health import HealthChecker


class TestHealthChecker:
    """Test HealthChecker functionality."""
    
    def test_health_checker_initialization(self):
        """Test HealthChecker initializes correctly."""
        checker = HealthChecker()
        assert checker.workspace_path == Path(".")
    
    def test_health_checker_with_custom_path(self):
        """Test HealthChecker with custom workspace path."""
        custom_path = Path("/custom/path")
        checker = HealthChecker(custom_path)
        assert checker.workspace_path == custom_path
    
    def test_check_health_default(self):
        """Test check_health with default parameters."""
        checker = HealthChecker()
        result = checker.check_health()
        assert result is True
    
    def test_check_health_component(self):
        """Test check_health with specific component."""
        checker = HealthChecker()
        result = checker.check_health("database")
        assert result is True
    
    def test_execute(self):
        """Test execute method."""
        checker = HealthChecker()
        result = checker.execute()
        assert result is True
    
    def test_status(self):
        """Test status method."""
        checker = HealthChecker()
        status = checker.status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "healthy" in status