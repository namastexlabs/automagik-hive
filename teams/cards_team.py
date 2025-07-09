"""
Cards Specialist Team for PagBank Multi-Agent System
Agent F: Specialist Teams Implementation
Handles all card-related queries using Claude Opus 4
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

# Import base team and configurations
from .base_team import SpecialistTeam, TeamResponse
from .team_config import TeamConfigManager
from .team_prompts import TeamPrompts
from .team_tools import get_team_tools

# Import shared resources



class CardsTeam(SpecialistTeam):
    """
    Specialized team for handling all card-related queries
    Includes credit, debit, prepaid, and virtual cards
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Cards specialist team"""
        # Get team configuration
        config = TeamConfigManager.get_team_config("cartoes")
        
        # Initialize with base team
        super().__init__(
            team_name="cartoes",
            team_role=config.team_role,
            team_description=config.team_description,
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filters=config.knowledge_filters,
            max_agents=config.max_agents,
            specialist_tools=get_team_tools("cartoes"),
            compliance_rules=config.compliance_rules,
            escalation_triggers=[
                self._fraud_escalation_trigger,
                self._high_value_escalation_trigger,
                self._multiple_block_escalation_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.teams.cards")
        self.special_features = config.special_features
    
    def _create_team_members(self) -> List[Agent]:
        """Create specialized agents for cards team"""
        members = []
        model = Claude(id="claude-sonnet-4-20250514")
        
        # Card Operations Specialist
        card_ops = Agent(
            name="Cards_Operations_Specialist",
            role="Especialista em operações de cartão",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                "Você é especialista em operações de cartão do PagBank",
                "Processe solicitações de bloqueio/desbloqueio com urgência",
                "Oriente sobre segunda via, senha, e ativação de cartões",
                "Explique limites e como aumentá-los via CDB",
                "Sempre verifique a segurança antes de realizar operações",
                "Para cartões virtuais, explique geração instantânea no app"
            ],
            add_datetime_to_instructions=True
        )
        members.append(card_ops)
        
        # Card Security Analyst
        security_analyst = Agent(
            name="Cards_Security_Analyst",
            role="Analista de segurança e fraudes em cartões",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                "Você é especialista em segurança de cartões",
                "Analise transações suspeitas e possíveis fraudes",
                "Processe contestações e chargebacks",
                "Oriente sobre medidas de segurança",
                "Em casos de fraude confirmada, bloqueie imediatamente",
                "Sempre registre detalhes para investigação"
            ]
        )
        members.append(security_analyst)
        
        # Card Benefits Advisor
        benefits_advisor = Agent(
            name="Cards_Benefits_Advisor",
            role="Consultor de benefícios e cashback",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                "Você é especialista em benefícios de cartões",
                "Explique programa de cashback e como maximizar ganhos",
                "Oriente sobre carteiras digitais (Apple Pay, Google Pay)",
                "Informe sobre anuidade zero e condições",
                "Destaque vantagens exclusivas PagBank",
                "Para cartão pré-pago, explique taxa de R$ 12,90",
                "PROGRAMAS DE FIDELIDADE:",
                "- Vai de Visa: exclusivo para cartões Visa",
                "- Mastercard Surpreenda: exclusivo para Mastercard",
                "IOF internacional: 3,38% + PTAX+5% na conversão"
            ]
        )
        members.append(benefits_advisor)
        
        return members
    
    def _get_team_instructions(self) -> List[str]:
        """Get specialized coordination instructions for cards team"""
        base_instructions = TeamPrompts.COORDINATION_INSTRUCTIONS.get("cartoes", [])
        
        return [
            "Você coordena o time de especialistas em cartões PagBank",
            "PRIORIZE casos de fraude e bloqueio urgente",
            *base_instructions,
            "Para solicitações de limite, sempre mencione aumento via CDB",
            "Cartões são GRATUITOS (exceto pré-pago: R$ 12,90)",
            "Sempre confirme tipo de cartão: crédito, débito, pré-pago ou virtual",
            "Use linguagem clara adaptada ao nível do cliente",
            "IOF INTERNACIONAL: 3,38% + conversão PTAX+5%",
            "PROGRAMAS: Vai de Visa (só Visa) e Mastercard Surpreenda (só MC)",
            "Limites pré-pago: R$5k pessoal, R$25k vendedor",
            "Sempre diferencie programas por bandeira"
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> TeamResponse:
        """Process card-related query with enhanced features"""
        try:
            # Detect query type for specialized handling
            query_type = self._detect_query_type(query)
            
            # Add query type to context
            enhanced_context = context or {}
            enhanced_context['query_type'] = query_type
            enhanced_context['specialist_features'] = self.special_features
            
            # For urgent cases, add priority flag
            if query_type in ['bloqueio_urgente', 'fraude_suspeita']:
                enhanced_context['priority'] = 'high'
                enhanced_context['requires_immediate_action'] = True
            
            # Process with base team
            response = super().process_query(
                query=query,
                user_id=user_id,
                session_id=session_id,
                context=enhanced_context,
                language=language
            )
            
            # Apply card-specific enhancements
            response = self._enhance_response(response, query_type, enhanced_context)
            
            # Check for escalation
            if self.should_escalate(query, response):
                response.suggested_actions.append("escalate_to_supervisor")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing cards query: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), language)
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of card query"""
        query_lower = query.lower()
        
        # Priority cases
        if any(word in query_lower for word in ['bloqueio', 'bloquear', 'perdi', 'roubaram']):
            return 'bloqueio_urgente'
        elif any(word in query_lower for word in ['fraude', 'não reconheço', 'compra estranha']):
            return 'fraude_suspeita'
        elif any(word in query_lower for word in ['contestar', 'contestação', 'chargeback']):
            return 'contestacao'
        
        # Regular operations
        elif any(word in query_lower for word in ['limite', 'aumentar limite', 'mais limite']):
            return 'limite_credito'
        elif any(word in query_lower for word in ['fatura', 'vencimento', 'pagar fatura']):
            return 'fatura'
        elif any(word in query_lower for word in ['segunda via', '2ª via', 'novo cartão']):
            return 'segunda_via'
        elif any(word in query_lower for word in ['cashback', 'benefício', 'vantagem']):
            return 'beneficios'
        elif any(word in query_lower for word in ['virtual', 'cartão virtual', 'online']):
            return 'cartao_virtual'
        elif any(word in query_lower for word in ['apple pay', 'google pay', 'samsung pay']):
            return 'carteira_digital'
        elif any(word in query_lower for word in ['anuidade', 'taxa', 'custo']):
            return 'taxas'
        else:
            return 'geral'
    
    def _enhance_response(
        self,
        response: TeamResponse,
        query_type: str,
        context: Dict[str, Any]
    ) -> TeamResponse:
        """Enhance response based on query type"""
        
        # Add specific actions based on query type
        if query_type == 'bloqueio_urgente':
            response.content = f"🚨 **AÇÃO IMEDIATA**\n\n{response.content}"
            response.suggested_actions = [
                "block_card_immediately",
                "order_replacement_card",
                "review_recent_transactions"
            ]
        
        elif query_type == 'fraude_suspeita':
            response.suggested_actions = [
                "analyze_transaction_pattern",
                "block_if_confirmed",
                "file_dispute",
                "monitor_account"
            ]
        
        elif query_type == 'limite_credito':
            # Always mention CDB option for limit increase
            if "cdb" not in response.content.lower():
                response.content += "\n\n💡 **Dica:** Você pode aumentar seu limite aplicando em CDB. O valor investido vira reserva para seu cartão!"
        
        elif query_type == 'cartao_virtual':
            response.suggested_actions.append("generate_virtual_card")
        
        # Add compliance warnings if needed
        if query_type in ['fraude_suspeita', 'contestacao']:
            response = self.apply_compliance_rules(response)
        
        return response
    
    def _fraud_escalation_trigger(self, query: str, response: TeamResponse) -> bool:
        """Check if fraud case needs escalation"""
        fraud_keywords = ['fraude confirmada', 'múltiplas transações', 'valor alto']
        return any(keyword in query.lower() for keyword in fraud_keywords)
    
    def _high_value_escalation_trigger(self, query: str, response: TeamResponse) -> bool:
        """Check if high value transaction needs escalation"""
        # Check for amounts above R$ 5,000
        import re
        amounts = re.findall(r'R?\$?\s*(\d+\.?\d*)', query)
        for amount in amounts:
            try:
                value = float(amount.replace('.', '').replace(',', '.'))
                if value > 5000:
                    return True
            except:
                continue
        return False
    
    def _multiple_block_escalation_trigger(self, query: str, response: TeamResponse) -> bool:
        """Check if user has multiple block requests"""
        # This would check user history in real implementation
        # For now, check if query mentions multiple blocks
        return 'várias vezes' in query.lower() or 'sempre bloqueio' in query.lower()
    
    def apply_compliance_rules(self, response: TeamResponse) -> TeamResponse:
        """Apply card-specific compliance rules"""
        # Add security warnings
        if any(word in response.content.lower() for word in ['senha', 'cvv', 'código']):
            warning = TeamPrompts.get_compliance_template(
                "security_warning",
                warning_message="Nunca compartilhe senha, CVV ou códigos do seu cartão"
            )
            response.content += f"\n\n{warning}"
        
        # Add fraud prevention tips
        if 'fraude' in response.content.lower():
            response.content += "\n\n**Dicas de Segurança:**"
            response.content += "\n• Sempre verifique o nome do estabelecimento"
            response.content += "\n• Ative notificações de compras no app"
            response.content += "\n• Use cartão virtual para compras online"
            response.content += "\n• Bloqueie imediatamente em caso de perda"
        
        return response
    
    def get_card_status(self, user_id: str, card_id: Optional[str] = None) -> Dict[str, Any]:
        """Get card status information (mock implementation)"""
        # In real implementation, this would query the actual system
        return {
            "card_id": card_id or "****1234",
            "status": "active",
            "type": "credit",
            "limit": 1500.00,
            "available_limit": 850.00,
            "has_virtual": True,
            "digital_wallets": ["apple_pay", "google_pay"],
            "last_transaction": datetime.now().isoformat()
        }
    
    def validate_card_operation(self, operation: str, card_data: Dict[str, Any]) -> bool:
        """Validate if card operation can be performed"""
        # Security validations
        validations = {
            "block": lambda: card_data.get("status") == "active",
            "unblock": lambda: card_data.get("status") == "blocked",
            "limit_increase": lambda: card_data.get("type") == "credit",
            "virtual_generation": lambda: card_data.get("has_virtual", True)
        }
        
        validator = validations.get(operation)
        return validator() if validator else False


def create_cards_team(
    knowledge_base: PagBankCSVKnowledgeBase,
    memory_manager: MemoryManager
) -> CardsTeam:
    """Factory function to create Cards team"""
    return CardsTeam(knowledge_base, memory_manager)