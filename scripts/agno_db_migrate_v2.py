#!/usr/bin/env python3
"""Automagik wrapper around Agno's v2 persistence migration script."""

from __future__ import annotations

import argparse
import asyncio
import importlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlparse, urlunparse

from lib.logging import logger
from lib.services.database_service import DatabaseService


def _ensure_pymongo_stubs() -> None:
    """Provide lightweight pymongo stubs so the Agno migration can import cleanly."""

    try:
        import pymongo  # noqa: F401

        return
    except ImportError:
        pass

    import sys
    import types

    pymongo_stub = types.ModuleType("pymongo")

    collection_module = types.ModuleType("pymongo.collection")
    database_module = types.ModuleType("pymongo.database")
    errors_module = types.ModuleType("pymongo.errors")

    class _Collection:  # pragma: no cover - compatibility shim
        ...

    class _Database:  # pragma: no cover - compatibility shim
        ...

    class _OperationFailureError(Exception):  # pragma: no cover - compatibility shim
        ...

    class _ReturnDocument:  # pragma: no cover - compatibility shim
        AFTER = "after"

    collection_module.Collection = _Collection
    database_module.Database = _Database
    errors_module.OperationFailure = _OperationFailureError

    pymongo_stub.collection = collection_module
    pymongo_stub.database = database_module
    pymongo_stub.errors = errors_module
    pymongo_stub.MongoClient = type("MongoClient", (object,), {})
    pymongo_stub.ReturnDocument = _ReturnDocument

    sys.modules.setdefault("pymongo", pymongo_stub)
    sys.modules.setdefault("pymongo.collection", collection_module)
    sys.modules.setdefault("pymongo.database", database_module)
    sys.modules.setdefault("pymongo.errors", errors_module)


_ensure_pymongo_stubs()

from agno.db.migrations.v1_to_v2 import migrate  # noqa: E402
from agno.db.postgres.postgres import PostgresDb  # noqa: E402


@dataclass(slots=True)
class MigrationContext:
    """Resolved runtime context for executing the migration."""

    dry_run: bool
    database_url: str | None
    batch_size: int
    log_path: Path
    settings: Any


def _mask_db_url(db_url: str) -> str:
    """Mask credentials in a database URL for safe logging."""

    try:
        parsed = urlparse(db_url)
    except ValueError:
        return "***"

    if not parsed.netloc or "@" not in parsed.netloc:
        return db_url

    username = parsed.username or ""
    host = parsed.hostname or "localhost"
    port_segment = f":{parsed.port}" if parsed.port else ""
    netloc = f"{username}:***@{host}{port_segment}"
    masked = parsed._replace(netloc=netloc)
    return urlunparse(masked)


def _qualify_table(schema: str | None, table_name: str) -> str:
    """Return a fully-qualified table reference for SQL usage."""

    if not table_name:
        return ""
    if "." in table_name:
        return table_name
    if not schema:
        return table_name
    return f'"{schema}"."{table_name}"'


async def _collect_counts(
    db_url: str,
    schema: str | None,
    tables: dict[str, str | None],
) -> dict[str, int | None]:
    """Collect row counts for the provided tables."""

    service = DatabaseService(db_url)
    await service.initialize()

    counts: dict[str, int | None] = {}

    try:
        for label, table_name in tables.items():
            if not table_name:
                counts[label] = None
                continue

            qualified = _qualify_table(schema, table_name)

            try:
                result = await service.fetch_one(
                    f"SELECT COUNT(*) AS total FROM {qualified}"  # noqa: S608 - Test/script SQL
                )
                counts[label] = int(result["total"]) if result else 0
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Unable to read table row count",
                    table=qualified,
                    error=str(exc),
                )
                counts[label] = None
    finally:
        await service.close()

    return counts


def _default_log_path(dry_run: bool) -> Path:
    """Return the default location for the migration transcript."""

    suffix = "dry-run" if dry_run else "apply"
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    reports_dir = Path("genie/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir / f"agno-v2-migration-{suffix}-{timestamp}.log"


def _prepare_context(args: argparse.Namespace) -> MigrationContext:
    try:
        settings_module = importlib.import_module("lib.config.settings")
        settings = settings_module.get_settings()  # type: ignore[attr-defined]
    except BaseException:  # pragma: no cover - fallback for missing env configuration
        logger.warning("Falling back to in-memory settings snapshot for migration wrapper")
        settings = SimpleNamespace(
            hive_database_url=None,
            hive_agno_v2_migration_enabled=False,
            hive_agno_v1_schema="agno",
            hive_agno_v1_agent_sessions_table="agent_sessions",
            hive_agno_v1_team_sessions_table="team_sessions",
            hive_agno_v1_workflow_sessions_table="workflow_sessions",
            hive_agno_v1_memories_table="memories",
            hive_agno_v1_metrics_table=None,
            hive_agno_v1_knowledge_table=None,
            hive_agno_v1_evals_table=None,
            hive_agno_v2_sessions_table="hive_sessions",
            hive_agno_v2_memories_table="hive_memories",
            hive_agno_v2_metrics_table="hive_metrics",
            hive_agno_v2_knowledge_table="hive_knowledge",
            hive_agno_v2_evals_table="hive_evals",
        )

        settings.agno_v1_tables = {
            "schema": settings.hive_agno_v1_schema,
            "agent_sessions": settings.hive_agno_v1_agent_sessions_table,
            "team_sessions": settings.hive_agno_v1_team_sessions_table,
            "workflow_sessions": settings.hive_agno_v1_workflow_sessions_table,
            "memories": settings.hive_agno_v1_memories_table,
            "metrics": settings.hive_agno_v1_metrics_table,
            "knowledge": settings.hive_agno_v1_knowledge_table,
            "evals": settings.hive_agno_v1_evals_table,
        }
        settings.agno_v2_tables = {
            "sessions": settings.hive_agno_v2_sessions_table,
            "memories": settings.hive_agno_v2_memories_table,
            "metrics": settings.hive_agno_v2_metrics_table,
            "knowledge": settings.hive_agno_v2_knowledge_table,
            "evals": settings.hive_agno_v2_evals_table,
        }

    database_url = args.database_url or settings.hive_database_url
    log_path = Path(args.log_path) if args.log_path else _default_log_path(args.dry_run)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    return MigrationContext(
        dry_run=args.dry_run,
        database_url=database_url,
        batch_size=args.batch_size,
        log_path=log_path,
        settings=settings,
    )


def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Agno v2 persistence migration with Automagik defaults",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip the migration execution but capture diagnostics",
    )
    parser.add_argument(
        "--database-url",
        help="Override the HIVE_DATABASE_URL for this invocation",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size to use for the upstream migration routine",
    )
    parser.add_argument(
        "--log-path",
        help="Optional destination for the structured migration log",
    )
    return parser.parse_args()


def _write_transcript(log_path: Path, payload: dict[str, Any]) -> None:
    formatted = json_dumps(payload)
    log_path.write_text(formatted, encoding="utf-8")


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _build_summary(
    context: MigrationContext,
    v1_counts_before: dict[str, int | None] | None,
    v2_counts_before: dict[str, int | None] | None,
    v1_counts_after: dict[str, int | None] | None,
    v2_counts_after: dict[str, int | None] | None,
    outcome: str,
) -> dict[str, Any]:
    masked_url = _mask_db_url(context.database_url) if context.database_url else None

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "dry_run": context.dry_run,
        "database_url": masked_url,
        "batch_size": context.batch_size,
        "outcome": outcome,
        "v1_counts_before": v1_counts_before,
        "v1_counts_after": v1_counts_after,
        "v2_counts_before": v2_counts_before,
        "v2_counts_after": v2_counts_after,
        "settings_snapshot": {
            "v1_tables": context.settings.agno_v1_tables,
            "v2_tables": context.settings.agno_v2_tables,
        },
    }


def _run_migration(context: MigrationContext) -> str:
    """Execute the upstream migration when not in dry-run mode."""

    if not context.database_url:
        return "skipped-no-database-url"

    if context.dry_run:
        logger.info("Dry run active - skipping migrate() execution")
        return "dry-run"

    logger.info(
        "Running Agno migrate()",
        batch_size=context.batch_size,
        db_url=_mask_db_url(context.database_url),
    )

    db = PostgresDb(
        db_url=context.database_url,
        session_table=context.settings.hive_agno_v2_sessions_table,
        memory_table=context.settings.hive_agno_v2_memories_table,
    )

    migrate(
        db=db,
        v1_db_schema=context.settings.hive_agno_v1_schema,
        agent_sessions_table_name=context.settings.hive_agno_v1_agent_sessions_table,
        team_sessions_table_name=context.settings.hive_agno_v1_team_sessions_table,
        workflow_sessions_table_name=context.settings.hive_agno_v1_workflow_sessions_table,
        memories_table_name=context.settings.hive_agno_v1_memories_table,
    )

    logger.info("Agno migrate() completed successfully")
    return "migrated"


def main() -> None:
    args = _parse_cli()
    context = _prepare_context(args)

    logger.info(
        "Starting Agno v2 migration wrapper",
        dry_run=context.dry_run,
        db_url=_mask_db_url(context.database_url) if context.database_url else None,
    )

    v1_counts_before: dict[str, int | None] | None = None
    v2_counts_before: dict[str, int | None] | None = None
    v1_counts_after: dict[str, int | None] | None = None
    v2_counts_after: dict[str, int | None] | None = None

    if context.database_url:
        logger.info("Collecting pre-migration row counts")
        v1_tables = context.settings.agno_v1_tables
        v2_tables = context.settings.agno_v2_tables

        v1_counts_before = asyncio.run(
            _collect_counts(
                context.database_url,
                v1_tables.get("schema"),
                {
                    "agent_sessions": v1_tables.get("agent_sessions"),
                    "team_sessions": v1_tables.get("team_sessions"),
                    "workflow_sessions": v1_tables.get("workflow_sessions"),
                    "memories": v1_tables.get("memories"),
                    "metrics": v1_tables.get("metrics"),
                    "knowledge": v1_tables.get("knowledge"),
                    "evals": v1_tables.get("evals"),
                },
            )
        )

        v2_counts_before = asyncio.run(
            _collect_counts(
                context.database_url,
                v1_tables.get("schema"),
                v2_tables,
            )
        )
    else:
        logger.warning("No database URL available - skipping table snapshot collection")

    outcome = _run_migration(context)

    if context.database_url:
        logger.info("Collecting post-migration row counts")
        v1_tables = context.settings.agno_v1_tables
        v2_tables = context.settings.agno_v2_tables

        v1_counts_after = asyncio.run(
            _collect_counts(
                context.database_url,
                v1_tables.get("schema"),
                {
                    "agent_sessions": v1_tables.get("agent_sessions"),
                    "team_sessions": v1_tables.get("team_sessions"),
                    "workflow_sessions": v1_tables.get("workflow_sessions"),
                    "memories": v1_tables.get("memories"),
                    "metrics": v1_tables.get("metrics"),
                    "knowledge": v1_tables.get("knowledge"),
                    "evals": v1_tables.get("evals"),
                },
            )
        )

        v2_counts_after = asyncio.run(
            _collect_counts(
                context.database_url,
                v1_tables.get("schema"),
                v2_tables,
            )
        )

    summary = _build_summary(
        context,
        v1_counts_before,
        v2_counts_before,
        v1_counts_after,
        v2_counts_after,
        outcome,
    )

    _write_transcript(context.log_path, summary)
    logger.info("Migration transcript saved", log_path=str(context.log_path))


if __name__ == "__main__":
    main()
