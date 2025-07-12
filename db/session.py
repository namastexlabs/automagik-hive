"""
Database session management for PagBank V2.
Based on agno-demo-app patterns with PagBank-specific optimizations.
"""

from typing import Generator
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from .settings import db_settings

# Create SQLAlchemy Engine using database URL
db_url: str = db_settings.get_db_url()
db_engine: Engine = create_engine(
    db_url, 
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    echo=False  # Set to True for SQL debugging
)

# Create SessionLocal class
# https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-sessionlocal-class
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=db_engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a database session.
    Compatible with FastAPI dependency injection.

    Yields:
        Session: An SQLAlchemy database session.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """Test database connection."""
    try:
        with db_engine.connect() as conn:
            result = conn.execute("SELECT 1;")
            return result.fetchone()[0] == 1
    except Exception:
        return False


def init_database():
    """Initialize database with extensions."""
    from .tables.base import Base
    
    # Create all tables
    Base.metadata.create_all(bind=db_engine)
    
    # Initialize PgVector if using PostgreSQL
    if "postgresql" in db_url.lower():
        try:
            with db_engine.connect() as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
        except Exception as e:
            print(f"⚠️ Could not initialize PgVector: {e}")
    
    return True