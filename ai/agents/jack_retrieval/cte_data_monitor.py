"""CTE Data Monitor

Hot reload system that monitors CTE JSON files for changes and provides
vector update callbacks for real-time data processing.
"""

import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CTEDataMonitor:
    """Monitor CTE data files for changes and hot reload."""
    
    def __init__(self, cte_directory: str):
        """Initialize CTE data monitor.
        
        Args:
            cte_directory: Directory path containing CTE JSON files
        """
        self.cte_dir = Path(cte_directory)
        self.is_monitoring = False
        self.vector_update_callbacks: List[Callable[[Path, Dict[str, Any]], Awaitable[None]]] = []
        self._observer: Optional[Observer] = None
        self._handler: Optional[CTEDataHandler] = None
    
    def add_vector_update_callback(self, callback: Callable[[Path, Dict[str, Any]], Awaitable[None]]) -> None:
        """Add a callback for vector updates.
        
        Args:
            callback: Async function to call when CTE data changes
        """
        self.vector_update_callbacks.append(callback)
    
    def load_cte_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load CTE data from JSON file.
        
        Args:
            file_path: Path to CTE JSON file
            
        Returns:
            Loaded CTE data or None if error/invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required structure
            if not isinstance(data, dict):
                return None
            
            # Check for required orders field
            if 'orders' not in data:
                return None
                
            return data
            
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            print(f"Error loading CTE data from {file_path}: {e}")
            return None
    
    def get_latest_cte_file(self) -> Optional[Path]:
        """Get the latest CTE file based on filename pattern.
        
        Returns:
            Path to latest CTE file or None if none found
        """
        cte_files = self.get_all_cte_files()
        if not cte_files:
            return None
        
        # Sort by filename (which includes timestamp) to get latest
        return sorted(cte_files, key=lambda f: f.name, reverse=True)[0]
    
    def get_all_cte_files(self) -> List[Path]:
        """Get all CTE files matching the pattern.
        
        Returns:
            List of CTE file paths
        """
        if not self.cte_dir.exists():
            return []
        
        # Match pattern: consolidated_ctes_daily_*.json
        cte_files = []
        for file_path in self.cte_dir.glob("consolidated_ctes_daily_*.json"):
            if file_path.is_file():
                cte_files.append(file_path)
        
        return cte_files
    
    async def handle_cte_file_change(self, file_path: Path) -> None:
        """Handle CTE file change event.
        
        Args:
            file_path: Path to changed CTE file
        """
        # Load the changed data
        cte_data = self.load_cte_data(file_path)
        if cte_data is None:
            return
        
        # Call all registered callbacks
        for callback in self.vector_update_callbacks:
            try:
                await callback(file_path, cte_data)
            except Exception as e:
                print(f"Error in vector update callback: {e}")
    
    async def get_current_cte_data(self) -> Optional[Dict[str, Any]]:
        """Get current CTE data from latest file.
        
        Returns:
            Current CTE data or None if no valid data
        """
        latest_file = self.get_latest_cte_file()
        if latest_file is None:
            return None
        
        return self.load_cte_data(latest_file)
    
    def start_monitoring(self) -> None:
        """Start monitoring CTE directory for file changes."""
        if self.is_monitoring:
            return
        
        if not self.cte_dir.exists():
            print(f"CTE directory does not exist: {self.cte_dir}")
            return
        
        # Create handler with file change callback
        async def handle_change(file_path: Path) -> None:
            await self.handle_cte_file_change(file_path)
        
        self._handler = CTEDataHandler(handle_change)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.cte_dir), recursive=False)
        self._observer.start()
        self.is_monitoring = True
        print(f"Started monitoring CTE directory: {self.cte_dir}")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring CTE directory."""
        if not self.is_monitoring:
            return
        
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        self._handler = None
        self.is_monitoring = False
        print("Stopped monitoring CTE directory")


class CTEDataHandler(FileSystemEventHandler):
    """File system event handler for CTE data files."""
    
    def __init__(self, callback_func: Callable[[Path], Awaitable[None]]):
        """Initialize CTE data handler.
        
        Args:
            callback_func: Async function to call on file changes
        """
        super().__init__()
        self.callback_func = callback_func
        self.debounce_time = 2.0  # seconds
        self.last_modified: Dict[str, float] = {}
    
    def _should_handle_event(self, event) -> bool:
        """Check if event should be handled.
        
        Args:
            event: File system event
            
        Returns:
            True if event should be handled
        """
        # Ignore directory events
        if event.is_directory:
            return False
        
        # Check if it's a CTE file
        file_path = Path(event.src_path)
        if not file_path.name.startswith("consolidated_ctes_daily_"):
            return False
        
        if not file_path.suffix == ".json":
            return False
        
        # Debounce rapid changes
        current_time = time.time()
        last_time = self.last_modified.get(event.src_path, 0)
        
        if current_time - last_time < self.debounce_time:
            return False
        
        self.last_modified[event.src_path] = current_time
        return True
    
    def on_modified(self, event):
        """Handle file modified event."""
        if not self._should_handle_event(event):
            return
        
        file_path = Path(event.src_path)
        
        # Run callback in event loop
        def run_callback():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.callback_func(file_path))
                else:
                    asyncio.run(self.callback_func(file_path))
            except Exception as e:
                print(f"Error running callback for {file_path}: {e}")
        
        # Schedule callback execution
        try:
            asyncio.create_task(self.callback_func(file_path))
        except RuntimeError:
            # No event loop running, create one
            import threading
            thread = threading.Thread(target=lambda: asyncio.run(self.callback_func(file_path)))
            thread.daemon = True
            thread.start()
    
    def on_created(self, event):
        """Handle file created event."""
        # Treat creation same as modification
        self.on_modified(event)


# Global monitor instance - updated for mctech/ctes directory
cte_monitor = CTEDataMonitor(cte_directory="mctech/ctes")


async def initialize_cte_monitoring(cte_directory: str = "mctech/ctes") -> CTEDataMonitor:
    """Initialize CTE monitoring system.
    
    Args:
        cte_directory: Directory path containing CTE JSON files
    
    Returns:
        Configured CTE monitor instance
    """
    # Create monitor for the specified directory
    monitor = CTEDataMonitor(cte_directory=cte_directory)
    
    # Check for existing data
    current_data = await monitor.get_current_cte_data()
    
    if current_data:
        summary = current_data.get('summary', {})
        print(f"Found existing CTE data: "
              f"{summary.get('total_orders', 0)} orders, "
              f"{summary.get('total_ctes', 0)} CTEs, "
              f"R${summary.get('total_value', 0):.2f}")
    else:
        print("No existing CTE data found")
    
    # Start monitoring
    monitor.start_monitoring()
    
    return monitor