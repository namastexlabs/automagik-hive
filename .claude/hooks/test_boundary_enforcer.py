#!/usr/bin/env python3
"""
Testing Agent File Boundary Enforcer Hook

ONLY blocks testing agents (hive-testing-fixer/hive-testing-maker) from modifying 
files outside tests/ and genie/ directories. All other agents are allowed.
"""

import json
import sys
import os
from pathlib import Path

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # LOG ALL INPUT DATA TO DEBUG DETECTION
    debug_log_path = "/tmp/hook_debug.log"
    try:
        with open(debug_log_path, "a") as f:
            f.write(f"\n=== HOOK DEBUG LOG ===\n")
            f.write(f"Full input_data: {json.dumps(input_data, indent=2)}\n")
            f.write(f"Available keys: {list(input_data.keys())}\n")
            f.write(f"======================\n")
    except Exception as e:
        pass  # Don't fail if logging fails

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only apply to file-writing tools and Bash
    if tool_name not in ["Write", "Edit", "MultiEdit", "Task", "Bash"]:
        sys.exit(0)
    
    # Skip documentation files 
    file_path = tool_input.get("file_path", "")
    if file_path and any(file_path.endswith(ext) for ext in ['.md', '.txt', '.rst', '.json']):
        sys.exit(0)
    
    # ONLY block Task calls to testing agents
    if tool_name == "Task":
        subagent_type = tool_input.get("subagent_type", "")
        if subagent_type not in ["hive-testing-fixer", "hive-testing-maker", "hive-hook-tester"]:
            sys.exit(0)  # Not a testing agent, allow
        
        # For Task calls, we need to block regardless of file_path
        # because testing agents shouldn't be spawned for source code at all
        error_message = f"""🚨 TESTING AGENT TASK BLOCKED 🚨

TASK TO TESTING AGENT DENIED: {subagent_type}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ TESTING AGENTS CAN ONLY WORK ON TEST FILES

Testing agents (hive-testing-fixer/hive-testing-maker) should ONLY be used for:
✅ Fixing failing tests in tests/ directory
✅ Creating test files in tests/ directory  
✅ Updating test configurations in tests/

FORBIDDEN: Using testing agents for source code modifications

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NEVER TRY TO BYPASS THIS PROTECTION
❌ No using sed/awk on source files
❌ No shell tricks or workarounds  
❌ No indirect modification methods

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ CORRECT APPROACH:

For SOURCE CODE work, use:
• hive-dev-fixer - Debug and fix source code
• hive-dev-coder - Implement new features
• hive-dev-planner - Plan implementations

For TEST work, use:
• hive-testing-fixer - Fix failing tests
• hive-testing-maker - Create new tests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REMEMBER: Testing agents are for TESTS only, not source code!"""
        
        # Block the Task call to testing agent
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny", 
                "permissionDecisionReason": error_message
            }
        }
        print(json.dumps(output))
        sys.exit(0)
    
    # Rest of the original logic for checking file paths
    # Check if the command is from a testing agent context based on path
    # The original logic checked file paths for tests/ or genie/ directories
    
    # For file operations (Write, Edit, MultiEdit)
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        # Original logic - this is NOT for testing agents, just general file operations
        # The hook already blocks testing agents at the Task level above
        sys.exit(0)  # Allow normal operations
    
    # For Bash commands - add check for sed/awk attempts on source by testing agents
    if tool_name == "Bash":
        # This is hard to determine if it's from a testing agent without context
        # But we can check for patterns that look suspicious
        command = tool_input.get("command", "")
        
        # If command contains testing agent patterns and tries to modify source
        if any(agent in command for agent in ["testing-fixer", "testing-maker"]):
            if any(cmd in command.lower() for cmd in ["sed", "awk"]) and \
               any(src in command for src in ["lib/", "api/", "ai/"]):
                error_message = """🚨 TESTING AGENT BYPASS ATTEMPT BLOCKED

⚠️ NEVER TRY TO BYPASS PROTECTION WITH SED/AWK

Testing agents cannot use shell commands to modify source code.
Use the correct agent type for source code modifications."""
                
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": error_message
                    }
                }
                print(json.dumps(output))
                sys.exit(0)
    
    # Allow everything else
    sys.exit(0)

if __name__ == "__main__":
    main()