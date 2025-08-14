#!/usr/bin/env python3
"""Debug test for agent-start command to verify the fix."""

import sys
from unittest.mock import patch, Mock
import pytest

def test_agent_start_success():
    """Test --agent-start command routing works with success."""
    with patch('cli.main.AgentCommands') as mock_agent_class:
        mock_agent_instance = Mock()
        mock_agent_instance.start.return_value = True
        mock_agent_class.return_value = mock_agent_instance
        
        from cli.main import main
        with patch('sys.argv', ['automagik-hive', '--agent-start']):
            result = main()
        
        assert result == 0
        mock_agent_instance.start.assert_called_once_with('.')

def test_agent_start_failure():
    """Test --agent-start command routing returns error on failure."""
    with patch('cli.main.AgentCommands') as mock_agent_class:
        mock_agent_instance = Mock()
        mock_agent_instance.start.return_value = False  # Simulate failure
        mock_agent_class.return_value = mock_agent_instance
        
        from cli.main import main
        with patch('sys.argv', ['automagik-hive', '--agent-start']):
            result = main()
        
        assert result == 1, "Command should return exit code 1 on failure"
        mock_agent_instance.start.assert_called_once_with('.')

if __name__ == "__main__":
    test_agent_start_success()
    print("✅ Agent start success test passed")
    
    test_agent_start_failure()
    print("✅ Agent start failure test passed")
    
    print("🎉 All tests passed!")