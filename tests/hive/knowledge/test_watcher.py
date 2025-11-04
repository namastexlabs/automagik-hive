"""Tests for file watcher with debounced reload."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hive.knowledge.watcher import DebouncedFileWatcher


@pytest.fixture
def test_file(tmp_path: Path) -> Path:
    """Create a test file."""
    file_path = tmp_path / "test.csv"
    file_path.write_text("test data")
    return file_path


def test_watcher_initialization(test_file: Path) -> None:
    """Test watcher initialization."""
    callback = MagicMock()
    watcher = DebouncedFileWatcher(
        file_path=test_file,
        callback=callback,
        debounce_delay=0.5,
    )

    assert watcher.file_path == test_file.resolve()
    assert watcher.debounce_delay == 0.5
    assert watcher.observer is None


def test_watcher_start_stop(test_file: Path) -> None:
    """Test watcher start and stop."""
    callback = MagicMock()
    watcher = DebouncedFileWatcher(
        file_path=test_file,
        callback=callback,
        debounce_delay=0.1,
    )

    # Start watching
    watcher.start()
    assert watcher.observer is not None
    assert watcher.observer.is_alive()

    # Stop watching
    watcher.stop()
    # Observer is set to None after stop
    assert watcher.observer is None


def test_watcher_context_manager(test_file: Path) -> None:
    """Test watcher context manager."""
    callback = MagicMock()

    with DebouncedFileWatcher(test_file, callback, debounce_delay=0.1) as watcher:
        assert watcher.observer is not None
        assert watcher.observer.is_alive()

    # Should be stopped after exiting context (observer set to None)
    assert watcher.observer is None


def test_watcher_file_not_found() -> None:
    """Test watcher with non-existent file."""
    callback = MagicMock()
    watcher = DebouncedFileWatcher(
        file_path="nonexistent.csv",
        callback=callback,
        debounce_delay=0.1,
    )

    with pytest.raises(FileNotFoundError):
        watcher.start()


def test_watcher_detects_modification(test_file: Path) -> None:
    """Test that watcher detects file modifications."""
    callback = MagicMock()
    watcher = DebouncedFileWatcher(
        file_path=test_file,
        callback=callback,
        debounce_delay=0.1,  # Short delay for testing
    )

    try:
        watcher.start()

        # Modify file
        test_file.write_text("modified data")

        # Wait for debounce + processing
        time.sleep(0.3)

        # Callback should have been called
        callback.assert_called_once_with(str(test_file))
    finally:
        watcher.stop()


def test_watcher_debouncing(test_file: Path) -> None:
    """Test that multiple rapid changes are debounced."""
    callback = MagicMock()
    watcher = DebouncedFileWatcher(
        file_path=test_file,
        callback=callback,
        debounce_delay=0.2,  # Longer delay for debouncing
    )

    try:
        watcher.start()

        # Modify file multiple times rapidly
        for i in range(5):
            test_file.write_text(f"data {i}")
            time.sleep(0.05)  # Short delay between writes

        # Wait for debounce + processing
        time.sleep(0.4)

        # Callback should have been called only once (debounced)
        assert callback.call_count == 1
    finally:
        watcher.stop()


def test_watcher_callback_error_handling(test_file: Path) -> None:
    """Test that callback errors are handled gracefully."""
    callback = MagicMock(side_effect=Exception("Test error"))
    watcher = DebouncedFileWatcher(
        file_path=test_file,
        callback=callback,
        debounce_delay=0.1,
    )

    try:
        watcher.start()

        # Modify file
        test_file.write_text("trigger error")

        # Wait for callback
        time.sleep(0.3)

        # Callback was called but error was caught
        callback.assert_called_once()
    finally:
        watcher.stop()
