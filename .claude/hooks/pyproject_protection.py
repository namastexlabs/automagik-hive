#!/usr/bin/env python3
"""
PyProject Protection Hook - Prevents ALL modifications to pyproject.toml
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
    
    # Check for file-editing tools
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        if file_path:
            path = Path(file_path)
            if path.name == "pyproject.toml":
                # BLOCK ALL ATTEMPTS
                return block_modification(file_path, tool_name, "direct edit")
    
    # Check for Bash commands
    elif tool_name == "Bash":
        command = tool_input.get("command", "").lower()
        
        if "pyproject.toml" in command:
            # Check if it's a package management command (allowed)
            if any(safe_cmd in command for safe_cmd in ["uv add", "uv remove", "uv sync"]):
                # This is OK - package management commands
                sys.exit(0)
            else:
                # Any other command touching pyproject.toml is blocked
                return block_modification("pyproject.toml", "Bash", f"shell command")
    
    # Allow the operation if it doesn't involve pyproject.toml
    sys.exit(0)

def block_modification(file_path, tool_name, operation_type):
    """Block the modification and provide clear instructions."""
    
    error_message = """🚫 PYPROJECT.TOML MODIFICATION BLOCKED

⚠️ NEVER TRY TO BYPASS THIS PROTECTION
❌ No sed, awk, or shell commands
❌ No scripts or indirect methods
❌ No environment variable tricks

✅ FOR PACKAGE MANAGEMENT USE:
• uv add <package>
• uv add --dev <package>
• uv remove <package>
• uv sync

📋 FOR OTHER CHANGES:
Report to the human with:
1. WHAT needs changing
2. WHY it needs changing
3. EXACT changes required

The human will make the change manually."""
    
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": error_message
        }
    }
    print(json.dumps(output))
    sys.exit(0)

if __name__ == "__main__":
    main()
