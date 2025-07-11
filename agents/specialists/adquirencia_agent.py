"""
Adquirência Web Specialist Agent for PagBank Multi-Agent System
Handles anticipation of sales and acquiring services
"""

import logging
from typing import Any, Dict, List, Optional

from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

from .base_agent import BaseSpecialistAgent, AgentResponse
from agents.tools.agent_tools import get_agent_tools
from agents.prompts import get_prompt_manager


class AdquirenciaAgent(BaseSpecialistAgent):
    """
    Specialist agent for handling acquiring and sales anticipation queries
    Covers both Web and Presencial acquiring services
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Adquirência specialist agent"""
        super().__init__(
            agent_name="adquirencia_specialist",
            agent_role="Especialista em Adquirência e Antecipação de Vendas",
            agent_description="Especialista em antecipação de vendas do PagBank e multiadquirência",
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filter={"business_unit": "Adquirência Web"},
            tools=get_agent_tools("adquirencia_specialist"),
            compliance_rules=[],
            escalation_triggers=[
                self._high_value_anticipation_trigger,
                self._blocked_anticipation_trigger,
                self._fraud_anticipation_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.agents.adquirencia")
    
    def _get_agent_instructions(self) -> List[str]:
        """Get specialized instructions for adquirência agent"""
        prompt_manager = get_prompt_manager()
        base_prompt = prompt_manager.get_specialist_prompt("adquirencia", "base")
        return [base_prompt]
    
    def _high_value_anticipation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves high value anticipation"""
        import re
        money_pattern = r'R\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(money_pattern, query)
        
        for match in matches:
            value_str = match.replace('.', '').replace(',', '.')
            try:
                value = float(value_str)
                if value > 10000:  # R$ 10,000 threshold for anticipation
                    return True
            except:
                pass
        
        return False
    
    def _blocked_anticipation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if user mentions blocked anticipation multiple times"""
        blocked_keywords = [
            "não consigo antecipar", "antecipação bloqueada", 
            "não aparece opção", "sem elegibilidade", "não elegível"
        ]
        return any(keyword in query.lower() for keyword in blocked_keywords)
    
    def _fraud_anticipation_trigger(self, query: str, response: AgentResponse) -> bool:
        """Check if query involves potential fraud in anticipation"""
        fraud_keywords = [
            "antecipação falsa", "cobrança indevida", "taxa abusiva",
            "não recebi antecipação", "valor errado"
        ]
        return any(keyword in query.lower() for keyword in fraud_keywords)
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> AgentResponse:
        """Process acquiring-related queries with specialized logic"""
        # Check for urgent anticipation needs
        urgent_keywords = ["urgente", "hoje", "agora", "emergência", "imprevisto"]
        is_urgent = any(keyword in query.lower() for keyword in urgent_keywords)
        
        if is_urgent:
            self.logger.warning(f"URGENT anticipation request: {query[:50]}...")
        
        # Process through base implementation
        response = super().process_query(query, user_id, session_id, context, language)
        
        # Add anticipation-specific suggested actions
        if "antecipar" in query.lower() or "antecipação" in query.lower():
            response.suggested_actions.append("check_anticipation_eligibility")
            response.suggested_actions.append("view_available_sales_for_anticipation")
        elif "taxa" in query.lower():
            response.suggested_actions.append("calculate_anticipation_fees")
        elif "multiadquirência" in query.lower():
            response.suggested_actions.append("register_other_acquiring_machines")
        
        return response