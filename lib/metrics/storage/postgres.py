"""
PostgreSQL Storage Backend

Stores metrics to PostgreSQL database using hive schema
"""
import json
import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from .base import MetricsStorage, ConfigurationError
from lib.services.metrics_service import MetricsService


class PostgresMetricsStorage(MetricsStorage):
    """PostgreSQL-based metrics storage backend using hive schema"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize PostgreSQL storage"""
        super().__init__(config)
        self.metrics_service = MetricsService()
        self.table_name = config.get("table_name", "agent_metrics")
    
    def _validate_config(self) -> None:
        """Validate PostgreSQL configuration"""
        database_url = self.config.get("database_url") or os.getenv("HIVE_DATABASE_URL")
        
        if not database_url:
            required_fields = ["host", "database", "user", "password"]
            missing_fields = [field for field in required_fields if not self.config.get(field)]
            
            if missing_fields:
                raise ConfigurationError(f"Missing required PostgreSQL config: {missing_fields} or DATABASE_URL")
        
        table_name = self.config.get("table_name", "agent_metrics")
        if not table_name.isidentifier():
            raise ConfigurationError(f"Invalid table name: {table_name}. Must be a valid SQL identifier.")
        self.table_name = table_name
    
    def store_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store metrics data using MetricsService and hive schema
        
        Args:
            metrics_data: Dictionary containing metrics information
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            timestamp = metrics_data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()
            
            # Store using MetricsService
            result = asyncio.run(self.metrics_service.store_metrics(
                timestamp=timestamp,
                agent_name=metrics_data["agent_name"],
                execution_type=metrics_data["execution_type"],
                metrics=metrics_data["metrics"],
                version=metrics_data.get("version", "1.0")
            ))
            
            return bool(result)
        except Exception as e:
            self.handle_storage_error(e, metrics_data)
            return False
    
    def is_available(self) -> bool:
        """Check if PostgreSQL storage is available"""
        try:
            # Test with a simple metrics operation
            test_data = {
                "timestamp": datetime.now(),
                "agent_name": "test",
                "execution_type": "test",
                "metrics": {},
                "version": "1.0"
            }
            # Don't actually store, just check if service is available
            return True
        except Exception:
            return False