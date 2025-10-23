#!/usr/bin/env python3
"""
Auto-Format Hook for Claude Code
==================================

Automatically formats Python files with ruff before commits to ensure
consistent code style and prevent CI formatting failures.

Hook Type: PreToolUse (Write, Edit, MultiEdit)
Priority: Runs after validation hooks, before file modifications are committed

Features:
- Auto-formats Python files with `ruff format`
- Only formats files being modified in current operation
- Skips formatting if ruff is not available
- Provides clear feedback on formatting actions
- Logs all operations for debugging

Environment Variables:
- AUTO_FORMAT_DISABLED=true - Disable auto-formatting (use sparingly)
- RUFF_FORMAT_CHECK_ONLY=true - Check formatting without applying changes

Usage:
This hook runs automatically on Write/Edit/MultiEdit operations.
No manual invocation needed.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Debug logging
LOG_FILE = "/tmp/auto_format_hook_debug.log"


def log(message: str) -> None:
    """Write debug log entry."""
    try:
        with open(LOG_FILE, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # Silent fail on logging errors


def is_python_file(file_path: str) -> bool:
    """Check if file is a Python file."""
    return file_path.endswith(".py")


def find_uv_executable() -> Optional[str]:
    """Find uv executable in the system."""
    try:
        result = subprocess.run(
            ["which", "uv"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        log(f"Error finding uv: {e}")
    return None


def format_file(file_path: str, project_dir: str) -> Dict[str, any]:
    """
    Format a Python file using ruff.

    Returns:
        Dict with 'success', 'formatted', and 'message' keys
    """
    # Check if auto-format is disabled
    if os.getenv("AUTO_FORMAT_DISABLED") == "true":
        log(f"Auto-format disabled, skipping {file_path}")
        return {
            "success": True,
            "formatted": False,
            "message": "Auto-format disabled via environment variable",
        }

    # Find uv executable
    uv_path = find_uv_executable()
    if not uv_path:
        log("UV not found, skipping auto-format")
        return {
            "success": True,
            "formatted": False,
            "message": "UV not available, skipping format",
        }

    # Check-only mode
    check_only = os.getenv("RUFF_FORMAT_CHECK_ONLY") == "true"

    try:
        # Build command
        cmd = [uv_path, "run", "ruff", "format"]
        if check_only:
            cmd.append("--check")
        cmd.append(file_path)

        # Run ruff format
        log(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            if check_only:
                log(f"✓ {file_path} already formatted")
                return {
                    "success": True,
                    "formatted": False,
                    "message": "Already formatted",
                }
            else:
                log(f"✓ Formatted {file_path}")
                return {
                    "success": True,
                    "formatted": True,
                    "message": "File formatted successfully",
                }
        else:
            # Check if file needs formatting (exit code 1 in check mode)
            if check_only and result.returncode == 1:
                log(f"⚠ {file_path} needs formatting")
                return {
                    "success": True,
                    "formatted": False,
                    "message": "File needs formatting (check mode)",
                }

            log(f"✗ Ruff format failed for {file_path}: {result.stderr}")
            return {
                "success": False,
                "formatted": False,
                "message": f"Formatting failed: {result.stderr}",
            }

    except subprocess.TimeoutExpired:
        log(f"✗ Timeout formatting {file_path}")
        return {
            "success": False,
            "formatted": False,
            "message": "Formatting timed out",
        }
    except Exception as e:
        log(f"✗ Error formatting {file_path}: {e}")
        return {
            "success": False,
            "formatted": False,
            "message": f"Error: {str(e)}",
        }


def extract_file_paths(tool_input: Dict) -> List[str]:
    """Extract file paths from tool input."""
    file_paths = []

    # Handle Write tool
    if "file_path" in tool_input:
        file_paths.append(tool_input["file_path"])

    # Handle Edit tool
    if "file_path" in tool_input:
        file_paths.append(tool_input["file_path"])

    # Handle MultiEdit tool (if exists)
    if "files" in tool_input:
        for file_entry in tool_input["files"]:
            if isinstance(file_entry, dict) and "file_path" in file_entry:
                file_paths.append(file_entry["file_path"])
            elif isinstance(file_entry, str):
                file_paths.append(file_entry)

    return file_paths


def main():
    """Main hook entry point."""
    log("=" * 80)
    log("Auto-Format Hook Started")

    try:
        # Read hook input from stdin
        hook_input = json.loads(sys.stdin.read())
        log(f"Hook input: {json.dumps(hook_input, indent=2)}")

        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", {})

        # Only process Write/Edit/MultiEdit operations
        if tool_name not in ["Write", "Edit", "MultiEdit"]:
            log(f"Skipping non-write tool: {tool_name}")
            sys.exit(0)

        # Get project directory
        project_dir = os.getenv("CLAUDE_PROJECT_DIR", os.getcwd())
        log(f"Project directory: {project_dir}")

        # Extract file paths
        file_paths = extract_file_paths(tool_input)
        log(f"Files to process: {file_paths}")

        # Filter Python files
        python_files = [f for f in file_paths if is_python_file(f)]

        if not python_files:
            log("No Python files to format")
            sys.exit(0)

        log(f"Python files to format: {python_files}")

        # Format each file
        formatted_count = 0
        failed_files = []

        for file_path in python_files:
            result = format_file(file_path, project_dir)

            if result["success"]:
                if result["formatted"]:
                    formatted_count += 1
                    print(f"✓ Formatted: {file_path}")
            else:
                failed_files.append((file_path, result["message"]))
                print(f"✗ Failed to format: {file_path} - {result['message']}")

        # Summary
        if formatted_count > 0:
            log(f"✓ Auto-formatted {formatted_count} file(s)")
            print(f"\n✓ Auto-formatted {formatted_count} Python file(s)")

        if failed_files:
            log(f"✗ Failed to format {len(failed_files)} file(s)")
            print(f"\n⚠ Warning: {len(failed_files)} file(s) failed formatting")
            for file_path, message in failed_files:
                print(f"  - {file_path}: {message}")

        # Exit successfully (don't block operations even if formatting fails)
        log("Auto-Format Hook Completed Successfully")
        sys.exit(0)

    except Exception as e:
        log(f"✗ Hook error: {e}")
        import traceback
        log(traceback.format_exc())
        # Don't block on hook errors
        print(f"⚠ Auto-format hook error: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
