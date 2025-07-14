"""
Database settings for PagBank V2.
Based on agno-demo-app with PagBank-specific configurations.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()

from utils.log import logger


class DbSettings(BaseSettings):
    """
    Database settings for PostgreSQL.
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
        Get PostgreSQL database URL from environment.
        This enterprise setup requires PostgreSQL.
        """
        # Get DATABASE_URL from environment
        database_url = os.getenv("DATABASE_URL")
        
        if database_url and "postgresql" in database_url:
            print(f"✅ Using PostgreSQL: {database_url.split('@')[1] if '@' in database_url else database_url}")
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
            print(f"✅ Using PostgreSQL from components: {self.db_host}:{self.db_port}")
            return db_url
        
        # Enterprise setup requires PostgreSQL
        raise RuntimeError(
            "❌ PostgreSQL required but DATABASE_URL not found!\n"
            "Please set DATABASE_URL in .env:\n"
            "DATABASE_URL=postgresql+psycopg://ai:ai@localhost:5532/ai"
        )

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.get_db_url().lower()


# Create global db_settings instance
db_settings = DbSettings()