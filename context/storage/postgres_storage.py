"""
Simplified PostgreSQL Storage Configuration for PagBank Multi-Agent System
Uses Agno's built-in PostgreSQL support
"""

import os
from typing import Optional

from agno.storage.postgres import PostgresStorage
from agno.memory.v2.db.postgres import PostgresMemoryDb


class PostgresConfig:
    """
    Simple PostgreSQL configuration for all components
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """Initialize with database URL from environment"""
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")
    
    def get_team_storage(self) -> PostgresStorage:
        """Get PostgresStorage for team sessions (Agno will auto-create table)"""
        return PostgresStorage(
            table_name="team_sessions",
            db_url=self.db_url,
            auto_upgrade_schema=True
        )
    
    def get_agent_storage(self) -> PostgresStorage:
        """Get PostgresStorage for agent sessions (Agno will auto-create table)"""
        return PostgresStorage(
            table_name="agent_sessions",
            db_url=self.db_url,
            auto_upgrade_schema=True
        )
    
    def get_user_memory_db(self) -> PostgresMemoryDb:
        """Get PostgresMemoryDb for general user memories (Agno will auto-create table)"""
        return PostgresMemoryDb(
            table_name="user_memories",
            db_url=self.db_url
        )
    
    def get_ana_memory_db(self) -> PostgresMemoryDb:
        """Get PostgresMemoryDb for Ana's personalized memories (Agno will auto-create table)"""
        return PostgresMemoryDb(
            table_name="ana_user_memories",
            db_url=self.db_url
        )


# Singleton instance
_postgres_config = None


def get_postgres_config() -> PostgresConfig:
    """Get or create PostgreSQL configuration singleton"""
    global _postgres_config
    if _postgres_config is None:
        _postgres_config = PostgresConfig()
    return _postgres_config