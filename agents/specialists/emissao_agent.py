"""
Emissão Specialist Agent for PagBank Multi-Agent System
Handles all card emission and card-related services
"""

import logging
from typing import Any, Dict, List, Optional

from context.knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from context.memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools
from agents.prompts import get_prompt_manager


class EmissaoAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling card emission and management
    Includes credit, debit, prepaid, and multiple cards
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Emissão specialist agent"""
        super().__init__(
            agent_name="emissao_specialist",
            agent_role="Especialista em Emissão de Cartões",
            agent_description="Especialista em todos os tipos de cartões - crédito, débito, pré-pago e múltiplo",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"business_unit": "Emissão"},
            tools=get_agent_tools("emissao_specialist"),
            compliance_rules=[],
            escalation_triggers=[
                self._fraud_card_trigger,
                self._multiple_card_issues_trigger,
                self._international_transaction_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.emissao")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for emission agent"""
        prompt_manager = get_prompt_manager()
        base_prompt = prompt_manager.get_specialist_prompt("emissao", "base")
        return [base_prompt]
    
    def _fraud_card_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves card fraud"""
        fraud_keywords = [
            "fraude", "clonagem", "roubo", "cartão clonado",
            "transação não reconhecida", "compra que não fiz",
            "cobrança indevida", "cartão roubado"
        ]
        return any(keyword in query.lower() for keyword in fraud_keywords)
    
    def _multiple_card_issues_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if user mentions multiple card problems"""
        issue_keywords = [
            "vários problemas", "múltiplos cartões", "todos os cartões",
            "nenhum cartão funciona", "problema recorrente"
        ]
        return any(keyword in query.lower() for keyword in issue_keywords)
    
    def _international_transaction_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves complex international transactions"""
        intl_keywords = [
            "iof alto", "conversão errada", "taxa cambial",
            "transação internacional bloqueada", "compra no exterior negada"
        ]
        return any(keyword in query.lower() for keyword in intl_keywords)
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process card emission queries with specialized logic"""
        # Check for urgent card operations
        urgent_keywords = ["bloquear", "bloqueio", "perdi", "roubaram", "clonaram", "urgente"]
        is_urgent = any(keyword in query.lower() for keyword in urgent_keywords)
        
        if is_urgent:
            self.logger.warning(f"URGENT card operation requested: {query[:50]}...")
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add card-specific suggested actions
        if "limite" in query.lower():
            response.suggested_actions.append("request_limit_increase")
            response.suggested_actions.append("check_credit_analysis_status")
        elif "fatura" in query.lower():
            response.suggested_actions.append("view_invoice_in_app")
            response.suggested_actions.append("configure_invoice_notifications")
        elif "virtual" in query.lower() or "temporário" in query.lower():
            response.suggested_actions.append("generate_virtual_card")
            response.suggested_actions.append("set_virtual_card_limits")
        elif "internacional" in query.lower():
            response.suggested_actions.append("enable_international_transactions")
            response.suggested_actions.append("check_iof_rates")
        elif "não chegou" in query.lower() or "entrega" in query.lower():
            response.suggested_actions.append("track_card_delivery")
            response.suggested_actions.append("request_new_card_delivery")
        
        return response