"""Infrastructure adapter for Git operations.

This module provides an abstraction layer for Git operations needed by
the pre-commit validation system. It handles detection of staged changes
and maps Git status codes to domain entities.
"""

import os
import subprocess

from ..domain.entities import FileChange, FileOperation


class GitAdapter:
    """Adapter for Git operations and staged file detection.
    
    This class provides methods to interact with Git repository state
    and convert Git information into domain entities that can be used
    by the validation system.
    """

    def __init__(self, repo_path: str | None = None):
        """Initialize Git adapter with optional repository path.
        
        Args:
            repo_path: Path to Git repository, uses current directory if None
        """
        self.repo_path = repo_path or os.getcwd()

    def get_staged_changes(self) -> list[FileChange]:
        """Get list of staged file changes from Git.
        
        Returns:
            List of FileChange objects representing staged modifications
            
        Raises:
            RuntimeError: If Git command fails or repository is invalid
        """
        try:
            # Get staged files with their status
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                return []

            changes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                try:
                    # Parse Git status line (e.g., "A\tfilename.py" or "M\tpath/file.txt")
                    parts = line.split("\t", 1)
                    if len(parts) != 2:
                        continue

                    status, path = parts
                    operation = self._map_git_status(status)

                    change = FileChange(
                        path=path,
                        operation=operation,
                        is_root_level=self._is_root_level(path),
                        file_extension=self._get_extension(path),
                        is_directory=self._is_directory(path)
                    )
                    changes.append(change)

                except ValueError as e:
                    # Skip malformed lines but continue processing
                    print(f"Warning: Skipping malformed Git status line: {line} ({e})")
                    continue

            return changes

        except subprocess.CalledProcessError as e:
            if e.returncode == 128:
                raise RuntimeError("Not a Git repository or Git not found")
            raise RuntimeError(f"Git command failed with code {e.returncode}: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Git command not found. Please ensure Git is installed and in PATH")

    def get_all_changes(self, compare_ref: str = "HEAD") -> list[FileChange]:
        """Get all changes compared to a specific reference.
        
        Args:
            compare_ref: Git reference to compare against (default: HEAD)
            
        Returns:
            List of FileChange objects representing all modifications
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", compare_ref],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                return []

            changes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue

                status, path = parts
                operation = self._map_git_status(status)

                change = FileChange(
                    path=path,
                    operation=operation,
                    is_root_level=self._is_root_level(path),
                    file_extension=self._get_extension(path),
                    is_directory=self._is_directory(path)
                )
                changes.append(change)

            return changes

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git diff command failed: {e}")

    def is_git_repository(self) -> bool:
        """Check if current directory is a Git repository.
        
        Returns:
            True if directory contains a valid Git repository
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_repository_root(self) -> str:
        """Get the root directory of the Git repository.
        
        Returns:
            Absolute path to repository root
            
        Raises:
            RuntimeError: If not in a Git repository
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("Not in a Git repository")

    def _map_git_status(self, status: str) -> FileOperation:
        """Map Git status code to FileOperation enum.
        
        Args:
            status: Git status code (A, M, D, R, etc.)
            
        Returns:
            Corresponding FileOperation enum value
        """
        # Handle multi-character status codes (e.g., "R100")
        first_char = status[0] if status else "M"

        mapping = {
            "A": FileOperation.CREATE,
            "M": FileOperation.MODIFY,
            "D": FileOperation.DELETE,
            "R": FileOperation.RENAME,
            "C": FileOperation.CREATE,  # Copy treated as create
            "T": FileOperation.MODIFY,  # Type change treated as modify
        }

        return mapping.get(first_char, FileOperation.MODIFY)

    def _is_root_level(self, path: str) -> bool:
        """Check if file path is at repository root level.
        
        Args:
            path: File path relative to repository root
            
        Returns:
            True if file is at root level (no directory separators)
        """
        # Normalize path separators for cross-platform compatibility
        normalized_path = path.replace("\\", "/")
        return "/" not in normalized_path

    def _get_extension(self, path: str) -> str | None:
        """Extract file extension from path.
        
        Args:
            path: File path to extract extension from
            
        Returns:
            File extension including dot (e.g., '.py'), or None if no extension
        """
        _, ext = os.path.splitext(path)
        return ext if ext else None

    def _is_directory(self, path: str) -> bool:
        """Determine if path represents a directory.
        
        Args:
            path: File path to check
            
        Returns:
            True if path represents a directory
        """
        # Check if file exists and is directory
        full_path = os.path.join(self.repo_path, path)
        if os.path.exists(full_path):
            return os.path.isdir(full_path)

        # For non-existent paths, assume directory if ends with /
        return path.endswith("/") or path.endswith("\\")

    def get_current_branch(self) -> str:
        """Get name of current Git branch.
        
        Returns:
            Name of current branch
            
        Raises:
            RuntimeError: If unable to determine branch name
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Fallback method for older Git versions
            try:
                result = subprocess.run(
                    ["git", "symbolic-ref", "--short", "HEAD"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError:
                raise RuntimeError("Unable to determine current Git branch")

    def has_staged_changes(self) -> bool:
        """Check if repository has any staged changes.
        
        Returns:
            True if there are staged changes, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                check=False, cwd=self.repo_path,
                capture_output=True
            )
            # Git diff --quiet returns 0 if no differences, 1 if differences
            return result.returncode != 0
        except subprocess.CalledProcessError:
            # If command fails, assume there are changes to be safe
            return True
