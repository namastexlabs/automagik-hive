"""
Database settings for PagBank V2.
Based on agno-demo-app with PagBank-specific configurations.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

from utils.log import logger


class DbSettings(BaseSettings):
    """
    Database settings with automatic fallback from PostgreSQL to SQLite.
    Compatible with Agno storage patterns.
    
    Reference: https://docs.pydantic.dev/latest/usage/pydantic_settings/
    """

    # PostgreSQL configuration (preferred)
    db_host: Optional[str] = None
    db_port: Optional[int] = None  
    db_user: Optional[str] = None
    db_pass: Optional[str] = None
    db_database: Optional[str] = None
    db_driver: str = "postgresql+psycopg"
    
    # Migration settings
    migrate_db: bool = False
    auto_upgrade_schema: bool = True

    def get_db_url(self) -> str:
        """
        Get database URL with automatic fallback.
        Returns PostgreSQL URL if environment is configured, 
        otherwise falls back to SQLite.
        """
        # Check for full DATABASE_URL first (highest priority)
        if database_url := os.getenv("DATABASE_URL"):
            if "None" not in database_url and database_url.strip():
                return database_url
        
        # Try to construct PostgreSQL URL from individual components
        if all([self.db_host, self.db_port, self.db_user, self.db_database]):
            db_url = "{}://{}{}@{}:{}/{}".format(
                self.db_driver,
                self.db_user,
                f":{self.db_pass}" if self.db_pass else "",
                self.db_host,
                self.db_port,
                self.db_database,
            )
            if "None" not in db_url:
                return db_url
        
        # Fallback to workspace PostgreSQL (agno-demo-app pattern)
        try:
            from workspace.dev_resources import dev_db
            logger.debug("Using workspace dev database connection")
            local_db_url = dev_db.get_db_connection_local()
            if local_db_url:
                return local_db_url
        except Exception:
            pass
        
        # Final fallback to SQLite
        print("⚠️ PostgreSQL not available, falling back to SQLite")
        sqlite_path = os.path.join(os.getcwd(), "data", "pagbank_v2.db")
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        return f"sqlite:///{sqlite_path}"

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.get_db_url().lower()
    
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.get_db_url().lower()


# Create global db_settings instance
db_settings = DbSettings()