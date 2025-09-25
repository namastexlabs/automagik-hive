"""CSV hot reload manager aligned with Agno v2 knowledge system."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Timer
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

from agno.db.postgres import PostgresDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector

from lib.knowledge.row_based_csv_knowledge import RowBasedCSVKnowledgeBase
from lib.logging import logger


DEFAULT_EMBEDDER_ID = "text-embedding-3-small"


def load_global_knowledge_config() -> dict[str, Any]:
    """Expose knowledge config loader for patchability."""

    from lib.utils.version_factory import load_global_knowledge_config as loader

    return loader()


class CSVHotReloadManager:
    """Watch a CSV file and keep the Agno knowledge base in sync."""

    def __init__(
        self,
        csv_path: str | None = None,
        *,
        config: Optional[dict[str, Any]] = None,
    ) -> None:
        self._config = config or self._load_config()
        self.csv_path = self._resolve_csv_path(csv_path)
        self.is_running = False
        self.observer = None
        self.knowledge_base: Optional[RowBasedCSVKnowledgeBase] = None
        self._debounce_timer: Optional[Timer] = None
        self._debounce_delay = self._extract_debounce_delay()
        self._contents_db: Optional[PostgresDb] = None

        logger.info(
            "CSV Hot Reload Manager initialized",
            path=str(self.csv_path),
            mode="agno_native_incremental",
        )

        self._initialize_knowledge_base()

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def _load_config(self) -> dict[str, Any]:
        try:
            return load_global_knowledge_config()
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "Could not load centralized knowledge configuration",
                error=str(exc),
            )
            return {}

    def _resolve_csv_path(self, supplied: Optional[str]) -> Path:
        if supplied:
            candidate = Path(supplied)
            if not candidate.is_absolute():
                candidate = (Path(__file__).parent / candidate).resolve()
            return candidate

        knowledge_cfg: Dict[str, Any] = self._config.get("knowledge", {})
        csv_setting = knowledge_cfg.get("csv_file_path") or self._config.get(
            "csv_file_path"
        )

        if csv_setting:
            candidate = Path(csv_setting)
            if not candidate.is_absolute():
                candidate = (Path(__file__).parent / candidate).resolve()
            logger.debug("Using CSV path from configuration", csv_path=str(candidate))
            return candidate

        fallback = (Path(__file__).parent / "knowledge_rag.csv").resolve()
        logger.warning(
            "No CSV path provided; using default fallback",
            csv_path=str(fallback),
        )
        return fallback

    def _extract_debounce_delay(self) -> float:
        try:
            return float(
                self._config.get("knowledge", {})
                .get("hot_reload", {})
                .get("debounce_delay", 1.0)
            )
        except Exception:  # pragma: no cover - defensive parsing
            return 1.0

    # ------------------------------------------------------------------
    # Knowledge base wiring
    # ------------------------------------------------------------------
    def _initialize_knowledge_base(self) -> None:
        db_url = os.getenv("HIVE_DATABASE_URL")
        if not db_url:
            logger.warning(
                "HIVE_DATABASE_URL not set; knowledge base hot reload disabled"
            )
            self.knowledge_base = None
            return

        try:
            embedder = self._build_embedder()
            vector_db = self._build_vector_db(db_url, embedder)
            contents_db = self._build_contents_db(db_url)

            # Create knowledge base without constructor drift; attach contents DB afterward
            self.knowledge_base = RowBasedCSVKnowledgeBase(
                csv_path=str(self.csv_path),
                vector_db=vector_db,
            )
            
            # Inject contents_db post-instantiation to enable remove_content_by_id during reloads
            self._contents_db = contents_db
            if contents_db is not None and self.knowledge_base is not None:
                try:
                    # Attach to KB instance
                    setattr(self.knowledge_base, "contents_db", contents_db)
                    # And to the underlying Knowledge instance if available
                    kb_knowledge = getattr(self.knowledge_base, "knowledge", None)
                    if kb_knowledge is not None:
                        setattr(kb_knowledge, "contents_db", contents_db)
                        logger.debug("Activated contents DB", table=getattr(contents_db, "session_table", None))
                except Exception:  # pragma: no cover - defensive safety
                    # Non-fatal: continue without contents DB
                    pass

            if self.csv_path.exists():
                self.knowledge_base.load(recreate=False, skip_existing=True)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to initialize knowledge base", error=str(exc))
            self.knowledge_base = None

    def _build_embedder(self) -> OpenAIEmbedder:
        vector_cfg = self._vector_config()
        embedder_id = vector_cfg.get("embedder", DEFAULT_EMBEDDER_ID)

        try:
            return OpenAIEmbedder(id=embedder_id)
        except Exception as exc:
            logger.warning(
                "Falling back to default embedder", error=str(exc)
            )
            return OpenAIEmbedder(id=DEFAULT_EMBEDDER_ID)

    def _vector_config(self) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        if isinstance(self._config, dict):
            top_level = self._config.get("vector_db")
            if isinstance(top_level, dict):
                merged.update(top_level)

            knowledge_cfg = self._config.get("knowledge", {})
            if isinstance(knowledge_cfg, dict):
                nested = knowledge_cfg.get("vector_db")
                if isinstance(nested, dict):
                    merged.update(nested)

        return merged

    def _build_vector_db(self, db_url: str, embedder: OpenAIEmbedder) -> PgVector:
        vector_cfg = self._vector_config()
        table_name = vector_cfg.get("table_name", "knowledge_base")
        schema = vector_cfg.get("schema", "agno")
        distance = vector_cfg.get("distance", "cosine")

        return PgVector(
            table_name=table_name,
            schema=schema,
            db_url=db_url,
            embedder=embedder,
        )

    def _build_contents_db(self, db_url: str) -> Optional[PostgresDb]:
        vector_cfg = self._vector_config()
        knowledge_table = vector_cfg.get("knowledge_table", "agno_knowledge")
        schema = vector_cfg.get("schema", "agno")

        try:
            return PostgresDb(
                db_url=db_url,
                db_schema=schema,
                knowledge_table=knowledge_table,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "Could not initialize contents database", error=str(exc)
            )
            return None

    # ------------------------------------------------------------------
    # File watching & reload mechanics
    # ------------------------------------------------------------------
    def start_watching(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        logger.info("File watching started", path=str(self.csv_path))

        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            class Handler(FileSystemEventHandler):
                def __init__(self, manager: "CSVHotReloadManager") -> None:
                    self._manager = manager

                def _is_target(self, event_path: str) -> bool:
                    return event_path.endswith(self._manager.csv_path.name)

                def on_modified(self, event):  # type: ignore[override]
                    if not getattr(event, "is_directory", False) and self._is_target(
                        event.src_path
                    ):
                        self._manager._schedule_reload()

                def on_moved(self, event):  # type: ignore[override]
                    dest_path = getattr(event, "dest_path", "")
                    if dest_path and self._is_target(dest_path):
                        self._manager._schedule_reload()

            self.observer = Observer()
            handler = Handler(self)
            self.observer.schedule(handler, str(self.csv_path.parent), recursive=False)
            self.observer.start()

            logger.info("File watching active", observer_started=True)
        except Exception as exc:
            logger.error("Error setting up file watcher", error=str(exc))
            self.stop_watching()

    def stop_watching(self) -> None:
        if not self.is_running:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.is_running = False

        if self._debounce_timer:
            try:
                self._debounce_timer.cancel()
            finally:
                self._debounce_timer = None

        logger.info("File watching stopped", path=str(self.csv_path))

    def _schedule_reload(self) -> None:
        if self._debounce_timer:
            try:
                self._debounce_timer.cancel()
            except Exception:  # pragma: no cover - defensive
                pass

        self._debounce_timer = Timer(self._debounce_delay, self._reload_knowledge_base)
        self._debounce_timer.daemon = True
        self._debounce_timer.start()

    def _reload_knowledge_base(self) -> None:
        if not self.knowledge_base:
            return

        try:
            self.knowledge_base.load(recreate=False, skip_existing=True)
            logger.info(
                "Knowledge base reload completed",
                path=str(self.csv_path),
            )
        except Exception as exc:
            logger.error(
                "Knowledge base reload failed", error=str(exc), component="csv_hot_reload"
            )

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------
    def get_status(self) -> dict[str, Any]:
        return {
            "status": "running" if self.is_running else "stopped",
            "csv_path": str(self.csv_path),
            "mode": "agno_native_incremental",
            "file_exists": self.csv_path.exists(),
        }

    def force_reload(self) -> None:
        logger.info("Force reloading knowledge base", component="csv_hot_reload")
        self._reload_knowledge_base()


__all__ = ["CSVHotReloadManager", "load_global_knowledge_config", "OpenAIEmbedder", "PgVector", "PostgresDb"]
