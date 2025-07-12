"""
Test suite for Session Manager
Tests session lifecycle, timeout handling, and state management
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from context.memory.session_manager import SessionManager, create_session_manager


class TestSessionManager:
    """Test Session Manager functionality"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield str(Path(temp_dir) / "test_sessions.db")
    
    @pytest.fixture
    def session_manager(self, temp_db_path):
        """Create session manager instance"""
        return SessionManager(temp_db_path, timeout_minutes=30)
    
    def test_session_manager_initialization(self, session_manager, temp_db_path):
        """Test session manager initialization"""
        assert session_manager.db_path == temp_db_path
        assert session_manager.timeout_minutes == 30
        
        # Verify database and table creation
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        table_exists = cursor.fetchone() is not None
        conn.close()
        assert table_exists
    
    def test_create_session(self, session_manager):
        """Test creating new session"""
        user_id = "test_user_001"
        initial_context = {"customer_type": "premium", "language": "pt-BR"}
        
        session = session_manager.create_session(user_id, initial_context)
        
        assert session is not None
        assert session["user_id"] == user_id
        assert session["context"] == initial_context
        assert session["status"] == "active"
        assert session["created_at"] is not None
        assert session["last_activity"] is not None
        assert session["interaction_count"] == 0
    
    def test_get_session(self, session_manager):
        """Test retrieving session"""
        user_id = "test_user_002"
        context = {"test": "data"}
        
        # Create session first
        created_session = session_manager.create_session(user_id, context)
        session_id = created_session["session_id"]
        
        # Retrieve session
        retrieved_session = session_manager.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session["session_id"] == session_id
        assert retrieved_session["user_id"] == user_id
        assert retrieved_session["context"] == context
    
    def test_update_session(self, session_manager):
        """Test updating session data"""
        user_id = "test_user_003"
        session = session_manager.create_session(user_id, {})
        session_id = session["session_id"]
        
        # Update context and interaction count
        new_context = {"team_history": ["cartoes", "seguros"], "awaiting_human": False}
        updated_session = session_manager.update_session(
            session_id,
            context=new_context,
            interaction_count=5
        )
        
        assert updated_session is not None
        assert updated_session["context"] == new_context
        assert updated_session["interaction_count"] == 5
        assert updated_session["last_activity"] > session["last_activity"]
    
    def test_session_timeout_detection(self, session_manager):
        """Test session timeout detection"""
        user_id = "test_user_004"
        session = session_manager.create_session(user_id, {})
        session_id = session["session_id"]
        
        # Manually set old timestamp to simulate timeout
        conn = sqlite3.connect(session_manager.db_path)
        cursor = conn.cursor()
        old_timestamp = (datetime.now() - timedelta(hours=2)).isoformat()
        cursor.execute(
            "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
            (old_timestamp, session_id)
        )
        conn.commit()
        conn.close()
        
        # Check if session is timed out
        is_timed_out = session_manager.is_session_timed_out(session_id)
        assert is_timed_out is True
        
        # Check active session
        fresh_session = session_manager.create_session("fresh_user", {})
        is_fresh_timed_out = session_manager.is_session_timed_out(fresh_session["session_id"])
        assert is_fresh_timed_out is False
    
    def test_close_session(self, session_manager):
        """Test closing session"""
        user_id = "test_user_005"
        session = session_manager.create_session(user_id, {})
        session_id = session["session_id"]
        
        # Close session
        closed_session = session_manager.close_session(session_id, "completed")
        
        assert closed_session is not None
        assert closed_session["status"] == "completed"
        assert closed_session["ended_at"] is not None
    
    def test_get_user_sessions(self, session_manager):
        """Test retrieving all sessions for a user"""
        user_id = "test_user_006"
        
        # Create multiple sessions
        session1 = session_manager.create_session(user_id, {"session": 1})
        session2 = session_manager.create_session(user_id, {"session": 2})
        session_manager.close_session(session1["session_id"], "completed")
        
        # Get all user sessions
        user_sessions = session_manager.get_user_sessions(user_id)
        
        assert len(user_sessions) >= 2
        user_session_ids = [s["session_id"] for s in user_sessions]
        assert session1["session_id"] in user_session_ids
        assert session2["session_id"] in user_session_ids
    
    def test_get_active_sessions(self, session_manager):
        """Test retrieving active sessions"""
        # Create mix of active and closed sessions
        user1 = "active_user_1"
        user2 = "active_user_2"
        user3 = "closed_user"
        
        active_session1 = session_manager.create_session(user1, {})
        active_session2 = session_manager.create_session(user2, {})
        closed_session = session_manager.create_session(user3, {})
        
        session_manager.close_session(closed_session["session_id"], "timeout")
        
        # Get active sessions
        active_sessions = session_manager.get_active_sessions()
        
        assert len(active_sessions) >= 2
        active_ids = [s["session_id"] for s in active_sessions]
        assert active_session1["session_id"] in active_ids
        assert active_session2["session_id"] in active_ids
        assert closed_session["session_id"] not in active_ids
    
    def test_cleanup_old_sessions(self, session_manager):
        """Test cleaning up old sessions"""
        user_id = "cleanup_user"
        
        # Create session and make it old
        session = session_manager.create_session(user_id, {})
        session_id = session["session_id"]
        
        # Manually set old timestamp
        conn = sqlite3.connect(session_manager.db_path)
        cursor = conn.cursor()
        old_timestamp = (datetime.now() - timedelta(days=8)).isoformat()
        cursor.execute(
            "UPDATE sessions SET created_at = ?, last_activity = ? WHERE session_id = ?",
            (old_timestamp, old_timestamp, session_id)
        )
        conn.commit()
        conn.close()
        
        # Clean up sessions older than 7 days
        cleaned_count = session_manager.cleanup_old_sessions(days_old=7)
        
        assert cleaned_count >= 1
        
        # Verify session was removed
        retrieved_session = session_manager.get_session(session_id)
        assert retrieved_session is None
    
    def test_session_statistics(self, session_manager):
        """Test session statistics"""
        # Create various sessions
        users = ["stats_user_1", "stats_user_2", "stats_user_3"]
        
        for user in users:
            session = session_manager.create_session(user, {})
            # Update with different interaction counts
            session_manager.update_session(
                session["session_id"],
                interaction_count=len(user)  # Different counts per user
            )
        
        # Close one session
        user_sessions = session_manager.get_user_sessions(users[0])
        session_manager.close_session(user_sessions[0]["session_id"], "completed")
        
        # Get statistics
        stats = session_manager.get_session_statistics()
        
        assert stats is not None
        assert stats["total_sessions"] >= 3
        assert stats["active_sessions"] >= 2
        assert stats["completed_sessions"] >= 1
        assert "average_interactions"] >= 0
        assert "average_duration_minutes" in stats
    
    def test_session_context_updates(self, session_manager):
        """Test incremental context updates"""
        user_id = "context_user"
        session = session_manager.create_session(user_id, {"initial": "data"})
        session_id = session["session_id"]
        
        # First update
        session_manager.update_session(
            session_id,
            context={"initial": "data", "team": "cartoes", "query_count": 1}
        )
        
        # Second update - should preserve previous data
        session_manager.update_session(
            session_id,
            context={"initial": "data", "team": "cartoes", "query_count": 2, "last_query": "limite"}
        )
        
        # Verify final state
        final_session = session_manager.get_session(session_id)
        context = final_session["context"]
        
        assert context["initial"] == "data"
        assert context["team"] == "cartoes"
        assert context["query_count"] == 2
        assert context["last_query"] == "limite"
    
    def test_concurrent_session_access(self, session_manager):
        """Test concurrent access to sessions"""
        user_id = "concurrent_user"
        session = session_manager.create_session(user_id, {})
        session_id = session["session_id"]
        
        # Simulate concurrent updates
        session_manager.update_session(session_id, interaction_count=1)
        session_manager.update_session(session_id, context={"concurrent": "update"})
        
        # Verify both updates are reflected
        final_session = session_manager.get_session(session_id)
        
        assert final_session["interaction_count"] == 1
        assert final_session["context"]["concurrent"] == "update"
    
    def test_invalid_session_operations(self, session_manager):
        """Test handling of invalid session operations"""
        # Test getting non-existent session
        non_existent_session = session_manager.get_session("non_existent_id")
        assert non_existent_session is None
        
        # Test updating non-existent session
        updated_session = session_manager.update_session("non_existent_id", interaction_count=5)
        assert updated_session is None
        
        # Test closing non-existent session
        closed_session = session_manager.close_session("non_existent_id", "completed")
        assert closed_session is None
    
    def test_session_status_transitions(self, session_manager):
        """Test valid session status transitions"""
        user_id = "status_user"
        session = session_manager.create_session(user_id, {})
        session_id = session["session_id"]
        
        # Valid transitions
        valid_statuses = ["active", "paused", "completed", "timeout", "error"]
        
        for status in valid_statuses:
            updated_session = session_manager.update_session(session_id, status=status)
            assert updated_session["status"] == status
    
    def test_session_data_persistence(self, temp_db_path):
        """Test session data persistence across manager instances"""
        user_id = "persistent_user"
        context = {"persistent": "data"}
        
        # Create session with first manager
        manager1 = SessionManager(temp_db_path, timeout_minutes=30)
        session = manager1.create_session(user_id, context)
        session_id = session["session_id"]
        
        # Access with second manager
        manager2 = SessionManager(temp_db_path, timeout_minutes=30)
        retrieved_session = manager2.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session["user_id"] == user_id
        assert retrieved_session["context"] == context


class TestSessionManagerCreation:
    """Test session manager creation utilities"""
    
    def test_create_session_manager_default(self):
        """Test creating session manager with defaults"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.db")
            manager = create_session_manager(db_path)
            assert manager is not None
            assert isinstance(manager, SessionManager)
            assert manager.timeout_minutes == 30
    
    def test_create_session_manager_custom_timeout(self):
        """Test creating session manager with custom timeout"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "test.db")
            manager = create_session_manager(db_path, timeout_minutes=60)
            assert manager.timeout_minutes == 60


if __name__ == '__main__':
    pytest.main([__file__, '-v'])