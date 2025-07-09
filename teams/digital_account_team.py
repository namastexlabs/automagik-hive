"""
Digital Account Specialist Team for PagBank Multi-Agent System
Agent F: Specialist Teams Implementation
Handles all digital account and PIX-related queries using Claude Opus 4
"""

import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from memory.memory_manager import MemoryManager

# Import base team and configurations
from .base_team import SpecialistTeam, TeamResponse
from .team_config import TeamConfigManager
from .team_prompts import TeamPrompts
from .team_tools import get_team_tools, pagbank_validator

# Import shared resources



class DigitalAccountTeam(SpecialistTeam):
    """
    Specialized team for handling digital account queries
    Includes PIX, transfers, payments, and account management
    """
    
    def __init__(
        self,
        knowledge_base: PagBankCSVKnowledgeBase,
        memory_manager: MemoryManager
    ):
        """Initialize Digital Account specialist team"""
        # Get team configuration
        config = TeamConfigManager.get_team_config("conta_digital")
        
        # Initialize with base team
        super().__init__(
            team_name="conta_digital",
            team_role=config.team_role,
            team_description=config.team_description,
            knowledge_base=knowledge_base,
            memory_manager=memory_manager,
            knowledge_filters=config.knowledge_filters,
            max_agents=config.max_agents,
            specialist_tools=get_team_tools("conta_digital"),
            compliance_rules=config.compliance_rules,
            escalation_triggers=[
                self._pix_error_escalation_trigger,
                self._account_blocked_escalation_trigger,
                self._high_value_transfer_escalation_trigger
            ]
        )
        
        self.logger = logging.getLogger("pagbank.teams.digital_account")
        self.special_features = config.special_features
    
    def _create_team_members(self) -> List[Agent]:
        """Create specialized agents for digital account team"""
        members = []
        model = Claude(id="claude-sonnet-4-20250514", max_tokens=500)
        
        # PIX Specialist
        pix_specialist = Agent(
            name="PIX_Transfer_Specialist",
            role="Especialista em PIX e transferências instantâneas",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                "Especialista em PIX - busque sempre limites atualizados no knowledge base",
                "PIX bloqueado? Verifique: limite diário (R$ 20k), chave válida, dados destinatário",
                "Destaque: PIX é GRATUITO e ILIMITADO no PagBank",
                "Para QR Code: explique diferença entre estático e dinâmico se perguntado"
            ],
            add_datetime_to_instructions=True
        )
        members.append(pix_specialist)
        
        # Account Operations Manager
        account_manager = Agent(
            name="Account_Operations_Manager",
            role="Gerente de operações de conta digital",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                "Gerente de conta digital - sempre destaque: rende 100% CDI automaticamente",
                "Conta GRATUITA, sem tarifas de manutenção",
                "Para lojistas: antecipação de vendas 1x/dia (Cielo, Rede, Stone, Getnet, SafraPay)",
                "Busque no knowledge: portabilidade, cashback em recargas"
            ]
        )
        members.append(account_manager)
        
        # Payment Processing Expert
        payment_expert = Agent(
            name="Payment_Processing_Expert",
            role="Especialista em pagamentos e cobranças",
            model=model,
            instructions=[
                TeamPrompts.BASE_INSTRUCTIONS,
                "Especialista em pagamentos - valide sempre códigos de barras",
                "Horários: TED até 17h30, boletos até 22h",
                "Busque cashback atual para recargas no knowledge base",
                "Para agendamentos: explique configuração se solicitado"
            ]
        )
        members.append(payment_expert)
        
        return members
    
    def _get_team_instructions(self) -> List[str]:
        """Get specialized coordination instructions for digital account team"""
        base_instructions = TeamPrompts.COORDINATION_INSTRUCTIONS.get("conta_digital", [])
        
        return [
            "Você coordena o time de conta digital PagBank",
            "DESTAQUE: Conta rende 100% CDI automaticamente",
            "PRIORIZE: PIX com erro e transferências não recebidas",
            *base_instructions,
            "PIX é gratuito e ilimitado - sempre mencione isso",
            "Para portabilidade, explique benefícios completos",
            "Use linguagem simples para operações complexas",
            "Sempre confirme horários para TED/DOC",
            "ANTECIPAÇÃO: Lojistas podem antecipar vendas do crédito",
            "Antecipação multiadquirente: Cielo, Rede, Stone, Getnet, SafraPay",
            "Limite: 1 antecipação por dia, valor em 1-2 horas",
            "Explique FIDC/Oliveira Trust se questionado sobre comprometimento"
        ]
    
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> TeamResponse:
        """Process digital account query with enhanced features"""
        try:
            # Detect query type for specialized handling
            query_type = self._detect_query_type(query)
            
            # Add query type to context
            enhanced_context = context or {}
            enhanced_context['query_type'] = query_type
            enhanced_context['specialist_features'] = self.special_features
            
            # Check operation hours for certain services
            operation_status = self._check_operation_hours(query_type)
            enhanced_context['operation_status'] = operation_status
            
            # For urgent PIX issues, add priority
            if query_type in ['pix_erro', 'transferencia_nao_recebida']:
                enhanced_context['priority'] = 'high'
                enhanced_context['requires_verification'] = True
            
            # Process with base team
            response = super().process_query(
                query=query,
                user_id=user_id,
                session_id=session_id,
                context=enhanced_context,
                language=language
            )
            
            # Apply account-specific enhancements
            response = self._enhance_response(response, query_type, enhanced_context)
            
            # Check for escalation
            if self.should_escalate(query, response):
                response.suggested_actions.append("escalate_to_supervisor")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing account query: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), language)
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of account query"""
        query_lower = query.lower()
        
        # PIX related
        if any(word in query_lower for word in ['pix', 'chave pix', 'qr code']):
            if any(word in query_lower for word in ['erro', 'não chegou', 'voltou']):
                return 'pix_erro'
            elif any(word in query_lower for word in ['cadastrar', 'criar chave']):
                return 'pix_cadastro'
            elif any(word in query_lower for word in ['limite', 'máximo pix']):
                return 'pix_limite'
            else:
                return 'pix_geral'
        
        # Transfers
        elif any(word in query_lower for word in ['transferência', 'transferencia', 'ted', 'doc']):
            if 'não' in query_lower and 'receb' in query_lower:
                return 'transferencia_nao_recebida'
            else:
                return 'transferencia'
        
        # Account features
        elif any(word in query_lower for word in ['saldo', 'extrato', 'comprovante']):
            return 'consulta_conta'
        elif any(word in query_lower for word in ['portabilidade', 'salário', 'salario']):
            return 'portabilidade'
        elif any(word in query_lower for word in ['pagamento', 'boleto', 'conta de']):
            return 'pagamento'
        elif any(word in query_lower for word in ['recarga', 'celular', 'crédito']):
            return 'recarga'
        elif any(word in query_lower for word in ['rendimento', 'cdi', 'render']):
            return 'rendimento'
        elif any(word in query_lower for word in ['bloqueada', 'suspensa', 'congelada']):
            return 'conta_bloqueada'
        else:
            return 'geral'
    
    def _check_operation_hours(self, query_type: str) -> Dict[str, Any]:
        """Check if operation is available based on current time"""
        current_time = datetime.now().time()
        
        # PIX is 24/7
        if 'pix' in query_type:
            return {
                'available': True,
                'service': 'PIX',
                'message': 'PIX disponível 24 horas por dia, 7 dias por semana'
            }
        
        # TED/DOC have business hours
        elif query_type == 'transferencia':
            business_hours = time(6, 0) <= current_time <= time(17, 30)
            return {
                'available': business_hours,
                'service': 'TED/DOC',
                'message': 'TED/DOC disponível das 6h às 17h30 em dias úteis' if not business_hours else 'Serviço disponível'
            }
        
        # Other services are 24/7
        return {
            'available': True,
            'service': 'Conta Digital',
            'message': 'Serviço disponível'
        }
    
    def _enhance_response(
        self,
        response: TeamResponse,
        query_type: str,
        context: Dict[str, Any]
    ) -> TeamResponse:
        """Enhance response based on query type"""
        
        # Add operation hours info if relevant
        operation_status = context.get('operation_status', {})
        if not operation_status.get('available', True):
            response.content = f"⏰ **Atenção:** {operation_status['message']}\n\n{response.content}"
        
        # Enhance based on query type
        if query_type == 'pix_erro':
            response.content = f"🔍 **Verificando sua transferência PIX**\n\n{response.content}"
            response.suggested_actions = [
                "verify_pix_key",
                "check_transaction_status",
                "request_receipt",
                "contact_recipient_bank"
            ]
        
        elif query_type == 'portabilidade':
            if '100% cdi' not in response.content.lower():
                response.content += "\n\n💰 **Vantagem:** Seu salário rende 100% do CDI automaticamente na conta PagBank!"
            response.suggested_actions.append("start_salary_portability")
        
        elif query_type == 'rendimento':
            response.content += "\n\n📈 **Rendimento Automático:**"
            response.content += "\n• Seu dinheiro rende 100% CDI todos os dias"
            response.content += "\n• Sem necessidade de aplicação mínima"
            response.content += "\n• Liquidez diária - use quando quiser"
            response.content += "\n• Sem IOF ou taxas"
        
        elif query_type == 'recarga':
            response.content += "\n\n🎁 **Cashback:** Ganhe dinheiro de volta nas suas recargas!"
        
        elif query_type in ['pix_cadastro', 'pix_geral']:
            # Always mention PIX is free
            if 'gratuito' not in response.content.lower():
                response.content += "\n\n✅ **PIX no PagBank:** Gratuito e ilimitado!"
        
        # Add suggested actions based on type
        if query_type == 'conta_bloqueada':
            response.suggested_actions = [
                "verify_account_status",
                "check_security_alerts",
                "update_documentation",
                "contact_support"
            ]
        elif query_type == 'pagamento':
            response.suggested_actions.append("schedule_payment")
        
        # Apply compliance if needed
        if query_type in ['pix_erro', 'transferencia_nao_recebida', 'conta_bloqueada']:
            response = self.apply_compliance_rules(response)
        
        return response
    
    def _pix_error_escalation_trigger(self, query: str, response: TeamResponse) -> bool:
        """Check if PIX error needs escalation"""
        error_keywords = ['dinheiro sumiu', 'não devolveram', 'dias sem resposta', 'urgente']
        return any(keyword in query.lower() for keyword in error_keywords)
    
    def _account_blocked_escalation_trigger(self, query: str, response: TeamResponse) -> bool:
        """Check if blocked account needs escalation"""
        return 'conta bloqueada' in query.lower() and response.confidence < 0.8
    
    def _high_value_transfer_escalation_trigger(self, query: str, response: TeamResponse) -> bool:
        """Check if high value transfer needs escalation"""
        import re
        amounts = re.findall(r'R?\$?\s*(\d+\.?\d*)', query)
        for amount in amounts:
            try:
                value = float(amount.replace('.', '').replace(',', '.'))
                if value > 20000:  # Daily PIX limit
                    return True
            except:
                continue
        return False
    
    def apply_compliance_rules(self, response: TeamResponse) -> TeamResponse:
        """Apply account-specific compliance rules"""
        # Add security warnings for sensitive operations
        if any(word in response.content.lower() for word in ['senha', 'token', 'código']):
            warning = TeamPrompts.get_compliance_template(
                "security_warning",
                warning_message="Nunca compartilhe senhas ou códigos de acesso"
            )
            response.content += f"\n\n{warning}"
        
        # Add KYC/AML notices for certain operations
        if 'portabilidade' in response.content.lower():
            response.content += "\n\n📋 **Documentos necessários:**"
            response.content += "\n• Comprovante de vínculo empregatício"
            response.content += "\n• Último contracheque"
            response.content += "\n• Documento de identidade"
        
        # PIX security tips
        if 'pix' in response.content.lower():
            response.content += "\n\n🔒 **Segurança PIX:**"
            response.content += "\n• Sempre confirme os dados do destinatário"
            response.content += "\n• Desconfie de QR Codes suspeitos"
            response.content += "\n• Ative notificações para todas as transações"
        
        return response
    
    def validate_pix_key(self, key: str) -> Dict[str, Any]:
        """Validate PIX key using team tools"""
        result = pagbank_validator("pix_key", key)
        
        if result.is_valid:
            return {
                "valid": True,
                "key_type": result.data.get("pix_key_type", "unknown"),
                "formatted_key": result.data.get("key", key)
            }
        else:
            return {
                "valid": False,
                "errors": result.errors,
                "suggestions": self._get_pix_key_suggestions(key)
            }
    
    def _get_pix_key_suggestions(self, key: str) -> List[str]:
        """Get suggestions for invalid PIX keys"""
        suggestions = []
        
        if '@' not in key and len(key) > 10:
            suggestions.append("Se for CPF, use apenas números (11 dígitos)")
            suggestions.append("Se for CNPJ, use apenas números (14 dígitos)")
        elif '@' in key:
            suggestions.append("Verifique se o email está correto")
        elif len(key) <= 11:
            suggestions.append("Se for telefone, inclua o DDD")
        
        suggestions.append("Chaves aleatórias têm formato UUID")
        return suggestions
    
    def check_account_limits(self, user_id: str, operation: str) -> Dict[str, Any]:
        """Check account limits for operations (mock implementation)"""
        # In real implementation, this would query actual limits
        limits = {
            "pix": {
                "per_transaction": 20000.00,
                "daily": 20000.00,
                "monthly": 40000.00,
                "current_daily_usage": 0.00,
                "current_monthly_usage": 0.00
            },
            "ted": {
                "per_transaction": 100000.00,
                "daily": 100000.00,
                "available_hours": "6:00 - 17:30"
            },
            "bill_payment": {
                "per_transaction": 50000.00,
                "daily": 50000.00
            }
        }
        
        return limits.get(operation, {})


def create_digital_account_team(
    knowledge_base: PagBankCSVKnowledgeBase,
    memory_manager: MemoryManager
) -> DigitalAccountTeam:
    """Factory function to create Digital Account team"""
    return DigitalAccountTeam(knowledge_base, memory_manager)