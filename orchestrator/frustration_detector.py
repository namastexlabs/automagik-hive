"""
Frustration Detection System for PagBank Multi-Agent System
Detects frustration indicators in Portuguese messages
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class FrustrationDetector:
    """
    Detects frustration indicators in customer messages
    Specialized for Brazilian Portuguese
    """
    
    def __init__(self):
        # Portuguese frustration keywords categorized by severity
        self.frustration_keywords = {
            'high': [
                'droga', 'merda', 'porra', 'caralho', 'desgraça',
                'ódio', 'raiva', 'furioso', 'furiosa', 'puto', 'puta',
                'incompetente', 'lixo', 'bosta', 'ridículo', 'absurdo',
                'palhaçada', 'sacanagem', 'putaria', 'inferno'
            ],
            'medium': [
                'não funciona', 'péssimo', 'horrível', 'terrível',
                'não aguento mais', 'cansei', 'cansado', 'irritado',
                'chateado', 'decepcionado', 'frustrado', 'que saco',
                'estressado', 'nervoso', 'bravo', 'zangado'
            ],
            'low': [
                'difícil', 'complicado', 'confuso', 'demorado',
                'ruim', 'mal', 'problema', 'erro', 'falha',
                'não consigo', 'não dá', 'travou', 'bugou'
            ]
        }
        
        # Explicit human escalation phrases
        self.escalation_phrases = [
            'quero falar com humano',
            'quero atendente',
            'falar com pessoa',
            'atendimento humano',
            'operador humano',
            'me transfere',
            'transferir para atendente',
            'falar com alguém',
            'pessoa real',
            'não quero robô',
            'chega de robô',
            'cansei de robô'
        ]
        
        # Phrases that indicate giving up
        self.giving_up_phrases = [
            'desisto', 'vou embora', 'tchau', 'cancela',
            'deixa pra lá', 'esquece', 'não quero mais',
            'vou procurar outro banco', 'vou sair do pagbank',
            'fecha minha conta', 'cancela tudo'
        ]
        
        # Compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        # Create pattern for repeated punctuation (!!!!, ????, etc)
        self.repeated_punctuation = re.compile(r'[!?]{3,}')
        
        # Create pattern for CAPS LOCK detection
        self.caps_pattern = re.compile(r'\b[A-Z]{4,}\b')
        
        # Create pattern for repeated characters (aaaaaaa, etc)
        self.repeated_chars = re.compile(r'(.)\1{4,}')
    
    def detect_frustration(self, message: str, 
                         interaction_count: int = 0,
                         failed_attempts: int = 0) -> Dict[str, any]:
        """
        Detect frustration level in a message
        
        Args:
            message: Customer message
            interaction_count: Number of interactions in session
            failed_attempts: Number of failed resolution attempts
            
        Returns:
            Dictionary with frustration analysis
        """
        normalized_message = message.lower()
        
        # Initialize results
        result = {
            'frustration_level': 0,  # 0-3 scale
            'detected_keywords': [],
            'severity_breakdown': {'high': 0, 'medium': 0, 'low': 0},
            'explicit_escalation': False,
            'giving_up': False,
            'emotional_indicators': [],
            'recommended_action': 'continue'
        }
        
        # Check for explicit escalation request
        for phrase in self.escalation_phrases:
            if phrase in normalized_message:
                result['explicit_escalation'] = True
                result['frustration_level'] = 3
                result['recommended_action'] = 'escalate_human'
                return result
        
        # Check for giving up
        for phrase in self.giving_up_phrases:
            if phrase in normalized_message:
                result['giving_up'] = True
                result['frustration_level'] = 3
                result['recommended_action'] = 'urgent_intervention'
                
        # Detect frustration keywords
        for severity, keywords in self.frustration_keywords.items():
            for keyword in keywords:
                if keyword in normalized_message:
                    result['detected_keywords'].append(keyword)
                    result['severity_breakdown'][severity] += 1
        
        # Check emotional indicators
        if self.repeated_punctuation.search(message):
            result['emotional_indicators'].append('repeated_punctuation')
        
        if len(self.caps_pattern.findall(message)) > 2:
            result['emotional_indicators'].append('excessive_caps')
            
        if self.repeated_chars.search(message):
            result['emotional_indicators'].append('repeated_characters')
        
        # Calculate frustration level
        frustration_score = (
            result['severity_breakdown']['high'] * 3 +
            result['severity_breakdown']['medium'] * 2 +
            result['severity_breakdown']['low'] * 1 +
            len(result['emotional_indicators']) * 1
        )
        
        # Consider interaction history
        if interaction_count > 5:
            frustration_score += 1
        if failed_attempts > 2:
            frustration_score += 1
        
        # Determine frustration level (0-3)
        if frustration_score >= 6:
            result['frustration_level'] = 3
            result['recommended_action'] = 'escalate_human'
        elif frustration_score >= 4:
            result['frustration_level'] = 2
            result['recommended_action'] = 'empathetic_response'
        elif frustration_score >= 2:
            result['frustration_level'] = 1
            result['recommended_action'] = 'acknowledge_concern'
        else:
            result['frustration_level'] = 0
            result['recommended_action'] = 'continue'
        
        return result
    
    def get_empathetic_response(self, frustration_level: int) -> str:
        """Get appropriate empathetic response based on frustration level"""
        responses = {
            0: "",
            1: "Entendo sua preocupação e estou aqui para ajudar. ",
            2: "Compreendo sua frustração e peço desculpas pela dificuldade. Vou resolver isso rapidamente. ",
            3: "Lamento muito pela experiência negativa. Vou transferir você para um especialista imediatamente. "
        }
        
        return responses.get(frustration_level, "")
    
    def analyze_conversation_trend(self, messages: List[Tuple[str, datetime]]) -> Dict[str, any]:
        """
        Analyze frustration trend over conversation
        
        Args:
            messages: List of (message, timestamp) tuples
            
        Returns:
            Trend analysis
        """
        if not messages:
            return {'trend': 'neutral', 'escalating': False}
        
        frustration_scores = []
        
        for i, (message, timestamp) in enumerate(messages):
            detection = self.detect_frustration(
                message, 
                interaction_count=i+1
            )
            frustration_scores.append(detection['frustration_level'])
        
        # Analyze trend
        if len(frustration_scores) < 2:
            return {'trend': 'insufficient_data', 'escalating': False}
        
        # Check if frustration is increasing
        recent_scores = frustration_scores[-3:]
        if len(recent_scores) >= 2 and all(recent_scores[i] <= recent_scores[i+1] 
                                          for i in range(len(recent_scores)-1)):
            return {
                'trend': 'escalating',
                'escalating': True,
                'current_level': frustration_scores[-1],
                'recommendation': 'immediate_intervention'
            }
        
        # Check if consistently high
        if sum(frustration_scores[-3:]) / len(frustration_scores[-3:]) >= 2:
            return {
                'trend': 'consistently_high',
                'escalating': False,
                'current_level': frustration_scores[-1],
                'recommendation': 'escalate_specialist'
            }
        
        return {
            'trend': 'stable',
            'escalating': False,
            'current_level': frustration_scores[-1],
            'recommendation': 'continue_monitoring'
        }
    
    def should_escalate(self, detection_result: Dict[str, any],
                       session_data: Optional[Dict] = None) -> bool:
        """
        Determine if escalation to human is needed
        
        Args:
            detection_result: Result from detect_frustration
            session_data: Optional session context
            
        Returns:
            Boolean indicating if escalation is needed
        """
        # Explicit escalation request
        if detection_result.get('explicit_escalation'):
            return True
        
        # High frustration level
        if detection_result.get('frustration_level', 0) >= 3:
            return True
        
        # Customer giving up
        if detection_result.get('giving_up'):
            return True
        
        # Check session context if provided
        if session_data:
            # Too many interactions without resolution
            if session_data.get('interaction_count', 0) > 10:
                return True
            
            # Multiple failed attempts
            if session_data.get('failed_attempts', 0) > 3:
                return True
        
        return False


# Module-level instance for easy import
frustration_detector = FrustrationDetector()