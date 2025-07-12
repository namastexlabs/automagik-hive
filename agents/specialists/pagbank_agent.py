"""
PagBank Specialist Agent for PagBank Multi-Agent System
Handles digital account, PIX, transfers, and banking services
"""

import logging
from typing import Any, Dict, List, Optional

from context.knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from context.memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools
from agents.prompts import get_prompt_manager


class PagBankAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling PagBank digital account services
    Includes PIX, transfers, payroll, mobile top-up, and app issues
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize PagBank specialist agent"""
        super().__init__(
            agent_name="pagbank_specialist",
            agent_role="Especialista em Conta Digital PagBank",
            agent_description="Especialista em PIX, transferências, folha de pagamento e serviços bancários digitais",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"business_unit": "PagBank"},
            tools=get_agent_tools("pagbank_specialist"),
            compliance_rules=[],
            escalation_triggers=[
                self._high_value_transfer_trigger,
                self._security_block_trigger,
                self._payroll_issue_trigger,
                self._app_critical_error_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.pagbank")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for PagBank agent"""
        prompt_manager = get_prompt_manager()
        base_prompt = prompt_manager.get_specialist_prompt("pagbank", "base")
        return [base_prompt]
    
    def _high_value_transfer_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves high value PIX/transfers"""
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 5000:  # R$ 5,000 threshold for transfers
                    return True
            except:
                pass
        
        return False
    
    def _security_block_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if transaction was blocked for security"""
        security_keywords = [
            "bloqueio por segurança", "transação bloqueada", "pix bloqueado",
            "transferência negada", "suspeita de fraude", "conta bloqueada"
        ]
        return any(keyword in query.lower() for keyword in security_keywords)
    
    def _payroll_issue_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves payroll processing issues"""
        payroll_keywords = [
            "folha não processada", "erro na folha", "pagamento não realizado",
            "funcionários não receberam", "folha rejeitada"
        ]
        return any(keyword in query.lower() for keyword in payroll_keywords)
    
    def _app_critical_error_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if app has critical errors affecting operations"""
        critical_keywords = [
            "app não abre", "tela branca", "erro crítico", "perdeu dados",
            "não consigo acessar", "travado", "fechando sozinho"
        ]
        return any(keyword in query.lower() for keyword in critical_keywords)
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process PagBank account queries with specialized logic"""
        # Check for urgent financial operations
        urgent_keywords = ["urgente", "agora", "bloqueado", "não consegue", "erro", "travado"]
        is_urgent = any(keyword in query.lower() for keyword in urgent_keywords)
        
        if is_urgent:
            self.logger.warning(f"URGENT banking operation: {query[:50]}...")
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add PagBank-specific suggested actions
        if "pix" in query.lower():
            response.suggested_actions.append("check_pix_limits")
            response.suggested_actions.append("view_pix_keys")
            if "chave" in query.lower():
                response.suggested_actions.append("register_pix_key")
        elif "transferência" in query.lower() or "ted" in query.lower():
            response.suggested_actions.append("check_transfer_limits")
            response.suggested_actions.append("view_transfer_schedule")
        elif "folha" in query.lower() or "pagamento" in query.lower():
            response.suggested_actions.append("access_payroll_portal")
            response.suggested_actions.append("check_payroll_status")
        elif "aplicativo" in query.lower() or "app" in query.lower():
            response.suggested_actions.append("update_app_version")
            response.suggested_actions.append("clear_app_cache")
        elif "tarifa" in query.lower():
            response.suggested_actions.append("view_fee_schedule")
            response.suggested_actions.append("check_fee_exemption_criteria")
        elif "recarga" in query.lower():
            response.suggested_actions.append("access_mobile_topup")
            response.suggested_actions.append("view_favorite_topups")
        elif "portabilidade" in query.lower():
            response.suggested_actions.append("check_salary_portability_status")
            response.suggested_actions.append("contact_origin_bank")
        
        return response