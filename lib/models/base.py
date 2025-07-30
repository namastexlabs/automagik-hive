"""
Base SQLAlchemy model configuration for Hive schema
"""

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Configure metadata for hive schema
metadata = MetaData(schema="hive")
Base = declarative_base(metadata=metadata)
