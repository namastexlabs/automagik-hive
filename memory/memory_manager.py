"""
Memory Manager for PagBank Multi-Agent System
Agent C: Memory System Foundation
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude

from .memory_config import MemoryConfig, get_memory_config
from .pattern_detector import create_pattern_detector
from .session_manager import create_session_manager


class MemoryManager:
    """
    Main memory management system for PagBank multi-agent system
    Integrates memory persistence, pattern detection, and session management
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """Initialize memory manager with configuration"""
        self.config = config or get_memory_config()
        
        # Initialize components
        self.memory_db = SqliteMemoryDb(
            table_name=self.config.table_name,
            db_file=str(self.config.get_db_path())
        )
        
        self.memory = Memory(
            model=Claude(id=self.config.memory_model),
            db=self.memory_db,
            delete_memories=True,
            clear_memories=True
        )
        
        self.pattern_detector = create_pattern_detector(
            self.config.pattern_similarity_threshold
        )
        
        self.session_manager = create_session_manager(
            str(self.config.get_db_path().parent / "pagbank_sessions.db"),
            self.config.session_timeout_minutes
        )
        
        # Memory statistics
        self.interaction_count = 0
        self.last_cleanup = datetime.now()
    
    def process_interaction(self, user_id: str, message: str, 
                          team_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user interaction and update memory systems
        
        Args:
            user_id: User identifier
            message: User message
            team_id: Team handling the interaction
            session_id: Session identifier
            metadata: Additional metadata
            
        Returns:
            Dictionary with processing results
        """
        current_time = datetime.now()
        self.interaction_count += 1
        
        # Get or create session
        if session_id:
            session = self.session_manager.get_session(session_id)
        else:
            session = None
        
        if not session:
            session = self.session_manager.create_session(user_id, team_id)
        
        # Update session activity
        session_metadata = {
            'team_id': team_id,
            'message_length': len(message),
            'timestamp': current_time.isoformat()
        }
        
        if metadata:
            session_metadata.update(metadata)
        
        self.session_manager.update_session_activity(
            session.session_id, 
            session_metadata
        )
        
        # Detect patterns
        pattern_metadata = {
            'session_id': session.session_id,
            'team_id': team_id,
            'interaction_count': session.interaction_count
        }
        
        detected_patterns = self.pattern_detector.analyze_message(
            user_id, message, pattern_metadata
        )
        
        # Process with memory system
        memory_result = self._process_memory_interaction(
            user_id, message, session.session_id, detected_patterns
        )
        
        # Update pattern detection if needed
        if self.interaction_count % self.config.pattern_update_frequency == 0:
            self._update_pattern_insights(user_id)
        
        # Cleanup if needed
        if self.interaction_count % self.config.memory_cleanup_interval == 0:
            self._perform_cleanup()
        
        return {
            'session_id': session.session_id,
            'patterns_detected': len(detected_patterns),
            'memory_updated': memory_result['updated'],
            'insights': self._get_user_insights(user_id),
            'processing_time': (datetime.now() - current_time).total_seconds()
        }
    
    def _process_memory_interaction(self, user_id: str, message: str, 
                                   session_id: str, patterns: List) -> Dict[str, Any]:
        """Process interaction with memory system"""
        try:
            # Get existing memories
            existing_memories = self.memory.get_user_memories(user_id=user_id)
            
            # Create memory context from patterns
            pattern_context = {}
            for pattern in patterns:
                pattern_context[pattern.pattern_type] = pattern.pattern_value
            
            # Store interaction in memory (this will be handled by the agent)
            # For now, we'll track that memory should be updated
            
            return {
                'updated': True,
                'existing_memories': len(existing_memories) if existing_memories else 0,
                'pattern_context': pattern_context
            }
            
        except Exception as e:
            return {
                'updated': False,
                'error': str(e)
            }
    
    def _update_pattern_insights(self, user_id: str):
        """Update pattern insights for user"""
        insights = self.pattern_detector.get_pattern_insights(user_id)
        
        # Store insights in session context
        sessions = self.session_manager.get_user_sessions(user_id)
        if sessions:
            latest_session = sessions[0]
            self.session_manager.update_session_context(
                latest_session.session_id,
                {'pattern_insights': insights}
            )
    
    def _perform_cleanup(self):
        """Perform memory and session cleanup"""
        current_time = datetime.now()
        
        # Clean up expired sessions
        expired_sessions = self.session_manager.cleanup_expired_sessions()
        
        # Memory cleanup would be handled by the Memory object
        # For now, we'll just track the cleanup
        
        self.last_cleanup = current_time
        
        return {
            'expired_sessions': expired_sessions,
            'cleanup_time': current_time.isoformat()
        }
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context"""
        # Get user memories
        memories = self.memory.get_user_memories(user_id=user_id)
        
        # Get user patterns
        patterns = self.pattern_detector.get_user_patterns(user_id)
        pattern_insights = self.pattern_detector.get_pattern_insights(user_id)
        
        # Get user sessions
        sessions = self.session_manager.get_user_sessions(user_id)
        
        return {
            'user_id': user_id,
            'memories': {
                'count': len(memories) if memories else 0,
                'recent': [m.content for m in memories[:3]] if memories else []
            },
            'patterns': {
                'count': len(patterns),
                'top_patterns': [p.to_dict() for p in patterns[:5]],
                'insights': pattern_insights
            },
            'sessions': {
                'count': len(sessions),
                'active_sessions': len([s for s in sessions if s.is_active]),
                'latest_session': sessions[0].to_dict() if sessions else None
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get user insights for response"""
        patterns = self.pattern_detector.get_top_patterns(user_id, limit=5)
        
        insights = {
            'recent_patterns': [p.pattern_type for p in patterns[:3]],
            'interaction_style': 'unknown',
            'preferences': []
        }
        
        # Analyze interaction style
        complexity_patterns = [p for p in patterns if p.pattern_type == 'complexity_preference']
        if complexity_patterns:
            insights['interaction_style'] = complexity_patterns[0].pattern_value
        
        # Get preferences
        pref_patterns = [p for p in patterns if p.pattern_type in ['investment_preference', 'card_usage']]
        insights['preferences'] = [p.pattern_value for p in pref_patterns[:3]]
        
        return insights
    
    def create_memory_for_agent(self, user_id: str, session_id: Optional[str] = None) -> Memory:
        """Create a Memory object for an agent"""
        return self.memory
    
    def get_team_memory(self, team_name: str) -> Optional[Memory]:
        """Get or create team-specific memory"""
        # For now, return the shared memory instance
        # In a real implementation, this could create team-specific memory instances
        return self.memory
    
    def store_interaction(self, user_id: str, session_id: str, team_name: str, 
                         query: str, response: str) -> bool:
        """Store interaction in memory"""
        try:
            # Store in pattern detector
            self.pattern_detector.analyze_message(
                user_id, 
                query, 
                {"team": team_name, "session_id": session_id}
            )
            
            # Update session
            self.session_manager.update_session_activity(
                session_id,
                {"last_query": query, "last_response": response[:200]}
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error storing interaction: {e}")
            return False
    
    def get_user_patterns(self, user_id: str) -> List[Any]:
        """Get user patterns for context"""
        return self.pattern_detector.get_user_patterns(user_id)
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        pattern_stats = self.pattern_detector.get_pattern_statistics()
        session_stats = self.session_manager.get_session_statistics()
        
        return {
            'interaction_count': self.interaction_count,
            'last_cleanup': self.last_cleanup.isoformat(),
            'pattern_statistics': pattern_stats,
            'session_statistics': session_stats,
            'memory_config': self.config.to_dict()
        }
    
    def export_user_data(self, user_id: str) -> str:
        """Export all user data"""
        context = self.get_user_context(user_id)
        pattern_export = self.pattern_detector.export_patterns(user_id)
        session_export = self.session_manager.export_session_data(user_id)
        
        export_data = {
            'user_id': user_id,
            'export_time': datetime.now().isoformat(),
            'context': context,
            'patterns': json.loads(pattern_export),
            'sessions': json.loads(session_export)
        }
        
        return json.dumps(export_data, indent=2)
    
    def clear_user_data(self, user_id: str) -> bool:
        """Clear all user data"""
        try:
            # Clear memories
            self.memory.clear_user_memories(user_id=user_id)
            
            # Clear patterns
            self.pattern_detector.clear_user_patterns(user_id)
            
            # Deactivate sessions
            sessions = self.session_manager.get_user_sessions(user_id)
            for session in sessions:
                self.session_manager.deactivate_session(session.session_id)
            
            return True
            
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on memory system"""
        health = {
            'status': 'healthy',
            'issues': [],
            'components': {}
        }
        
        try:
            # Check memory database
            memories = self.memory.get_user_memories(user_id="health_check")
            health['components']['memory_db'] = 'healthy'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['issues'].append(f"Memory DB error: {e}")
            health['components']['memory_db'] = 'unhealthy'
        
        try:
            # Check pattern detector
            stats = self.pattern_detector.get_pattern_statistics()
            health['components']['pattern_detector'] = 'healthy'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['issues'].append(f"Pattern detector error: {e}")
            health['components']['pattern_detector'] = 'unhealthy'
        
        try:
            # Check session manager
            session_stats = self.session_manager.get_session_statistics()
            health['components']['session_manager'] = 'healthy'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['issues'].append(f"Session manager error: {e}")
            health['components']['session_manager'] = 'unhealthy'
        
        return health


def create_memory_manager(config: Optional[MemoryConfig] = None) -> MemoryManager:
    """Create and return a memory manager instance"""
    return MemoryManager(config)