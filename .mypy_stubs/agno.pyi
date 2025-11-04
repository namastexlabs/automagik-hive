"""Type stubs for agno library.

This file provides minimal type hints for agno's external API surface
to satisfy mypy type checking without requiring full package annotations.
"""

from typing import Any

# agno.document
class CSVReader:
    """CSV document reader for knowledge bases."""

    def __init__(self, path: str) -> None: ...

# agno.knowledge
class DocumentKnowledgeBase:
    """Knowledge base powered by document embeddings."""

    def __init__(self, reader: Any, num_documents: int = 5) -> None: ...

# agno.storage.postgres
class PostgresStorage:
    """PostgreSQL-backed agent session storage."""

    def __init__(
        self,
        connection_url: str,
        table_name: str = "agent_sessions",
        auto_upgrade_schema: bool = True,
    ) -> None: ...

# agno.storage.sqlite
class SqliteStorage:
    """SQLite-backed agent session storage."""

    def __init__(
        self,
        db_file: str = "./data/agent.db",
        table_name: str = "agent_sessions",
        auto_upgrade_schema: bool = True,
    ) -> None: ...
