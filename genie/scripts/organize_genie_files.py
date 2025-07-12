#!/usr/bin/env python3
"""
Organize genie/ folder files based on relevance and V2 development status
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base paths
GENIE_DIR = Path("/home/namastex/workspace/pagbank-multiagents/genie")
ACTIVE_DIR = GENIE_DIR / "active"
COMPLETED_DIR = GENIE_DIR / "completed"
ARCHIVE_DIR = COMPLETED_DIR / "archive"
REFERENCE_DIR = GENIE_DIR / "reference"

# Ensure directories exist
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

# Files to organize
files_to_organize = {
    # Files in active/ that should be archived (outdated V1 analysis)
    "active/agent-api-analysis.md": {
        "action": "archive",
        "reason": "V1 analysis comparing with official repo - outdated for V2"
    },
    "active/strategy-flaws-and-improvements.md": {
        "action": "archive", 
        "reason": "V1 strategy critique - no longer relevant for clean V2 rewrite"
    },
    
    # Files in active/ that should stay (current V2 work)
    "active/project-status.md": {
        "action": "keep",
        "reason": "Central V2 project tracking - actively used"
    },
    "active/agent-coordination.md": {
        "action": "keep",
        "reason": "Multi-agent coordination framework for V2 development"
    },
    
    # Root level files that should move to reference
    "csv_typification_analysis.md": {
        "action": "reference",
        "reason": "Useful CSV structure analysis for typification implementation"
    },
    "typification_hierarchy_analysis.md": {
        "action": "reference",
        "reason": "Detailed hierarchy documentation needed for V2 typification"
    },
    
    # The agno-demo-app folder
    "agno-demo-app/": {
        "action": "keep",
        "reason": "Reference implementation from Agno - needed for V2 patterns"
    },
    
    # Scripts folder
    "scripts/": {
        "action": "keep",
        "reason": "Contains utility scripts for task management"
    },
    
    # Task cards folder
    "task-cards/": {
        "action": "keep",
        "reason": "V2 implementation task cards - actively used"
    }
}

def move_file(src, dest_dir, filename=None):
    """Move file to destination directory"""
    src_path = GENIE_DIR / src
    if not src_path.exists():
        print(f"⚠️  File not found: {src}")
        return False
    
    if filename is None:
        filename = src_path.name
    
    dest_path = dest_dir / filename
    
    # Add date prefix if archiving
    if dest_dir == ARCHIVE_DIR:
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_prefix}-{filename}"
        dest_path = dest_dir / filename
    
    print(f"📦 Moving: {src} → {dest_path.relative_to(GENIE_DIR)}")
    
    # Create parent directories if needed
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Move the file
    shutil.move(str(src_path), str(dest_path))
    return True

def main():
    print("🧹 PagBank Genie Folder Organization Script")
    print("=" * 50)
    
    # Process each file
    for file_path, info in files_to_organize.items():
        action = info["action"]
        reason = info["reason"]
        
        print(f"\n📄 {file_path}")
        print(f"   Action: {action}")
        print(f"   Reason: {reason}")
        
        if action == "archive":
            move_file(file_path, ARCHIVE_DIR)
        elif action == "reference":
            move_file(file_path, REFERENCE_DIR)
        elif action == "keep":
            print(f"   ✅ Keeping in current location")
        elif action == "delete":
            src_path = GENIE_DIR / file_path
            if src_path.exists():
                print(f"   🗑️  Deleting: {file_path}")
                if src_path.is_dir():
                    shutil.rmtree(src_path)
                else:
                    os.remove(src_path)
    
    print("\n" + "=" * 50)
    print("✨ Organization complete!")
    
    # Report final structure
    print("\n📊 Final Structure:")
    print("\nactive/ (V2 development):")
    for f in sorted(ACTIVE_DIR.glob("*.md")):
        print(f"  - {f.name}")
    
    print("\nreference/ (patterns & documentation):")
    for f in sorted(REFERENCE_DIR.glob("*.md")):
        print(f"  - {f.name}")
    
    print("\ncompleted/archive/ (V1 historical):")
    archive_count = len(list(ARCHIVE_DIR.glob("*.md")))
    print(f"  - {archive_count} archived files")

if __name__ == "__main__":
    main()