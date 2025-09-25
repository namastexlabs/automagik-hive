#!/usr/bin/env python3
"""
Smart Incremental Loader – Smoke Runner

Usage:
  uv run python -m lib.knowledge.smart_incremental_loader_smoke --csv lib/knowledge/data/knowledge_rag.csv

This performs a lightweight smart_load execution and prints a JSON summary.
If the knowledge base cannot be constructed (no vector DB), it still proceeds
with a no-op KB to exercise the strategy planner and hash population paths.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from lib.logging import logger


def run_smoke(csv_path: str | None, force: bool) -> int:
    # Validate environment early for a better error message
    db_url = os.getenv("HIVE_DATABASE_URL")
    if not db_url:
        logger.error("HIVE_DATABASE_URL is required for smoke run")
        logger.info(json.dumps({"error": "HIVE_DATABASE_URL not set"}))
        return 2

    try:
        from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
        from lib.knowledge.smart_incremental_loader import SmartIncrementalLoader
    except Exception as exc:  # pragma: no cover - CLI-only
        logger.error("Failed to import knowledge modules", error=str(exc))
        logger.info(json.dumps({"error": str(exc)}))
        return 3

    # Resolve CSV path
    resolved_csv: Path | None = None
    if csv_path:
        candidate = Path(csv_path)
        resolved_csv = candidate if candidate.is_absolute() else (Path(__file__).parent / candidate).resolve()

    try:
        loader = SmartIncrementalLoader(str(resolved_csv) if resolved_csv else None)
        # Ensure a KB exists even without vector DB to exercise code paths
        if loader.kb is None:
            loader.kb = RowBasedCSVKnowledgeBase(csv_path=str(loader.csv_path), vector_db=None)

        result = loader.smart_load(force_recreate=force)
        logger.info(json.dumps(result, indent=2))
        return 0 if "error" not in result else 1
    except Exception as exc:  # pragma: no cover - CLI-only
        logger.error("Smoke run failed", error=str(exc))
        logger.info(json.dumps({"error": str(exc)}))
        return 4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smart Incremental Loader smoke runner")
    parser.add_argument("--csv", dest="csv", help="Path to CSV file", default=None)
    parser.add_argument("--force", dest="force", help="Force full rebuild", action="store_true")
    args = parser.parse_args(argv)
    return run_smoke(args.csv, args.force)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
