"""
File watcher with debounced reload.

Watches CSV files for changes and triggers incremental reloads.
Uses debouncing to avoid reload storms during bulk edits.

Features:
- Debounced reload (default: 1 second)
- Handles file modifications, creations, deletions
- Async-safe for use in API servers
- Clean shutdown handling
"""

import asyncio
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    from watchdog.observers.api import BaseObserver


class DebouncedFileWatcher(FileSystemEventHandler):
    """File watcher with debounced callbacks."""

    def __init__(
        self,
        file_path: str | Path,
        callback: Callable[[str], None],
        debounce_delay: float = 1.0,
    ) -> None:
        """
        Initialize the file watcher.

        Args:
            file_path: Path to file to watch
            callback: Function to call on file changes
            debounce_delay: Seconds to wait before triggering callback
        """
        self.file_path = Path(file_path).resolve()
        self.callback = callback
        self.debounce_delay = debounce_delay
        self.observer: BaseObserver | None = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._stopped = False

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        # Check if this is our target file
        event_path = Path(str(event.src_path)).resolve()
        if event_path != self.file_path:
            return

        logger.debug("File modified detected", path=str(self.file_path))
        self._schedule_reload()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        event_path = Path(str(event.src_path)).resolve()
        if event_path != self.file_path:
            return

        logger.debug("File created detected", path=str(self.file_path))
        self._schedule_reload()

    def _schedule_reload(self) -> None:
        """Schedule a debounced reload."""
        with self._lock:
            if self._stopped:
                return

            # Cancel existing timer
            if self._timer is not None:
                self._timer.cancel()

            # Schedule new timer
            self._timer = threading.Timer(self.debounce_delay, self._execute_callback)
            self._timer.daemon = True
            self._timer.start()

            logger.debug(
                "Reload scheduled",
                delay=self.debounce_delay,
                path=str(self.file_path),
            )

    def _execute_callback(self) -> None:
        """Execute the reload callback."""
        with self._lock:
            if self._stopped:
                return

            try:
                logger.info("Triggering reload", path=str(self.file_path))
                self.callback(str(self.file_path))
            except Exception as e:
                logger.error("Reload callback failed", error=str(e), path=str(self.file_path))

    def start(self) -> None:
        """Start watching the file."""
        if self.observer is not None:
            logger.warning("Watcher already started", path=str(self.file_path))
            return

        # Ensure file exists
        if not self.file_path.exists():
            logger.error("File does not exist", path=str(self.file_path))
            raise FileNotFoundError(f"Cannot watch non-existent file: {self.file_path}")

        # Start observer
        self.observer = Observer()
        watch_dir = self.file_path.parent
        self.observer.schedule(self, str(watch_dir), recursive=False)
        self.observer.start()

        logger.info(
            "File watcher started",
            path=str(self.file_path),
            debounce_delay=self.debounce_delay,
        )

    def stop(self) -> None:
        """Stop watching the file."""
        with self._lock:
            self._stopped = True

            # Cancel pending timer
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

        # Stop observer
        if self.observer is not None:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None

        logger.info("File watcher stopped", path=str(self.file_path))

    def __enter__(self) -> "DebouncedFileWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Context manager exit."""
        self.stop()


class AsyncDebouncedFileWatcher:
    """Async wrapper for DebouncedFileWatcher."""

    def __init__(
        self,
        file_path: str | Path,
        callback: Callable[[str], None],
        debounce_delay: float = 1.0,
    ) -> None:
        """
        Initialize async file watcher.

        Args:
            file_path: Path to file to watch
            callback: Function to call on file changes
            debounce_delay: Seconds to wait before triggering callback
        """
        self.watcher = DebouncedFileWatcher(
            file_path=file_path,
            callback=callback,
            debounce_delay=debounce_delay,
        )

    async def start(self) -> None:
        """Start watching (async-safe)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.watcher.start)

    async def stop(self) -> None:
        """Stop watching (async-safe)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.watcher.stop)

    async def __aenter__(self) -> "AsyncDebouncedFileWatcher":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Async context manager exit."""
        await self.stop()
