#!/usr/bin/env python3

import os
import shutil

def cleanup_dead_code():
    """Remove dead code files."""
    base_path = "/home/namastex/workspace/genie-agents"
    
    # Files to remove
    files_to_remove = [
        "api/middleware/context_middleware.py",
        "context/session_context_manager.py",
        "db/tables/user_session_context.py", 
        "db/migrations/versions/002_add_user_session_context.py",
        "CLEANUP_DEAD_CODE.md",
        "cleanup_dead_code.sh",
        "remove_dead_code.py"
    ]
    
    # Directories to remove if empty
    dirs_to_check = [
        "api/middleware"
    ]
    
    print("🧹 Cleaning up dead code files...")
    
    for file_path in files_to_remove:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"✅ Removed: {file_path}")
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")
    
    # Check directories
    for dir_path in dirs_to_check:
        full_path = os.path.join(base_path, dir_path)
        if os.path.exists(full_path):
            try:
                # Remove if empty
                if not os.listdir(full_path):
                    os.rmdir(full_path)
                    print(f"✅ Removed empty directory: {dir_path}")
                else:
                    print(f"⚠️ Directory not empty: {dir_path}")
            except Exception as e:
                print(f"❌ Error removing directory {dir_path}: {e}")
    
    print("🎯 Dead code cleanup complete!")

if __name__ == "__main__":
    cleanup_dead_code()