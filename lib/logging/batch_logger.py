"""
Batch Logging Utility for Automagik Hive
Reduces log volume by batching similar operations and providing summaries.
"""

import os
from collections import Counter, defaultdict
from contextlib import contextmanager

from loguru import logger


class BatchLogger:
    """Context-aware batch logger that reduces repetitive log messages."""

    def __init__(self):
        self.startup_mode = True
        self.batches = defaultdict(list)
        self.counters = Counter()
        self.seen_messages = set()

        # Configuration
        self.verbose = os.getenv("HIVE_VERBOSE_LOGS", "false").lower() == "true"
        self.log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()

    def set_runtime_mode(self):
        """Switch from startup to runtime logging mode."""
        self.startup_mode = False
        self._flush_startup_batches()

    def _should_log_verbose(self) -> bool:
        """Check if verbose logging should be enabled."""
        return self.verbose or self.log_level == "DEBUG"

    def log_agent_inheritance(self, agent_id: str):
        """Log agent inheritance application (batched during startup)."""
        if self._should_log_verbose():
            logger.debug(f"Applied inheritance to agent {agent_id}")
            return

        if self.startup_mode:
            self.batches["agent_inheritance"].append(agent_id)
        else:
            logger.debug(f"Applied inheritance to agent {agent_id}")

    def log_model_resolved(self, model_id: str, provider: str):
        """Log model resolution (batched during startup)."""
        if self._should_log_verbose():
            logger.info(
                "Model resolved successfully", model_id=model_id, provider=provider
            )
            return

        if self.startup_mode:
            self.batches["model_resolved"].append((model_id, provider))
        else:
            logger.debug(f"🔧 Model resolved: {model_id}")

    def log_storage_created(self, storage_type: str, component_id: str):
        """Log storage creation (batched during startup)."""
        if self._should_log_verbose():
            logger.info(
                f"Successfully created {storage_type} storage for {component_id}"
            )
            return

        if self.startup_mode:
            self.batches["storage_created"].append((storage_type, component_id))
        else:
            logger.debug(f"🔧 Storage created: {component_id}")

    def log_agent_created(self, component_id: str, parameter_count: int):
        """Log agent creation (batched during startup)."""
        if self._should_log_verbose():
            logger.info(
                f"🤖 Agent {component_id} created with inheritance and {parameter_count} available parameters"
            )
            return

        if self.startup_mode:
            self.batches["agent_created"].append((component_id, parameter_count))
        else:
            logger.info(f"🤖 Agent {component_id} ready")

    def log_team_member_loaded(self, member_name: str, team_id: str | None = None):
        """Log team member loading (batched during startup)."""
        if self._should_log_verbose():
            logger.info(f"🤖 Loaded team member: {member_name}")
            return

        if self.startup_mode:
            key = f"team_members_{team_id}" if team_id else "team_members"
            self.batches[key].append(member_name)
        else:
            logger.debug(f"🤖 Member loaded: {member_name}")

    def log_csv_processing(self, source: str, document_count: int):
        """Log CSV processing (batched during startup)."""
        if self._should_log_verbose():
            logger.info(f"{source}: {document_count} documents processed")
            return

        if self.startup_mode:
            self.batches["csv_processing"].append((source, document_count))
        else:
            logger.debug(f"{source}: {document_count} docs")

    def log_once(self, message: str, level: str = "info", **kwargs):
        """Log a message only once (deduplication)."""
        message_key = f"{message}_{kwargs}"
        if message_key not in self.seen_messages:
            self.seen_messages.add(message_key)
            getattr(logger, level.lower())(message, **kwargs)

    def _flush_startup_batches(self):
        """Flush all accumulated startup batches as summary messages."""
        if not self.batches:
            return

        # Agent inheritance summary
        if self.batches["agent_inheritance"]:
            agents = self.batches["agent_inheritance"]
            logger.info(
                f"Applied inheritance to {len(agents)} agents: {', '.join(agents)}"
            )

        # Model resolution summary
        if self.batches["model_resolved"]:
            models = self.batches["model_resolved"]
            unique_providers = {provider for _, provider in models}
            logger.info(
                f"Model resolution: {len(models)} operations across {len(unique_providers)} providers"
            )

        # Storage creation summary
        if self.batches["storage_created"]:
            storage_ops = self.batches["storage_created"]
            storage_types = Counter(storage_type for storage_type, _ in storage_ops)
            logger.info(f"Storage initialization: {dict(storage_types)}")

        # Agent creation summary
        if self.batches["agent_created"]:
            agents = self.batches["agent_created"]
            total_params = sum(count for _, count in agents)
            avg_params = total_params // len(agents) if agents else 0
            agent_names = [name for name, _ in agents]
            logger.info(
                f"Created {len(agents)} agents: {', '.join(agent_names)} (avg {avg_params} params)"
            )

        # Team member loading summary
        team_keys = [key for key in self.batches if key.startswith("team_members")]
        for team_key in team_keys:
            members = self.batches[team_key]
            if team_key == "team_members":
                logger.info(
                    f"🤖 Loaded {len(members)} team members: {', '.join(members)}"
                )
            else:
                team_id = team_key.replace("team_members_", "")
                logger.info(
                    f"🤖 Team {team_id}: {len(members)} members loaded ({', '.join(members)})"
                )

        # CSV processing summary
        if self.batches["csv_processing"]:
            csv_ops = self.batches["csv_processing"]
            total_docs = sum(count for _, count in csv_ops)
            sources = len({source for source, _ in csv_ops})
            logger.info(
                f"Knowledge base: {sources} sources, {total_docs} documents loaded"
            )

        # Clear batches
        self.batches.clear()

    @contextmanager
    def startup_context(self):
        """Context manager for startup logging batch mode."""
        self.startup_mode = True
        try:
            yield self
        finally:
            self.set_runtime_mode()

    def force_flush(self):
        """Force flush all pending batches (for testing/debugging)."""
        self._flush_startup_batches()


# Global batch logger instance
batch_logger = BatchLogger()


def log_agent_inheritance(agent_id: str):
    """Convenience function for agent inheritance logging."""
    batch_logger.log_agent_inheritance(agent_id)


def log_model_resolved(model_id: str, provider: str = "unknown"):
    """Convenience function for model resolution logging."""
    batch_logger.log_model_resolved(model_id, provider)


def log_storage_created(storage_type: str, component_id: str):
    """Convenience function for storage creation logging."""
    batch_logger.log_storage_created(storage_type, component_id)


def log_agent_created(component_id: str, parameter_count: int):
    """Convenience function for agent creation logging."""
    batch_logger.log_agent_created(component_id, parameter_count)


def log_team_member_loaded(member_name: str, team_id: str | None = None):
    """Convenience function for team member loading."""
    batch_logger.log_team_member_loaded(member_name, team_id)


def log_csv_processing(source: str, document_count: int):
    """Convenience function for CSV processing logging."""
    batch_logger.log_csv_processing(source, document_count)


def set_runtime_mode():
    """Switch to runtime logging mode and flush startup batches."""
    batch_logger.set_runtime_mode()


def startup_logging():
    """Context manager for startup batch logging."""
    return batch_logger.startup_context()
