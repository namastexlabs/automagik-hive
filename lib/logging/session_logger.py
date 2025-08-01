"""
Agent Session Lifecycle Logging

This module provides comprehensive logging for agent session lifecycle events,
helping with monitoring, debugging, and preventing session-related issues.
"""

from datetime import datetime
from typing import Any

from lib.logging import logger


class SessionLifecycleLogger:
    """
    Logger for tracking agent session lifecycle events.

    This class provides structured logging for agent sessions, runs, and
    conversation management to help with debugging and monitoring.
    """

    def __init__(self):
        """Initialize the session lifecycle logger."""

    def log_session_start(
        self,
        session_id: str,
        agent_id: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log the start of a new agent session.

        Args:
            session_id: Unique identifier for the session
            agent_id: ID of the agent being used
            user_id: Optional user identifier
            metadata: Additional metadata about the session
        """
        logger.info(
            "Agent session started",
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            event="session_start",
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )

    def log_run_creation(
        self,
        run_id: str,
        session_id: str,
        agent_id: str,
        user_message: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """
        Log the creation of a new agent run.

        Args:
            run_id: Unique identifier for the run
            session_id: Session this run belongs to
            agent_id: ID of the agent
            user_message: The user's message that started the run
            user_id: Optional user identifier
        """
        logger.info(
            "Agent run created",
            run_id=run_id,
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            event="run_created",
            message_length=len(user_message) if user_message else 0,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_run_continuation_attempt(
        self,
        run_id: str,
        session_id: str,
        agent_id: str,
        user_id: str | None = None,
        has_tools: bool = False,
    ) -> None:
        """
        Log an attempt to continue an existing run.

        Args:
            run_id: The run ID being continued
            session_id: Session this run belongs to
            agent_id: ID of the agent
            user_id: Optional user identifier
            has_tools: Whether tools were provided for continuation
        """
        logger.info(
            "Agent run continuation attempted",
            run_id=run_id,
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            event="run_continuation_attempt",
            has_tools=has_tools,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_run_continuation_success(
        self,
        run_id: str,
        session_id: str,
        agent_id: str,
        user_id: str | None = None,
        response_length: int | None = None,
    ) -> None:
        """
        Log successful run continuation.

        Args:
            run_id: The run ID that was continued
            session_id: Session this run belongs to
            agent_id: ID of the agent
            user_id: Optional user identifier
            response_length: Length of the agent's response
        """
        logger.info(
            "Agent run continuation successful",
            run_id=run_id,
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            event="run_continuation_success",
            response_length=response_length,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_run_continuation_failure(
        self,
        run_id: str,
        session_id: str,
        agent_id: str,
        error: str,
        error_type: str,
        user_id: str | None = None,
    ) -> None:
        """
        Log failed run continuation.

        Args:
            run_id: The run ID that failed to continue
            session_id: Session this run belongs to
            agent_id: ID of the agent
            error: Error message
            error_type: Type of error that occurred
            user_id: Optional user identifier
        """
        logger.warning(
            "Agent run continuation failed",
            run_id=run_id,
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            event="run_continuation_failure",
            error=error,
            error_type=error_type,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_session_cleanup(
        self,
        session_id: str,
        agent_id: str,
        reason: str,
        user_id: str | None = None,
        run_count: int | None = None,
    ) -> None:
        """
        Log session cleanup events.

        Args:
            session_id: Session being cleaned up
            agent_id: ID of the agent
            reason: Reason for cleanup (timeout, manual, restart, etc.)
            user_id: Optional user identifier
            run_count: Number of runs in the session
        """
        logger.info(
            "Agent session cleanup",
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            event="session_cleanup",
            reason=reason,
            run_count=run_count,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_memory_status(
        self,
        agent_id: str,
        session_count: int,
        run_count: int,
        memory_type: str,
        additional_info: dict[str, Any] | None = None,
    ) -> None:
        """
        Log current memory status for monitoring.

        Args:
            agent_id: ID of the agent
            session_count: Number of active sessions
            run_count: Total number of runs in memory
            memory_type: Type of memory being used (AgentMemory, Memory, etc.)
            additional_info: Additional memory information
        """
        logger.debug(
            "Agent memory status",
            agent_id=agent_id,
            event="memory_status",
            session_count=session_count,
            run_count=run_count,
            memory_type=memory_type,
            additional_info=additional_info or {},
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_server_restart_detection(
        self, detected_at: str | None = None, affected_sessions: int | None = None
    ) -> None:
        """
        Log detection of server restart that affects sessions.

        Args:
            detected_at: When the restart was detected
            affected_sessions: Estimated number of affected sessions
        """
        logger.warning(
            "Server restart detected - sessions may be lost",
            event="server_restart_detected",
            detected_at=detected_at or datetime.utcnow().isoformat(),
            affected_sessions=affected_sessions,
            impact="All in-memory agent runs will be lost",
            recommendation="Users will need to start new conversations",
        )


# Global instance for easy access
session_logger = SessionLifecycleLogger()


# Convenience functions for easy import and use
def log_session_start(
    session_id: str, agent_id: str, user_id: str | None = None, **kwargs
) -> None:
    """Convenience function to log session start."""
    session_logger.log_session_start(session_id, agent_id, user_id, kwargs)


def log_run_creation(run_id: str, session_id: str, agent_id: str, **kwargs) -> None:
    """Convenience function to log run creation."""
    session_logger.log_run_creation(run_id, session_id, agent_id, **kwargs)


def log_run_continuation_attempt(
    run_id: str, session_id: str, agent_id: str, **kwargs
) -> None:
    """Convenience function to log run continuation attempt."""
    session_logger.log_run_continuation_attempt(run_id, session_id, agent_id, **kwargs)


def log_run_continuation_success(
    run_id: str, session_id: str, agent_id: str, **kwargs
) -> None:
    """Convenience function to log run continuation success."""
    session_logger.log_run_continuation_success(run_id, session_id, agent_id, **kwargs)


def log_run_continuation_failure(
    run_id: str, session_id: str, agent_id: str, error: str, **kwargs
) -> None:
    """Convenience function to log run continuation failure."""
    session_logger.log_run_continuation_failure(
        run_id, session_id, agent_id, error, type(error).__name__, **kwargs
    )
