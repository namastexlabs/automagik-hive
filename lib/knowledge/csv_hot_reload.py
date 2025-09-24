"""Compatibility layer for legacy imports of csv_hot_reload."""

from lib.knowledge.datasources.csv_hot_reload import *  # noqa: F401,F403

try:
    from lib.knowledge.factories.knowledge_factory import PgVector as PgVector  # noqa: F401
except Exception:  # pragma: no cover - defensive if dependency missing
    PgVector = None  # type: ignore
