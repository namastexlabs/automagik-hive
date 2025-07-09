"""
Digital Account Specialist Agent for PagBank Multi-Agent System
Simplified from DigitalAccountTeam - single agent handling all digital account queries
"""

import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools


class DigitalAccountAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling digital account queries
    Includes PIX, transfers, payments, and account management
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Digital Account specialist agent"""
        super().__init__(
            agent_name="digital_account_specialist",
            agent_role="Especialista em Conta Digital e PIX do PagBank",
            agent_description="Especialista em conta digital, PIX, transferências e pagamentos",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "conta_digital"},
            tools=get_agent_tools("digital_account_specialist"),
            compliance_rules=[],
            escalation_triggers=[
                self._pix_error_escalation_trigger,
                self._account_blocked_escalation_trigger,
                self._high_value_transfer_escalation_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.digital_account")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for digital account agent"""
        return [
            "Você é o especialista em conta digital e PIX do PagBank",
            "",
            "SUAS RESPONSABILIDADES:",
            "- PIX (cadastro, limites, transferências, QR Code)",
            "- Transferências (TED, DOC, entre contas PagBank)",
            "- Pagamentos de contas e boletos",
            "- Saques e depósitos",
            "- Abertura e manutenção de contas",
            "- Extratos e comprovantes",
            "",
            "INFORMAÇÕES IMPORTANTES DO PIX:",
            "- PIX é GRATUITO e ILIMITADO no PagBank",
            "- Limite padrão: R$ 20.000 por dia",
            "- Disponível 24/7",
            "- Transferência instantânea",
            "",
            "REGRAS DE ATENDIMENTO:",
            "1. Responda SEMPRE em português brasileiro",
            "2. Limite suas respostas a 3-4 frases no máximo",
            "3. Seja direto e objetivo",
            "4. SEMPRE busque limites atualizados na base de conhecimento",
            "",
            "FLUXO PARA PROBLEMAS COMUNS:",
            "- PIX bloqueado: Verifique limite diário, chave válida, dados do destinatário",
            "- Transferência não processada: Confirme saldo, horário e tipo de transferência",
            "- Conta bloqueada: Oriente a contatar suporte pelo app",
            "",
            "HORÁRIOS IMPORTANTES:",
            "- PIX: 24 horas, todos os dias",
            "- TED: Dias úteis até 17h",
            "- DOC: Dias úteis até 22h",
            "",
            "Se a pergunta for vaga, faça UMA pergunta clarificadora e pare."
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process digital account queries with specialized logic"""
        # Check current time for transfer availability
        current_time = datetime.now().time()
        is_business_hours = time(9, 0) <= current_time <= time(17, 0)
        is_weekend = datetime.now().weekday() >= 5
        
        # Add time context
        if context is None:
            context = {}
        context["is_business_hours"] = is_business_hours
        context["is_weekend"] = is_weekend
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add digital account-specific suggested actions
        query_lower = query.lower()
        
        if "pix" in query_lower:
            response.suggested_actions.append("check_pix_keys_in_app")
            if "limite" in query_lower:
                response.suggested_actions.append("view_pix_limits")
        elif "transferência" in query_lower or "ted" in query_lower or "doc" in query_lower:
            if not is_business_hours or is_weekend:
                response.suggested_actions.append("use_pix_for_instant_transfer")
        elif "extrato" in query_lower:
            response.suggested_actions.append("download_statement_in_app")
        elif "saldo" in query_lower:
            response.suggested_actions.append("check_balance_in_app")
        
        return response
    
    def _pix_error_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if PIX error needs escalation"""
        pix_error_keywords = [
            "pix falhou", "erro no pix", "pix não foi",
            "pix devolvido", "pix estornado", "pix sumiu"
        ]
        return any(keyword in query.lower() for keyword in pix_error_keywords)
    
    def _account_blocked_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if account is blocked and needs escalation"""
        blocked_keywords = [
            "conta bloqueada", "bloquearam minha conta",
            "não consigo acessar", "senha bloqueada",
            "conta suspensa", "conta travada"
        ]
        return any(keyword in query.lower() for keyword in blocked_keywords)
    
    def _high_value_transfer_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if high-value transfer needs special attention"""
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 20000:  # Above PIX daily limit
                    return True
            except:
                pass
        
        return False