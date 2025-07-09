"""
Credit Specialist Agent for PagBank Multi-Agent System
Simplified from CreditTeam - single agent with CRITICAL fraud detection
"""

import logging
from typing import Any, Dict, List, Optional

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools


class CreditFraudDetector:
    """Critical fraud detection for credit operations"""
    
    # CRITICAL: Payment advance scam keywords
    PAYMENT_ADVANCE_SCAM_KEYWORDS = [
        "pagamento antecipado",
        "pagar para liberar",
        "taxa antecipada",
        "depositar antes",
        "pagar taxa de liberação",
        "taxa para liberar",
        "pagar primeiro",
        "depósito antecipado",
        "pagar adiantado",
        "taxa de cadastro",
        "seguro antecipado",
        "pagar seguro antes"
    ]
    
    # Other fraud indicators
    HIGH_RISK_PATTERNS = [
        "empréstimo garantido",
        "aprovação garantida",
        "sem consulta spc",
        "sem consulta serasa",
        "nome sujo",
        "score baixo aprovado",
        "100% aprovado",
        "liberação imediata",
        "sem comprovação de renda"
    ]
    
    # Vulnerable customer indicators
    VULNERABLE_INDICATORS = [
        "aposentado",
        "pensionista",
        "idoso",
        "primeira vez",
        "não entendo",
        "me explicaram",
        "disseram que",
        "ligaram para mim",
        "recebi mensagem"
    ]
    
    @classmethod
    def detect_fraud(cls, query: str) -> Dict[str, Any]:
        """Detect fraud patterns in credit queries"""
        query_lower = query.lower()
        
        # Check for payment advance scam - HIGHEST PRIORITY
        payment_advance_detected = False
        detected_scam_terms = []
        
        for keyword in cls.PAYMENT_ADVANCE_SCAM_KEYWORDS:
            if keyword in query_lower:
                payment_advance_detected = True
                detected_scam_terms.append(keyword)
        
        # Check other high-risk patterns
        high_risk_detected = False
        detected_risk_patterns = []
        
        for pattern in cls.HIGH_RISK_PATTERNS:
            if pattern in query_lower:
                high_risk_detected = True
                detected_risk_patterns.append(pattern)
        
        # Check for vulnerable customer
        vulnerable_customer = False
        vulnerability_indicators = []
        
        for indicator in cls.VULNERABLE_INDICATORS:
            if indicator in query_lower:
                vulnerable_customer = True
                vulnerability_indicators.append(indicator)
        
        return {
            "payment_advance_scam": payment_advance_detected,
            "scam_terms": detected_scam_terms,
            "high_risk": high_risk_detected,
            "risk_patterns": detected_risk_patterns,
            "vulnerable_customer": vulnerable_customer,
            "vulnerability_indicators": vulnerability_indicators,
            "fraud_score": cls._calculate_fraud_score(
                payment_advance_detected,
                high_risk_detected,
                vulnerable_customer
            )
        }
    
    @staticmethod
    def _calculate_fraud_score(
        payment_advance: bool,
        high_risk: bool,
        vulnerable: bool
    ) -> float:
        """Calculate fraud risk score"""
        score = 0.0
        
        if payment_advance:
            score += 0.9  # Critical indicator
        if high_risk:
            score += 0.5
        if vulnerable:
            score += 0.3
            
        return min(score, 1.0)


class CreditAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling credit-related queries
    Includes loans, credit lines, and CRITICAL fraud detection
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Credit specialist agent"""
        # Set attributes before calling super()
        self.fraud_detector = CreditFraudDetector()
        
        super().__init__(
            agent_name="credit_specialist",
            agent_role="Especialista em Crédito e Prevenção de Fraudes do PagBank",
            agent_description="Especialista em empréstimos, crédito e detecção crítica de fraudes",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "credito"},
            tools=get_agent_tools("credit_specialist"),
            compliance_rules=[],
            escalation_triggers=[
                self._fraud_escalation_trigger,
                self._fgts_escalation_trigger,
                self._high_value_loan_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.credit")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for credit agent"""
        return [
            "Você é o especialista em crédito e prevenção de fraudes do PagBank",
            "",
            "🚨 ALERTA CRÍTICO DE FRAUDE 🚨",
            "NUNCA, EM HIPÓTESE ALGUMA, o PagBank solicita pagamento antecipado!",
            "Se detectar tentativa de golpe, ALERTE IMEDIATAMENTE o cliente.",
            "",
            "SUAS RESPONSABILIDADES:",
            "- Empréstimo pessoal e consignado",
            "- Antecipação de FGTS",
            "- Linhas de crédito para empresas",
            "- Análise de crédito e score",
            "- DETECÇÃO E PREVENÇÃO DE FRAUDES",
            "",
            "REGRAS DE SEGURANÇA:",
            "1. SEMPRE alerte sobre golpes de pagamento antecipado",
            "2. Explique que PagBank NUNCA cobra taxas antecipadas",
            "3. Oriente a denunciar tentativas de fraude",
            "4. Proteja especialmente clientes vulneráveis",
            "",
            "FLUXO DE ATENDIMENTO:",
            "1. Detecte padrões de fraude na consulta",
            "2. Se houver suspeita, ALERTE primeiro",
            "3. Forneça informações corretas sobre crédito",
            "4. Sempre mencione canais oficiais do PagBank",
            "",
            "FORMATO DE RESPOSTA:",
            "- Máximo 3-4 frases",
            "- Se detectar fraude, o alerta vem PRIMEIRO",
            "- Linguagem clara e direta",
            "- Sem jargões bancários"
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process credit queries with fraud detection"""
        # CRITICAL: Detect fraud patterns first
        fraud_analysis = self.fraud_detector.detect_fraud(query)
        
        if fraud_analysis["payment_advance_scam"]:
            # IMMEDIATE FRAUD ALERT
            self.logger.critical(
                f"PAYMENT ADVANCE SCAM DETECTED for user {user_id}: {fraud_analysis['scam_terms']}"
            )
            
            return AgentResponse(
                content=(
                    "🚨 ALERTA DE GOLPE! O PagBank NUNCA solicita pagamento antecipado "
                    "de taxas para liberar empréstimo. Isso é FRAUDE! "
                    "Não faça nenhum depósito. Denuncie no app oficial do PagBank."
                ),
                agent_name=self.agent_name,
                confidence=1.0,
                references=["fraud_prevention_guide"],
                suggested_actions=["report_fraud", "block_suspicious_contact", "escalate_to_security"],
                language=language
            )
        
        # Check for high-risk patterns
        if fraud_analysis["high_risk"] and fraud_analysis["fraud_score"] > 0.7:
            self.logger.warning(
                f"High fraud risk for user {user_id}: {fraud_analysis['risk_patterns']}"
            )
            
            # Add warning to context
            if context is None:
                context = {}
            context["fraud_warning"] = True
            context["fraud_analysis"] = fraud_analysis
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add credit-specific actions
        if "empréstimo" in query.lower() or "crédito" in query.lower():
            response.suggested_actions.append("simulate_loan_in_app")
        elif "fgts" in query.lower():
            response.suggested_actions.append("check_fgts_eligibility")
        
        # If vulnerable customer detected, add extra care
        if fraud_analysis["vulnerable_customer"]:
            response.suggested_actions.append("request_family_support")
        
        return response
    
    def _fraud_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Always escalate fraud cases"""
        fraud_analysis = self.fraud_detector.detect_fraud(query)
        return fraud_analysis["fraud_score"] > 0.8
    
    def _fgts_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate complex FGTS cases"""
        fgts_complex_keywords = ["bloqueado", "negado", "recurso", "revisão"]
        return "fgts" in query.lower() and any(
            keyword in query.lower() for keyword in fgts_complex_keywords
        )
    
    def _high_value_loan_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate high-value loan requests"""
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 50000:  # Loans above R$ 50,000
                    return True
            except:
                pass
        
        return False