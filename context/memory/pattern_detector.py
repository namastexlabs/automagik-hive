"""
Pattern Detection for PagBank Memory System
Agent C: Memory System Foundation
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DetectedPattern:
    """Represents a detected pattern in user interactions"""
    pattern_type: str
    pattern_value: str
    confidence: float
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary"""
        return {
            'pattern_type': self.pattern_type,
            'pattern_value': self.pattern_value,
            'confidence': self.confidence,
            'occurrences': self.occurrences,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'metadata': self.metadata
        }


class PatternDetector:
    """
    Detects patterns in user interactions for PagBank agents
    Identifies financial preferences, communication patterns, and behavior trends
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.patterns: Dict[str, Dict[str, DetectedPattern]] = defaultdict(dict)
        
        # Pattern detection rules
        self.financial_patterns = {
            'investment_preference': [
                r'investir? em ([a-zA-Z]+)',
                r'aplicar? em ([a-zA-Z]+)',
                r'render? mais que ([0-9]+%|poupança)',
                r'cdi|tesouro|cdb|lci|lca|fundos'
            ],
            'credit_needs': [
                r'empréstimo|crédito|financiamento',
                r'fgts|consignado|antecipação',
                r'taxa de juros|parcela|prazo'
            ],
            'card_usage': [
                r'cartão (de )?crédito|cartão (de )?débito',
                r'limite|anuidade|fatura',
                r'cashback|benefícios|pontos'
            ],
            'account_behavior': [
                r'pix|transferência|ted|doc',
                r'saldo|extrato|conta',
                r'pagamento de contas|recarga'
            ]
        }
        
        self.communication_patterns = {
            'complexity_preference': [
                r'explicar? (simples|fácil|básico)',
                r'detalhar?|específico|técnico',
                r'passo a passo|como funciona'
            ],
            'urgency_level': [
                r'urgente|rápido|agora|hoje',
                r'quando|prazo|tempo',
                r'pode esperar|sem pressa'
            ],
            'question_type': [
                r'como (fazer|solicitar|pedir)',
                r'quanto (custa|cobre|taxa)',
                r'onde (encontrar|acessar|ver)'
            ]
        }
        
        self.behavioral_patterns = {
            'session_timing': [],  # Filled during runtime
            'interaction_frequency': [],  # Filled during runtime
            'topic_persistence': []  # Filled during runtime
        }
    
    def analyze_message(self, user_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> List[DetectedPattern]:
        """Analyze a message for patterns"""
        detected_patterns = []
        message_lower = message.lower()
        current_time = datetime.now()
        
        # Analyze financial patterns
        for pattern_type, patterns_list in self.financial_patterns.items():
            for pattern in patterns_list:
                matches = re.finditer(pattern, message_lower)
                for match in matches:
                    pattern_value = match.group(0) if match.groups() == () else match.group(1)
                    
                    detected_pattern = self._create_or_update_pattern(
                        user_id, pattern_type, pattern_value, current_time, metadata
                    )
                    detected_patterns.append(detected_pattern)
        
        # Analyze communication patterns
        for pattern_type, patterns_list in self.communication_patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, message_lower):
                    detected_pattern = self._create_or_update_pattern(
                        user_id, pattern_type, pattern, current_time, metadata
                    )
                    detected_patterns.append(detected_pattern)
        
        # Analyze behavioral patterns based on metadata
        if metadata:
            behavioral_patterns = self._analyze_behavioral_patterns(user_id, metadata, current_time)
            detected_patterns.extend(behavioral_patterns)
        
        return detected_patterns
    
    def _create_or_update_pattern(self, user_id: str, pattern_type: str, pattern_value: str, 
                                 current_time: datetime, metadata: Optional[Dict[str, Any]] = None) -> DetectedPattern:
        """Create new pattern or update existing one"""
        
        if user_id not in self.patterns:
            self.patterns[user_id] = {}
        
        pattern_key = f"{pattern_type}:{pattern_value}"
        
        if pattern_key in self.patterns[user_id]:
            # Update existing pattern
            existing_pattern = self.patterns[user_id][pattern_key]
            existing_pattern.occurrences += 1
            existing_pattern.last_seen = current_time
            existing_pattern.confidence = min(1.0, existing_pattern.confidence + 0.1)
            
            # Update metadata
            if metadata:
                existing_pattern.metadata.update(metadata)
            
            return existing_pattern
        else:
            # Create new pattern
            new_pattern = DetectedPattern(
                pattern_type=pattern_type,
                pattern_value=pattern_value,
                confidence=0.5,
                occurrences=1,
                first_seen=current_time,
                last_seen=current_time,
                metadata=metadata or {}
            )
            
            self.patterns[user_id][pattern_key] = new_pattern
            return new_pattern
    
    def _analyze_behavioral_patterns(self, user_id: str, metadata: Dict[str, Any], 
                                   current_time: datetime) -> List[DetectedPattern]:
        """Analyze behavioral patterns from metadata"""
        patterns = []
        
        # Session timing pattern
        if 'session_start' in metadata:
            session_hour = current_time.hour
            if 6 <= session_hour < 12:
                timing_pattern = "morning_user"
            elif 12 <= session_hour < 18:
                timing_pattern = "afternoon_user"
            else:
                timing_pattern = "evening_user"
            
            pattern = self._create_or_update_pattern(
                user_id, 'session_timing', timing_pattern, current_time, metadata
            )
            patterns.append(pattern)
        
        # Interaction frequency pattern
        if 'interaction_count' in metadata:
            count = metadata['interaction_count']
            if count > 10:
                frequency_pattern = "high_frequency"
            elif count > 3:
                frequency_pattern = "medium_frequency"
            else:
                frequency_pattern = "low_frequency"
            
            pattern = self._create_or_update_pattern(
                user_id, 'interaction_frequency', frequency_pattern, current_time, metadata
            )
            patterns.append(pattern)
        
        return patterns
    
    def get_user_patterns(self, user_id: str, pattern_type: Optional[str] = None) -> List[DetectedPattern]:
        """Get patterns for a specific user"""
        if user_id not in self.patterns:
            return []
        
        user_patterns = list(self.patterns[user_id].values())
        
        if pattern_type:
            user_patterns = [p for p in user_patterns if p.pattern_type == pattern_type]
        
        # Sort by confidence and recency
        user_patterns.sort(key=lambda x: (x.confidence, x.last_seen), reverse=True)
        
        return user_patterns
    
    def get_top_patterns(self, user_id: str, limit: int = 10) -> List[DetectedPattern]:
        """Get top patterns for a user"""
        patterns = self.get_user_patterns(user_id)
        return patterns[:limit]
    
    def get_pattern_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights about user patterns"""
        patterns = self.get_user_patterns(user_id)
        
        insights = {
            'total_patterns': len(patterns),
            'pattern_types': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'most_common_patterns': [],
            'recent_patterns': [],
            'behavioral_summary': {}
        }
        
        # Analyze pattern types
        for pattern in patterns:
            if pattern.pattern_type not in insights['pattern_types']:
                insights['pattern_types'][pattern.pattern_type] = 0
            insights['pattern_types'][pattern.pattern_type] += 1
            
            # Confidence distribution
            if pattern.confidence >= 0.8:
                insights['confidence_distribution']['high'] += 1
            elif pattern.confidence >= 0.5:
                insights['confidence_distribution']['medium'] += 1
            else:
                insights['confidence_distribution']['low'] += 1
        
        # Most common patterns
        patterns_by_occurrence = sorted(patterns, key=lambda x: x.occurrences, reverse=True)
        insights['most_common_patterns'] = [p.to_dict() for p in patterns_by_occurrence[:5]]
        
        # Recent patterns
        recent_patterns = sorted(patterns, key=lambda x: x.last_seen, reverse=True)
        insights['recent_patterns'] = [p.to_dict() for p in recent_patterns[:5]]
        
        # Behavioral summary
        insights['behavioral_summary'] = self._create_behavioral_summary(patterns)
        
        return insights
    
    def _create_behavioral_summary(self, patterns: List[DetectedPattern]) -> Dict[str, Any]:
        """Create a behavioral summary from patterns"""
        summary = {
            'financial_preferences': [],
            'communication_style': [],
            'usage_patterns': [],
            'risk_profile': 'unknown'
        }
        
        # Analyze financial preferences
        investment_patterns = [p for p in patterns if p.pattern_type == 'investment_preference']
        if investment_patterns:
            summary['financial_preferences'] = [p.pattern_value for p in investment_patterns[:3]]
        
        # Analyze communication style
        complexity_patterns = [p for p in patterns if p.pattern_type == 'complexity_preference']
        if complexity_patterns:
            most_common = max(complexity_patterns, key=lambda x: x.occurrences)
            summary['communication_style'] = [most_common.pattern_value]
        
        # Analyze usage patterns
        timing_patterns = [p for p in patterns if p.pattern_type == 'session_timing']
        if timing_patterns:
            most_common = max(timing_patterns, key=lambda x: x.occurrences)
            summary['usage_patterns'] = [most_common.pattern_value]
        
        # Determine risk profile
        risk_indicators = [p for p in patterns if p.pattern_type in ['investment_preference', 'credit_needs']]
        if risk_indicators:
            conservative_count = sum(1 for p in risk_indicators if 'poupança' in p.pattern_value.lower())
            aggressive_count = sum(1 for p in risk_indicators if any(term in p.pattern_value.lower() 
                                                                   for term in ['ações', 'renda_variavel', 'fundos']))
            
            if conservative_count > aggressive_count:
                summary['risk_profile'] = 'conservative'
            elif aggressive_count > conservative_count:
                summary['risk_profile'] = 'aggressive'
            else:
                summary['risk_profile'] = 'moderate'
        
        return summary
    
    def export_patterns(self, user_id: str) -> str:
        """Export user patterns to JSON"""
        patterns = self.get_user_patterns(user_id)
        export_data = {
            'user_id': user_id,
            'export_time': datetime.now().isoformat(),
            'patterns': [p.to_dict() for p in patterns],
            'insights': self.get_pattern_insights(user_id)
        }
        
        return json.dumps(export_data, indent=2)
    
    def clear_user_patterns(self, user_id: str) -> bool:
        """Clear all patterns for a user"""
        if user_id in self.patterns:
            del self.patterns[user_id]
            return True
        return False
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get overall pattern statistics"""
        total_users = len(self.patterns)
        total_patterns = sum(len(user_patterns) for user_patterns in self.patterns.values())
        
        pattern_type_counts = defaultdict(int)
        for user_patterns in self.patterns.values():
            for pattern in user_patterns.values():
                pattern_type_counts[pattern.pattern_type] += 1
        
        return {
            'total_users': total_users,
            'total_patterns': total_patterns,
            'pattern_type_distribution': dict(pattern_type_counts),
            'average_patterns_per_user': total_patterns / total_users if total_users > 0 else 0
        }


def create_pattern_detector(similarity_threshold: float = 0.8) -> PatternDetector:
    """Create and return a pattern detector instance"""
    return PatternDetector(similarity_threshold)