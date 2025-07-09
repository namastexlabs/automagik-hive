"""
Pattern Learning System for Escalations
Learns from escalation patterns to improve decision making
"""

import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .escalation_types import EscalationTrigger


@dataclass
class EscalationPattern:
    """Represents a learned escalation pattern"""
    pattern_id: str
    pattern_type: str  # trigger combination, time-based, keyword-based
    triggers: List[str]
    keywords: List[str]
    success_rate: float
    occurrence_count: int
    last_seen: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass  
class EscalationOutcome:
    """Tracks outcome of an escalation"""
    escalation_id: str
    timestamp: str
    trigger: str
    target: str
    was_successful: bool
    resolution_time_minutes: Optional[float]
    customer_satisfaction: Optional[int]  # 1-5 scale
    notes: Optional[str]


class PatternType(Enum):
    """Types of patterns to learn"""
    TRIGGER_COMBINATION = "trigger_combination"
    TIME_BASED = "time_based"
    KEYWORD_BASED = "keyword_based"
    CUSTOMER_PROFILE = "customer_profile"
    ISSUE_COMPLEXITY = "issue_complexity"


class EscalationPatternLearner:
    """
    Learns from escalation patterns to improve future decisions
    Analyzes successful and unsuccessful escalations
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize pattern learner
        
        Args:
            db_path: Path to SQLite database for pattern storage
        """
        self.db_path = db_path or "data/pagbank.db"
        self.conn = None
        self._initialize_database()
        
        # In-memory pattern cache
        self.pattern_cache: Dict[str, EscalationPattern] = {}
        self.keyword_patterns: Dict[str, List[str]] = defaultdict(list)
        self.trigger_combinations: Dict[Tuple[str, ...], Dict[str, Any]] = {}
        
        # Learning parameters
        self.min_occurrences = 5  # Minimum occurrences to consider a pattern
        self.success_threshold = 0.7  # Minimum success rate to recommend
        self.pattern_expiry_days = 30  # Days before pattern is considered stale
        
        # Load existing patterns
        self._load_patterns()
    
    def _initialize_database(self):
        """Initialize SQLite database for pattern storage"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escalation_records (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                trigger TEXT NOT NULL,
                target TEXT NOT NULL,
                session_state TEXT NOT NULL,
                message TEXT NOT NULL,
                outcome TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                success_rate REAL NOT NULL,
                occurrence_count INTEGER NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escalation_outcomes (
                escalation_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                trigger TEXT NOT NULL,
                target TEXT NOT NULL,
                was_successful INTEGER NOT NULL,
                resolution_time_minutes REAL,
                customer_satisfaction INTEGER,
                notes TEXT
            )
        ''')
        
        self.conn.commit()
    
    def record_escalation(self, session_state: Dict[str, Any],
                         trigger: EscalationTrigger,
                         target: str,
                         outcome: str = 'pending',
                         message: str = '') -> str:
        """
        Record an escalation event
        
        Args:
            session_state: Current session state
            trigger: Escalation trigger
            target: Escalation target
            outcome: Initial outcome (pending, successful, failed)
            message: User message that triggered escalation
            
        Returns:
            Escalation ID for tracking
        """
        import uuid
        escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{trigger.value[:3].upper()}-{str(uuid.uuid4())[:8]}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO escalation_records 
            (id, timestamp, trigger, target, session_state, message, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            escalation_id,
            datetime.now().isoformat(),
            trigger.value,
            target,
            json.dumps(session_state),
            message,
            outcome
        ))
        self.conn.commit()
        
        # Extract and update patterns
        self._extract_patterns(session_state, trigger, target, message)
        
        return escalation_id
    
    def update_outcome(self, escalation_id: str,
                      was_successful: bool,
                      resolution_time_minutes: Optional[float] = None,
                      customer_satisfaction: Optional[int] = None,
                      notes: Optional[str] = None):
        """
        Update the outcome of an escalation
        
        Args:
            escalation_id: ID of the escalation
            was_successful: Whether escalation was successful
            resolution_time_minutes: Time to resolution
            customer_satisfaction: Customer satisfaction score (1-5)
            notes: Additional notes
        """
        cursor = self.conn.cursor()
        
        # Get original escalation record
        cursor.execute('''
            SELECT trigger, target FROM escalation_records WHERE id = ?
        ''', (escalation_id,))
        
        result = cursor.fetchone()
        if not result:
            return
        
        trigger, target = result
        
        # Record outcome
        cursor.execute('''
            INSERT INTO escalation_outcomes
            (escalation_id, timestamp, trigger, target, was_successful,
             resolution_time_minutes, customer_satisfaction, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            escalation_id,
            datetime.now().isoformat(),
            trigger,
            target,
            1 if was_successful else 0,
            resolution_time_minutes,
            customer_satisfaction,
            notes
        ))
        
        # Update original record
        cursor.execute('''
            UPDATE escalation_records 
            SET outcome = ? 
            WHERE id = ?
        ''', ('successful' if was_successful else 'failed', escalation_id))
        
        self.conn.commit()
        
        # Update pattern success rates
        self._update_pattern_success_rates()
    
    def _extract_patterns(self, session_state: Dict[str, Any],
                         trigger: EscalationTrigger,
                         target: str,
                         message: str):
        """Extract patterns from escalation event"""
        # Extract keyword patterns
        keywords = self._extract_keywords(message)
        if keywords:
            pattern_key = f"keywords_{trigger.value}_{target}"
            self.keyword_patterns[pattern_key].extend(keywords)
        
        # Extract trigger combinations
        frustration_level = session_state.get('frustration_level', 0)
        interaction_count = session_state.get('interaction_count', 0)
        failed_attempts = session_state.get('customer_context', {}).get('failed_attempts', 0)
        
        trigger_combo = (
            trigger.value,
            f"frustration_{frustration_level}",
            f"interactions_{min(interaction_count // 5, 3)}",  # Group by 5s
            f"failures_{min(failed_attempts, 3)}"
        )
        
        if trigger_combo not in self.trigger_combinations:
            self.trigger_combinations[trigger_combo] = {
                'occurrences': 0,
                'successful': 0,
                'targets': Counter()
            }
        
        self.trigger_combinations[trigger_combo]['occurrences'] += 1
        self.trigger_combinations[trigger_combo]['targets'][target] += 1
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract significant keywords from message"""
        # Simple keyword extraction - in production, use NLP
        important_words = []
        
        # Define important keyword categories
        keywords = {
            'technical': ['erro', 'bug', 'trava', 'crash', 'código'],
            'security': ['fraude', 'roubo', 'invasão', 'suspeito'],
            'frustration': ['péssimo', 'horrível', 'desisto', 'raiva'],
            'urgency': ['urgente', 'agora', 'imediato', 'rápido']
        }
        
        message_lower = message.lower()
        for category, words in keywords.items():
            for word in words:
                if word in message_lower:
                    important_words.append(f"{category}:{word}")
        
        return important_words
    
    def _update_pattern_success_rates(self):
        """Update success rates for all patterns"""
        cursor = self.conn.cursor()
        
        # Calculate success rates for trigger combinations
        for trigger_combo, data in self.trigger_combinations.items():
            if data['occurrences'] >= self.min_occurrences:
                # Get success count for this combination
                trigger_str = trigger_combo[0]
                cursor.execute('''
                    SELECT COUNT(*) FROM escalation_outcomes
                    WHERE trigger = ? AND was_successful = 1
                ''', (trigger_str,))
                
                success_count = cursor.fetchone()[0]
                success_rate = success_count / data['occurrences'] if data['occurrences'] > 0 else 0
                
                # Store pattern if successful enough
                if success_rate >= self.success_threshold:
                    pattern_id = f"trigger_combo_{hash(trigger_combo)}"
                    pattern = EscalationPattern(
                        pattern_id=pattern_id,
                        pattern_type=PatternType.TRIGGER_COMBINATION.value,
                        triggers=list(trigger_combo),
                        keywords=[],
                        success_rate=success_rate,
                        occurrence_count=data['occurrences'],
                        last_seen=datetime.now().isoformat(),
                        metadata={
                            'most_common_target': data['targets'].most_common(1)[0][0]
                        }
                    )
                    
                    self._save_pattern(pattern)
    
    def _save_pattern(self, pattern: EscalationPattern):
        """Save pattern to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO learned_patterns
            (pattern_id, pattern_type, pattern_data, success_rate, 
             occurrence_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            pattern.pattern_id,
            pattern.pattern_type,
            json.dumps(pattern.to_dict()),
            pattern.success_rate,
            pattern.occurrence_count,
            datetime.now().isoformat()
        ))
        self.conn.commit()
        
        # Update cache
        self.pattern_cache[pattern.pattern_id] = pattern
    
    def _load_patterns(self):
        """Load patterns from database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT pattern_data FROM learned_patterns
            WHERE last_updated > datetime('now', '-{} days')
        '''.format(self.pattern_expiry_days))
        
        for row in cursor.fetchall():
            pattern_data = json.loads(row[0])
            pattern = EscalationPattern(**pattern_data)
            self.pattern_cache[pattern.pattern_id] = pattern
    
    def get_pattern_recommendation(self, session_state: Dict[str, Any],
                                  message: str,
                                  current_trigger: Optional[EscalationTrigger] = None) -> Optional[Dict[str, Any]]:
        """
        Get pattern-based recommendation for escalation
        
        Args:
            session_state: Current session state
            message: User message
            current_trigger: Current detected trigger
            
        Returns:
            Recommendation or None
        """
        recommendations = []
        
        # Check trigger combination patterns
        if current_trigger:
            frustration_level = session_state.get('frustration_level', 0)
            interaction_count = session_state.get('interaction_count', 0)
            failed_attempts = session_state.get('customer_context', {}).get('failed_attempts', 0)
            
            trigger_combo = (
                current_trigger.value,
                f"frustration_{frustration_level}",
                f"interactions_{min(interaction_count // 5, 3)}",
                f"failures_{min(failed_attempts, 3)}"
            )
            
            # Look for matching patterns
            for pattern in self.pattern_cache.values():
                if (pattern.pattern_type == PatternType.TRIGGER_COMBINATION.value and
                    tuple(pattern.triggers) == trigger_combo):
                    recommendations.append({
                        'pattern_id': pattern.pattern_id,
                        'confidence': pattern.success_rate,
                        'target': pattern.metadata.get('most_common_target', 'human'),
                        'reason': f"Padrão histórico com {pattern.success_rate:.0%} de sucesso"
                    })
        
        # Check keyword patterns
        keywords = self._extract_keywords(message)
        for keyword in keywords:
            for pattern in self.pattern_cache.values():
                if pattern.pattern_type == PatternType.KEYWORD_BASED.value and keyword in pattern.keywords:
                    recommendations.append({
                        'pattern_id': pattern.pattern_id,
                        'confidence': pattern.success_rate,
                        'target': pattern.metadata.get('recommended_target', 'technical'),
                        'reason': f"Palavra-chave '{keyword}' detectada"
                    })
        
        # Return highest confidence recommendation
        if recommendations:
            return max(recommendations, key=lambda x: x['confidence'])
        
        return None
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """Get insights from learned patterns"""
        cursor = self.conn.cursor()
        
        # Get trigger statistics
        cursor.execute('''
            SELECT trigger, COUNT(*) as count,
                   SUM(was_successful) as successes
            FROM escalation_outcomes
            GROUP BY trigger
        ''')
        
        trigger_stats = {}
        for trigger, count, successes in cursor.fetchall():
            trigger_stats[trigger] = {
                'total': count,
                'successful': successes or 0,
                'success_rate': (successes or 0) / count if count > 0 else 0
            }
        
        # Get time-based patterns
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour,
                   COUNT(*) as count,
                   AVG(was_successful) as success_rate
            FROM escalation_outcomes
            GROUP BY hour
        ''')
        
        hourly_patterns = {}
        for hour, count, success_rate in cursor.fetchall():
            hourly_patterns[int(hour)] = {
                'count': count,
                'success_rate': success_rate or 0
            }
        
        # Get average resolution times
        cursor.execute('''
            SELECT target,
                   AVG(resolution_time_minutes) as avg_time,
                   MIN(resolution_time_minutes) as min_time,
                   MAX(resolution_time_minutes) as max_time
            FROM escalation_outcomes
            WHERE resolution_time_minutes IS NOT NULL
            GROUP BY target
        ''')
        
        resolution_times = {}
        for target, avg_time, min_time, max_time in cursor.fetchall():
            resolution_times[target] = {
                'average': round(avg_time or 0, 2),
                'minimum': round(min_time or 0, 2),
                'maximum': round(max_time or 0, 2)
            }
        
        return {
            'total_patterns': len(self.pattern_cache),
            'trigger_statistics': trigger_stats,
            'hourly_patterns': hourly_patterns,
            'resolution_times': resolution_times,
            'most_successful_patterns': self._get_top_patterns(5),
            'pattern_types': Counter(p.pattern_type for p in self.pattern_cache.values())
        }
    
    def _get_top_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing patterns"""
        sorted_patterns = sorted(
            self.pattern_cache.values(),
            key=lambda p: (p.success_rate, p.occurrence_count),
            reverse=True
        )
        
        return [
            {
                'pattern_id': p.pattern_id,
                'type': p.pattern_type,
                'success_rate': p.success_rate,
                'occurrences': p.occurrence_count,
                'metadata': p.metadata
            }
            for p in sorted_patterns[:limit]
        ]
    
    def export_patterns(self, output_file: str):
        """Export patterns to JSON file"""
        patterns_data = {
            'export_date': datetime.now().isoformat(),
            'patterns': [p.to_dict() for p in self.pattern_cache.values()],
            'insights': self.get_pattern_insights()
        }
        
        with open(output_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old escalation data"""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            DELETE FROM escalation_records WHERE timestamp < ?
        ''', (cutoff_date,))
        
        cursor.execute('''
            DELETE FROM escalation_outcomes WHERE timestamp < ?
        ''', (cutoff_date,))
        
        self.conn.commit()


def create_pattern_learner(db_path: Optional[str] = None) -> EscalationPatternLearner:
    """
    Create and return pattern learner instance
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Configured pattern learner
    """
    return EscalationPatternLearner(db_path)


if __name__ == '__main__':
    # Test the pattern learner
    print("=== PagBank Escalation Pattern Learner Test ===")
    
    learner = create_pattern_learner("data/pagbank.db")
    
    # Simulate some escalations
    test_escalations = [
        {
            'session_state': {
                'customer_id': 'CUST001',
                'frustration_level': 3,
                'interaction_count': 8,
                'customer_context': {'failed_attempts': 2}
            },
            'trigger': EscalationTrigger.HIGH_FRUSTRATION,
            'target': 'human',
            'message': 'Estou muito frustrado com esse app!'
        },
        {
            'session_state': {
                'customer_id': 'CUST002',
                'frustration_level': 2,
                'interaction_count': 5,
                'customer_context': {'failed_attempts': 1}
            },
            'trigger': EscalationTrigger.TECHNICAL_BUG,
            'target': 'technical',
            'message': 'Aparece erro código E1234 quando tento fazer PIX'
        },
        {
            'session_state': {
                'customer_id': 'CUST003',
                'frustration_level': 3,
                'interaction_count': 12,
                'customer_context': {'failed_attempts': 3}
            },
            'trigger': EscalationTrigger.REPEATED_FAILURES,
            'target': 'human',
            'message': 'Já tentei de tudo e nada funciona!'
        }
    ]
    
    # Record escalations
    escalation_ids = []
    for test in test_escalations:
        esc_id = learner.record_escalation(
            session_state=test['session_state'],
            trigger=test['trigger'],
            target=test['target'],
            message=test['message']
        )
        escalation_ids.append(esc_id)
        print(f"Recorded escalation: {esc_id}")
    
    # Simulate outcomes
    for i, esc_id in enumerate(escalation_ids):
        was_successful = i % 2 == 0  # Alternate success/failure
        learner.update_outcome(
            escalation_id=esc_id,
            was_successful=was_successful,
            resolution_time_minutes=15 + (i * 10),
            customer_satisfaction=4 if was_successful else 2,
            notes=f"Test outcome {i+1}"
        )
        print(f"Updated outcome for {esc_id}: {'Success' if was_successful else 'Failed'}")
    
    # Get pattern recommendation
    test_state = {
        'customer_id': 'CUST004',
        'frustration_level': 3,
        'interaction_count': 8,
        'customer_context': {'failed_attempts': 2}
    }
    
    recommendation = learner.get_pattern_recommendation(
        session_state=test_state,
        message="Isso é frustrante demais!",
        current_trigger=EscalationTrigger.HIGH_FRUSTRATION
    )
    
    print(f"\n{'='*40}")
    print("Pattern Recommendation:")
    if recommendation:
        print(f"Target: {recommendation['target']}")
        print(f"Confidence: {recommendation['confidence']:.2%}")
        print(f"Reason: {recommendation['reason']}")
    else:
        print("No pattern recommendation available yet")
    
    # Show insights
    insights = learner.get_pattern_insights()
    print(f"\n{'='*40}")
    print("Pattern Insights:")
    print(f"Total patterns: {insights['total_patterns']}")
    print(f"Trigger statistics: {insights['trigger_statistics']}")
    print(f"Resolution times: {insights['resolution_times']}")