#!/usr/bin/env python3
"""
Automagik Hive Git Hooks Setup and Management Script

This script provides utilities to manage git hooks for the Automagik Hive project.
It can install, test, and configure the pre-commit hook system.
"""

import os
import stat
import subprocess
import sys
from pathlib import Path


class GitHookManager:
    """Manages git hooks for the Automagik Hive project."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.git_dir = self.project_root / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        self.pre_commit_hook = self.hooks_dir / "pre-commit"

    def check_git_repo(self) -> bool:
        """Check if we're in a git repository."""
        return self.git_dir.exists() and self.git_dir.is_dir()

    def check_automagik_project(self) -> bool:
        """Check if we're in an Automagik Hive project."""
        return (self.project_root / "pyproject.toml").exists()

    def get_git_status(self) -> tuple[list[str], list[str], list[str]]:
        """Get git status for staged, modified, and untracked files."""
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            staged = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            # Get modified files
            result = subprocess.run(
                ["git", "diff", "--name-only"], cwd=self.project_root, capture_output=True, text=True, check=True
            )
            modified = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            # Get untracked files
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            untracked = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            return staged, modified, untracked

        except subprocess.CalledProcessError:
            return [], [], []

    def check_hook_exists(self) -> bool:
        """Check if the pre-commit hook exists."""
        return self.pre_commit_hook.exists()

    def check_hook_executable(self) -> bool:
        """Check if the pre-commit hook is executable."""
        if not self.check_hook_exists():
            return False
        return os.access(self.pre_commit_hook, os.X_OK)

    def make_hook_executable(self) -> bool:
        """Make the pre-commit hook executable."""
        if not self.check_hook_exists():
            return False

        try:
            # Add execute permissions
            current_permissions = os.stat(self.pre_commit_hook).st_mode
            os.chmod(self.pre_commit_hook, current_permissions | stat.S_IEXEC)
            return True
        except OSError:
            return False

    def test_hook(self, dry_run: bool = True) -> bool:
        """Test the pre-commit hook."""
        if not self.check_hook_exists():
            return False

        if not self.check_hook_executable():
            if not self.make_hook_executable():
                return False

        # Check if there are any staged files
        staged, _, _ = self.get_git_status()

        if not staged:
            if not dry_run:
                # Create a temporary test file
                test_file = self.project_root / "test_hook_temp.py"
                test_file.write_text("# Temporary test file\ndef hello():\n    return 'world'\n")

                try:
                    subprocess.run(["git", "add", str(test_file)], cwd=self.project_root, check=True)
                except subprocess.CalledProcessError:
                    test_file.unlink(missing_ok=True)
                    return False

        try:
            # Run the hook directly
            result = subprocess.run(
                [str(self.pre_commit_hook)],
                cwd=self.project_root,
                capture_output=False,  # Let it show output directly
                text=True,
                check=False,  # Don't raise exception on non-zero exit
            )

            if result.returncode == 0:
                return True
            else:
                return False

        except Exception:
            return False
        finally:
            # Clean up temporary test file if it was created
            if not staged and not dry_run:
                test_file = self.project_root / "test_hook_temp.py"
                if test_file.exists():
                    try:
                        subprocess.run(["git", "reset", "HEAD", str(test_file)], cwd=self.project_root, check=True)
                        test_file.unlink()
                    except subprocess.CalledProcessError:
                        pass

    def show_hook_status(self) -> None:
        """Show the current status of git hooks."""

        # Show git status
        staged, modified, untracked = self.get_git_status()

        if staged:
            pass

    def enable_hook(self) -> bool:
        """Enable the pre-commit hook."""
        if not self.check_git_repo():
            return False

        if not self.check_automagik_project():
            return False

        if not self.check_hook_exists():
            return False

        return self.make_hook_executable()

    def disable_hook(self) -> bool:
        """Disable the pre-commit hook."""
        if not self.check_hook_exists():
            return True

        try:
            # Remove execute permissions
            current_permissions = os.stat(self.pre_commit_hook).st_mode
            os.chmod(self.pre_commit_hook, current_permissions & ~stat.S_IEXEC)
            return True
        except OSError:
            return False


def main():
    """Main entry point for the git hook management script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage git hooks for Automagik Hive project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_git_hooks.py status        # Show hook status
  python scripts/setup_git_hooks.py enable        # Enable pre-commit hook
  python scripts/setup_git_hooks.py disable       # Disable pre-commit hook  
  python scripts/setup_git_hooks.py test          # Test the pre-commit hook
  python scripts/setup_git_hooks.py test --run    # Test with actual staging
        """,
    )

    parser.add_argument("action", choices=["status", "enable", "disable", "test"], help="Action to perform")

    parser.add_argument("--run", action="store_true", help="For test action: actually stage files (not dry-run)")

    args = parser.parse_args()

    # Initialize hook manager
    manager = GitHookManager()

    if args.action == "status":
        manager.show_hook_status()

    elif args.action == "enable":
        success = manager.enable_hook()
        sys.exit(0 if success else 1)

    elif args.action == "disable":
        success = manager.disable_hook()
        sys.exit(0 if success else 1)

    elif args.action == "test":
        success = manager.test_hook(dry_run=not args.run)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
