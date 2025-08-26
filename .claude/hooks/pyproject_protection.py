#!/usr/bin/env python3
"""
PyProject Protection Hook - Prevents ALL modifications to pyproject.toml
"""

import json
import sys
import os
import re
from pathlib import Path

def is_readonly_operation(command: str) -> bool:
    """
    Determines if a bash command is a read-only operation on pyproject.toml.
    
    ALLOWED (read-only operations):
    - git show, git diff, git log operations
    - cat, head, tail, less, more file viewing
    - grep, ripgrep searching
    - file inspection commands
    
    BLOCKED (modification operations):
    - sed, awk editing
    - echo >> redirection
    - direct file modification
    """
    # Read-only git operations
    readonly_git_patterns = [
        r'\bgit\s+show\b',
        r'\bgit\s+diff\b', 
        r'\bgit\s+log\b',
        r'\bgit\s+blame\b',
        r'\bgit\s+cat-file\b'
    ]
    
    # Read-only file viewing commands (must start with command name)
    readonly_file_patterns = [
        r'^cat\s+.*pyproject\.toml',
        r'^head\s+.*pyproject\.toml',
        r'^tail\s+.*pyproject\.toml',
        r'^less\s+.*pyproject\.toml',
        r'^more\s+.*pyproject\.toml',
        r'^grep\s+.*pyproject\.toml',
        r'^rg\s+.*pyproject\.toml',
        r'^ripgrep\s+.*pyproject\.toml'
    ]
    
    # Modification operations (blocked)
    modification_patterns = [
        r'^sed\s+.*pyproject\.toml',
        r'^awk\s+.*pyproject\.toml',
        r'.*>>\s*pyproject\.toml',  # Any redirection to pyproject.toml
        r'.*>\s*pyproject\.toml',   # Any output redirection to pyproject.toml  
        r'^tee\s+.*pyproject\.toml',
        r'^perl\s+-i.*pyproject\.toml',
        r'^vim?\s+.*pyproject\.toml',
        r'^emacs\s+.*pyproject\.toml',
        r'^nano\s+.*pyproject\.toml'
    ]
    
    # Check for modification patterns first (these are always blocked)
    for pattern in modification_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False
    
    # Check for read-only patterns
    all_readonly_patterns = readonly_git_patterns + readonly_file_patterns
    for pattern in all_readonly_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    
    # Special case: git operations mentioning pyproject.toml are generally read-only
    # unless they involve commit, add, or other modification commands
    if re.search(r'\bgit\s+\w+.*pyproject\.toml', command, re.IGNORECASE):
        modification_git_patterns = [
            r'\bgit\s+add\b',
            r'\bgit\s+commit\b',
            r'\bgit\s+mv\b',
            r'\bgit\s+rm\b',
            r'\bgit\s+reset\s+.*--hard',
            r'\bgit\s+checkout\s+.*--\s*pyproject\.toml',  # checkout specific file
            r'\bgit\s+checkout\s+\w+\s+--\s*pyproject\.toml'  # checkout from specific commit
        ]
        
        for pattern in modification_git_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        
        # If it's git but not a modification command, likely read-only
        return True
    
    # Default: if pyproject.toml is mentioned but we can't categorize it, block it
    return False

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
            
            # Check if it's a read-only operation (allowed)
            if is_readonly_operation(command):
                # This is OK - read-only operations
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
❌ No sed, awk, or direct editing
❌ No scripts or indirect methods
❌ No environment variable tricks

✅ ALLOWED OPERATIONS:
• uv add/remove/sync (package management)
• git show/diff/log (read-only git)
• cat/head/tail (file viewing)
• grep/rg (searching)

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
