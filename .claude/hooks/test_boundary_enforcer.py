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
    
    # Only apply to file-writing tools
    if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
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

VIOLATION: Testing agents (hive-testing-fixer/hive-testing-maker) should ONLY be used for:
- ✅ Fixing failing tests in tests/ directory
- ✅ Creating test files in tests/ directory  
- ✅ Updating test configurations in tests/

FORBIDDEN: Using testing agents for source code modifications

CORRECT APPROACH:
1. ✅ Use hive-dev-fixer for source code debugging
2. ✅ Use hive-dev-coder for source code implementation
3. ✅ Use testing agents ONLY for test-related work

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
    
    else:
        # For direct Edit/Write calls, check if we're in a testing agent context
        # by looking at the transcript for recent Task calls
        transcript_path = input_data.get("transcript_path", "")
        if not transcript_path or not os.path.exists(transcript_path):
            sys.exit(0)
        
        # Check recent transcript for testing agent activity
        is_testing_context = False
        try:
            with open(transcript_path, 'r') as f:
                lines = f.readlines()
                # Check last 10 lines for testing agent patterns
                recent_lines = lines[-10:] if len(lines) >= 10 else lines
                transcript_content = ''.join(recent_lines)
                
                testing_patterns = [
                    '"subagent_type":"hive-testing-fixer"',
                    '"subagent_type":"hive-testing-maker"',
                    '"subagent_type":"hive-hook-tester"',
                    '"subagent_type": "hive-testing-fixer"',
                    '"subagent_type": "hive-testing-maker"',
                    '"subagent_type": "hive-hook-tester"'
                ]
                
                for pattern in testing_patterns:
                    if pattern in transcript_content:
                        is_testing_context = True
                        break
        except Exception:
            sys.exit(0)  # If we can't read transcript, allow the operation
        
        if not is_testing_context:
            sys.exit(0)
    
    # We have a testing agent trying to modify a file - check boundaries
    try:
        abs_path = Path(file_path).resolve()
        project_root = Path(input_data.get("cwd", os.getcwd())).resolve()
        
        # Get relative path within project
        try:
            relative_path = abs_path.relative_to(project_root)
        except ValueError:
            # File is outside project, allow (might be temp files, etc.)
            sys.exit(0)
        
        # Check if file is in allowed directories
        allowed_prefixes = ["tests/", "genie/"]
        is_allowed = any(str(relative_path).startswith(prefix) for prefix in allowed_prefixes)
        
        if not is_allowed:
            # BLOCK: Testing agent trying to modify source code
            error_message = f"""🚨 TESTING AGENT BOUNDARY VIOLATION BLOCKED 🚨

FILE MODIFICATION DENIED: {relative_path}

VIOLATION: Testing agents (hive-testing-fixer/hive-testing-maker/hive-hook-tester) are FORBIDDEN from modifying files outside tests/ and genie/ directories.

ALLOWED DIRECTORIES:
- ✅ tests/ - All test files and test configurations  
- ✅ genie/ - Analysis reports, experimental code, documentation

FORBIDDEN: Source code files ({relative_path})

CORRECT APPROACH:
1. ✅ Fix test expectations/mocks to match existing source code behavior
2. ✅ Update test setup and configuration in tests/ directory  
3. ✅ Create automagik-forge tasks for any source code issues found
4. ✅ Use genie/experiments/ for prototype solutions

REMEMBER: Testing agents fix TESTS and create ANALYSIS, not source code!"""
            
            # Use JSON output to block with detailed feedback
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": error_message
                }
            }
            print(json.dumps(output))
            sys.exit(0)
    
    except Exception:
        # If path resolution fails, allow the operation
        sys.exit(0)
    
    # File is in allowed directory - allow the operation
    sys.exit(0)

if __name__ == "__main__":
    main()