#!/usr/bin/env python3
"""Debug script to understand what the PostgreSQL logs method actually prints."""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.commands.postgres import PostgreSQLCommands

def debug_postgres_logs():
    """Debug what the postgres_logs method actually prints."""
    postgres_cmd = PostgreSQLCommands()
    
    print("=== Testing default tail (50) ===")
    result1 = postgres_cmd.postgres_logs("/test/workspace")
    print(f"Result: {result1}")
    
    print("\n=== Testing custom tail (100) ===")
    result2 = postgres_cmd.postgres_logs("/test/workspace", tail=100)
    print(f"Result: {result2}")

if __name__ == "__main__":
    debug_postgres_logs()