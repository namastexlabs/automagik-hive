"""Docker container management for Automagik Hive.

This module provides Docker container lifecycle management,
specifically for PostgreSQL with pgvector integration.

NOTE: Docker infrastructure is OPTIONAL. Only required when using
HIVE_DATABASE_BACKEND=postgresql. PGlite and SQLite backends do not
require Docker.
"""

import os
from typing import TYPE_CHECKING

# Conditional imports based on backend selection
# Only load Docker managers when PostgreSQL backend is configured
_BACKEND = os.getenv("HIVE_DATABASE_BACKEND", "pglite").lower()
_REQUIRES_DOCKER = _BACKEND == "postgresql"

if TYPE_CHECKING or _REQUIRES_DOCKER:
    from .compose_manager import DockerComposeManager
    from .postgres_manager import PostgreSQLManager

    __all__ = [
        "DockerComposeManager",
        "PostgreSQLManager",
    ]
else:
    # No Docker infrastructure needed for PGlite/SQLite backends
    __all__ = []
