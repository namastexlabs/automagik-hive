"""
Simple Human Handoff Detection for PagBank Multi-Agent System
Silent detection for immediate human transfer
"""

from typing import Dict, Any


class HumanHandoffDetector:
    """
    Simple detector for when human handoff is needed
    No levels, just boolean decision
    """
    
    def __init__(self):
        # Direct human request phrases
        self.human_phrases = [
            'quero falar com humano',
            'quero humano',
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
            'cansei de robô',
            'quero falar com gente',
            'preciso de uma pessoa'
        ]
        
        # Frustration indicators (bad words)
        self.bad_words = [
            'droga', 'merda', 'porra', 'caralho', 'desgraça',
            'bosta', 'inferno', 'puta', 'cacete', 'foda',
            'cu', 'buceta', 'viado', 'fdp', 'vsf', 'pqp'
        ]
    
    def needs_human_handoff(self, message: str) -> Dict[str, Any]:
        """
        Simple check if human handoff is needed
        
        Args:
            message: Customer message
            
        Returns:
            Dict with handoff decision and reason
        """
        message_lower = message.lower()
        
        # Check for direct human request
        for phrase in self.human_phrases:
            if phrase in message_lower:
                return {
                    'needs_handoff': True,
                    'reason': 'explicit_request',
                    'detected_phrase': phrase
                }
        
        # Check for bad words
        for word in self.bad_words:
            if word in message_lower:
                return {
                    'needs_handoff': True,
                    'reason': 'frustration_language',
                    'detected_word': word
                }
        
        # Check for CAPS LOCK yelling (more than 70% caps and at least 10 chars)
        if len(message) > 10:
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
            if caps_ratio > 0.7:
                return {
                    'needs_handoff': True,
                    'reason': 'caps_lock_yelling'
                }
        
        # No handoff needed
        return {
            'needs_handoff': False,
            'reason': None
        }


# Module-level instance for easy import
human_handoff_detector = HumanHandoffDetector()