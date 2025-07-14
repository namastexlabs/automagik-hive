"""
Human Handoff Workflow Implementation
====================================

Agno workflow for escalating customer service to human agents with context preservation,
protocol generation, and WhatsApp notifications using MCP.
"""

import os
import re
from datetime import datetime
from textwrap import dedent
from typing import Dict, Iterator, Optional, Union

from agno.agent import Agent, RunResponseEvent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools.mcp import MCPTools
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow, WorkflowCompletedEvent
from db.session import db_url

from .models import (
    BusinessUnit,
    ConversationContext,
    CustomerEmotion,
    CustomerInfo,
    EscalationAnalysis,
    EscalationProtocol,
    EscalationReason,
    HandoffResult,
    IssueDetails,
    UrgencyLevel,
    WhatsAppNotification
)


class HumanHandoffWorkflow(Workflow):
    """
    Workflow for escalating customer service to human agents.
    
    Handles:
    1. Escalation detection and analysis
    2. Customer information collection
    3. Protocol generation with unique ID
    4. WhatsApp notifications to appropriate teams
    5. Context preservation for human agents
    """
    
    description: str = dedent("""\
    Workflow de escalação para atendimento humano do PagBank.
    
    Detecta necessidade de escalação, coleta contexto completo,
    gera protocolo estruturado e notifica equipes via WhatsApp.
    
    Funcionalidades:
    - Análise inteligente de necessidade de escalação
    - Coleta estruturada de informações do cliente
    - Geração de protocolo com ID único
    - Notificações WhatsApp para equipes especializadas
    - Preservação completa de contexto
    """)
    
    def __init__(self, **kwargs):
        # Extract our custom kwargs before passing to parent
        self.debug_mode = kwargs.pop('debug_mode', False)
        self.whatsapp_enabled = kwargs.pop('whatsapp_enabled', True)
        self.whatsapp_instance = kwargs.pop('whatsapp_instance', 'pagbank_support')
        
        super().__init__(**kwargs)
        
        if self.debug_mode:
            logger.debug("🔧 DEBUG MODE: Human Handoff Workflow initialized")
    
    # Step 1: Escalation Detection Agent
    escalation_detector: Agent = Agent(
        name="Escalation Detector",
        model=Claude(id="claude-sonnet-4-20250514"),
        description=dedent("""\
        Especialista em detecção de necessidade de escalação para humanos.
        Analisa conversas para identificar quando clientes precisam de atendimento humano.
        """),
        instructions=dedent("""\
        Analise a conversa e determine se é necessário escalar para atendimento humano.
        
        CRITÉRIOS DE ESCALAÇÃO:
        
        🗣️ SOLICITAÇÃO EXPLÍCITA:
        - "quero falar com humano/atendente/pessoa"
        - "me transfere para alguém"
        - "não quero robô"
        - "preciso de supervisor/gerente"
        
        😤 FRUSTRAÇÃO DETECTADA:
        - Xingamentos ou linguagem ofensiva
        - CAPS LOCK excessivo (>70% maiúsculas)
        - Repetição da mesma reclamação
        - Demonstração clara de raiva
        
        🔧 COMPLEXIDADE TÉCNICA:
        - Problemas que envolvem múltiplos sistemas
        - Questões de segurança ou fraude
        - Disputas ou chargebacks
        - Investigações necessárias
        
        💰 ALTO VALOR:
        - Transações ou perdas > R$ 10.000
        - Contas empresariais importantes
        - Questões que impactam receita
        
        🔄 MÚLTIPLAS TENTATIVAS:
        - Cliente já tentou resolver várias vezes
        - Problema persistente sem solução
        - Histórico de escalações anteriores
        
        🚫 LIMITAÇÃO DO SISTEMA:
        - Problema fora do escopo dos especialistas IA
        - Necessita aprovação manual
        - Requer acesso a sistemas restritos
        
        INSTRUÇÕES:
        - Analise o contexto completo da conversa
        - Identifique o motivo principal da escalação
        - Avalie o nível de urgência (low/medium/high/critical)
        - Detecte o estado emocional do cliente
        - Justifique sua decisão com evidências específicas
        - Seja conservador - prefira escalar quando em dúvida
        """),
        response_model=EscalationAnalysis,
        structured_outputs=True
    )
    
    # Step 2: Customer Information Collector
    info_collector: Agent = Agent(
        name="Customer Info Collector",
        model=Claude(id="claude-sonnet-4-20250514"),
        description=dedent("""\
        Especialista em extração de informações do cliente para escalação.
        Coleta dados essenciais para o protocolo de atendimento humano.
        """),
        instructions=dedent("""\
        Extraia e organize as informações do cliente da conversa.
        
        INFORMAÇÕES ESSENCIAIS:
        - Nome completo do cliente
        - CPF (se mencionado)
        - Telefone de contato
        - Email (se disponível)
        - Tipo de conta/produto PagBank
        
        INSTRUÇÕES:
        - Extraia apenas informações explicitamente mencionadas
        - NÃO invente ou assuma dados não fornecidos
        - Se informação crítica estiver faltando, marque como None
        - Mantenha formatação original (ex: CPF com pontos/traços)
        - Seja preciso - essas informações serão usadas pelo atendente
        
        EXEMPLO DE EXTRAÇÃO:
        Cliente: "Meu nome é João Silva, CPF 123.456.789-00"
        → customer_name: "João Silva", customer_cpf: "123.456.789-00"
        """),
        response_model=CustomerInfo,
        structured_outputs=True
    )
    
    # Step 3: Issue Details Analyzer
    issue_analyzer: Agent = Agent(
        name="Issue Details Analyzer", 
        model=Claude(id="claude-sonnet-4-20250514"),
        description=dedent("""\
        Especialista em análise e estruturação de problemas para escalação.
        Organiza detalhes do problema para transferência efetiva.
        """),
        instructions=dedent("""\
        Analise e estruture os detalhes do problema para o atendente humano.
        
        ANÁLISE OBRIGATÓRIA:
        
        📝 DESCRIÇÃO DO PROBLEMA:
        - Resuma o problema principal em 2-3 frases claras
        - Inclua sintomas específicos mencionados
        - Destaque impactos mencionados pelo cliente
        
        🏢 UNIDADE DE NEGÓCIO:
        - adquirencia: máquinas, antecipação, vendas
        - emissao: cartões, limites, faturas
        - pagbank: conta, PIX, app, transferências
        - general: fraude, segurança, disputas
        
        🔄 TENTATIVAS ANTERIORES:
        - Soluções já tentadas pelo cliente
        - Canais já utilizados (app, site, chat)
        - Resultados das tentativas anteriores
        
        💰 VALOR ENVOLVIDO:
        - Montante financeiro se mencionado
        - Impacto econômico do problema
        
        📋 RESUMO DA CONVERSA:
        - Pontos-chave da interação
        - Evolução do problema na conversa
        - Contexto importante para o atendente
        
        🎯 AÇÃO RECOMENDADA:
        - Próximos passos sugeridos
        - Verificações que o atendente deve fazer
        - Soluções potenciais para investigar
        
        INSTRUÇÕES:
        - Seja objetivo e específico
        - Use linguagem profissional para atendentes
        - Inclua todos os detalhes relevantes
        - Priorize informações que economizam tempo do atendente
        """),
        response_model=IssueDetails,
        structured_outputs=True
    )
    
    async def run(  # type: ignore
        self,
        conversation_context: ConversationContext,
        escalation_trigger: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Iterator[Union[WorkflowCompletedEvent, RunResponseEvent]]:
        """
        Execute the complete human handoff workflow
        
        Args:
            conversation_context: Complete conversation context
            escalation_trigger: Optional specific trigger that initiated escalation
            metadata: Additional context metadata
        """
        
        logger.info(f"Starting human handoff workflow for session {conversation_context.session_id}")
        
        if self.run_id is None:
            raise ValueError("Run ID is not set")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze if escalation is truly needed
            logger.info("Step 1: Analyzing escalation necessity...")
            escalation_response: RunResponse = self.escalation_detector.run(
                f"Conversa para análise de escalação:\n\n{conversation_context.conversation_history}\n\n"
                f"Trigger específico: {escalation_trigger or 'Não especificado'}"
            )
            
            if not escalation_response.content or not isinstance(escalation_response.content, EscalationAnalysis):
                raise ValueError("Invalid escalation analysis response")
            
            escalation_analysis = escalation_response.content
            logger.info(f"Escalation analysis: {escalation_analysis.should_escalate} - {escalation_analysis.escalation_reason}")
            
            # If escalation is not needed, return early
            if not escalation_analysis.should_escalate:
                logger.info("Escalation not required based on analysis")
                yield WorkflowCompletedEvent(
                    run_id=self.run_id,
                    content={
                        "status": "no_escalation_needed",
                        "analysis": escalation_analysis.model_dump(),
                        "message": "Escalação desnecessária baseada na análise do contexto"
                    }
                )
                return
            
            # Step 2: Collect customer information
            logger.info("Step 2: Collecting customer information...")
            info_response: RunResponse = self.info_collector.run(
                f"Conversa para extração de informações:\n\n{conversation_context.conversation_history}"
            )
            
            if not info_response.content or not isinstance(info_response.content, CustomerInfo):
                raise ValueError("Invalid customer info response")
            
            customer_info = info_response.content
            logger.info(f"Customer info collected: {customer_info.customer_name or 'Nome não fornecido'}")
            
            # Step 3: Analyze issue details
            logger.info("Step 3: Analyzing issue details...")
            issue_response: RunResponse = self.issue_analyzer.run(
                f"Conversa para análise do problema:\n\n{conversation_context.conversation_history}"
            )
            
            if not issue_response.content or not isinstance(issue_response.content, IssueDetails):
                raise ValueError("Invalid issue details response")
            
            issue_details = issue_response.content
            logger.info(f"Issue analyzed: {issue_details.business_unit} - {issue_details.issue_description[:100]}...")
            
            # Step 4: Generate escalation protocol
            logger.info("Step 4: Generating escalation protocol...")
            protocol_id = f"ESC-{conversation_context.session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            escalation_protocol = EscalationProtocol(
                protocol_id=protocol_id,
                escalation_analysis=escalation_analysis,
                customer_info=customer_info,
                issue_details=issue_details,
                assigned_team=issue_details.business_unit
            )
            
            # Step 5: Send WhatsApp notification if enabled
            notification_sent = False
            notification_details = None
            
            if self.whatsapp_enabled:
                logger.info("Step 5: Sending WhatsApp notification...")
                try:
                    notification_result = await self._send_whatsapp_notification(escalation_protocol)
                    notification_sent = notification_result["success"]
                    notification_details = notification_result.get("details")
                    logger.info(f"WhatsApp notification sent: {notification_sent}")
                except Exception as e:
                    logger.error(f"WhatsApp notification failed: {str(e)}")
                    # Continue workflow even if notification fails
            
            # Step 6: Create final handoff result
            handoff_result = HandoffResult(
                protocol=escalation_protocol,
                notification_sent=notification_sent,
                notification_details=notification_details,
                success=True
            )
            
            # Save to session state
            self._save_handoff_result(handoff_result)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Human handoff completed: Protocol {protocol_id}, Duration: {duration:.2f}s")
            
            # Yield completion event
            yield WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "status": "completed",
                    "protocol": escalation_protocol.model_dump(),
                    "handoff_result": handoff_result.model_dump(),
                    "duration_seconds": duration,
                    "notification_sent": notification_sent
                }
            )
            
        except Exception as e:
            logger.error(f"Human handoff workflow failed: {str(e)}")
            yield WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "status": "failed",
                    "error": str(e),
                    "partial_results": {}
                }
            )
    
    async def _send_whatsapp_notification(self, protocol: EscalationProtocol) -> Dict:
        """Send WhatsApp notification using MCP tools"""
        
        try:
            # Get target phone number based on business unit
            team_phones = {
                BusinessUnit.ADQUIRENCIA: "+5511999999001",
                BusinessUnit.EMISSAO: "+5511999999002", 
                BusinessUnit.PAGBANK: "+5511999999003",
                BusinessUnit.GENERAL: "+5511999999000"  # Supervisor
            }
            
            target_phone = team_phones.get(protocol.assigned_team, team_phones[BusinessUnit.GENERAL])
            
            # Format notification message
            message = self._format_notification_message(protocol)
            
            # Create WhatsApp notification object
            notification = WhatsAppNotification(
                instance=self.whatsapp_instance,
                target_number=target_phone,
                message=message,
                priority=protocol.escalation_analysis.urgency_level,
                protocol_id=protocol.protocol_id
            )
            
            # Send via MCP WhatsApp tools
            # Use the MCP tool function directly
            # This requires the mcp__send_whatsapp_message server to be available
            
            # For proper integration, we'll create a specialized notification agent
            # with MCP tools configured
            result = await self._send_via_mcp_agent(message, target_phone)
            
            if result.get("success", False):
                logger.info(f"📱 WhatsApp notification sent to {target_phone}")
                return {
                    "success": True,
                    "details": notification,
                    "message": "Notification sent successfully",
                    "mcp_result": result
                }
            else:
                logger.error(f"📱 WhatsApp notification failed: {result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": result.get("error", "MCP call failed"),
                    "mcp_result": result
                }
            
        except ImportError as e:
            logger.error(f"MCP WhatsApp tools not available: {str(e)}")
            return {
                "success": False,
                "error": f"MCP tools not available: {str(e)}"
            }
        except Exception as e:
            logger.error(f"WhatsApp notification error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_notification_message(self, protocol: EscalationProtocol) -> str:
        """Format WhatsApp notification message"""
        
        urgency_emoji = {
            UrgencyLevel.LOW: "🟢",
            UrgencyLevel.MEDIUM: "🟡", 
            UrgencyLevel.HIGH: "🟠",
            UrgencyLevel.CRITICAL: "🔴"
        }
        
        emoji = urgency_emoji.get(protocol.escalation_analysis.urgency_level, "⚪")
        
        return dedent(f"""\
        🚨 *Escalação para Atendimento Humano* {emoji}
        
        📋 *Protocolo:* {protocol.protocol_id}
        👤 *Cliente:* {protocol.customer_info.customer_name or 'Não informado'}
        📱 *CPF:* {protocol.customer_info.customer_cpf or 'Não informado'}
        ⚠️ *Motivo:* {protocol.escalation_analysis.escalation_reason.value}
        🎯 *Urgência:* {protocol.escalation_analysis.urgency_level.value.upper()}
        🕐 *Horário:* {protocol.timestamp.strftime('%d/%m/%Y %H:%M')}
        
        📝 *Descrição:*
        {protocol.issue_details.issue_description}
        
        💬 *Resumo da Conversa:*
        {protocol.issue_details.conversation_summary}
        
        🎯 *Ação Recomendada:*
        {protocol.issue_details.recommended_action}
        
        📊 *Confiança na Escalação:* {protocol.escalation_analysis.confidence:.1%}
        """).strip()
    
    def _save_handoff_result(self, result: HandoffResult):
        """Save handoff result to session state"""
        if not hasattr(self, 'session_state'):
            self.session_state = {}
        
        self.session_state.setdefault('handoff_results', [])
        self.session_state['handoff_results'].append(result.model_dump())
        
        logger.info(f"Saved handoff result: Protocol {result.protocol.protocol_id}")
    
    async def _send_via_mcp_agent(self, message: str, target_phone: str) -> Dict:
        """Send WhatsApp message via dedicated MCP WhatsApp agent"""
        try:
            # Import the WhatsApp notifier agent
            from agents.whatsapp_notifier.agent import get_whatsapp_notifier
            
            # Get the WhatsApp notifier agent
            notifier = await get_whatsapp_notifier(self.whatsapp_instance)
            
            # Send the message using the MCP-enabled agent
            result = await notifier.send_message(
                message=message,
                number=target_phone if not os.getenv("EVOLUTION_API_FIXED_RECIPIENT") else None
            )
            
            logger.info(f"📱 MCP WhatsApp via agent: {result.get('success', False)}")
            return result
                
        except ImportError as e:
            logger.error(f"WhatsApp notifier agent not available: {str(e)}")
            return {
                "success": False,
                "error": f"WhatsApp agent import failed: {str(e)}",
                "method": "mcp_agent_import"
            }
        except Exception as e:
            logger.error(f"MCP WhatsApp agent send failed: {str(e)}")
            return {
                "success": False,
                "error": f"MCP agent error: {str(e)}",
                "method": "mcp_agent"
            }
    
    def _test_mcp_availability(self) -> bool:
        """Test if MCP WhatsApp tools are available"""
        try:
            # Check environment variables for MCP WhatsApp
            required_vars = [
                "EVOLUTION_API_BASE_URL",
                "EVOLUTION_API_API_KEY", 
                "EVOLUTION_API_INSTANCE"
            ]
            
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.warning(f"MCP WhatsApp missing env vars: {missing_vars}")
                return False
            
            # TODO: Add actual MCP server connectivity test
            logger.info("✅ MCP WhatsApp environment variables configured")
            return True
            
        except Exception as e:
            logger.error(f"MCP availability test failed: {str(e)}")
            return False


def get_human_handoff_workflow(
    debug_mode: bool = False,
    whatsapp_enabled: bool = True,
    whatsapp_instance: str = "pagbank_support"
) -> HumanHandoffWorkflow:
    """Factory function to create a configured human handoff workflow"""
    
    logger.info(f"Creating human handoff workflow (WhatsApp: {whatsapp_enabled})")
    
    return HumanHandoffWorkflow(
        workflow_id="human-handoff",
        storage=PostgresStorage(
            table_name="human_handoff_workflows",
            db_url=db_url,
            mode="workflow",
            auto_upgrade_schema=True,
        ),
        debug_mode=debug_mode,
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_instance=whatsapp_instance
    )