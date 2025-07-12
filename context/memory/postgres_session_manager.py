"""
PostgreSQL-based Session Manager for PagBank Multi-Agent System
Replaces SQLite session management with PostgreSQL
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager

from .session_manager import SessionState


class PostgresSessionManager:
    """
    PostgreSQL-based session management for PagBank multi-agent system
    Handles session persistence, state tracking, and cleanup
    """
    
    def __init__(self, db_url: str, session_timeout_minutes: int = 120):
        self.db_url = db_url
        self.session_timeout_minutes = session_timeout_minutes
        self.active_sessions: Dict[str, SessionState] = {}
        
        # Verify connection
        self._verify_connection()
        
        # Load active sessions
        self._load_active_sessions()
    
    def _verify_connection(self):
        """Verify PostgreSQL connection"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _load_active_sessions(self):
        """Load active sessions from database"""
        cutoff_time = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM user_sessions 
                    WHERE is_active = TRUE 
                    AND last_activity > %s
                """, (cutoff_time,))
                
                for row in cursor.fetchall():
                    session = SessionState(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        team_id=row['team_id'],
                        created_at=row['created_at'],
                        last_activity=row['last_activity'],
                        interaction_count=row['interaction_count'],
                        session_context=row['session_context'],
                        is_active=row['is_active'],
                        metadata=row['metadata']
                    )
                    self.active_sessions[session.session_id] = session
    
    def create_session(self, user_id: str, team_id: Optional[str] = None,
                      initial_context: Optional[Dict[str, Any]] = None) -> SessionState:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            team_id=team_id,
            created_at=current_time,
            last_activity=current_time,
            interaction_count=0,
            session_context=initial_context or {},
            is_active=True,
            metadata={}
        )
        
        # Store in memory
        self.active_sessions[session_id] = session
        
        # Persist to database
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if self._is_session_active(session):
                return session
            else:
                # Session expired, deactivate
                self.deactivate_session(session_id)
                return None
        
        # Try to load from database
        session = self._load_session_from_db(session_id)
        if session and self._is_session_active(session):
            self.active_sessions[session_id] = session
            return session
        
        return None
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[SessionState]:
        """Get all sessions for a user"""
        sessions = []
        
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if active_only:
                    cutoff_time = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
                    cursor.execute("""
                        SELECT * FROM user_sessions 
                        WHERE user_id = %s 
                        AND is_active = TRUE
                        AND last_activity > %s
                        ORDER BY last_activity DESC
                    """, (user_id, cutoff_time))
                else:
                    cursor.execute("""
                        SELECT * FROM user_sessions 
                        WHERE user_id = %s 
                        ORDER BY last_activity DESC
                    """, (user_id,))
                
                for row in cursor.fetchall():
                    session = SessionState(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        team_id=row['team_id'],
                        created_at=row['created_at'],
                        last_activity=row['last_activity'],
                        interaction_count=row['interaction_count'],
                        session_context=row['session_context'],
                        is_active=row['is_active'],
                        metadata=row['metadata']
                    )
                    sessions.append(session)
        
        return sessions
    
    def update_session_activity(self, session_id: str, 
                              interaction_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update session activity"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.last_activity = datetime.now()
        session.interaction_count += 1
        
        if interaction_data:
            session.session_context.update(interaction_data)
        
        self._save_session(session)
        return True
    
    def update_session_context(self, session_id: str, 
                             context_updates: Dict[str, Any]) -> bool:
        """Update session context"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.session_context.update(context_updates)
        session.last_activity = datetime.now()
        
        self._save_session(session)
        return True
    
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.is_active = False
        session.last_activity = datetime.now()
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Update database
        self._save_session(session)
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        expired_count = 0
        cutoff_time = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE is_active = TRUE 
                    AND last_activity < %s
                    RETURNING session_id
                """, (cutoff_time,))
                
                expired_sessions = [row[0] for row in cursor.fetchall()]
                expired_count = len(expired_sessions)
                
                # Remove from active sessions
                for session_id in expired_sessions:
                    if session_id in self.active_sessions:
                        del self.active_sessions[session_id]
        
        return expired_count
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get overall statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COUNT(*) FILTER (WHERE is_active = TRUE) as active_sessions,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(DISTINCT team_id) as unique_teams,
                        AVG(interaction_count) as avg_interactions,
                        MIN(created_at) as earliest_session,
                        MAX(last_activity) as latest_activity
                    FROM user_sessions
                """)
                
                stats = cursor.fetchone()
                
                # Get session duration statistics for active sessions
                cursor.execute("""
                    SELECT 
                        AVG(EXTRACT(EPOCH FROM (last_activity - created_at)) / 60) as avg_duration_minutes,
                        MIN(EXTRACT(EPOCH FROM (last_activity - created_at)) / 60) as min_duration_minutes,
                        MAX(EXTRACT(EPOCH FROM (last_activity - created_at)) / 60) as max_duration_minutes
                    FROM user_sessions
                    WHERE is_active = TRUE
                """)
                
                duration_stats = cursor.fetchone()
                
                stats.update({
                    'active_in_memory': len(self.active_sessions),
                    'session_duration_stats': duration_stats
                })
                
                return stats
    
    def _is_session_active(self, session: SessionState) -> bool:
        """Check if session is still active"""
        if not session.is_active:
            return False
        
        cutoff_time = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        return session.last_activity >= cutoff_time
    
    def _save_session(self, session: SessionState):
        """Save session to database"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_sessions 
                    (session_id, user_id, team_id, created_at, last_activity, 
                     interaction_count, session_context, is_active, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) 
                    DO UPDATE SET
                        last_activity = EXCLUDED.last_activity,
                        interaction_count = EXCLUDED.interaction_count,
                        session_context = EXCLUDED.session_context,
                        is_active = EXCLUDED.is_active,
                        metadata = EXCLUDED.metadata
                """, (
                    session.session_id,
                    session.user_id,
                    session.team_id,
                    session.created_at,
                    session.last_activity,
                    session.interaction_count,
                    Json(session.session_context),
                    session.is_active,
                    Json(session.metadata)
                ))
    
    def _load_session_from_db(self, session_id: str) -> Optional[SessionState]:
        """Load session from database"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM user_sessions WHERE session_id = %s
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return SessionState(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        team_id=row['team_id'],
                        created_at=row['created_at'],
                        last_activity=row['last_activity'],
                        interaction_count=row['interaction_count'],
                        session_context=row['session_context'],
                        is_active=row['is_active'],
                        metadata=row['metadata']
                    )
        return None
    
    def export_session_data(self, user_id: str) -> str:
        """Export session data for a user"""
        sessions = self.get_user_sessions(user_id, active_only=False)
        
        export_data = {
            'user_id': user_id,
            'export_time': datetime.now().isoformat(),
            'sessions': [s.to_dict() for s in sessions],
            'statistics': {
                'total_sessions': len(sessions),
                'active_sessions': len([s for s in sessions if s.is_active]),
                'total_interactions': sum(s.interaction_count for s in sessions)
            }
        }
        
        return json.dumps(export_data, indent=2)


def create_postgres_session_manager(db_url: str,
                                  session_timeout_minutes: int = 120) -> PostgresSessionManager:
    """Create and return a PostgreSQL session manager instance"""
    return PostgresSessionManager(db_url, session_timeout_minutes)