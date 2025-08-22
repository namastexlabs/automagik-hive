#!/usr/bin/env python3
"""
Naming Convention Validation Hook

CRITICAL PREVENTION: Pre-creation validation to prevent forbidden naming patterns.
USER FEEDBACK: "its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, enhanced, etc"

This hook integrates with the agent environment to prevent naming convention violations
before they occur in any file or code creation operation.
"""

import json
import sys
import os
import re
from pathlib import Path

def main():
    """Main hook execution."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only apply to file-writing tools and Bash
    if tool_name not in ["Write", "Edit", "MultiEdit", "Bash"]:
        sys.exit(0)
    
    # For Bash commands, check for sed/awk bypass attempts
    if tool_name == "Bash":
        command = tool_input.get("command", "").lower()
        # Check for sed/awk attempts to create files with forbidden names
        if any(cmd in command for cmd in ["sed", "awk"]):
            if any(pattern in command for pattern in ["fixed", "enhanced", "improved", "updated", "refactored"]):
                error_message = """🚨 NAMING CONVENTION BYPASS ATTEMPT BLOCKED 🚨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NEVER TRY TO BYPASS NAMING RULES WITH SED/AWK

Using shell commands to create files with forbidden naming patterns 
(fixed, enhanced, improved, updated, refactored) is NOT allowed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ FORBIDDEN PATTERNS:
• NO files/functions with: fixed, enhanced, improved, updated, refactored
• NO using sed/awk to bypass these rules
• NO shell tricks or workarounds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ CORRECT APPROACH:
• Use clean, descriptive names without status suffixes
• Name files based on what they DO, not their version
• Example: auth.py (NOT auth_fixed.py)
• Example: process_data() (NOT process_data_enhanced())

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 USER DIRECTIVE: "its completly forbidden, across all codebase, 
to write files and functions etc, with fixed, enhanced, etc"

REMEMBER: Clean naming is mandatory, not optional!"""
                
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": error_message
                    }
                }
                print(json.dumps(output))
                sys.exit(0)
        # Allow other Bash commands
        sys.exit(0)
    
    # For file operations, validate the file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    
    # Check for forbidden patterns in the file name
    forbidden_patterns = ["fixed", "enhanced", "improved", "updated", "refactored"]
    file_name = Path(file_path).name.lower()
    
    for pattern in forbidden_patterns:
        if pattern in file_name:
            error_message = f"""🚨 NAMING CONVENTION VIOLATION BLOCKED 🚨

FILE CREATION DENIED: {file_path}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ FORBIDDEN NAMING PATTERN DETECTED: '{pattern}'

This violates our strict naming conventions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ FORBIDDEN PATTERNS:
• NO files/functions with: fixed, enhanced, improved, updated, refactored
• NO version indicators in names
• NO modification status suffixes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NEVER TRY TO BYPASS THIS PROTECTION
❌ No using sed/awk to create forbidden names
❌ No shell tricks or workarounds
❌ No indirect naming methods

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ CORRECT APPROACH:
• Use clean, descriptive names without status suffixes
• Name based on functionality, not version
• Examples:
  - auth.py ✅ (NOT auth_fixed.py ❌)
  - process_data() ✅ (NOT process_data_enhanced() ❌)
  - user_service.py ✅ (NOT user_service_improved.py ❌)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 USER DIRECTIVE: "its completly forbidden, across all codebase, 
to write files and functions etc, with fixed, enhanced, etc"

🎯 BEHAVIORAL LEARNING: Zero tolerance for modification-status naming

REMEMBER: Clean naming is mandatory, not optional!"""
            
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": error_message
                }
            }
            print(json.dumps(output))
            sys.exit(0)
    
    # Validation passed
    sys.exit(0)


if __name__ == "__main__":
    main()