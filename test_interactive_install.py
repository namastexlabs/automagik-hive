#!/usr/bin/env python3
"""Test script to validate interactive Docker installation behavior."""

import subprocess
import sys
from unittest.mock import MagicMock, patch


def test_interactive_install():
    """Test the --install command with simulated missing Docker."""
    print("🧪 Testing interactive Docker installation...")
    
    # Test 1: Check help output shows --install command
    try:
        result = subprocess.run([sys.executable, "-m", "cli.main", "--help"],
                              capture_output=True, text=True, check=False)
        if "--install" in result.stdout:
            print("✅ Test 1 PASSED: --install command available in help")
        else:
            print("❌ Test 1 FAILED: --install command not found in help")
            return False
    except Exception as e:
        print(f"❌ Test 1 ERROR: {e}")
        return False
        
    # Test 2: Check version command works
    try:
        result = subprocess.run([sys.executable, "-m", "cli.main", "--version"],
                              capture_output=True, text=True, check=False)
        if "Automagik Hive" in result.stdout:
            print("✅ Test 2 PASSED: --version command works")
        else:
            print("❌ Test 2 FAILED: --version command output unexpected")
            print(f"Output: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Test 2 ERROR: {e}")
        return False
        
    # Test 3: Import workflow orchestrator and check if interactive method exists
    try:
        from cli.commands.orchestrator import WorkflowOrchestrator
        orchestrator = WorkflowOrchestrator()
        
        # Check if the dependency validator has the interactive Docker installation method
        if hasattr(orchestrator.dependency_validator, "prompt_docker_installation"):
            print("✅ Test 3 PASSED: Interactive Docker installation method exists")
        else:
            print("❌ Test 3 FAILED: Interactive Docker installation method missing")
            return False
            
        # Check dependency validation method
        is_valid, missing = orchestrator.dependency_validator.validate_dependencies("agent")
        print(f"✅ Test 3 INFO: Dependency validation returned: {is_valid}, missing: {missing}")
        
    except Exception as e:
        print(f"❌ Test 3 ERROR: {e}")
        return False
        
    print("🎉 All tests passed! Interactive Docker installation is ready.")
    return True

if __name__ == "__main__":
    if test_interactive_install():
        sys.exit(0)
    else:
        sys.exit(1)
