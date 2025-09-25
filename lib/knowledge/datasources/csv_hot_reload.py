"""Compatibility shim re-exporting the CSV hot reload manager and CLI."""

from lib.knowledge.csv_hot_reload import (  # noqa: F401
    CSVHotReloadManager,
    load_global_knowledge_config,
    OpenAIEmbedder,
    PgVector,
    PostgresDb,
)

# Explicitly expose main for tests that import it
from lib.knowledge.csv_hot_reload import main  # noqa: F401


__all__ = [
    "CSVHotReloadManager",
    "load_global_knowledge_config",
    "OpenAIEmbedder",
    "PgVector",
    "PostgresDb",
    "main",
]
