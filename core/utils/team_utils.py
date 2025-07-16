"""
Minimal team utilities - only includes actually used functions
Cleaned up version removing 75% of dead code
"""

import re
from typing import Any, Dict, Optional


class TeamUtils:
    """Minimal utility functions for team operations - only used functions"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Portuguese text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u',
            'ç': 'c'
        }
        
        for original, replacement in replacements.items():
            text = text.replace(original, replacement)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def detect_intent(text: str) -> Dict[str, Any]:
        """Detect user intent from text"""
        normalized_text = TeamUtils.normalize_text(text)
        
        # Intent patterns
        intents = {
            "transferencia": ["transferir", "transferencia", "pix", "ted", "doc", "enviar dinheiro"],
            "cartao_problema": ["cartao nao funciona", "bloqueado", "bloqueio", "senha cartao", "limite", "fatura"],
            "investimento_info": ["investir", "investimento", "cdb", "rendimento", "aplicacao"],
            "credito_solicitacao": ["emprestimo", "credito", "fgts", "consignado", "financiamento"],
            "urgente": ["urgente", "emergencia", "agora", "imediato", "rapido"]
        }
        
        detected_intents = {}
        for intent, patterns in intents.items():
            for pattern in patterns:
                if pattern in normalized_text:
                    detected_intents[intent] = detected_intents.get(intent, 0) + 1
        
        # Get primary intent
        primary_intent = max(detected_intents.items(), key=lambda x: x[1])[0] if detected_intents else "general_inquiry"
        
        # Check urgency
        is_urgent = "urgente" in detected_intents
        
        return {
            "primary_intent": primary_intent,
            "all_intents": detected_intents,
            "is_urgent": is_urgent,
            "sentiment": "neutral"
        }
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Format value as Brazilian currency"""
        return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """Mask sensitive data in text"""
        # CPF pattern
        text = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', 'XXX.XXX.XXX-XX', text)
        text = re.sub(r'\b\d{11}\b', 'XXXXXXXXXXX', text)
        
        # Email pattern
        text = re.sub(r'\b[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b', 'XXX@XXX.com', text, flags=re.IGNORECASE)
        
        # Phone pattern
        text = re.sub(r'\b\(\d{2}\)\s?\d{4,5}-?\d{4}\b', '(XX) XXXXX-XXXX', text)
        
        return text


class ResponseFormatter:
    """Minimal response formatter - only used functions"""
    
    @staticmethod
    def format_error_response(message: str, suggestion: Optional[str] = None) -> str:
        """Format an error response"""
        response = f"❌ **{message}**"
        
        if suggestion:
            response += f"\n\n💡 **Sugestão:** {suggestion}"
        
        return response


# Export utility instances
team_utils = TeamUtils()
response_formatter = ResponseFormatter()