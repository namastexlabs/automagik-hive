"""
Insurance Specialist Agent for PagBank Multi-Agent System
Simplified from InsuranceTeam - single agent handling all insurance queries
"""

import logging
from typing import Any, Dict, List, Optional

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools


class InsuranceAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling insurance queries
    Includes life, home, health plans, and account protection
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Insurance specialist agent"""
        # Set attributes before calling super()
        self.prize_amount = "R$ 20.000"
        self.health_plan_price = "R$ 24,90"
        
        super().__init__(
            agent_name="insurance_specialist",
            agent_role="Especialista em Seguros e Proteção Familiar do PagBank",
            agent_description="Especialista em seguros de vida, residencial, saúde e proteção de conta",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "seguros"},
            tools=get_agent_tools("insurance_specialist"),
            compliance_rules=[self._apply_insurance_compliance],
            escalation_triggers=[
                self._claim_escalation_trigger,
                self._urgent_health_trigger,
                self._high_value_coverage_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.insurance")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for insurance agent"""
        return [
            "Você é o especialista em seguros e proteção familiar do PagBank",
            "",
            "PRODUTOS DISPONÍVEIS:",
            "- Seguro de vida (proteção familiar)",
            "- Seguro residencial (casa protegida)",
            f"- Plano de saúde ({self.health_plan_price}/mês, sem carência)",
            "- Proteção de conta (contra fraudes)",
            f"- Sorteio mensal de {self.prize_amount} para clientes",
            "",
            "BENEFÍCIOS EXCLUSIVOS:",
            "- Contratação 100% digital pelo app",
            "- Sem burocracia ou exames médicos",
            "- Cobertura imediata (exceto carências legais)",
            "- Preços acessíveis para toda família",
            "",
            "REGRAS DE ATENDIMENTO:",
            "1. Responda SEMPRE em português brasileiro",
            "2. Limite suas respostas a 3-4 frases no máximo",
            "3. Destaque sempre o sorteio mensal",
            "4. Use linguagem simples e acolhedora",
            "5. Enfatize proteção e tranquilidade familiar",
            "",
            "INFORMAÇÕES IMPORTANTES:",
            "- Para sinistros: oriente uso do app ou 0800",
            "- Sempre mencione coberturas incluídas",
            "- Explique processo simples de contratação",
            "- Reforce ausência de burocracia",
            "",
            "COMPLIANCE:",
            "- Não prometa coberturas não incluídas",
            "- Mencione carências quando aplicável",
            "- Oriente leitura completa das condições",
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
        """Process insurance queries with specialized logic"""
        # Check for urgent insurance needs
        urgent_keywords = ["sinistro", "acidente", "morte", "internação", "urgente"]
        is_urgent = any(keyword in query.lower() for keyword in urgent_keywords)
        
        if is_urgent:
            self.logger.warning(f"URGENT insurance query from user {user_id}: {query[:50]}...")
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add insurance-specific suggested actions
        query_lower = query.lower()
        
        if "sinistro" in query_lower or "acionar" in query_lower:
            response.suggested_actions.append("file_insurance_claim")
            response.suggested_actions.append("contact_insurance_support")
        elif "vida" in query_lower:
            response.suggested_actions.append("simulate_life_insurance")
        elif "residencial" in query_lower or "casa" in query_lower:
            response.suggested_actions.append("quote_home_insurance")
        elif "saúde" in query_lower or "plano" in query_lower:
            response.suggested_actions.append("view_health_plan_benefits")
        elif "sorteio" in query_lower:
            response.suggested_actions.append("check_prize_draw_rules")
        
        # Always mention the monthly prize draw in insurance queries
        if self.prize_amount not in response.content and "sorteio" not in response.content:
            response.content += f" Lembre-se: clientes participam do sorteio mensal de {self.prize_amount}!"
        
        return response
    
    def _apply_insurance_compliance(self, response: str) -> str:
        """Apply insurance-specific compliance rules"""
        # Add compliance notice if discussing coverage
        if any(word in response.lower() for word in ["cobertura", "cobre", "protege"]):
            if "condições gerais" not in response.lower():
                response += " Consulte condições gerais no app."
        
        return response
    
    def _claim_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate insurance claims"""
        claim_keywords = ["sinistro", "acionar seguro", "usar seguro", "morte", "acidente grave"]
        return any(keyword in query.lower() for keyword in claim_keywords)
    
    def _urgent_health_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate urgent health situations"""
        health_urgent = ["internação", "cirurgia", "emergência médica", "hospital"]
        return any(keyword in query.lower() for keyword in health_urgent)
    
    def _high_value_coverage_trigger(self, query: str, response: AgentResponse) -> bool:
        """Escalate high-value coverage requests"""
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 100000:  # High-value coverage
                    return True
            except:
                pass
        
        return False