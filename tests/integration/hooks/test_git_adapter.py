"""Tests for the GitAdapter infrastructure layer.

This module tests the Git integration functionality, ensuring proper
detection and mapping of staged changes to domain entities.
"""

import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.hooks.domain.entities import FileOperation
from src.hooks.infrastructure.git_adapter import GitAdapter


class TestGitAdapter:
    """Test suite for the GitAdapter class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for Git operations
        self.test_dir = tempfile.mkdtemp()
        self.adapter = GitAdapter(self.test_dir)

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_get_staged_changes_empty(self, mock_run):
        """Test get_staged_changes with no staged files."""
        # Mock empty git diff output
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        changes = self.adapter.get_staged_changes()

        assert len(changes) == 0
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--name-status"],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_get_staged_changes_single_file(self, mock_run):
        """Test get_staged_changes with single staged file."""
        # Mock git diff output for single file
        mock_run.return_value = MagicMock(stdout="A\tREADME.md\n", returncode=0)

        changes = self.adapter.get_staged_changes()

        assert len(changes) == 1
        change = changes[0]
        assert change.path == "README.md"
        assert change.operation == FileOperation.CREATE
        assert change.is_root_level is True
        assert change.file_extension == ".md"
        assert change.is_directory is False

    @patch("subprocess.run")
    def test_get_staged_changes_multiple_files(self, mock_run):
        """Test get_staged_changes with multiple staged files."""
        # Mock git diff output for multiple files
        mock_run.return_value = MagicMock(
            stdout="A\tREADME.md\nM\tpyproject.toml\nD\told_file.py\nR\trenamed.txt\n",
            returncode=0,
        )

        changes = self.adapter.get_staged_changes()

        assert len(changes) == 4

        # Check each file
        readme_change = next(c for c in changes if c.path == "README.md")
        assert readme_change.operation == FileOperation.CREATE
        assert readme_change.is_root_level is True

        pyproject_change = next(c for c in changes if c.path == "pyproject.toml")
        assert pyproject_change.operation == FileOperation.MODIFY
        assert pyproject_change.is_root_level is True

        old_file_change = next(c for c in changes if c.path == "old_file.py")
        assert old_file_change.operation == FileOperation.DELETE
        assert old_file_change.is_root_level is True

        renamed_change = next(c for c in changes if c.path == "renamed.txt")
        assert renamed_change.operation == FileOperation.RENAME
        assert renamed_change.is_root_level is True

    @patch("subprocess.run")
    def test_get_staged_changes_subdirectory_files(self, mock_run):
        """Test get_staged_changes with files in subdirectories."""
        # Mock git diff output for subdirectory files
        mock_run.return_value = MagicMock(
            stdout="A\tlib/utils.py\nM\tsrc/hooks/domain/entities.py\nA\ttests/test_something.py\n",
            returncode=0,
        )

        changes = self.adapter.get_staged_changes()

        assert len(changes) == 3

        # All should be non-root level
        for change in changes:
            assert change.is_root_level is False

        # Check specific files
        utils_change = next(c for c in changes if c.path == "lib/utils.py")
        assert utils_change.file_extension == ".py"
        assert utils_change.operation == FileOperation.CREATE

        entities_change = next(
            c for c in changes if c.path == "src/hooks/domain/entities.py"
        )
        assert entities_change.file_extension == ".py"
        assert entities_change.operation == FileOperation.MODIFY

    @patch("subprocess.run")
    def test_get_staged_changes_git_error(self, mock_run):
        """Test get_staged_changes handles Git command errors."""
        # Mock git command failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="fatal: not a git repository"
        )

        with pytest.raises(RuntimeError, match="Git command failed"):
            self.adapter.get_staged_changes()

    @patch("subprocess.run")
    def test_get_staged_changes_git_not_found(self, mock_run):
        """Test get_staged_changes handles missing Git."""
        # Mock git command not found
        mock_run.side_effect = FileNotFoundError("git not found")

        with pytest.raises(RuntimeError, match="Git command not found"):
            self.adapter.get_staged_changes()

    @patch("subprocess.run")
    def test_get_staged_changes_malformed_line(self, mock_run):
        """Test get_staged_changes handles malformed Git output."""
        # Mock git diff output with malformed line
        mock_run.return_value = MagicMock(
            stdout="A\tREADME.md\nMALFORMED_LINE\nM\tpyproject.toml\n", returncode=0
        )

        changes = self.adapter.get_staged_changes()

        # Should skip malformed line and process valid ones
        assert len(changes) == 2
        paths = [c.path for c in changes]
        assert "README.md" in paths
        assert "pyproject.toml" in paths

    @patch("subprocess.run")
    def test_is_git_repository_true(self, mock_run):
        """Test is_git_repository returns True for valid repo."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.adapter.is_git_repository()

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--git-dir"],
            cwd=self.test_dir,
            capture_output=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_is_git_repository_false(self, mock_run):
        """Test is_git_repository returns False for non-repo."""
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")

        result = self.adapter.is_git_repository()

        assert result is False

    @patch("subprocess.run")
    def test_get_repository_root(self, mock_run):
        """Test get_repository_root returns correct path."""
        mock_run.return_value = MagicMock(stdout="/path/to/repo\n", returncode=0)

        root = self.adapter.get_repository_root()

        assert root == "/path/to/repo"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_get_repository_root_error(self, mock_run):
        """Test get_repository_root handles error."""
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")

        with pytest.raises(RuntimeError, match="Not in a Git repository"):
            self.adapter.get_repository_root()

    def test_map_git_status_operations(self):
        """Test _map_git_status correctly maps Git status codes."""
        test_cases = [
            ("A", FileOperation.CREATE),
            ("M", FileOperation.MODIFY),
            ("D", FileOperation.DELETE),
            ("R", FileOperation.RENAME),
            ("R100", FileOperation.RENAME),  # Rename with similarity score
            ("C", FileOperation.CREATE),  # Copy treated as create
            ("T", FileOperation.MODIFY),  # Type change treated as modify
            ("X", FileOperation.MODIFY),  # Unknown defaults to modify
        ]

        for git_status, expected_operation in test_cases:
            result = self.adapter._map_git_status(git_status)
            assert result == expected_operation, f"Failed for status: {git_status}"

    def test_is_root_level_detection(self):
        """Test _is_root_level correctly identifies root-level files."""
        test_cases = [
            ("README.md", True),
            ("pyproject.toml", True),
            ("Makefile", True),
            ("lib/utils.py", False),
            ("src/hooks/domain/entities.py", False),
            ("tests/test_file.py", False),
            ("deep/nested/path/file.txt", False),
        ]

        for path, expected_root in test_cases:
            result = self.adapter._is_root_level(path)
            assert result == expected_root, f"Failed for path: {path}"

    def test_get_extension(self):
        """Test _get_extension correctly extracts file extensions."""
        test_cases = [
            ("README.md", ".md"),
            ("pyproject.toml", ".toml"),
            ("Makefile", ""),
            ("script.sh", ".sh"),
            ("lib/utils.py", ".py"),
            ("config.yaml", ".yaml"),
            ("file", ""),
            ("file.", "."),
        ]

        for path, expected_ext in test_cases:
            result = self.adapter._get_extension(path)
            if expected_ext == "":
                assert result is None, f"Failed for path: {path}"
            else:
                assert result == expected_ext, f"Failed for path: {path}"

    @patch("os.path.exists")
    @patch("os.path.isdir")
    def test_is_directory_existing_path(self, mock_isdir, mock_exists):
        """Test _is_directory for existing paths."""
        # Test existing directory
        mock_exists.return_value = True
        mock_isdir.return_value = True

        result = self.adapter._is_directory("existing_dir")
        assert result is True

        # Test existing file
        mock_isdir.return_value = False
        result = self.adapter._is_directory("existing_file.py")
        assert result is False

    @patch("os.path.exists")
    def test_is_directory_non_existing_path(self, mock_exists):
        """Test _is_directory for non-existing paths."""
        mock_exists.return_value = False

        # Test path ending with slash (assumed directory)
        result = self.adapter._is_directory("new_dir/")
        assert result is True

        # Test path not ending with slash (assumed file)
        result = self.adapter._is_directory("new_file.py")
        assert result is False

    @patch("subprocess.run")
    def test_get_current_branch(self, mock_run):
        """Test get_current_branch returns correct branch name."""
        mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

        branch = self.adapter.get_current_branch()

        assert branch == "main"
        mock_run.assert_called_once_with(
            ["git", "branch", "--show-current"],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_get_current_branch_fallback(self, mock_run):
        """Test get_current_branch fallback method."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),
            MagicMock(stdout="develop\n", returncode=0),
        ]

        branch = self.adapter.get_current_branch()

        assert branch == "develop"
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_has_staged_changes_true(self, mock_run):
        """Test has_staged_changes returns True when changes exist."""
        # Git diff --quiet returns 1 when differences exist
        mock_run.return_value = MagicMock(returncode=1)

        result = self.adapter.has_staged_changes()

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--quiet"],
            cwd=self.test_dir,
            capture_output=True,
        )

    @patch("subprocess.run")
    def test_has_staged_changes_false(self, mock_run):
        """Test has_staged_changes returns False when no changes."""
        # Git diff --quiet returns 0 when no differences
        mock_run.return_value = MagicMock(returncode=0)

        result = self.adapter.has_staged_changes()

        assert result is False
