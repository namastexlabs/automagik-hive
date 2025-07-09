"""
Test suite for Memory Manager
Comprehensive tests for PagBank memory system
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from memory.memory_config import MemoryConfig
from memory.memory_manager import MemoryManager, create_memory_manager


class TestMemoryManager:
    """Test Memory Manager functionality"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test_memory.db"
    
    @pytest.fixture
    def memory_config(self, temp_db_path):
        """Create test memory configuration"""
        return MemoryConfig(
            db_path=temp_db_path,
            table_name="test_memories",
            memory_model="claude-3-5-haiku-20241022",
            session_timeout_minutes=30,
            max_memories=1000,
            pattern_similarity_threshold=0.8
        )
    
    @pytest.fixture
    def memory_manager(self, memory_config):
        """Create memory manager instance"""
        return MemoryManager(memory_config)
    
    def test_memory_manager_initialization(self, memory_manager, memory_config):
        """Test memory manager initialization"""
        assert memory_manager.config == memory_config
        assert memory_manager.memory_db is not None
        assert memory_manager.memory is not None
        assert memory_manager.pattern_detector is not None
        assert memory_manager.session_manager is not None
    
    def test_store_interaction(self, memory_manager):
        """Test storing user interactions"""
        interaction_data = {
            "user_id": "test_user_001",
            "session_id": "test_session_001", 
            "team": "cartoes",
            "query": "Como aumentar o limite do cartão?",
            "response": "Para aumentar o limite, você pode solicitar análise.",
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store interaction
        success = memory_manager.store_interaction(interaction_data)
        assert success is True
        
        # Verify memory count increased
        memories = memory_manager.memory_db.read()
        assert len(memories) > 0
    
    def test_get_user_context(self, memory_manager):
        """Test retrieving user context"""
        user_id = "test_user_002"
        
        # Store some interactions first
        interactions = [
            {
                "user_id": user_id,
                "session_id": "session_001",
                "team": "cartoes",
                "query": "Qual a anuidade?",
                "response": "Cartão sem anuidade",
                "timestamp": datetime.now().isoformat()
            },
            {
                "user_id": user_id,
                "session_id": "session_002", 
                "team": "investimentos",
                "query": "CDB rende quanto?",
                "response": "CDB rende 105% do CDI",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        for interaction in interactions:
            memory_manager.store_interaction(interaction)
        
        # Get user context
        context = memory_manager.get_user_context(user_id)
        
        assert context is not None
        assert context["user_id"] == user_id
        assert context["total_interactions"] >= 2
        assert "teams_used" in context
        assert "cartoes" in context["teams_used"]
        assert "investimentos" in context["teams_used"]
    
    def test_get_user_patterns(self, memory_manager):
        """Test detecting user patterns"""
        user_id = "test_user_003"
        
        # Create pattern data - user asking about cards multiple times
        for i in range(5):
            interaction = {
                "user_id": user_id,
                "session_id": f"session_{i}",
                "team": "cartoes",
                "query": f"Pergunta sobre cartão {i}",
                "response": "Resposta sobre cartão",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat()
            }
            memory_manager.store_interaction(interaction)
        
        # Get patterns
        patterns = memory_manager.get_user_patterns(user_id)
        
        assert patterns is not None
        assert len(patterns) > 0
        
        # Should detect frequent team usage
        card_pattern = next((p for p in patterns if p["type"] == "frequent_team"), None)
        assert card_pattern is not None
        assert card_pattern["team"] == "cartoes"
        assert card_pattern["frequency"] >= 5
    
    def test_get_team_memory(self, memory_manager):
        """Test retrieving team-specific memory"""
        team = "investimentos"
        
        # Store interactions for different teams
        teams_data = {
            "investimentos": ["CDB rendimento", "Tesouro direto", "Fundos"],
            "cartoes": ["Limite cartão", "Anuidade", "Fatura"],
            "seguros": ["Seguro vida", "Seguro casa"]
        }
        
        for team_name, queries in teams_data.items():
            for query in queries:
                interaction = {
                    "user_id": f"user_{team_name}",
                    "session_id": f"session_{team_name}",
                    "team": team_name,
                    "query": query,
                    "response": f"Resposta para {query}",
                    "timestamp": datetime.now().isoformat()
                }
                memory_manager.store_interaction(interaction)
        
        # Get team memory
        team_memory = memory_manager.get_team_memory(team)
        
        assert team_memory is not None
        assert team_memory["team"] == team
        assert team_memory["interaction_count"] >= 3
        assert "common_queries" in team_memory
    
    def test_clear_old_memories(self, memory_manager):
        """Test clearing old memories"""
        user_id = "test_user_004"
        
        # Store old and new memories
        old_interaction = {
            "user_id": user_id,
            "session_id": "old_session",
            "team": "cartoes", 
            "query": "Pergunta antiga",
            "response": "Resposta antiga",
            "timestamp": (datetime.now() - timedelta(days=60)).isoformat()
        }
        
        new_interaction = {
            "user_id": user_id,
            "session_id": "new_session",
            "team": "cartoes",
            "query": "Pergunta nova", 
            "response": "Resposta nova",
            "timestamp": datetime.now().isoformat()
        }
        
        memory_manager.store_interaction(old_interaction)
        memory_manager.store_interaction(new_interaction)
        
        # Clear old memories (older than 30 days)
        cleared_count = memory_manager.clear_old_memories(days_old=30)
        
        assert cleared_count >= 1
        
        # Verify new memory still exists
        context = memory_manager.get_user_context(user_id)
        assert context["total_interactions"] >= 1
    
    def test_get_memory_statistics(self, memory_manager):
        """Test memory statistics"""
        # Store some test data
        for i in range(10):
            interaction = {
                "user_id": f"user_{i % 3}",  # 3 different users
                "session_id": f"session_{i}",
                "team": ["cartoes", "investimentos", "seguros"][i % 3],
                "query": f"Query {i}",
                "response": f"Response {i}",
                "timestamp": datetime.now().isoformat()
            }
            memory_manager.store_interaction(interaction)
        
        # Get statistics
        stats = memory_manager.get_memory_statistics()
        
        assert stats is not None
        assert stats["total_memories"] >= 10
        assert stats["unique_users"] >= 3
        assert stats["teams_usage"] is not None
        assert len(stats["teams_usage"]) >= 3
    
    def test_find_similar_interactions(self, memory_manager):
        """Test finding similar interactions"""
        # Store some interactions
        queries = [
            "Como aumentar limite do cartão?",
            "Quero aumentar meu limite",
            "Processo para aumentar limite cartão",
            "Como fazer PIX?",
            "PIX não funciona"
        ]
        
        for i, query in enumerate(queries):
            interaction = {
                "user_id": f"user_{i}",
                "session_id": f"session_{i}",
                "team": "cartoes" if "cartão" in query else "conta_digital",
                "query": query,
                "response": "Resposta relevante",
                "timestamp": datetime.now().isoformat()
            }
            memory_manager.store_interaction(interaction)
        
        # Find similar to limit increase queries
        similar = memory_manager.find_similar_interactions(
            "Aumentar limite cartão",
            limit=3
        )
        
        assert len(similar) > 0
        # Should find limit-related queries
        limit_queries = [s for s in similar if "limite" in s["query"].lower()]
        assert len(limit_queries) >= 2
    
    def test_memory_cleanup_by_user(self, memory_manager):
        """Test cleaning up memories for specific user"""
        user_id = "test_user_cleanup"
        other_user = "other_user"
        
        # Store memories for both users
        for user in [user_id, other_user]:
            for i in range(3):
                interaction = {
                    "user_id": user,
                    "session_id": f"session_{user}_{i}",
                    "team": "cartoes",
                    "query": f"Query from {user}",
                    "response": "Response",
                    "timestamp": datetime.now().isoformat()
                }
                memory_manager.store_interaction(interaction)
        
        # Clear memories for one user
        cleared = memory_manager.clear_user_memories(user_id)
        assert cleared >= 3
        
        # Verify other user's memories are intact
        other_context = memory_manager.get_user_context(other_user)
        assert other_context["total_interactions"] >= 3
        
        # Verify target user's memories are cleared
        user_context = memory_manager.get_user_context(user_id)
        assert user_context["total_interactions"] == 0
    
    def test_memory_persistence(self, memory_config):
        """Test memory persistence across manager instances"""
        # Create first manager and store data
        manager1 = MemoryManager(memory_config)
        interaction = {
            "user_id": "persistent_user",
            "session_id": "persistent_session",
            "team": "cartoes",
            "query": "Persistent query",
            "response": "Persistent response",
            "timestamp": datetime.now().isoformat()
        }
        manager1.store_interaction(interaction)
        
        # Create second manager with same config
        manager2 = MemoryManager(memory_config)
        
        # Verify data persists
        context = manager2.get_user_context("persistent_user")
        assert context["total_interactions"] >= 1
    
    def test_error_handling(self, memory_manager):
        """Test error handling in memory operations"""
        # Test invalid interaction data
        invalid_interaction = {
            "invalid_field": "invalid_value"
        }
        
        result = memory_manager.store_interaction(invalid_interaction)
        assert result is False or result is None
        
        # Test non-existent user context
        context = memory_manager.get_user_context("non_existent_user")
        assert context is not None
        assert context["total_interactions"] == 0
    
    def test_session_integration(self, memory_manager):
        """Test integration with session manager"""
        user_id = "session_test_user"
        session_id = "session_test_001"
        
        # Store interaction
        interaction = {
            "user_id": user_id,
            "session_id": session_id,
            "team": "cartoes",
            "query": "Session test query",
            "response": "Session test response",
            "timestamp": datetime.now().isoformat()
        }
        memory_manager.store_interaction(interaction)
        
        # Verify session was created/updated
        session = memory_manager.session_manager.get_session(session_id)
        assert session is not None
        assert session["user_id"] == user_id
    
    def test_pattern_detection_integration(self, memory_manager):
        """Test integration with pattern detector"""
        user_id = "pattern_test_user"
        
        # Create repeated pattern
        for i in range(5):
            interaction = {
                "user_id": user_id,
                "session_id": f"pattern_session_{i}",
                "team": "cartoes",
                "query": f"Problema com cartão {i}",
                "response": "Resolvido",
                "timestamp": datetime.now().isoformat()
            }
            memory_manager.store_interaction(interaction)
        
        # Get patterns
        patterns = memory_manager.get_user_patterns(user_id)
        
        # Should detect repetitive issue pattern
        issue_pattern = next(
            (p for p in patterns if p["type"] == "repetitive_issue"), 
            None
        )
        assert issue_pattern is not None


class TestMemoryManagerCreation:
    """Test memory manager creation utilities"""
    
    def test_create_memory_manager_default(self):
        """Test creating memory manager with defaults"""
        with patch('memory.memory_manager.get_memory_config') as mock_config:
            mock_config.return_value = Mock()
            manager = create_memory_manager()
            assert manager is not None
            assert isinstance(manager, MemoryManager)
    
    def test_create_memory_manager_custom_config(self):
        """Test creating memory manager with custom config"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = MemoryConfig(
                db_path=Path(temp_dir) / "custom.db",
                table_name="custom_memories"
            )
            manager = create_memory_manager(config)
            assert manager is not None
            assert manager.config.table_name == "custom_memories"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])