#!/usr/bin/env python3

import os
import sys

def main():
    # Files to remove
    files = [
        "/home/namastex/workspace/genie-agents/api/middleware/context_middleware.py",
        "/home/namastex/workspace/genie-agents/context/session_context_manager.py",
        "/home/namastex/workspace/genie-agents/db/tables/user_session_context.py",
        "/home/namastex/workspace/genie-agents/db/migrations/versions/002_add_user_session_context.py",
        "/home/namastex/workspace/genie-agents/CLEANUP_DEAD_CODE.md",
        "/home/namastex/workspace/genie-agents/cleanup_dead_code.sh",
        "/home/namastex/workspace/genie-agents/remove_dead_code.py",
        "/home/namastex/workspace/genie-agents/temp_cleanup.py",
        "/home/namastex/workspace/genie-agents/cleanup_now.py"
    ]
    
    print("🧹 Removing dead code files...")
    
    for file_path in files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"❌ Error removing {os.path.basename(file_path)}: {e}")
        else:
            print(f"⚠️ File not found: {os.path.basename(file_path)}")
    
    # Check if middleware directory is empty and remove it
    middleware_dir = "/home/namastex/workspace/genie-agents/api/middleware"
    if os.path.exists(middleware_dir):
        try:
            if not os.listdir(middleware_dir):
                os.rmdir(middleware_dir)
                print("✅ Removed empty middleware directory")
            else:
                print("⚠️ Middleware directory not empty, keeping it")
        except Exception as e:
            print(f"❌ Error with middleware directory: {e}")
    
    print("🎯 Dead code cleanup complete!")
    print("📝 The middleware approach was replaced by Agno's session_state pattern")
    print("🚀 System now uses elegant session_state instead of complex middleware")

if __name__ == "__main__":
    main()