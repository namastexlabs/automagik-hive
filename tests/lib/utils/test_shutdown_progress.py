"""
Tests for shutdown progress display utility
"""

import io
import time
from unittest.mock import patch

import pytest

from lib.utils.shutdown_progress import ShutdownProgress, create_automagik_shutdown_progress


class TestShutdownProgress:
    """Test the shutdown progress display functionality"""

    def test_shutdown_progress_initialization(self):
        """Test that ShutdownProgress initializes correctly"""
        progress = ShutdownProgress()
        assert progress.steps == []
        assert progress.current_step == 0
        assert progress.running is False
        assert progress._stop_animation is False

    def test_add_step(self):
        """Test adding steps to progress display"""
        progress = ShutdownProgress()
        progress.add_step("Test Step", "Test Description")

        assert len(progress.steps) == 1
        step = progress.steps[0]
        assert step["title"] == "Test Step"
        assert step["description"] == "Test Description"
        assert step["status"] == "pending"
        assert step["start_time"] is None
        assert step["end_time"] is None

    def test_complete_step_success(self):
        """Test completing a step successfully"""
        progress = ShutdownProgress()
        progress.add_step("Test Step")

        # Capture stdout to verify output
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            progress.complete_step(0, success=True)

        step = progress.steps[0]
        assert step["status"] == "completed"
        assert step["end_time"] is not None

    def test_complete_step_failure(self):
        """Test completing a step with failure"""
        progress = ShutdownProgress()
        progress.add_step("Test Step")

        # Capture stdout to verify output
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            progress.complete_step(0, success=False)

        step = progress.steps[0]
        assert step["status"] == "failed"
        assert step["end_time"] is not None

    def test_step_context_manager_success(self):
        """Test step context manager for successful completion"""
        progress = ShutdownProgress()
        progress.add_step("Test Step")

        # Capture stdout to avoid animation output in tests
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            with progress.step(0):
                time.sleep(0.01)  # Brief sleep to test timing

        step = progress.steps[0]
        assert step["status"] == "completed"
        assert step["start_time"] is not None
        assert step["end_time"] is not None

    def test_step_context_manager_failure(self):
        """Test step context manager for failure handling"""
        progress = ShutdownProgress()
        progress.add_step("Test Step")

        # Capture stdout to avoid animation output in tests
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            with pytest.raises(ValueError):
                with progress.step(0):
                    raise ValueError("Test error")

        step = progress.steps[0]
        assert step["status"] == "failed"

    def test_windows_safe_characters(self):
        """Test that Windows-safe characters are used on Windows platform"""
        with patch("platform.system", return_value="Windows"):
            progress = ShutdownProgress()
            assert progress._animation_chars == ["-", "\\", "|", "/"]
            assert progress._success_icon == "+"
            assert progress._failure_icon == "x"
            assert progress._farewell_emoji == ":)"

    def test_unix_unicode_characters(self):
        """Test that Unicode characters are used on Unix platforms"""
        with patch("platform.system", return_value="Linux"):
            progress = ShutdownProgress()
            assert progress._animation_chars == ["□", "▢", "▣", "■"]
            assert progress._success_icon == "✓"
            assert progress._failure_icon == "✗"
            assert progress._farewell_emoji == "👋"

    def test_verbose_mode(self):
        """Test that verbose mode shows timing information"""
        progress = ShutdownProgress(verbose=True)
        assert progress.verbose is True

    def test_print_farewell_message(self):
        """Test farewell message output"""
        progress = ShutdownProgress()

        # Capture stdout to verify farewell message
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            progress.print_farewell_message()

        # Should have written to stdout (clearing and farewell)
        assert captured_output.getvalue()  # Some output should be present


class TestCreateAutomaikShutdownProgress:
    """Test the factory function for creating shutdown progress"""

    def test_create_automagik_shutdown_progress(self):
        """Test creating shutdown progress with predefined steps"""
        progress = create_automagik_shutdown_progress()

        assert len(progress.steps) == 5

        # Verify step titles match our shutdown phases
        expected_titles = [
            "Stopping Server",
            "Cancelling Background Tasks",
            "Cleaning Up Services",
            "Clearing Temporary Files",
            "Finalizing Shutdown",
        ]

        actual_titles = [step["title"] for step in progress.steps]
        assert actual_titles == expected_titles

    def test_create_automagik_shutdown_progress_verbose(self):
        """Test creating shutdown progress with verbose mode"""
        progress = create_automagik_shutdown_progress(verbose=True)

        assert progress.verbose is True
        assert len(progress.steps) == 5
