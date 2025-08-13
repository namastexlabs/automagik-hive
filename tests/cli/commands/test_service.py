"""Tests for CLI service commands."""

import pytest
from pathlib import Path
from cli.commands.service import ServiceManager


class TestServiceManager:
    """Test ServiceManager functionality."""
    
    def test_service_manager_initialization(self):
        """Test ServiceManager initializes correctly."""
        manager = ServiceManager()
        assert manager.workspace_path == Path(".")
    
    def test_service_manager_with_custom_path(self):
        """Test ServiceManager with custom workspace path."""
        custom_path = Path("/custom/path")
        manager = ServiceManager(custom_path)
        assert manager.workspace_path == custom_path
    
    def test_manage_service_default(self):
        """Test manage_service with default parameters."""
        manager = ServiceManager()
        result = manager.manage_service()
        assert result is True
    
    def test_manage_service_named(self):
        """Test manage_service with named service."""
        manager = ServiceManager()
        result = manager.manage_service("test_service")
        assert result is True
    
    def test_execute(self):
        """Test execute method."""
        manager = ServiceManager()
        result = manager.execute()
        assert result is True
    
    def test_status(self):
        """Test status method."""
        manager = ServiceManager()
        status = manager.status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "healthy" in status