"""Tests for Genie Commands Implementation.

Test the minimal genie command functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import subprocess

from cli.commands.genie import GenieCommands


class TestGenieCommands:
    """Test GenieCommands class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.genie_cmd = GenieCommands()
    
    def test_launch_claude_success(self):
        """Test successful claude launch with AGENTS.md."""
        agents_content = "# AGENTS\nTest agents content"
        
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=agents_content)), \
             patch('subprocess.run') as mock_run:
            
            # Setup mocks
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = True
            mock_run.return_value.returncode = 0
            
            # Execute
            result = self.genie_cmd.launch_claude(["--extra-arg"])
            
            # Verify
            assert result is True
            mock_run.assert_called_once()
            
            # Check claude command structure
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "claude"
            assert "--append-system-prompt" in call_args
            assert agents_content in call_args
            assert "--mcp-config" in call_args
            assert ".mcp.json" in call_args
            assert "--model" in call_args
            assert "sonnet" in call_args
            assert "--dangerously-skip-permissions" in call_args
            assert "--extra-arg" in call_args
    
    def test_launch_claude_agents_md_not_found(self):
        """Test failure when AGENTS.md is not found."""
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists:
            
            # Setup mocks - AGENTS.md doesn't exist anywhere
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = False
            
            # Execute
            result = self.genie_cmd.launch_claude()
            
            # Verify
            assert result is False
    
    def test_launch_claude_agents_md_read_error(self):
        """Test failure when AGENTS.md cannot be read."""
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', side_effect=IOError("Permission denied")):
            
            # Setup mocks
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = True
            
            # Execute
            result = self.genie_cmd.launch_claude()
            
            # Verify
            assert result is False
    
    def test_launch_claude_command_not_found(self):
        """Test failure when claude command is not found."""
        agents_content = "# AGENTS\nTest content"
        
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=genie_content)), \
             patch('subprocess.run', side_effect=FileNotFoundError()):
            
            # Setup mocks
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = True
            
            # Execute
            result = self.genie_cmd.launch_claude()
            
            # Verify
            assert result is False
    
    def test_launch_claude_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        agents_content = "# AGENTS\nTest content"
        
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=genie_content)), \
             patch('subprocess.run', side_effect=KeyboardInterrupt()):
            
            # Setup mocks
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = True
            
            # Execute
            result = self.genie_cmd.launch_claude()
            
            # Verify - KeyboardInterrupt should return True (not an error)
            assert result is True
    
    def test_launch_claude_finds_agents_md_in_parent(self):
        """Test that AGENTS.md is found in parent directory."""
        agents_content = "# AGENTS\nParent content"
        
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('builtins.open', mock_open(read_data=agents_content)), \
             patch('subprocess.run') as mock_run:
            
            # Setup mock filesystem structure
            workspace_path = Path("/test/workspace/subdir")
            parent_path = Path("/test/workspace")
            
            def mock_exists(path):
                # AGENTS.md doesn't exist in subdir but exists in parent
                if str(path).endswith("subdir/AGENTS.md"):
                    return False
                if str(path).endswith("workspace/AGENTS.md"):
                    return True
                return False
            
            mock_cwd.return_value = workspace_path
            mock_run.return_value.returncode = 0
            
            # Mock path exists and parents
            with patch.object(Path, 'exists', side_effect=mock_exists), \
                 patch.object(Path, 'parents', [parent_path]):
                
                # Execute
                result = self.genie_cmd.launch_claude()
                
                # Verify
                assert result is True
                mock_run.assert_called_once()
    
    def test_launch_claude_subprocess_error(self):
        """Test handling of subprocess error."""
        agents_content = "# AGENTS\nTest content"
        
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=genie_content)), \
             patch('subprocess.run', side_effect=Exception("Subprocess failed")):
            
            # Setup mocks
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = True
            
            # Execute
            result = self.genie_cmd.launch_claude()
            
            # Verify
            assert result is False
    
    def test_launch_claude_no_extra_args(self):
        """Test claude launch without extra arguments."""
        agents_content = "# AGENTS\nTest content"
        
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=genie_content)), \
             patch('subprocess.run') as mock_run:
            
            # Setup mocks
            mock_cwd.return_value = Path("/test/workspace")
            mock_exists.return_value = True
            mock_run.return_value.returncode = 0
            
            # Execute without extra args
            result = self.genie_cmd.launch_claude()
            
            # Verify
            assert result is True
            mock_run.assert_called_once()
            
            # Verify command doesn't contain extra args
            call_args = mock_run.call_args[0][0]
            assert "--extra-arg" not in call_args