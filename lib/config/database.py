"""Database configuration for PagBank Multi-Agent System."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://ai:ai@localhost:5532/ai"
)

class DatabaseConfig:
    """PostgreSQL with PgVector configuration."""
    
    def __init__(self):
        self.url = DATABASE_URL
        self.engine = None
        self.session_factory = None
        self.base = declarative_base()
    
    def create_engine(self):
        """Create SQLAlchemy engine."""
        if not self.engine:
            self.engine = create_engine(
                self.url,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
        return self.engine
    
    def create_session_factory(self):
        """Create session factory."""
        if not self.session_factory:
            engine = self.create_engine()
            self.session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False
            )
        return self.session_factory
    
    def get_session(self):
        """Get database session."""
        session_factory = self.create_session_factory()
        return session_factory()
    
    def init_pgvector(self):
        """Initialize PgVector extension."""
        with self.get_session() as session:
            # Enable PgVector extension
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            engine = self.create_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1;"))
                return result.fetchone()[0] == 1
        except Exception:
            return False
    
    def test_pgvector(self) -> bool:
        """Test PgVector functionality."""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT vector_dims(vector '[1,2,3]');"))
                return result.fetchone()[0] == 3
        except Exception:
            return False

# Global database instance
db_config = DatabaseConfig()

# Common database utilities
def get_db_session():
    """Get database session."""
    return db_config.get_session()

def init_database():
    """Initialize database with PgVector."""
    db_config.init_pgvector()
    return db_config

# Database health check
def health_check() -> dict:
    """Check database health."""
    return {
        "connection": db_config.test_connection(),
        "pgvector": db_config.test_pgvector(),
        "url": DATABASE_URL.replace(DATABASE_URL.split("@")[0].split("//")[1], "***")
    }