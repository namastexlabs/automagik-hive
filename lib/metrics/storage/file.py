"""
File Storage Backend

Stores metrics to a log file (default: logs/metrics.log)
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from .base import MetricsStorage, ConfigurationError


class FileMetricsStorage(MetricsStorage):
    """File-based metrics storage backend"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize file storage with path configuration"""
        super().__init__(config)
        self.file_path = self._validate_and_resolve_path(
            self.config.get("storage_path", "./logs/metrics.log")
        )
    
    def _validate_and_resolve_path(self, storage_path: str) -> Path:
        """
        Validate and resolve file path to prevent path traversal attacks
        
        Args:
            storage_path: User-provided storage path
            
        Returns:
            Validated and resolved Path object
            
        Raises:
            ConfigurationError: If path is invalid or outside allowed directory
        """
        # Define the allowed root directory for metrics storage
        metrics_root = Path(os.getenv("METRICS_ROOT", "./logs")).resolve()
        
        # Resolve the requested path
        try:
            # Convert relative paths to absolute within the root
            if not os.path.isabs(storage_path):
                resolved_path = (metrics_root / storage_path).resolve()
            else:
                resolved_path = Path(storage_path).resolve()
        except Exception as e:
            raise ConfigurationError(f"Invalid storage path: {e}")
        
        # Ensure the resolved path is within the allowed root directory
        try:
            resolved_path.relative_to(metrics_root)
        except ValueError:
            raise ConfigurationError(
                f"Storage path '{storage_path}' is outside allowed directory '{metrics_root}'"
            )
        
        # Validate the file extension (security measure)
        if resolved_path.suffix not in ['.log', '.json', '.txt']:
            raise ConfigurationError(
                f"Invalid file extension '{resolved_path.suffix}'. Allowed: .log, .json, .txt"
            )
        
        return resolved_path
    
    def _validate_config(self) -> None:
        """Validate file storage configuration"""
        storage_path = self.config.get("storage_path")
        if not storage_path:
            raise ConfigurationError("storage_path is required for file storage")
        
        # Ensure parent directory exists
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Cannot create directory for metrics file: {e}")
    
    def store_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store metrics data to file as JSON lines
        
        Args:
            metrics_data: Dictionary containing metrics information
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            # Append to file as JSON line
            with open(self.file_path, "a", encoding="utf-8") as f:
                json.dump(metrics_data, f, separators=(',', ':'))
                f.write('\n')
            
            return True
        except Exception as e:
            self.handle_storage_error(e, metrics_data)
            return False
    
    def is_available(self) -> bool:
        """Check if file storage is available"""
        try:
            # Test write permissions
            test_path = self.file_path.parent / ".metrics_test"
            test_path.touch()
            test_path.unlink()
            return True
        except Exception:
            return False
    
    def get_file_size(self) -> int:
        """Get current file size in bytes"""
        try:
            return self.file_path.stat().st_size
        except FileNotFoundError:
            return 0
    
    def rotate_if_needed(self, max_size_mb: int = 100) -> bool:
        """
        Rotate log file if it exceeds maximum size
        
        Args:
            max_size_mb: Maximum file size in MB before rotation
            
        Returns:
            bool: True if rotation occurred
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if self.get_file_size() > max_size_bytes:
            try:
                # Rotate: metrics.log -> metrics.log.1
                backup_path = self.file_path.with_suffix(self.file_path.suffix + ".1")
                if backup_path.exists():
                    backup_path.unlink()
                
                self.file_path.rename(backup_path)
                return True
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to rotate metrics log: {e}")
        
        return False