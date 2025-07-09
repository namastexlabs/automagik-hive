"""
Cards Specialist Agent for PagBank Multi-Agent System
Simplified from CardsTeam - single agent handling all card-related queries
"""

import logging
from typing import Any, Dict, List, Optional

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools
from agents.prompts import get_prompt_manager


class CardsAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling all card-related queries
    Includes credit, debit, prepaid, and virtual cards
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Cards specialist agent"""
        super().__init__(
            agent_name="cards_specialist",
            agent_role="Especialista em Cartões do PagBank",
            agent_description="Especialista em todos os tipos de cartões - crédito, débito, pré-pago e virtual",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"area": "cartoes"},
            tools=get_agent_tools("cards_specialist"),
            compliance_rules=[],
            escalation_triggers=[
                self._fraud_escalation_trigger,
                self._high_value_escalation_trigger,
                self._multiple_block_escalation_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.cards")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for cards agent"""
        prompt_manager = get_prompt_manager()
        base_prompt = prompt_manager.get_specialist_prompt("cards", "base")
        return [base_prompt]
    
    def _fraud_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves fraud and needs escalation"""
        fraud_keywords = [
            "fraude", "clonagem", "roubo", "transação não reconhecida",
            "compra que não fiz", "cobrança indevida", "cartão clonado"
        ]
        return any(keyword in query.lower() for keyword in fraud_keywords)
    
    def _high_value_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves high value transactions"""
        # Look for monetary values above R$ 5,000
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            # Convert Brazilian number format to float
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 5000:
                    return True
            except:
                pass
        
        return False
    
    def _multiple_block_escalation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if user has multiple card blocks in recent history"""
        # This would check memory for patterns, for now return False
        # In real implementation, would check self.memory_manager for patterns
        return False
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process card-related queries with specialized logic"""
        # Check for urgent card operations
        urgent_keywords = ["bloquear", "bloqueio", "perdi", "roubaram", "clonaram"]
        is_urgent = any(keyword in query.lower() for keyword in urgent_keywords)
        
        if is_urgent:
            self.logger.warning(f"URGENT card operation requested: {query[:50]}...")
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add card-specific suggested actions
        if "limite" in query.lower():
            response.suggested_actions.append("check_cdb_investment_for_limit_increase")
        elif "fatura" in query.lower():
            response.suggested_actions.append("view_invoice_in_app")
        elif "virtual" in query.lower():
            response.suggested_actions.append("generate_virtual_card_in_app")
        
        return response