"""
Hive Database Module.

Provides database utilities including embedded PostgreSQL for serverless deployments.
"""

from hive.database.embedded_postgres import (
    EmbeddedPostgres,
    get_embedded_postgres,
    stop_embedded_postgres,
)

__all__ = [
    "EmbeddedPostgres",
    "get_embedded_postgres",
    "stop_embedded_postgres",
]
