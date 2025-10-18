"""Test the genie commands."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from cli.commands.genie import GenieCommands


class TestGenieCommands:
    """Test genie commands."""

    @pytest.fixture
    def genie_cmd(self):
        """Create GenieCommands instance."""
        return GenieCommands()

    def test_launch_claude_success(self, genie_cmd):
        """Test successful claude launch with AGENTS.md."""
        # Mock Path.cwd to return test directory
        test_dir = Path("/test/dir")
        agents_content = "# AGENTS.md test content"

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=agents_content)),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)

            result = genie_cmd.launch_claude()

            assert result is True
            mock_run.assert_called_once()

            # Check command construction
            cmd = mock_run.call_args[0][0]
            assert cmd[0] == "claude"
            assert "--append-system-prompt" in cmd
            assert agents_content in cmd
            assert "--mcp-config" in cmd
            assert ".mcp.json" in cmd

    def test_launch_claude_with_extra_args(self, genie_cmd):
        """Test claude launch with additional arguments."""
        test_dir = Path("/test/dir")
        agents_content = "# AGENTS.md"
        extra_args = ["--help", "--version"]

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=agents_content)),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)

            result = genie_cmd.launch_claude(extra_args)

            assert result is True
            cmd = mock_run.call_args[0][0]
            assert "--help" in cmd
            assert "--version" in cmd

    def test_launch_claude_agents_md_not_found(self, genie_cmd):
        """Test when AGENTS.md is not found."""
        test_dir = Path("/test/dir")

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "parents", []),
        ):
            result = genie_cmd.launch_claude()

            assert result is False

    def test_launch_claude_agents_md_in_parent(self, genie_cmd):
        """Test finding AGENTS.md in parent directory."""
        test_dir = Path("/test/dir/subdir")
        parent_dir = Path("/test/dir")
        agents_content = "# Parent AGENTS.md"

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", side_effect=lambda: str(Path) == str(parent_dir / "AGENTS.md")),
            patch.object(Path, "parents", [parent_dir]),
            patch("builtins.open", mock_open(read_data=agents_content)),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)

            # Mock the exists check properly
            def mock_exists(self):
                return self == parent_dir / "AGENTS.md"

            with patch.object(Path, "exists", mock_exists):
                result = genie_cmd.launch_claude()

            assert result is True

    def test_launch_claude_read_failure(self, genie_cmd):
        """Test when AGENTS.md cannot be read."""
        test_dir = Path("/test/dir")

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):
            result = genie_cmd.launch_claude()

            assert result is False

    def test_launch_claude_command_not_found(self, genie_cmd):
        """Test when claude command is not found."""
        test_dir = Path("/test/dir")
        agents_content = "# AGENTS.md"

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=agents_content)),
            patch("subprocess.run", side_effect=FileNotFoundError()),
        ):
            result = genie_cmd.launch_claude()

            assert result is False

    def test_launch_claude_command_failure(self, genie_cmd):
        """Test when claude command fails."""
        test_dir = Path("/test/dir")
        agents_content = "# AGENTS.md"

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=agents_content)),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1)

            result = genie_cmd.launch_claude()

            assert result is False

    def test_launch_claude_keyboard_interrupt(self, genie_cmd):
        """Test handling KeyboardInterrupt."""
        test_dir = Path("/test/dir")
        agents_content = "# AGENTS.md"

        with (
            patch("pathlib.Path.cwd", return_value=test_dir),
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", mock_open(read_data=agents_content)),
        ):
            # Directly test the exception handler by calling with KeyboardInterrupt
            with patch("subprocess.run") as mock_run:
                # Configure mock to raise KeyboardInterrupt when called
                mock_run.side_effect = KeyboardInterrupt()

                # The method should catch the exception and return True
                try:
                    result = genie_cmd.launch_claude()
                    # If we get here, the exception was handled
                    assert result is True
                except KeyboardInterrupt:
                    # If KeyboardInterrupt escapes, the test should fail
                    pytest.fail("KeyboardInterrupt was not handled properly")
