#!/usr/bin/env python3
"""Debug test to understand error propagation issue."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from cli.commands.agent import AgentCommands


def debug_error_propagation():
    """Debug which scenario is failing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        commands = AgentCommands()
        
        # Test scenarios individually
        failure_scenarios = [
            ("install", {"install_agent_environment": False}),
            ("start", {"serve_agent": False}),
            ("stop", {"stop_agent": False}),
            ("restart", {"restart_agent": False}),
            ("reset", {"reset_agent_environment": False}),
        ]
        
        for command_name, mock_returns in failure_scenarios:
            print(f"\n=== Testing {command_name} scenario ===")
            method_name = next(iter(mock_returns.keys()))
            return_value = next(iter(mock_returns.values()))
            
            with patch.object(
                commands.agent_service,
                method_name,
                return_value=return_value,
            ):
                method = getattr(commands, command_name)
                result = method(temp_dir)
                print(f"Command: {command_name}")
                print(f"Mocked method: {method_name} -> {return_value}")
                print(f"Result: {result}")
                print(f"Expected: False")
                print(f"Pass: {result is False}")


if __name__ == "__main__":
    debug_error_propagation()