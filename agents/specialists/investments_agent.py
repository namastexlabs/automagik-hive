"""
Investments Specialist Agent for PagBank Multi-Agent System
Simplified from InvestmentsTeam - single agent with MANDATORY compliance
"""

import logging
from typing import Any, Dict, List, Optional

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools


class InvestmentComplianceRule:
    """Enforces mandatory compliance rules for investment responses"""
    
    MANDATORY_DISCLAIMER = (
        "\n\n⚠️ AVISO: Esta não é uma recomendação de investimento. "
        "Avalie se os produtos são adequados ao seu perfil. "
        "Rentabilidade passada não garante resultados futuros."
    )
    
    SIMPLIFIED_TERMS = {
        "CDB": "Certificado de Depósito Bancário",
        "CDI": "Taxa de referência para rendimentos",
        "LCI": "Letra de Crédito Imobiliário",
        "LCA": "Letra de Crédito do Agronegócio",
        "FGC": "Fundo Garantidor - protege até R$ 250 mil",
        "IOF": "Imposto sobre Operações Financeiras",
        "Come-cotas": "Imposto cobrado a cada 6 meses"
    }
    
    @classmethod
    def apply_compliance(cls, response: str) -> str:
        """Apply mandatory compliance rules to response"""
        # Always add disclaimer
        if cls.MANDATORY_DISCLAIMER not in response:
            response += cls.MANDATORY_DISCLAIMER
        
        # Add FGC protection notice when relevant
        if any(product in response.lower() for product in ["cdb", "lci", "lca"]):
            if "FGC" not in response:
                response = response.rstrip() + " Protegido pelo FGC até R$ 250 mil."
        
        return response
    
    @classmethod
    def check_fraud_patterns(cls, query: str) -> Dict[str, Any]:
        """Check for investment fraud patterns"""
        query_lower = query.lower()
        fraud_indicators = []
        risk_level = "low"
        
        # High-risk patterns
        high_risk_patterns = [
            "garantia de lucro",
            "retorno garantido",
            "sem risco",
            "ganho rápido",
            "pirâmide",
            "marketing multinível",
            "100% de retorno",
            "dobrar dinheiro"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in query_lower:
                fraud_indicators.append(pattern)
                risk_level = "high"
        
        # Medium-risk patterns
        medium_risk_patterns = [
            "indicação de amigo",
            "grupo de whatsapp",
            "investimento secreto",
            "oportunidade única"
        ]
        
        if risk_level != "high":
            for pattern in medium_risk_patterns:
                if pattern in query_lower:
                    fraud_indicators.append(pattern)
                    risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "fraud_indicators": fraud_indicators,
            "is_suspicious": len(fraud_indicators) > 0
        }


class InvestmentsAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling investment queries
    Includes CDB, savings, and investment guidance with compliance
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Investments specialist agent"""
        # Set attributes before calling super()
        self.compliance = InvestmentComplianceRule()
        
        super().__init__(
            agent_name="investments_specialist",
            agent_role="Especialista em Investimentos do PagBank",
            agent_description="Especialista em CDB, poupança e produtos de investimento com compliance obrigatório",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "investimentos"},
            tools=get_agent_tools("investments_specialist"),
            compliance_rules=[InvestmentComplianceRule.apply_compliance],
            escalation_triggers=[
                self._fraud_investment_trigger,
                self._complex_portfolio_trigger,
                self._high_value_investment_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.investments")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for investments agent"""
        return [
            "Você é o especialista em investimentos do PagBank",
            "",
            "⚠️ COMPLIANCE OBRIGATÓRIO:",
            "- SEMPRE adicione aviso de que não é recomendação",
            "- SEMPRE mencione que rentabilidade passada não garante futuro",
            "- SEMPRE explique proteção FGC quando aplicável",
            "",
            "SUAS RESPONSABILIDADES:",
            "- CDB (taxas, prazos, liquidez)",
            "- Poupança PagBank",
            "- Comparação entre produtos",
            "- Explicar rendimentos e impostos",
            "- Detectar e alertar sobre fraudes de investimento",
            "",
            "PRODUTOS DISPONÍVEIS:",
            "- CDB com liquidez diária (resgate imediato)",
            "- CDB com prazo fixo (maior rentabilidade)",
            "- Poupança PagBank (rendimento diário)",
            "",
            "REGRAS DE ATENDIMENTO:",
            "1. Responda em português brasileiro simples",
            "2. Máximo 3-4 frases + disclaimer obrigatório",
            "3. Evite jargões financeiros complexos",
            "4. SEMPRE busque taxas atualizadas na base",
            "",
            "ALERTA DE FRAUDE:",
            "- Se detectar promessas irreais, ALERTE",
            "- Oriente sobre investimentos apenas do PagBank",
            "- Reforce canais oficiais",
            "",
            "Se a pergunta for vaga, faça UMA pergunta clarificadora."
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process investment queries with compliance"""
        # Check for fraud patterns first
        fraud_check = self.compliance.check_fraud_patterns(query)
        
        if fraud_check["risk_level"] == "high":
            self.logger.warning(
                f"High-risk investment query from user {user_id}: {fraud_check['fraud_indicators']}"
            )
            
            return AgentResponse(
                content=(
                    "🚨 ALERTA: Cuidado com promessas de ganhos garantidos ou retornos irreais! "
                    "O PagBank oferece apenas CDB e Poupança com proteção FGC. "
                    "Invista apenas pelos canais oficiais do app PagBank."
                ),
                agent_name=self.agent_name,
                confidence=1.0,
                references=["investment_fraud_prevention"],
                suggested_actions=["report_suspicious_offer", "view_official_investments"],
                language=language
            )
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Apply compliance rules to response
        response.content = self.compliance.apply_compliance(response.content)
        
        # Add investment-specific actions
        query_lower = query.lower()
        
        if "cdb" in query_lower:
            response.suggested_actions.append("simulate_cdb_investment")
        elif "poupança" in query_lower:
            response.suggested_actions.append("open_savings_account")
        elif "rendimento" in query_lower or "rentabilidade" in query_lower:
            response.suggested_actions.append("compare_investment_rates")
        
        return response
    
    def _fraud_investment_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate potential investment fraud"""
        fraud_check = self.compliance.check_fraud_patterns(query)
        return fraud_check["risk_level"] in ["high", "medium"]
    
    def _complex_portfolio_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate complex portfolio questions"""
        complex_keywords = [
            "diversificação", "carteira", "portfolio",
            "alocação", "estratégia", "perfil de risco"
        ]
        return any(keyword in query.lower() for keyword in complex_keywords)
    
    def _high_value_investment_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate high-value investment requests"""
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 250000:  # Above FGC protection limit
                    return True
            except:
                pass
        
        return False