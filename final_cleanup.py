#!/usr/bin/env python3

"""
Final cleanup script to remove all dead code files from the first middleware attempt.
These files were replaced by Agno's session_state pattern implementation.
"""

import os
import shutil

def main():
    print("🧹 Final cleanup of dead code files...")
    
    # Dead code files to remove
    dead_files = [
        "api/middleware/context_middleware.py",
        "context/session_context_manager.py",
        "db/tables/user_session_context.py", 
        "db/migrations/versions/002_add_user_session_context.py",
        "CLEANUP_DEAD_CODE.md",
        "cleanup_dead_code.sh",
        "remove_dead_code.py",
        "direct_cleanup.py",
        "final_cleanup.py"  # Remove this script too
    ]
    
    removed_count = 0
    
    for file_path in dead_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
        else:
            print(f"⚠️ Not found: {file_path}")
    
    # Remove empty middleware directory
    middleware_dir = "api/middleware"
    if os.path.exists(middleware_dir):
        try:
            if not os.listdir(middleware_dir):
                os.rmdir(middleware_dir)
                print(f"✅ Removed empty directory: {middleware_dir}")
            else:
                print(f"⚠️ Directory not empty: {middleware_dir}")
        except Exception as e:
            print(f"❌ Error removing directory {middleware_dir}: {e}")
    
    print(f"\n🎯 Cleanup complete! Removed {removed_count} files.")
    print("📝 Current implementation uses Agno's session_state pattern")
    print("🚀 System now uses elegant session_state instead of complex middleware")

if __name__ == "__main__":
    main()