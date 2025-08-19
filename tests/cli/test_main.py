"""Tests for CLI main.py module.

Focused tests for the main CLI entry point functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

from cli.main import main, create_parser


class TestVersionCommand:
    """Test version command functionality."""
    
    def test_version_uses_dynamic_version_reader(self, capsys, monkeypatch):
        """Test that --version uses get_project_version() for accurate version display."""
        # Mock get_project_version to return a specific version
        with patch('lib.utils.version_reader.get_project_version') as mock_version:
            mock_version.return_value = "0.1.0a59"
            
            # Mock sys.argv to simulate --version command
            monkeypatch.setattr(sys, 'argv', ['automagik-hive', '--version'])
            
            # argparse with action="version" raises SystemExit
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should exit with code 0 for success
            assert exc_info.value.code == 0
            
            # Check that version was displayed correctly
            captured = capsys.readouterr()
            assert "automagik-hive v0.1.0a59" in captured.out
            
            # Verify get_project_version was called
            mock_version.assert_called_once()
    
    def test_version_fallback_on_import_error(self, capsys, monkeypatch):
        """Test version handling when version_reader import fails."""
        # Mock sys.argv
        monkeypatch.setattr(sys, 'argv', ['automagik-hive', '--version'])
        
        # Mock import failure and fallback
        with patch('lib.utils.version_reader.get_project_version') as mock_version:
            mock_version.side_effect = ImportError("Module not found")
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Should still exit successfully even with import error
            assert exc_info.value.code == 0


class TestParser:
    """Test argument parser creation and functionality."""
    
    def test_parser_has_version_argument(self):
        """Test that parser includes --version argument."""
        parser = create_parser()
        
        # Check that --version is in the parser
        help_text = parser.format_help()
        assert "--version" in help_text
    
    def test_parser_version_action(self):
        """Test that --version argument has correct action type."""
        parser = create_parser()
        
        # Parse --version argument
        with pytest.raises(SystemExit):
            # ArgumentParser exits on --version, so we expect SystemExit
            args = parser.parse_args(["--version"])


class TestStartCommand:
    """Test start command help text."""
    
    def test_cli_start_command(self):
        """Test that workspace argument help text is 'Start workspace server'."""
        parser = create_parser()
        
        # Get help text for the workspace argument
        help_text = parser.format_help()
        assert "Start workspace server" in help_text