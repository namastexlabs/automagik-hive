"""
PostgreSQL Storage Backend

Stores metrics to PostgreSQL database
"""
import json
import os
from typing import Dict, Any, Optional
from .base import MetricsStorage, ConfigurationError


class PostgresMetricsStorage(MetricsStorage):
    """PostgreSQL-based metrics storage backend"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize PostgreSQL storage"""
        super().__init__(config)
        self.connection = None
        self.table_name = config.get("table_name", "agent_metrics")
    
    def _validate_config(self) -> None:
        """Validate PostgreSQL configuration"""
        # Use DATABASE_URL if provided, otherwise fall back to individual fields
        database_url = self.config.get("database_url") or os.getenv("DATABASE_URL")
        
        if database_url:
            # Parse DATABASE_URL
            self.database_url = database_url
        else:
            # Fall back to individual fields
            required_fields = ["host", "database", "user", "password"]
            missing_fields = [field for field in required_fields if not self.config.get(field)]
            
            if missing_fields:
                raise ConfigurationError(f"Missing required PostgreSQL config: {missing_fields} or DATABASE_URL")
            
            self.database_url = None
        
        # Validate table name to prevent SQL injection
        table_name = self.config.get("table_name", "agent_metrics")
        if not table_name.isidentifier():
            raise ConfigurationError(f"Invalid table name: {table_name}. Must be a valid SQL identifier.")
        self.table_name = table_name
        
        # Try to establish connection
        try:
            self._get_connection()
        except Exception as e:
            raise ConfigurationError(f"Cannot connect to PostgreSQL: {e}")
    
    def _get_connection(self):
        """Get or create database connection"""
        if self.connection is None:
            try:
                import psycopg2
                
                if self.database_url:
                    # Use DATABASE_URL
                    self.connection = psycopg2.connect(self.database_url)
                else:
                    # Use individual fields
                    self.connection = psycopg2.connect(
                        host=self.config["host"],
                        port=self.config.get("port", 5432),
                        database=self.config["database"],
                        user=self.config["user"],
                        password=self.config["password"]
                    )
                
                # Create table if it doesn't exist
                self._create_table_if_not_exists()
                
            except ImportError:
                raise ConfigurationError("psycopg2 is required for PostgreSQL storage. Install with: pip install psycopg2-binary")
        
        return self.connection
    
    def _create_table_if_not_exists(self) -> None:
        """Create metrics table if it doesn't exist"""
        try:
            from psycopg2 import sql
        except ImportError:
            raise ConfigurationError("psycopg2.sql module required for safe SQL operations")
        
        # Use parameterized queries to prevent SQL injection
        create_table_query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            agent_name VARCHAR(255) NOT NULL,
            execution_type VARCHAR(50) NOT NULL,
            metrics JSONB NOT NULL,
            version VARCHAR(10) NOT NULL DEFAULT '1.0',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """).format(table=sql.Identifier(self.table_name))
        
        # Create indexes safely
        timestamp_index = sql.SQL("CREATE INDEX IF NOT EXISTS {index} ON {table}(timestamp)").format(
            index=sql.Identifier(f"idx_{self.table_name}_timestamp"),
            table=sql.Identifier(self.table_name)
        )
        
        agent_index = sql.SQL("CREATE INDEX IF NOT EXISTS {index} ON {table}(agent_name)").format(
            index=sql.Identifier(f"idx_{self.table_name}_agent_name"),
            table=sql.Identifier(self.table_name)
        )
        
        execution_index = sql.SQL("CREATE INDEX IF NOT EXISTS {index} ON {table}(execution_type)").format(
            index=sql.Identifier(f"idx_{self.table_name}_execution_type"),
            table=sql.Identifier(self.table_name)
        )
        
        with self.connection.cursor() as cursor:
            cursor.execute(create_table_query)
            cursor.execute(timestamp_index)
            cursor.execute(agent_index)
            cursor.execute(execution_index)
        self.connection.commit()
    
    def store_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """
        Store metrics data to PostgreSQL
        
        Args:
            metrics_data: Dictionary containing metrics information
            
        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            from psycopg2 import sql
            connection = self._get_connection()
            
            # Use parameterized query to prevent SQL injection
            insert_query = sql.SQL("""
            INSERT INTO {table} (timestamp, agent_name, execution_type, metrics, version)
            VALUES (%(timestamp)s, %(agent_name)s, %(execution_type)s, %(metrics)s, %(version)s)
            """).format(table=sql.Identifier(self.table_name))
            
            # Convert metrics to JSON string for JSONB storage
            data_to_insert = {
                "timestamp": metrics_data["timestamp"],
                "agent_name": metrics_data["agent_name"],
                "execution_type": metrics_data["execution_type"],
                "metrics": json.dumps(metrics_data["metrics"]),
                "version": metrics_data.get("version", "1.0")
            }
            
            with connection.cursor() as cursor:
                cursor.execute(insert_query, data_to_insert)
            connection.commit()
            
            return True
        except Exception as e:
            self.handle_storage_error(e, metrics_data)
            if self.connection:
                self.connection.rollback()
            return False
    
    def is_available(self) -> bool:
        """Check if PostgreSQL storage is available"""
        try:
            connection = self._get_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def close_connection(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Cleanup connection on object destruction"""
        self.close_connection()