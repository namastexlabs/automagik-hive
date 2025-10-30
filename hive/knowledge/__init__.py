"""
Smart RAG System - The Crown Jewel of Automagik Hive.

This module provides intelligent CSV-based knowledge management with:
- Hash-based incremental loading (only re-embed changed rows)
- Hot reload with file watching
- PgVector integration for efficient retrieval
- Thread-safe knowledge base factory

Key Features:
- 10x faster for large CSVs (1000+ rows)
- Saves embedding costs (only process changes)
- Hot reload without restart
- Tracks change history

Usage:
    from hive.knowledge import create_knowledge_base

    # Returns agno.knowledge.Knowledge instance
    kb = create_knowledge_base(
        csv_path="data/knowledge.csv",
        embedder="text-embedding-3-small",
        num_documents=5,
        hot_reload=True
    )
"""

from hive.knowledge.knowledge import create_knowledge_base

__all__ = ["create_knowledge_base"]
