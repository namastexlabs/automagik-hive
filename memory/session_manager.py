"""
Session Management for PagBank Memory System
Agent C: Memory System Foundation
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionState:
    """Represents a user session state"""
    session_id: str
    user_id: str
    team_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    interaction_count: int
    session_context: Dict[str, Any]
    is_active: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'interaction_count': self.interaction_count,
            'session_context': self.session_context,
            'is_active': self.is_active,
            'metadata': self.metadata
        }


class SessionManager:
    """
    Manages user sessions for PagBank multi-agent system
    Handles session persistence, state tracking, and cleanup
    """
    
    def __init__(self, db_file: str = "tmp/pagbank_sessions.db", 
                 session_timeout_minutes: int = 120):
        self.db_file = Path(db_file)
        self.session_timeout_minutes = session_timeout_minutes
        self.active_sessions: Dict[str, SessionState] = {}
        
        # Create database directory if needed
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load active sessions
        self._load_active_sessions()
    
    def _init_database(self):
        """Initialize SQLite database for session persistence"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    team_id TEXT,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    interaction_count INTEGER DEFAULT 0,
                    session_context TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON sessions(user_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_active 
                ON sessions(is_active, last_activity)
            ''')
    
    def _load_active_sessions(self):
        """Load active sessions from database"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM sessions 
                WHERE is_active = 1 
                AND datetime(last_activity) > datetime('now', '-{} minutes')
            '''.format(self.session_timeout_minutes))
            
            for row in cursor.fetchall():
                session = SessionState(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    team_id=row['team_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']),
                    interaction_count=row['interaction_count'],
                    session_context=json.loads(row['session_context'] or '{}'),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata'] or '{}')
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
        
        # Check active sessions
        for session in self.active_sessions.values():
            if session.user_id == user_id:
                if not active_only or self._is_session_active(session):
                    sessions.append(session)
        
        # Load from database if needed
        if not active_only:
            db_sessions = self._load_user_sessions_from_db(user_id)
            session_ids = {s.session_id for s in sessions}
            
            for db_session in db_sessions:
                if db_session.session_id not in session_ids:
                    sessions.append(db_session)
        
        return sorted(sessions, key=lambda s: s.last_activity, reverse=True)
    
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
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=self.session_timeout_minutes)
        
        # Clean up active sessions
        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            if session.last_activity < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.deactivate_session(session_id)
            expired_count += 1
        
        # Clean up database
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                UPDATE sessions 
                SET is_active = 0 
                WHERE is_active = 1 
                AND datetime(last_activity) < datetime('now', '-{} minutes')
            '''.format(self.session_timeout_minutes))
            
            expired_count += cursor.rowcount
        
        return expired_count
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        stats = {
            'active_sessions': len(self.active_sessions),
            'total_sessions': 0,
            'users_with_sessions': set(),
            'teams_with_sessions': set(),
            'average_interactions_per_session': 0,
            'session_duration_stats': {'min': 0, 'max': 0, 'avg': 0}
        }
        
        # Count active sessions stats
        total_interactions = 0
        durations = []
        
        for session in self.active_sessions.values():
            stats['users_with_sessions'].add(session.user_id)
            if session.team_id:
                stats['teams_with_sessions'].add(session.team_id)
            
            total_interactions += session.interaction_count
            
            duration = (session.last_activity - session.created_at).total_seconds() / 60
            durations.append(duration)
        
        if self.active_sessions:
            stats['average_interactions_per_session'] = total_interactions / len(self.active_sessions)
        
        if durations:
            stats['session_duration_stats'] = {
                'min': min(durations),
                'max': max(durations),
                'avg': sum(durations) / len(durations)
            }
        
        # Get total from database
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM sessions')
            stats['total_sessions'] = cursor.fetchone()[0]
        
        stats['users_with_sessions'] = len(stats['users_with_sessions'])
        stats['teams_with_sessions'] = len(stats['teams_with_sessions'])
        
        return stats
    
    def _is_session_active(self, session: SessionState) -> bool:
        """Check if session is still active"""
        if not session.is_active:
            return False
        
        cutoff_time = datetime.now() - timedelta(minutes=self.session_timeout_minutes)
        return session.last_activity >= cutoff_time
    
    def _save_session(self, session: SessionState):
        """Save session to database"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, team_id, created_at, last_activity, 
                 interaction_count, session_context, is_active, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.user_id,
                session.team_id,
                session.created_at.isoformat(),
                session.last_activity.isoformat(),
                session.interaction_count,
                json.dumps(session.session_context),
                session.is_active,
                json.dumps(session.metadata)
            ))
    
    def _load_session_from_db(self, session_id: str) -> Optional[SessionState]:
        """Load session from database"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM sessions WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                return SessionState(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    team_id=row['team_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']),
                    interaction_count=row['interaction_count'],
                    session_context=json.loads(row['session_context'] or '{}'),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata'] or '{}')
                )
        return None
    
    def _load_user_sessions_from_db(self, user_id: str) -> List[SessionState]:
        """Load all sessions for a user from database"""
        sessions = []
        
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM sessions WHERE user_id = ?
                ORDER BY last_activity DESC
            ''', (user_id,))
            
            for row in cursor.fetchall():
                session = SessionState(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    team_id=row['team_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']),
                    interaction_count=row['interaction_count'],
                    session_context=json.loads(row['session_context'] or '{}'),
                    is_active=bool(row['is_active']),
                    metadata=json.loads(row['metadata'] or '{}')
                )
                sessions.append(session)
        
        return sessions
    
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


def create_session_manager(db_file: str = "tmp/pagbank_sessions.db",
                          session_timeout_minutes: int = 120) -> SessionManager:
    """Create and return a session manager instance"""
    return SessionManager(db_file, session_timeout_minutes)