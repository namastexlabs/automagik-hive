#!/usr/bin/env python3
"""
Hook to prevent creating files in the project root directory.
Forces use of appropriate subdirectories like /genie/ for documentation.
"""

import os
import sys
import json

def main():
    # Read the tool input from stdin
    tool_input = json.loads(sys.stdin.read())
    
    # Check if this is a Write tool (for creating new files)
    # MultiEdit and Edit are for existing files only, so they're allowed
    if tool_input.get("tool") == "Write":
        file_path = tool_input.get("file_path", "")
        
        # Get project root and normalize paths
        project_root = os.environ.get("CLAUDE_PROJECT_DIR", "/home/namastex/workspace/automagik-hive")
        file_path = os.path.abspath(file_path)
        project_root = os.path.abspath(project_root)
        
        # Check if file already exists - if it does, allow editing
        if os.path.exists(file_path):
            sys.exit(0)  # Allow editing existing files
        
        # Check if file is being created directly in project root
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # List of allowed new root files (configuration files that belong in root)
        allowed_root_files = [
            ".env", ".env.example", ".gitignore", "README.md", 
            "pyproject.toml", "Makefile", "docker-compose.yml",
            "CLAUDE.md", "AGENTS.md", "AGENTS.md"  # System documentation
        ]
        
        # Check if attempting to create NEW file in project root
        if file_dir == project_root and file_name not in allowed_root_files:
            print("🚫 ROOT DIRECTORY WRITE VIOLATION 🚫", file=sys.stderr)
            print("", file=sys.stderr)
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
            print("", file=sys.stderr)
            print("⚠️ FORBIDDEN: Creating NEW files in project root", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"❌ ATTEMPTED: {file_path}", file=sys.stderr)
            print("", file=sys.stderr)
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
            print("", file=sys.stderr)
            print("✅ USE THE /genie/ FOLDER INSTEAD:", file=sys.stderr)
            print("", file=sys.stderr)
            print("The /genie/ directory is YOUR workspace for all autonomous work!", file=sys.stderr)
            print("", file=sys.stderr)
            print("📂 /genie/wishes/      → Wish documents, plans, investigations", file=sys.stderr)
            print("                         Example: database_fix_investigation.md", file=sys.stderr)
            print("", file=sys.stderr)
            print("📂 /genie/ideas/       → Brainstorms, concepts, proposals", file=sys.stderr)
            print("                         Example: metrics_optimization_ideas.md", file=sys.stderr)
            print("", file=sys.stderr)
            print("📂 /genie/experiments/ → Test scripts, prototypes, experiments", file=sys.stderr)
            print("                         Example: test_metrics_collection.py", file=sys.stderr)
            print("", file=sys.stderr)
            print("📂 /genie/knowledge/   → Learnings, documentation, reports", file=sys.stderr)
            print("                         Example: bug_fix_report.md", file=sys.stderr)
            print("", file=sys.stderr)
            print("OTHER VALID LOCATIONS:", file=sys.stderr)
            print("📂 /tests/             → Pytest test files only", file=sys.stderr)
            print("📂 /docs/              → User-facing documentation", file=sys.stderr)
            print("📂 /scripts/           → Utility and automation scripts", file=sys.stderr)
            print("", file=sys.stderr)
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
            print("", file=sys.stderr)
            print("⚠️ PROJECT ROOT IS SACRED - Keep it clean!", file=sys.stderr)
            print("", file=sys.stderr)
            print("❌ NO: Creating random .md files in root", file=sys.stderr)
            print("❌ NO: Test scripts or experiments in root", file=sys.stderr)
            print("❌ NO: Temporary work files in root", file=sys.stderr)
            print("", file=sys.stderr)
            print("✅ YES: Use /genie/ for ALL your autonomous work", file=sys.stderr)
            print("✅ YES: Edit existing root files when needed", file=sys.stderr)
            print("✅ YES: Create files in appropriate subdirectories", file=sys.stderr)
            print("", file=sys.stderr)
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
            print("", file=sys.stderr)
            print("💡 TIP: When in doubt, use /genie/wishes/ for your work!", file=sys.stderr)
            sys.exit(1)
    
    # Allow the operation to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()