"""CTE File Monitor

External watchdog library integration for JSON file change detection.
Watchdog is NOT an agent - it's external Python code that monitors files.

Implementation approach - External watchdog library with Python processor:
- Monitor mctech/ctes directory for JSON file changes
- Trigger Python file processing (not agent processing)
- Handle file system events with proper error handling
- Use proven external library (watchdog)
"""

import asyncio
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Optional

from .processor import CTEProcessor

logger = logging.getLogger(__name__)


class CTEFileHandler(FileSystemEventHandler):
    """Handle file system events for CTE JSON files."""
    
    def __init__(self, processor: CTEProcessor):
        """
        Initialize file handler.
        
        Args:
            processor: CTE processor instance to handle file changes
        """
        super().__init__()
        self.processor = processor
    
    def on_modified(self, event):
        """
        Handle file modification events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        if event.src_path.endswith('.json'):
            print(f"🔄 Detected change in {Path(event.src_path).name}")
            logger.info(f"File changed: {event.src_path}")
            
            # Python code processes file, not agent
            try:
                asyncio.run(self.processor.process_cte_file(event.src_path))
            except Exception as e:
                error_msg = f"Error processing file {event.src_path}: {e}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
    
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        if event.src_path.endswith('.json'):
            print(f"📄 New file detected: {Path(event.src_path).name}")
            logger.info(f"New file created: {event.src_path}")
            
            # Python code processes file, not agent
            try:
                asyncio.run(self.processor.process_cte_file(event.src_path))
            except Exception as e:
                error_msg = f"Error processing new file {event.src_path}: {e}"
                print(f"❌ {error_msg}")
                logger.error(error_msg)


class CTEFileMonitor:
    """Monitor CTE files using external watchdog library."""
    
    def __init__(self, watch_directory: str, processor: CTEProcessor):
        """
        Initialize file monitor.
        
        Args:
            watch_directory: Directory to monitor for CTE JSON files
            processor: CTE processor to handle file changes
        """
        self.watch_directory = watch_directory
        self.processor = processor
        self.observer: Optional[Observer] = None
        self.handler = CTEFileHandler(processor)
    
    def start_monitoring(self) -> None:
        """Start file monitoring."""
        if self.observer and self.observer.is_alive():
            logger.warning("Monitor is already running")
            return
        
        # Ensure directory exists
        Path(self.watch_directory).mkdir(parents=True, exist_ok=True)
        
        # Setup monitoring with Python processor (not agent)
        self.observer = Observer()
        self.observer.schedule(
            self.handler, 
            self.watch_directory, 
            recursive=False
        )
        
        self.observer.start()
        print(f"🔍 Started monitoring {self.watch_directory} for CTE files")
        logger.info(f"Started monitoring directory: {self.watch_directory}")
    
    def stop_monitoring(self) -> None:
        """Stop file monitoring."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            print("🛑 Stopped CTE file monitoring")
            logger.info("Stopped file monitoring")
    
    def is_monitoring(self) -> bool:
        """
        Check if monitoring is active.
        
        Returns:
            True if monitoring is active
        """
        return self.observer is not None and self.observer.is_alive()


def create_cte_monitor(watch_directory: str = "mctech/ctes", database_url: str = None) -> CTEFileMonitor:
    """
    Create CTE file monitor with processor.
    
    Args:
        watch_directory: Directory to monitor (default: mctech/ctes)
        database_url: PostgreSQL database URL
        
    Returns:
        CTEFileMonitor instance ready to start
    """
    import os
    
    if database_url is None:
        database_url = os.getenv('HIVE_DATABASE_URL')
    
    if not database_url:
        raise ValueError("Database URL is required")
    
    processor = CTEProcessor(database_url)
    monitor = CTEFileMonitor(watch_directory, processor)
    
    return monitor