"""Compatibility shim re-exporting the CSV hot reload manager and CLI."""

from lib.knowledge.csv_hot_reload import (
    CSVHotReloadManager,  # noqa: F401
    OpenAIEmbedder,  # noqa: F401
    PgVector,  # noqa: F401
    PostgresDb,  # noqa: F401
    load_global_knowledge_config,  # noqa: F401
    main,  # noqa: F401
)

__all__ = [
    "CSVHotReloadManager",
    "load_global_knowledge_config",
    "OpenAIEmbedder",
    "PgVector",
    "PostgresDb",
    "main",
]
