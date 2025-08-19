#!/usr/bin/env python3
"""Isolated test to understand the behavior of print mocking in PostgreSQL tests."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, call

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.commands.postgres import PostgreSQLCommands

def test_postgres_logs_behaviors():
    """Test both default and custom tail scenarios to understand the difference."""
    
    print("=== TESTING DEFAULT TAIL (50) ===")
    with patch('builtins.print') as mock_print:
        postgres_cmd = PostgreSQLCommands()
        result = postgres_cmd.postgres_logs("/test/workspace")
        print(f"Result: {result}")
        print(f"Number of print calls: {mock_print.call_count}")
        print("All print calls:")
        for i, call_obj in enumerate(mock_print.call_args_list):
            print(f"  {i+1}: {call_obj}")
        print(f"Last call: {mock_print.call_args}")
        
        # Try the assertion from the test
        try:
            mock_print.assert_called_with("📋 Showing PostgreSQL logs from: /test/workspace (last 50 lines)")
            print("✅ Default tail assertion PASSED")
        except AssertionError as e:
            print(f"❌ Default tail assertion FAILED: {e}")
    
    print("\n=== TESTING CUSTOM TAIL (100) ===")
    with patch('builtins.print') as mock_print:
        postgres_cmd = PostgreSQLCommands()
        result = postgres_cmd.postgres_logs("/test/workspace", tail=100)
        print(f"Result: {result}")
        print(f"Number of print calls: {mock_print.call_count}")
        print("All print calls:")
        for i, call_obj in enumerate(mock_print.call_args_list):
            print(f"  {i+1}: {call_obj}")
        print(f"Last call: {mock_print.call_args}")
        
        # Try the assertion from the test
        try:
            mock_print.assert_called_with("📋 Showing PostgreSQL logs from: /test/workspace (last 100 lines)")
            print("✅ Custom tail assertion PASSED")
        except AssertionError as e:
            print(f"❌ Custom tail assertion FAILED: {e}")

if __name__ == "__main__":
    test_postgres_logs_behaviors()