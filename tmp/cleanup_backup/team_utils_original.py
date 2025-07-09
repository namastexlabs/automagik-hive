"""
Helper functions and utilities for team operations
Agent E: Team Framework Development
Shared utilities for all PagBank teams
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class TeamUtils:
    """Utility functions for team operations"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Portuguese text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        for original, replacement in replacements.items():
            text = text.replace(original, replacement)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Normalize text first
        text = TeamUtils.normalize_text(text)
        
        # Remove common Portuguese stop words
        stop_words = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
            'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'com', 'sem',
            'e', 'ou', 'mas', 'que', 'se', 'como', 'quando', 'onde',
            'eu', 'voce', 'ele', 'ela', 'nos', 'eles', 'elas',
            'meu', 'minha', 'seu', 'sua', 'nosso', 'nossa',
            'este', 'esse', 'aquele', 'esta', 'essa', 'aquela',
            'muito', 'mais', 'menos', 'bem', 'bom', 'boa',
            'quero', 'queria', 'gostaria', 'preciso', 'posso'
        }
        
        # Split into words
        words = re.findall(r'\b\w+\b', text)
        
        # Filter keywords
        keywords = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        return keywords
    
    @staticmethod
    def detect_intent(text: str) -> Dict[str, Any]:
        """Detect user intent from text"""
        normalized_text = TeamUtils.normalize_text(text)
        
        # Intent patterns
        intents = {
            "consulta_saldo": [
                "saldo", "quanto tenho", "extrato", "movimentacao"
            ],
            "transferencia": [
                "transferir", "transferencia", "pix", "ted", "doc", "enviar dinheiro"
            ],
            "cartao_problema": [
                "cartao nao funciona", "bloqueado", "bloqueio", "senha cartao", 
                "limite", "fatura", "nao passou"
            ],
            "investimento_info": [
                "investir", "investimento", "cdb", "rendimento", "aplicacao"
            ],
            "credito_solicitacao": [
                "emprestimo", "credito", "fgts", "consignado", "financiamento"
            ],
            "seguro_info": [
                "seguro", "protecao", "cobertura", "sinistro", "cancelar seguro"
            ],
            "reclamacao": [
                "reclamar", "problema", "erro", "nao funciona", "pessimo", "horrivel"
            ],
            "urgente": [
                "urgente", "emergencia", "agora", "imediato", "rapido"
            ]
        }
        
        detected_intents = {}
        for intent, patterns in intents.items():
            for pattern in patterns:
                if pattern in normalized_text:
                    detected_intents[intent] = detected_intents.get(intent, 0) + 1
        
        # Get primary intent
        if detected_intents:
            primary_intent = max(detected_intents.items(), key=lambda x: x[1])[0]
        else:
            primary_intent = "general_inquiry"
        
        # Check urgency
        is_urgent = "urgente" in detected_intents
        
        # Check sentiment
        negative_words = ["nao", "problema", "erro", "ruim", "pessimo", "horrivel"]
        sentiment_score = sum(1 for word in negative_words if word in normalized_text)
        sentiment = "negative" if sentiment_score > 1 else "neutral"
        
        return {
            "primary_intent": primary_intent,
            "all_intents": detected_intents,
            "is_urgent": is_urgent,
            "sentiment": sentiment,
            "keywords": TeamUtils.extract_keywords(text)
        }
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Format value as Brazilian currency"""
        return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 2) -> str:
        """Format value as percentage"""
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def format_date(date: datetime, format: str = "dd/mm/yyyy") -> str:
        """Format date in Brazilian format"""
        if format == "dd/mm/yyyy":
            return date.strftime("%d/%m/%Y")
        elif format == "dd/mm/yyyy hh:mm":
            return date.strftime("%d/%m/%Y %H:%M")
        elif format == "extenso":
            months = [
                "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
            ]
            return f"{date.day} de {months[date.month-1]} de {date.year}"
        return str(date)
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """Mask sensitive data in text"""
        # CPF pattern: XXX.XXX.XXX-XX
        text = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', 'XXX.XXX.XXX-XX', text)
        text = re.sub(r'\b\d{11}\b', 'XXXXXXXXXXX', text)
        
        # CNPJ pattern: XX.XXX.XXX/XXXX-XX
        text = re.sub(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', 'XX.XXX.XXX/XXXX-XX', text)
        text = re.sub(r'\b\d{14}\b', 'XXXXXXXXXXXXXX', text)
        
        # Credit card pattern
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'XXXX XXXX XXXX XXXX', text)
        
        # Email pattern
        text = re.sub(r'\b[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b', 'XXX@XXX.com', text, flags=re.IGNORECASE)
        
        # Phone pattern
        text = re.sub(r'\b\(\d{2}\)\s?\d{4,5}-?\d{4}\b', '(XX) XXXXX-XXXX', text)
        
        return text
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)"""
        # Normalize both texts
        text1 = TeamUtils.normalize_text(text1)
        text2 = TeamUtils.normalize_text(text2)
        
        # Get words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def extract_amounts(text: str) -> List[float]:
        """Extract monetary amounts from text"""
        amounts = []
        
        # Pattern for Brazilian currency format
        patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',  # R$ 1.234,56
            r'R\$\s*(\d+(?:,\d{2})?)',  # R$ 1234,56
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*reais',  # 1.234,56 reais
            r'(\d+(?:,\d{2})?)\s*reais'  # 1234,56 reais
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Convert to float
                amount_str = match.replace('.', '').replace(',', '.')
                try:
                    amounts.append(float(amount_str))
                except ValueError:
                    continue
        
        return amounts
    
    @staticmethod
    def extract_dates(text: str) -> List[datetime]:
        """Extract dates from text"""
        dates = []
        
        # Common date patterns
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),
            (r'(\d{1,2}) de (\w+) de (\d{4})', None)  # Custom parsing needed
        ]
        
        for pattern, format_str in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if format_str:
                        date_str = f"{match[0]}/{match[1]}/{match[2]}"
                        dates.append(datetime.strptime(date_str, format_str))
                    else:
                        # Handle "XX de month de YYYY"
                        months = {
                            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                        }
                        month_name = match[1].lower()
                        if month_name in months:
                            date = datetime(int(match[2]), months[month_name], int(match[0]))
                            dates.append(date)
                except ValueError:
                    continue
        
        return dates
    
    @staticmethod
    def generate_reference_id(prefix: str = "REF") -> str:
        """Generate unique reference ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}-{timestamp}"
    
    @staticmethod
    def validate_business_hours() -> Tuple[bool, str]:
        """Check if current time is within business hours"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Business hours: Mon-Fri 8AM-8PM, Sat 9AM-4PM
        if weekday < 5:  # Monday to Friday
            is_open = 8 <= hour < 20
            next_open = "amanhã às 8h" if hour >= 20 else "hoje às 8h"
        elif weekday == 5:  # Saturday
            is_open = 9 <= hour < 16
            next_open = "segunda-feira às 8h" if hour >= 16 else "hoje às 9h"
        else:  # Sunday
            is_open = False
            next_open = "segunda-feira às 8h"
        
        return is_open, next_open
    
    @staticmethod
    def get_greeting() -> str:
        """Get appropriate greeting based on time"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Bom dia"
        elif 12 <= hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        
        # Try to break at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # If space is reasonably close
            truncated = truncated[:last_space]
        
        return truncated + suffix
    
    @staticmethod
    def sanitize_log_data(data: Any) -> Any:
        """Sanitize sensitive data for logging"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = ['senha', 'password', 'token', 'cpf', 'cnpj', 'card_number']
            
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = TeamUtils.sanitize_log_data(value)
                else:
                    sanitized[key] = TeamUtils.mask_sensitive_data(str(value))
            
            return sanitized
        elif isinstance(data, list):
            return [TeamUtils.sanitize_log_data(item) for item in data]
        else:
            return TeamUtils.mask_sensitive_data(str(data))


class ResponseFormatter:
    """Format responses for consistent output"""
    
    @staticmethod
    def format_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> str:
        """Format a success response"""
        response = f"✅ **{message}**"
        
        if data:
            response += "\n\n**Detalhes:**\n"
            for key, value in data.items():
                response += f"- {key}: {value}\n"
        
        return response
    
    @staticmethod
    def format_error_response(message: str, suggestion: Optional[str] = None) -> str:
        """Format an error response"""
        response = f"❌ **{message}**"
        
        if suggestion:
            response += f"\n\n💡 **Sugestão:** {suggestion}"
        
        return response
    
    @staticmethod
    def format_warning_response(message: str, details: Optional[List[str]] = None) -> str:
        """Format a warning response"""
        response = f"⚠️ **{message}**"
        
        if details:
            response += "\n\n**Pontos de atenção:**\n"
            for detail in details:
                response += f"- {detail}\n"
        
        return response
    
    @staticmethod
    def format_info_response(title: str, sections: Dict[str, Any]) -> str:
        """Format an informational response"""
        response = f"ℹ️ **{title}**\n\n"
        
        for section_title, content in sections.items():
            response += f"**{section_title}:**\n"
            
            if isinstance(content, list):
                for item in content:
                    response += f"- {item}\n"
            elif isinstance(content, dict):
                for key, value in content.items():
                    response += f"- {key}: {value}\n"
            else:
                response += f"{content}\n"
            
            response += "\n"
        
        return response.strip()
    
    @staticmethod
    def format_step_by_step(title: str, steps: List[str], notes: Optional[List[str]] = None) -> str:
        """Format step-by-step instructions"""
        response = f"📝 **{title}**\n\n"
        
        for i, step in enumerate(steps, 1):
            response += f"**{i}.** {step}\n"
        
        if notes:
            response += "\n**📌 Observações importantes:**\n"
            for note in notes:
                response += f"- {note}\n"
        
        return response


# Export utility instances
team_utils = TeamUtils()
response_formatter = ResponseFormatter()