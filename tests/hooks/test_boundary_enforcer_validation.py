#!/usr/bin/env python3
"""
Test script for the enhanced test_boundary_enforcer.py hook
"""
import json
import subprocess
import tempfile
import os

def test_hook_with_input(test_input):
    """Test the hook with given input data."""
    hook_path = "/home/namastex/workspace/automagik-hive/.claude/hooks/test_boundary_enforcer.py"
    
    try:
        process = subprocess.run(
            ["python3", hook_path],
            input=json.dumps(test_input),
            text=True,
            capture_output=True,
            timeout=10
        )
        return {
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
    except subprocess.TimeoutExpired:
        return {"error": "Hook timed out"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("Testing Enhanced Hook - test_boundary_enforcer.py")
    print("=" * 50)
    
    # Test Case 1: Testing agent with source code prompt (should BLOCK)
    test1 = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "hive-testing-fixer",
            "prompt": "Fix the bug in lib/knowledge/config_aware_filter.py by updating the source code"
        },
        "cwd": "/home/namastex/workspace/automagik-hive"
    }
    
    print("\n1. Testing agent targeting source code (should BLOCK):")
    result1 = test_hook_with_input(test1)
    print(f"   Return code: {result1.get('returncode', 'ERROR')}")
    if result1.get('stdout'):
        try:
            output = json.loads(result1['stdout'])
            decision = output.get('hookSpecificOutput', {}).get('permissionDecision', 'none')
            print(f"   Decision: {decision}")
            if decision == 'deny':
                print("   ✅ CORRECTLY BLOCKED source code targeting")
            else:
                print("   ❌ FAILED TO BLOCK source code targeting")
        except:
            print(f"   Raw output: {result1['stdout'][:100]}...")
    
    # Test Case 2: Testing agent with test-focused prompt (should ALLOW)
    test2 = {
        "tool_name": "Task", 
        "tool_input": {
            "subagent_type": "hive-testing-fixer",
            "prompt": "Fix failing test in tests/lib/knowledge/test_config_filter.py by updating test expectations"
        },
        "cwd": "/home/namastex/workspace/automagik-hive"
    }
    
    print("\n2. Testing agent targeting tests (should ALLOW):")
    result2 = test_hook_with_input(test2)
    print(f"   Return code: {result2.get('returncode', 'ERROR')}")
    if result2.get('returncode') == 0 and not result2.get('stdout'):
        print("   ✅ CORRECTLY ALLOWED test-focused work")
    else:
        print("   ❌ INCORRECTLY BLOCKED test-focused work")
    
    # Test Case 3: Non-testing agent (should ALLOW)
    test3 = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "hive-dev-fixer", 
            "prompt": "Fix the bug in lib/knowledge/config_aware_filter.py by updating the source code"
        },
        "cwd": "/home/namastex/workspace/automagik-hive"
    }
    
    print("\n3. Non-testing agent (should ALLOW):")
    result3 = test_hook_with_input(test3)
    print(f"   Return code: {result3.get('returncode', 'ERROR')}")
    if result3.get('returncode') == 0 and not result3.get('stdout'):
        print("   ✅ CORRECTLY ALLOWED non-testing agent")
    else:
        print("   ❌ INCORRECTLY BLOCKED non-testing agent")
    
    print("\n" + "=" * 50)
    print("HOOK ENHANCEMENT VALIDATION COMPLETE")
    print("Key improvement: Prompt analysis prevents false positives")
    print("Testing agents can work on tests/, blocked from source code")

if __name__ == "__main__":
    main()