#!/usr/bin/env python3
"""Mock test to understand the behavior difference between the two tests."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, call

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.commands.postgres import PostgreSQLCommands

def test_mock_postgres_logs():
    """Test with fully mocked Docker to understand print behavior."""
    
    print("=== Testing with mocked DockerManager ===")
    
    # Test default tail (50)
    print("\n--- Default tail test (50) ---")
    with patch('builtins.print') as mock_print, \
         patch('cli.commands.postgres.DockerManager') as mock_docker_manager_class:
        
        # Setup mocks
        mock_docker_manager = Mock()
        mock_docker_manager_class.return_value = mock_docker_manager
        mock_docker_manager._container_exists.return_value = True
        mock_docker_manager._container_running.return_value = True
        mock_docker_manager._run_command.return_value = None  # Success
        mock_docker_manager.CONTAINERS = {
            "workspace": {"postgres": "hive-main-postgres"},
            "agent": {"postgres": "hive-agent-postgres"}
        }
        
        postgres_cmd = PostgreSQLCommands()
        result = postgres_cmd.postgres_logs("/test/workspace")
        
        print(f"Result: {result}")
        print(f"Number of print calls: {mock_print.call_count}")
        print("All print calls:")
        for i, call_obj in enumerate(mock_print.call_args_list):
            print(f"  {i+1}: {call_obj}")
        
        # Check the assertion that should fail
        try:
            mock_print.assert_called_with("📋 Showing PostgreSQL logs from: /test/workspace (last 50 lines)")
            print("✅ Default assertion passed")
        except AssertionError as e:
            print(f"❌ Default assertion failed: {e}")
    
    # Test custom tail (100)
    print("\n--- Custom tail test (100) ---")
    with patch('builtins.print') as mock_print, \
         patch('cli.commands.postgres.DockerManager') as mock_docker_manager_class:
        
        # Setup mocks
        mock_docker_manager = Mock()
        mock_docker_manager_class.return_value = mock_docker_manager
        mock_docker_manager._container_exists.return_value = True
        mock_docker_manager._container_running.return_value = True
        mock_docker_manager._run_command.return_value = None  # Success
        mock_docker_manager.CONTAINERS = {
            "workspace": {"postgres": "hive-main-postgres"},
            "agent": {"postgres": "hive-agent-postgres"}
        }
        
        postgres_cmd = PostgreSQLCommands()
        result = postgres_cmd.postgres_logs("/test/workspace", tail=100)
        
        print(f"Result: {result}")
        print(f"Number of print calls: {mock_print.call_count}")
        print("All print calls:")
        for i, call_obj in enumerate(mock_print.call_args_list):
            print(f"  {i+1}: {call_obj}")
        
        # Check the assertion that should fail
        try:
            mock_print.assert_called_with("📋 Showing PostgreSQL logs from: /test/workspace (last 100 lines)")
            print("✅ Custom assertion passed")
        except AssertionError as e:
            print(f"❌ Custom assertion failed: {e}")

if __name__ == "__main__":
    test_mock_postgres_logs()