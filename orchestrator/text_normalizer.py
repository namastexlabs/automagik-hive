"""
Text Normalization System for Brazilian Portuguese
Handles common misspellings, informal language, and text standardization
"""

import re
from typing import Dict, List, Tuple


class PortugueseTextNormalizer:
    """
    Normalizes Brazilian Portuguese text for better understanding
    Handles informal language, common typos, and standardization
    """
    
    def __init__(self):
        # Common misspellings and informal variations
        self.replacements = {
            # Common word replacements
            'vc': 'você',
            'vcs': 'vocês',
            'tb': 'também',
            'tbm': 'também',
            'pq': 'porque',
            'pra': 'para',
            'pro': 'para o',
            'pras': 'para as',
            'pros': 'para os',
            'ta': 'está',
            'tá': 'está',
            'to': 'estou',
            'tô': 'estou',
            'nao': 'não',
            'voce': 'você',
            'ja': 'já',
            'eh': 'é',
            'ne': 'né',
            'dai': 'daí',
            'ai': 'aí',
            'la': 'lá',
            'so': 'só',
            'numero': 'número',
            'atraves': 'através',
            'voces': 'vocês',
            
            # Banking/Financial specific
            'cartao': 'cartão',
            'cartoes': 'cartões',
            'credito': 'crédito',
            'debito': 'débito',
            'transferencia': 'transferência',
            'operacao': 'operação',
            'operacoes': 'operações',
            'transacao': 'transação',
            'transacoes': 'transações',
            'aplicacao': 'aplicação',
            'aplicacoes': 'aplicações',
            'rendimento': 'rendimento',
            'deposito': 'depósito',
            'saque': 'saque',
            'emprestimo': 'empréstimo',
            'financiamento': 'financiamento',
            'seguro': 'seguro',
            'protecao': 'proteção',
            'conta corrente': 'conta-corrente',
            'conta poupanca': 'conta-poupança',
            
            # Common abbreviations
            'msg': 'mensagem',
            'msgs': 'mensagens',
            'tel': 'telefone',
            'cel': 'celular',
            'cpf': 'CPF',
            'cnpj': 'CNPJ',
            'rg': 'RG',
            'cep': 'CEP',
            'doc': 'documento',
            'docs': 'documentos',
            'info': 'informação',
            'infos': 'informações',
            
            # Internet slang
            'blz': 'beleza',
            'vlw': 'valeu',
            'obg': 'obrigado',
            'obgd': 'obrigado',
            'obgda': 'obrigada',
            'dps': 'depois',
            'hj': 'hoje',
            'amanha': 'amanhã',
            'ontem': 'ontem',
            'td': 'tudo',
            'tds': 'todos',
            'mto': 'muito',
            'mt': 'muito',
            'qto': 'quanto',
            'qts': 'quantos',
            'qdo': 'quando',
            'ond': 'onde',
            'cm': 'com',
            'sem': 'sem',
            
            # Common errors
            'agente': 'a gente',
            'apartir': 'a partir',
            'concerteza': 'com certeza',
            'derrepente': 'de repente',
            'denovo': 'de novo',
            'porisso': 'por isso',
            'oque': 'o que',
            'oq': 'o que',
            'porem': 'porém',
            'porque': 'por que',  # when questioning
            'porquê': 'por quê',  # at end of question
        }
        
        # Multi-word expressions that need space normalization
        self.multi_word_fixes = {
            r'\b(a)\s+(gente)\b': 'a gente',
            r'\b(por)\s+(favor)\b': 'por favor',
            r'\b(com)\s+(certeza)\b': 'com certeza',
            r'\b(de)\s+(novo)\b': 'de novo',
            r'\b(por)\s+(isso)\b': 'por isso',
            r'\b(a)\s+(partir)\b': 'a partir',
            r'\b(de)\s+(repente)\b': 'de repente',
            r'\b(conta)\s+(corrente)\b': 'conta-corrente',
            r'\b(conta)\s+(poupança)\b': 'conta-poupança',
            r'\b(cartão)\s+(de)\s+(crédito)\b': 'cartão de crédito',
            r'\b(cartão)\s+(de)\s+(débito)\b': 'cartão de débito',
        }
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        # Pattern for multiple spaces
        self.multiple_spaces = re.compile(r'\s+')
        
        # Pattern for repeated punctuation
        self.repeated_punctuation = re.compile(r'([.!?,;])\1+')
        
        # Pattern for missing spaces after punctuation
        self.punctuation_space = re.compile(r'([.!?,;])([A-Za-zÀ-ÿ])')
        
        # Pattern for repeated characters (but preserve valid words)
        self.repeated_chars = re.compile(r'(\w)\1{3,}')
        
        # Pattern to fix missing accents in common words
        self.accent_patterns = {
            r'\b(e)\b': 'é',  # Context-dependent, be careful
            r'\b(a)\b': 'à',  # Context-dependent, be careful
        }
    
    def normalize(self, text: str) -> Dict[str, any]:
        """
        Normalize Brazilian Portuguese text
        
        Args:
            text: Input text to normalize
            
        Returns:
            Dictionary with normalized text and applied changes
        """
        if not text:
            return {'normalized': '', 'changes': [], 'confidence': 1.0}
        
        original = text
        changes = []
        
        # Step 1: Basic cleaning
        text = text.strip()
        text = self.multiple_spaces.sub(' ', text)
        
        # Step 2: Fix casing issues (but preserve acronyms)
        text = self._normalize_case(text)
        
        # Step 3: Fix repeated characters
        text = self._fix_repeated_chars(text)
        
        # Step 4: Fix punctuation
        text = self._fix_punctuation(text)
        
        # Step 5: Apply word replacements
        text, word_changes = self._apply_replacements(text)
        changes.extend(word_changes)
        
        # Step 6: Fix multi-word expressions
        text, multi_changes = self._fix_multi_words(text)
        changes.extend(multi_changes)
        
        # Step 7: Final cleanup
        text = text.strip()
        text = self.multiple_spaces.sub(' ', text)
        
        # Calculate confidence based on changes
        confidence = self._calculate_confidence(original, text, len(changes))
        
        return {
            'normalized': text,
            'original': original,
            'changes': changes,
            'confidence': confidence
        }
    
    def _normalize_case(self, text: str) -> str:
        """Normalize text casing while preserving acronyms"""
        words = text.split()
        normalized_words = []
        
        for word in words:
            # Preserve acronyms (all caps, 2+ chars)
            if len(word) >= 2 and word.isupper() and word.isalpha():
                normalized_words.append(word)
            # Capitalize first word of sentence
            elif len(normalized_words) == 0 or normalized_words[-1].endswith(('.', '!', '?')):
                normalized_words.append(word.capitalize())
            else:
                normalized_words.append(word.lower())
        
        return ' '.join(normalized_words)
    
    def _fix_repeated_chars(self, text: str) -> str:
        """Fix repeated characters while preserving valid repetitions"""
        # Don't fix valid repeated chars in Portuguese (rr, ss, ll, etc.)
        valid_doubles = ['rr', 'ss', 'll', 'cc', 'mm', 'nn', 'pp', 'tt', 'ff', 'gg']
        
        def replace_repeated(match):
            char = match.group(1)
            repeated = match.group(0)
            
            # Check if it's a valid double
            if len(repeated) == 2 and repeated.lower() in valid_doubles:
                return repeated
            
            # Otherwise reduce to single or double
            return char if char.lower() not in 'rsclmnptfg' else char * 2
        
        return self.repeated_chars.sub(replace_repeated, text)
    
    def _fix_punctuation(self, text: str) -> str:
        """Fix punctuation issues"""
        # Remove repeated punctuation
        text = self.repeated_punctuation.sub(r'\1', text)
        
        # Add space after punctuation if missing
        text = self.punctuation_space.sub(r'\1 \2', text)
        
        # Fix common punctuation errors
        text = re.sub(r'\s+([.!?,;])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?])\s*$', r'\1', text)  # Ensure sentence ends with punctuation
        
        return text
    
    def _apply_replacements(self, text: str) -> Tuple[str, List[Dict]]:
        """Apply word replacements"""
        changes = []
        words = text.split()
        normalized_words = []
        
        for word in words:
            # Remove punctuation for lookup
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            punctuation = re.findall(r'[^\w\s]', word)
            
            if clean_word in self.replacements:
                replacement = self.replacements[clean_word]
                # Preserve original casing style
                if word.isupper():
                    replacement = replacement.upper()
                elif word[0].isupper():
                    replacement = replacement.capitalize()
                
                # Re-add punctuation
                if punctuation:
                    replacement += ''.join(punctuation)
                
                normalized_words.append(replacement)
                changes.append({
                    'type': 'word_replacement',
                    'original': word,
                    'replacement': replacement
                })
            else:
                normalized_words.append(word)
        
        return ' '.join(normalized_words), changes
    
    def _fix_multi_words(self, text: str) -> Tuple[str, List[Dict]]:
        """Fix multi-word expressions"""
        changes = []
        
        for pattern, replacement in self.multi_word_fixes.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                original = match.group(0)
                text = text.replace(original, replacement)
                changes.append({
                    'type': 'multi_word_fix',
                    'original': original,
                    'replacement': replacement
                })
        
        return text, changes
    
    def _calculate_confidence(self, original: str, normalized: str, num_changes: int) -> float:
        """Calculate confidence score for normalization"""
        if original == normalized:
            return 1.0
        
        # Calculate edit distance ratio
        original_len = len(original)
        if original_len == 0:
            return 1.0
        
        # Simple confidence calculation based on number of changes
        change_ratio = num_changes / len(original.split())
        confidence = max(0.5, 1.0 - (change_ratio * 0.3))
        
        return round(confidence, 2)


# Module-level instance for easy import
text_normalizer = PortugueseTextNormalizer()