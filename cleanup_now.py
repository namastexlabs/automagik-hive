import os
import subprocess

# Remove files
files = [
    "/home/namastex/workspace/genie-agents/api/middleware/context_middleware.py",
    "/home/namastex/workspace/genie-agents/context/session_context_manager.py",
    "/home/namastex/workspace/genie-agents/db/tables/user_session_context.py",
    "/home/namastex/workspace/genie-agents/db/migrations/versions/002_add_user_session_context.py",
    "/home/namastex/workspace/genie-agents/CLEANUP_DEAD_CODE.md",
    "/home/namastex/workspace/genie-agents/cleanup_dead_code.sh",
    "/home/namastex/workspace/genie-agents/remove_dead_code.py"
]

for file in files:
    if os.path.exists(file):
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except Exception as e:
            print(f"Error: {e}")

# Check if middleware directory is empty and remove it
middleware_dir = "/home/namastex/workspace/genie-agents/api/middleware"
if os.path.exists(middleware_dir):
    try:
        os.rmdir(middleware_dir)
        print("Removed empty middleware directory")
    except Exception as e:
        print(f"Middleware directory not empty or error: {e}")

print("Cleanup complete!")