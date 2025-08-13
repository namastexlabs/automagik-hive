#!/usr/bin/env python3
"""
Testing Agent File Boundary Enforcer Hook

Prevents genie-testing-fixer agents from modifying files outside tests/ directory.
Forces them to create automagik-forge tasks for source code issues instead.
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

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only apply to file-writing tools
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)
    
    # Check if this is a testing agent by looking at session context
    # We'll check the transcript for recent Task tool calls with genie-testing-* agents
    transcript_path = input_data.get("transcript_path", "")
    
    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)
    
    # Read recent transcript to detect if we're in a testing agent context
    is_testing_agent_context = False
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
            # Check last 50 lines for testing agent spawning
            recent_lines = lines[-50:] if len(lines) >= 50 else lines
            transcript_content = ''.join(recent_lines)
            
            # Look for genie-testing-fixer or genie-testing-maker agent spawning
            if any(agent in transcript_content for agent in [
                '"subagent_type": "genie-testing-fixer"',
                '"subagent_type": "genie-testing-maker"',
                'genie-testing-fixer',
                'genie-testing-maker'
            ]):
                is_testing_agent_context = True
    except Exception:
        # If we can't read transcript, allow the operation
        sys.exit(0)
    
    if not is_testing_agent_context:
        sys.exit(0)
    
    # Get the file path being modified
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    
    # Convert to absolute path and normalize
    try:
        abs_path = Path(file_path).resolve()
        project_root = Path(input_data.get("cwd", os.getcwd())).resolve()
        
        # Check if file is within project
        try:
            relative_path = abs_path.relative_to(project_root)
        except ValueError:
            # File is outside project, allow (might be temp files, etc.)
            sys.exit(0)
        
        # Check if the file is outside tests/ directory
        if not str(relative_path).startswith("tests/"):
            # BLOCK: Testing agent trying to modify source code
            error_message = f"""
🚨 TESTING AGENT BOUNDARY VIOLATION BLOCKED 🚨

FILE MODIFICATION DENIED: {relative_path}

VIOLATION: Testing agents (genie-testing-fixer/genie-testing-maker) are FORBIDDEN from modifying files outside tests/ directory.

CORRECT APPROACH:
1. ✅ Fix test expectations/mocks to match existing source code behavior
2. ✅ Update test setup and configuration only  
3. ✅ Create automagik-forge tasks for any source code issues found
4. ✅ Only modify files in tests/ directory

AUTOMAGIK-FORGE TASK CREATION:
If source code needs fixing, create a task using:
```
mcp__automagik_forge__create_task(
    project_id="your-project-id",
    title="Fix source code issue: [brief description]", 
    description="Source code modification needed: {relative_path}\\n\\nIssue: [describe the problem]\\n\\nRequested by: genie-testing-fixer during test repair",
    wish_id="test-repair-source-fix"
)
```

DOMAIN BOUNDARIES:
- genie-testing-fixer: ONLY tests/ directory modifications
- genie-dev-fixer: Source code debugging and fixes
- genie-dev-coder: Source code implementation

REMEMBER: Testing agents fix TESTS, not source code!
            """.strip()
            
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
    
    except Exception as e:
        # If path resolution fails, allow the operation
        sys.exit(0)
    
    # File is in tests/ directory or not a testing agent context - allow
    sys.exit(0)

if __name__ == "__main__":
    main()