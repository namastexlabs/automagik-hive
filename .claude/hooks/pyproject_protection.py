#!/usr/bin/env python3
"""
PyProject Protection Hook - Prevents ALL modifications to pyproject.toml
"""

import json
import sys
import os
import re
from pathlib import Path

def is_file_operation_command(command: str) -> bool:
    """
    Determines if a bash command performs an ACTUAL file operation on pyproject.toml.

    Returns True ONLY if the command directly operates on the pyproject.toml file.
    Returns False if pyproject.toml is just mentioned in text/strings/documentation.

    ACTUAL FILE OPERATIONS (check these):
    - Direct file commands: cat, sed, awk, vim, nano, etc.
    - File redirections: >, >>, tee
    - Git file operations: add, commit, checkout, mv, rm
    - Package managers: uv add/remove/sync (allowed separately)

    NOT FILE OPERATIONS (ignore these):
    - Text in quoted strings: "pyproject.toml", 'pyproject.toml'
    - Text in heredocs: <<EOF ... pyproject.toml ... EOF
    - Documentation commands: gh issue create, echo "...", printf
    - Comments: # pyproject.toml
    """
    # Commands that are NEVER file operations (safe to ignore pyproject.toml mentions)
    safe_commands = [
        r'^gh\s+issue\s+create\b',     # GitHub issue creation
        r'^gh\s+pr\s+create\b',         # GitHub PR creation
        r'^echo\s+',                    # Echo statements
        r'^printf\s+',                  # Printf statements
        r'^curl\s+',                    # HTTP requests
        r'^wget\s+',                    # Downloads
    ]

    for pattern in safe_commands:
        if re.search(pattern, command, re.IGNORECASE):
            return False  # These commands don't perform file operations

    # Now check if pyproject.toml appears as an actual file target
    # (not just mentioned in quoted text)

    # Read-only git operations on pyproject.toml (allowed)
    readonly_git_patterns = [
        r'\bgit\s+show\b.*pyproject\.toml',
        r'\bgit\s+diff\b.*pyproject\.toml',
        r'\bgit\s+log\b.*pyproject\.toml',
        r'\bgit\s+blame\b.*pyproject\.toml',
        r'\bgit\s+cat-file\b.*pyproject\.toml'
    ]

    # Read-only file viewing commands targeting pyproject.toml (allowed)
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

    # Modification operations targeting pyproject.toml (blocked)
    modification_patterns = [
        r'^sed\s+.*pyproject\.toml',
        r'^awk\s+.*pyproject\.toml',
        r'>>\s*pyproject\.toml\b',      # Redirection to file
        r'>\s*pyproject\.toml\b',        # Output to file
        r'^tee\s+.*pyproject\.toml',
        r'^perl\s+-i.*pyproject\.toml',
        r'^vim?\s+.*pyproject\.toml',
        r'^emacs\s+.*pyproject\.toml',
        r'^nano\s+.*pyproject\.toml'
    ]

    # Git modification operations (blocked)
    modification_git_patterns = [
        r'\bgit\s+add\b.*pyproject\.toml',
        r'\bgit\s+commit\b.*pyproject\.toml',
        r'\bgit\s+mv\b.*pyproject\.toml',
        r'\bgit\s+rm\b.*pyproject\.toml',
        r'\bgit\s+reset\s+.*--hard.*pyproject\.toml',
        r'\bgit\s+checkout\s+.*--\s*pyproject\.toml',  # checkout specific file
    ]

    # Check if this is an actual file operation
    all_file_patterns = (readonly_git_patterns + readonly_file_patterns +
                         modification_patterns + modification_git_patterns)

    for pattern in all_file_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True  # This IS a file operation on pyproject.toml

    # If pyproject.toml is mentioned but no file operation patterns match,
    # it's probably just text in a string/comment
    return False

def is_readonly_operation(command: str) -> bool:
    """
    Determines if a bash command is a read-only operation on pyproject.toml.
    Only called if is_file_operation_command() returns True.
    """
    # Read-only git operations
    readonly_git_patterns = [
        r'\bgit\s+show\b',
        r'\bgit\s+diff\b',
        r'\bgit\s+log\b',
        r'\bgit\s+blame\b',
        r'\bgit\s+cat-file\b'
    ]

    # Read-only file viewing commands
    readonly_file_patterns = [
        r'^cat\s+',
        r'^head\s+',
        r'^tail\s+',
        r'^less\s+',
        r'^more\s+',
        r'^grep\s+',
        r'^rg\s+',
        r'^ripgrep\s+'
    ]

    # Check for read-only patterns
    all_readonly_patterns = readonly_git_patterns + readonly_file_patterns
    for pattern in all_readonly_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True

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
        command = tool_input.get("command", "")

        # Only check if this is an ACTUAL file operation on pyproject.toml
        # (not just a mention in text/strings)
        if "pyproject.toml" in command.lower():
            # First: Check if it's a package management command (allowed)
            if any(safe_cmd in command.lower() for safe_cmd in ["uv add", "uv remove", "uv sync"]):
                # This is OK - package management commands
                sys.exit(0)

            # Second: Check if this is an actual file operation
            if not is_file_operation_command(command):
                # Not a file operation - just mentioned in text/documentation
                # This is OK - allow it
                sys.exit(0)

            # Third: If it IS a file operation, check if it's read-only
            if is_readonly_operation(command):
                # This is OK - read-only file operations
                sys.exit(0)
            else:
                # Block: This is a modification file operation
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
