"""
Test suite for Pattern Detector
Tests pattern recognition, analysis, and insights
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from memory.pattern_detector import PatternDetector, create_pattern_detector


class TestPatternDetector:
    """Test Pattern Detector functionality"""
    
    @pytest.fixture
    def pattern_detector(self):
        """Create pattern detector instance"""
        return PatternDetector(similarity_threshold=0.8)
    
    @pytest.fixture
    def sample_interactions(self):
        """Create sample interaction data"""
        return [
            {
                "user_id": "user_001",
                "team": "cartoes",
                "query": "Como aumentar limite do cartão?",
                "timestamp": datetime.now().isoformat(),
                "session_id": "session_001"
            },
            {
                "user_id": "user_001", 
                "team": "cartoes",
                "query": "Quero aumentar meu limite",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "session_id": "session_002"
            },
            {
                "user_id": "user_001",
                "team": "cartoes", 
                "query": "Processo para aumentar limite",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "session_id": "session_003"
            },
            {
                "user_id": "user_002",
                "team": "investimentos",
                "query": "CDB rendimento hoje",
                "timestamp": datetime.now().isoformat(),
                "session_id": "session_004"
            },
            {
                "user_id": "user_002",
                "team": "investimentos",
                "query": "Quanto rende CDB?",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "session_id": "session_005"
            }
        ]
    
    def test_pattern_detector_initialization(self, pattern_detector):
        """Test pattern detector initialization"""
        assert pattern_detector.similarity_threshold == 0.8
        assert pattern_detector.embedder is not None
        assert hasattr(pattern_detector, 'pattern_cache')
    
    def test_detect_frequent_team_pattern(self, pattern_detector, sample_interactions):
        """Test detecting frequent team usage patterns"""
        patterns = pattern_detector.detect_patterns(sample_interactions)
        
        # Should detect frequent cards team usage by user_001
        frequent_patterns = [p for p in patterns if p["type"] == "frequent_team"]
        assert len(frequent_patterns) > 0
        
        cards_pattern = next(
            (p for p in frequent_patterns if p["team"] == "cartoes" and p["user_id"] == "user_001"),
            None
        )
        assert cards_pattern is not None
        assert cards_pattern["frequency"] >= 3
        assert cards_pattern["confidence"] > 0.7
    
    def test_detect_repetitive_query_pattern(self, pattern_detector, sample_interactions):
        """Test detecting repetitive query patterns"""
        patterns = pattern_detector.detect_patterns(sample_interactions)
        
        # Should detect repetitive queries about card limits
        repetitive_patterns = [p for p in patterns if p["type"] == "repetitive_query"]
        assert len(repetitive_patterns) > 0
        
        limit_pattern = next(
            (p for p in repetitive_patterns if "limite" in p["query_theme"].lower()),
            None
        )
        assert limit_pattern is not None
        assert limit_pattern["occurrences"] >= 2
    
    def test_detect_session_switching_pattern(self, pattern_detector):
        """Test detecting session switching patterns"""
        switching_interactions = [
            {
                "user_id": "switcher_user",
                "team": "cartoes",
                "query": "Pergunta sobre cartão",
                "timestamp": datetime.now().isoformat(),
                "session_id": "session_1"
            },
            {
                "user_id": "switcher_user",
                "team": "seguros",
                "query": "Pergunta sobre seguro",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "session_id": "session_2"
            },
            {
                "user_id": "switcher_user", 
                "team": "investimentos",
                "query": "Pergunta sobre CDB",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "session_id": "session_3"
            }
        ]
        
        patterns = pattern_detector.detect_patterns(switching_interactions)
        
        # Should detect frequent session switching
        switching_patterns = [p for p in patterns if p["type"] == "frequent_session_switching"]
        assert len(switching_patterns) > 0
        
        switch_pattern = switching_patterns[0]
        assert switch_pattern["user_id"] == "switcher_user"
        assert switch_pattern["session_count"] >= 3
    
    def test_detect_escalation_pattern(self, pattern_detector):
        """Test detecting escalation patterns"""
        escalation_interactions = [
            {
                "user_id": "frustrated_user",
                "team": "cartoes",
                "query": "Problema com cartão",
                "response_confidence": 0.9,
                "escalated": False,
                "timestamp": datetime.now().isoformat(),
                "session_id": "session_1"
            },
            {
                "user_id": "frustrated_user",
                "team": "cartoes", 
                "query": "Mesmo problema ainda não resolvido",
                "response_confidence": 0.7,
                "escalated": False,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "session_id": "session_1"
            },
            {
                "user_id": "frustrated_user",
                "team": "technical_escalation",
                "query": "QUERO FALAR COM HUMANO!",
                "response_confidence": 0.5,
                "escalated": True,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "session_id": "session_1"
            }
        ]
        
        patterns = pattern_detector.detect_patterns(escalation_interactions)
        
        # Should detect escalation pattern
        escalation_patterns = [p for p in patterns if p["type"] == "escalation_pattern"]
        assert len(escalation_patterns) > 0
        
        escalation_pattern = escalation_patterns[0]
        assert escalation_pattern["user_id"] == "frustrated_user"
        assert escalation_pattern["escalation_triggers"] >= 1
    
    def test_calculate_query_similarity(self, pattern_detector):
        """Test query similarity calculation"""
        query1 = "Como aumentar limite do cartão?"
        query2 = "Quero aumentar meu limite"
        query3 = "Como fazer PIX?"
        
        # Similar queries should have high similarity
        similarity_1_2 = pattern_detector.calculate_query_similarity(query1, query2)
        assert similarity_1_2 > 0.7
        
        # Different queries should have low similarity
        similarity_1_3 = pattern_detector.calculate_query_similarity(query1, query3)
        assert similarity_1_3 < 0.5
    
    def test_group_similar_queries(self, pattern_detector):
        """Test grouping similar queries"""
        queries = [
            "Como aumentar limite cartão?",
            "Quero aumentar limite",
            "Processo aumentar limite",
            "Como fazer PIX?",
            "PIX não funciona",
            "Fazer transferência PIX"
        ]
        
        groups = pattern_detector.group_similar_queries(queries)
        
        assert len(groups) >= 2  # Should have at least 2 groups
        
        # Find limit group
        limit_group = next(
            (g for g in groups if any("limite" in q.lower() for q in g)),
            None
        )
        assert limit_group is not None
        assert len(limit_group) >= 3
        
        # Find PIX group
        pix_group = next(
            (g for g in groups if any("pix" in q.lower() for q in g)),
            None
        )
        assert pix_group is not None
        assert len(pix_group) >= 2
    
    def test_analyze_temporal_patterns(self, pattern_detector):
        """Test temporal pattern analysis"""
        # Create interactions with different time patterns
        interactions = []
        base_time = datetime.now()
        
        # Peak hours pattern (9 AM - 5 PM)
        peak_hours = [9, 10, 11, 14, 15, 16]
        for hour in peak_hours:
            interactions.append({
                "user_id": f"user_{hour}",
                "team": "cartoes",
                "query": f"Query at {hour}",
                "timestamp": base_time.replace(hour=hour).isoformat(),
                "session_id": f"session_{hour}"
            })
        
        # Off-peak hours
        off_peak_hours = [2, 3, 22, 23]
        for hour in off_peak_hours:
            interactions.append({
                "user_id": f"user_{hour}",
                "team": "cartoes",
                "query": f"Query at {hour}",
                "timestamp": base_time.replace(hour=hour).isoformat(),
                "session_id": f"session_{hour}"
            })
        
        temporal_patterns = pattern_detector.analyze_temporal_patterns(interactions)
        
        assert "peak_hours" in temporal_patterns
        assert "hourly_distribution" in temporal_patterns
        assert len(temporal_patterns["peak_hours"]) > 0
    
    def test_detect_user_journey_patterns(self, pattern_detector):
        """Test user journey pattern detection"""
        # Create journey interactions
        journey_interactions = [
            {
                "user_id": "journey_user",
                "team": "conta_digital",
                "query": "Como abrir conta?",
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "session_id": "session_1"
            },
            {
                "user_id": "journey_user",
                "team": "cartoes",
                "query": "Como solicitar cartão?",
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "session_id": "session_2"
            },
            {
                "user_id": "journey_user",
                "team": "investimentos",
                "query": "Quero investir em CDB",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "session_id": "session_3"
            }
        ]
        
        patterns = pattern_detector.detect_patterns(journey_interactions)
        
        # Should detect user journey progression
        journey_patterns = [p for p in patterns if p["type"] == "user_journey"]
        assert len(journey_patterns) > 0
        
        journey_pattern = journey_patterns[0]
        assert journey_pattern["user_id"] == "journey_user"
        assert len(journey_pattern["journey_stages"]) >= 3
        assert "progression_type" in journey_pattern
    
    def test_pattern_confidence_scoring(self, pattern_detector, sample_interactions):
        """Test pattern confidence scoring"""
        patterns = pattern_detector.detect_patterns(sample_interactions)
        
        for pattern in patterns:
            assert "confidence" in pattern
            assert 0.0 <= pattern["confidence"] <= 1.0
            
            # Patterns with more evidence should have higher confidence
            if pattern["type"] == "frequent_team" and pattern.get("frequency", 0) > 3:
                assert pattern["confidence"] > 0.7
    
    def test_pattern_cache_functionality(self, pattern_detector, sample_interactions):
        """Test pattern caching functionality"""
        # First call should compute patterns
        patterns1 = pattern_detector.detect_patterns(sample_interactions)
        
        # Second call with same data should use cache
        patterns2 = pattern_detector.detect_patterns(sample_interactions)
        
        assert patterns1 == patterns2
        
        # Cache should be used for identical input
        assert len(pattern_detector.pattern_cache) > 0
    
    def test_clear_pattern_cache(self, pattern_detector, sample_interactions):
        """Test clearing pattern cache"""
        # Generate patterns to populate cache
        pattern_detector.detect_patterns(sample_interactions)
        assert len(pattern_detector.pattern_cache) > 0
        
        # Clear cache
        pattern_detector.clear_cache()
        assert len(pattern_detector.pattern_cache) == 0
    
    def test_get_pattern_insights(self, pattern_detector, sample_interactions):
        """Test generating pattern insights"""
        patterns = pattern_detector.detect_patterns(sample_interactions)
        insights = pattern_detector.get_pattern_insights(patterns)
        
        assert insights is not None
        assert "summary" in insights
        assert "recommendations" in insights
        assert "pattern_count" in insights
        assert insights["pattern_count"] == len(patterns)
    
    def test_filter_patterns_by_confidence(self, pattern_detector, sample_interactions):
        """Test filtering patterns by confidence threshold"""
        all_patterns = pattern_detector.detect_patterns(sample_interactions)
        
        high_confidence_patterns = pattern_detector.filter_patterns_by_confidence(
            all_patterns, 
            min_confidence=0.8
        )
        
        # All returned patterns should meet threshold
        for pattern in high_confidence_patterns:
            assert pattern["confidence"] >= 0.8
        
        # Should be subset of all patterns
        assert len(high_confidence_patterns) <= len(all_patterns)
    
    def test_pattern_trend_analysis(self, pattern_detector):
        """Test analyzing pattern trends over time"""
        # Create time-series interactions
        interactions_timeline = []
        base_date = datetime.now() - timedelta(days=30)
        
        for day in range(30):
            date = base_date + timedelta(days=day)
            # Increasing frequency pattern
            for i in range(day // 10 + 1):
                interactions_timeline.append({
                    "user_id": f"trend_user_{i}",
                    "team": "cartoes",
                    "query": "Problema com cartão",
                    "timestamp": date.isoformat(),
                    "session_id": f"session_{day}_{i}"
                })
        
        trend_analysis = pattern_detector.analyze_pattern_trends(interactions_timeline)
        
        assert "trend_direction" in trend_analysis
        assert "growth_rate" in trend_analysis
        assert "trend_confidence" in trend_analysis
    
    def test_error_handling(self, pattern_detector):
        """Test error handling in pattern detection"""
        # Test with empty data
        empty_patterns = pattern_detector.detect_patterns([])
        assert empty_patterns == []
        
        # Test with malformed data
        malformed_data = [
            {"invalid": "data"},
            {"user_id": "user", "missing_fields": True}
        ]
        
        try:
            patterns = pattern_detector.detect_patterns(malformed_data)
            # Should either return empty list or handle gracefully
            assert isinstance(patterns, list)
        except Exception:
            # Exception handling is also acceptable
            pass


class TestPatternDetectorCreation:
    """Test pattern detector creation utilities"""
    
    def test_create_pattern_detector_default(self):
        """Test creating pattern detector with defaults"""
        detector = create_pattern_detector()
        assert detector is not None
        assert isinstance(detector, PatternDetector)
        assert detector.similarity_threshold == 0.8
    
    def test_create_pattern_detector_custom_threshold(self):
        """Test creating pattern detector with custom threshold"""
        detector = create_pattern_detector(similarity_threshold=0.9)
        assert detector.similarity_threshold == 0.9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])