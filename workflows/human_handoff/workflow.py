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
from typing import AsyncIterator, Dict, Iterator, Optional, Union

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools.mcp import MCPTools
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow
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
    
    def __init__(self, mcp_tools=None, **kwargs):
        # Extract our custom kwargs before passing to parent
        self.debug_mode = kwargs.pop('debug_mode', False)
        self.whatsapp_enabled = kwargs.pop('whatsapp_enabled', True)
        self.whatsapp_instance = kwargs.pop('whatsapp_instance', 'SofIA')
        self.mcp_tools = mcp_tools  # Store pre-initialized MCP tools
        
        super().__init__(**kwargs)
        
        if self.debug_mode:
            logger.debug("🔧 DEBUG MODE: Human Handoff Workflow initialized")
            if self.mcp_tools:
                logger.debug("📱 MCP WhatsApp tools available")
            else:
                logger.debug("⚠️  No MCP tools provided")
    
    # Step 1: Customer Information Collector
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
    
    def run(  # type: ignore
        self,
        conversation_context: Optional[ConversationContext] = None,
        escalation_trigger: Optional[str] = None,
        metadata: Optional[Dict] = None,
        # Legacy parameters for backward compatibility
        customer_message: Optional[str] = None,
        customer_query: Optional[str] = None,
        conversation_history: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        business_unit: Optional[str] = None,
        urgency_level: Optional[str] = None,
        **kwargs
    ) -> Iterator[RunResponse]:
        """
        Execute the complete human handoff workflow
        
        Args:
            conversation_context: Complete conversation context
            escalation_trigger: Optional specific trigger that initiated escalation
            metadata: Additional context metadata
        """
        
        # Handle legacy parameter format for backward compatibility
        if conversation_context is None:
            # Build ConversationContext from legacy parameters
            customer_msg = customer_message or customer_query or "Customer request for human assistance"
            session_id_value = session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create minimal ConversationContext for legacy calls
            from .models import CustomerInfo, IssueDetails
            
            customer_info = CustomerInfo(
                customer_id=customer_id or "unknown",
                session_id=session_id_value,
                business_unit=business_unit or "general"
            )
            
            issue_details = IssueDetails(
                summary=customer_msg,
                category="escalation_request",
                urgency=urgency_level or "medium",
                conversation_history=conversation_history or ""
            )
            
            conversation_context = ConversationContext(
                session_id=session_id_value,
                customer_info=customer_info,
                issue_details=issue_details,
                conversation_history=conversation_history or "",
                current_message=customer_msg,
                start_time=datetime.now(),
                last_interaction=datetime.now(),
                interaction_count=1
            )
            
            # Map legacy escalation_reason to escalation_trigger
            if escalation_reason and not escalation_trigger:
                escalation_trigger = escalation_reason
        
        logger.info(f"Starting human handoff workflow for session {conversation_context.session_id}")
        
        # Initialize run_id if not set
        if self.run_id is None:
            import uuid
            self.run_id = str(uuid.uuid4())
        
        start_time = datetime.now()
        
        try:
            # Ana team has already decided to escalate - proceed with handoff process
            logger.info("Step 1: Executing human handoff (escalation decision made by Ana)...")
            
            # Create escalation analysis based on provided context
            escalation_analysis = EscalationAnalysis(
                should_escalate=True,
                escalation_reason=EscalationReason.EXPLICIT_REQUEST if not escalation_trigger else EscalationReason.EXPLICIT_REQUEST,
                confidence=1.0,  # Ana made the decision
                urgency_level=UrgencyLevel.HIGH if conversation_context.issue_details.urgency == "high" else UrgencyLevel.MEDIUM,
                customer_emotion=CustomerEmotion.FRUSTRATED,
                reasoning=f"Ana team initiated escalation: {escalation_trigger or 'Human assistance required'}",
                detected_indicators=["ana_team_decision"]
            )
            
            logger.info(f"Proceeding with escalation: {escalation_analysis.escalation_reason}")
            
            # Step 2: Collect customer information  
            logger.info("Step 2: Collecting customer information...")
            info_response: RunResponse = self.info_collector.run(
                f"Conversa para extração de informações:\n\n{conversation_context.conversation_history}"
            )
            
            if not info_response.content:
                raise ValueError("Empty customer info response")
            
            # Handle both structured and unstructured responses
            if isinstance(info_response.content, CustomerInfo):
                customer_info = info_response.content
            else:
                # Create a default customer info for unstructured responses
                customer_info = CustomerInfo(
                    customer_id=conversation_context.customer_id,
                    session_id=conversation_context.session_id,
                    business_unit="general"
                )
            logger.info(f"Customer info collected: {customer_info.customer_name or 'Nome não fornecido'}")
            
            # Step 3: Analyze issue details
            logger.info("Step 3: Analyzing issue details...")
            issue_response: RunResponse = self.issue_analyzer.run(
                f"Conversa para análise do problema:\n\n{conversation_context.conversation_history}"
            )
            
            if not issue_response.content:
                raise ValueError("Empty issue details response")
            
            # Handle both structured and unstructured responses
            if isinstance(issue_response.content, IssueDetails):
                issue_details = issue_response.content
            else:
                # Create a default issue details for unstructured responses
                issue_details = IssueDetails(
                    summary=conversation_context.current_message,
                    conversation_history=conversation_context.conversation_history
                )
            logger.info(f"Issue analyzed: {issue_details.business_unit} - {issue_details.issue_description[:100]}...")
            
            # Step 4: Generate escalation protocol
            logger.info("Step 4: Generating escalation protocol...")
            protocol_id = f"ESC-{conversation_context.session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Determine assigned team based on business unit
            assigned_team = getattr(issue_details.business_unit, 'value', 'general') if issue_details.business_unit else 'general'
            
            escalation_protocol = EscalationProtocol(
                protocol_id=protocol_id,
                escalation_analysis=escalation_analysis,
                customer_info=customer_info,
                issue_details=issue_details,
                assigned_team=assigned_team
            )
            
            # Step 5: Send WhatsApp notification if enabled
            notification_sent = False
            notification_details = None
            
            if self.whatsapp_enabled:
                logger.info("Step 5: Sending WhatsApp notification...")
                try:
                    if self.mcp_tools:
                        logger.warning("🔄 MCP tools available but running in sync mode - notification skipped")
                        logger.info("💡 Use arun() method for proper MCP WhatsApp integration")
                        notification_sent = False
                        notification_details = {"info": "Use arun() for MCP integration"}
                    else:
                        logger.warning("No MCP tools available for WhatsApp notifications")
                        notification_sent = False
                        notification_details = {"error": "No MCP tools"}
                except Exception as e:
                    logger.error(f"WhatsApp notification failed: {str(e)}")
                    notification_sent = False
                    notification_details = {"error": str(e)}
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
            
            # Return final response
            response = RunResponse(
                run_id=self.run_id,
                content=f"""✅ Transferência para atendimento humano concluída com sucesso!

📋 **Protocolo:** {protocol_id}
🎯 **Prioridade:** {escalation_analysis.urgency_level.value.upper()}
⏰ **Tempo de resposta esperado:** 15-30 minutos
📞 **Notificação enviada:** {'Sim' if notification_sent else 'Não'}

Um atendente especializado da equipe {assigned_team} entrará em contato em breve.
Mantenha este protocolo para referência.

🙏 Obrigado pela paciência!"""
            )
            # Add metadata if supported
            if hasattr(response, 'metadata'):
                response.metadata = {
                    "workflow_type": "human_handoff",
                    "protocol_id": protocol_id,
                    "escalation_reason": escalation_analysis.escalation_reason.value,
                    "urgency_level": escalation_analysis.urgency_level.value,
                    "assigned_team": assigned_team,
                    "notification_sent": notification_sent,
                    "duration_seconds": duration
                }
            yield response
            
        except Exception as e:
            logger.error(f"Human handoff workflow failed: {str(e)}")
            error_response = RunResponse(
                run_id=self.run_id,
                content=f"❌ Erro na transferência para atendimento humano: {str(e)}. Por favor, tente novamente ou contate nosso suporte."
            )
            # Add metadata if supported
            if hasattr(error_response, 'metadata'):
                error_response.metadata = {
                    "workflow_type": "human_handoff",
                    "status": "failed",
                    "error": str(e)
                }
            yield error_response
    
    async def arun(  # type: ignore
        self,
        conversation_context: Optional[ConversationContext] = None,
        escalation_trigger: Optional[str] = None,
        metadata: Optional[Dict] = None,
        # Legacy parameters for backward compatibility
        customer_message: Optional[str] = None,
        customer_query: Optional[str] = None,
        conversation_history: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        business_unit: Optional[str] = None,
        urgency_level: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[RunResponse]:
        """
        Execute the complete human handoff workflow asynchronously with proper MCP integration
        
        This async version properly handles MCP WhatsApp tools following Agno best practices.
        Use this method when MCP tools are provided to the workflow.
        """
        
        # Handle legacy parameter format for backward compatibility (same as sync version)
        if conversation_context is None:
            customer_msg = customer_message or customer_query or "Customer request for human assistance"
            session_id_value = session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            from .models import CustomerInfo, IssueDetails
            
            customer_info = CustomerInfo(
                customer_id=customer_id or "unknown",
                session_id=session_id_value,
                business_unit=business_unit or "general"
            )
            
            issue_details = IssueDetails(
                summary=customer_msg,
                category="escalation_request",
                urgency=urgency_level or "medium",
                conversation_history=conversation_history or ""
            )
            
            conversation_context = ConversationContext(
                session_id=session_id_value,
                customer_info=customer_info,
                issue_details=issue_details,
                conversation_history=conversation_history or "",
                current_message=customer_msg,
                start_time=datetime.now(),
                last_interaction=datetime.now(),
                interaction_count=1
            )
            
            if escalation_reason and not escalation_trigger:
                escalation_trigger = escalation_reason
        
        logger.info(f"Starting async human handoff workflow for session {conversation_context.session_id}")
        
        # Initialize run_id if not set (for async workflows)
        if self.run_id is None:
            import uuid
            self.run_id = str(uuid.uuid4())
        
        start_time = datetime.now()
        
        try:
            # Ana team has already decided to escalate - proceed with handoff process
            logger.info("Step 1: Executing human handoff (escalation decision made by Ana)...")
            
            # Create escalation analysis based on provided context
            escalation_analysis = EscalationAnalysis(
                should_escalate=True,
                escalation_reason=EscalationReason.EXPLICIT_REQUEST if not escalation_trigger else EscalationReason.EXPLICIT_REQUEST,
                confidence=1.0,  # Ana made the decision
                urgency_level=UrgencyLevel.HIGH if conversation_context.issue_details.urgency == "high" else UrgencyLevel.MEDIUM,
                customer_emotion=CustomerEmotion.FRUSTRATED,
                reasoning=f"Ana team initiated escalation: {escalation_trigger or 'Human assistance required'}",
                detected_indicators=["ana_team_decision"]
            )
            
            logger.info(f"Proceeding with escalation: {escalation_analysis.escalation_reason}")
            
            # Step 2: Collect customer information (async)
            logger.info("Step 2: Collecting customer information...")
            info_response: RunResponse = await self.info_collector.arun(
                f"Conversa para extração de informações:\n\n{conversation_context.conversation_history}"
            )
            
            if not info_response.content:
                raise ValueError("Empty customer info response")
            
            # Handle both structured and unstructured responses
            if isinstance(info_response.content, CustomerInfo):
                customer_info = info_response.content
            else:
                customer_info = CustomerInfo(
                    customer_id=conversation_context.customer_id,
                    session_id=conversation_context.session_id,
                    business_unit="general"
                )
            logger.info(f"Customer info collected: {customer_info.customer_name or 'Nome não fornecido'}")
            
            # Step 3: Analyze issue details (async)
            logger.info("Step 3: Analyzing issue details...")
            issue_response: RunResponse = await self.issue_analyzer.arun(
                f"Conversa para análise do problema:\n\n{conversation_context.conversation_history}"
            )
            
            if not issue_response.content:
                raise ValueError("Empty issue details response")
            
            # Handle both structured and unstructured responses
            if isinstance(issue_response.content, IssueDetails):
                issue_details = issue_response.content
            else:
                issue_details = IssueDetails(
                    summary=conversation_context.current_message,
                    conversation_history=conversation_context.conversation_history
                )
            logger.info(f"Issue analyzed: {issue_details.business_unit} - {issue_details.issue_description[:100]}...")
            
            # Step 4: Generate escalation protocol
            logger.info("Step 4: Generating escalation protocol...")
            protocol_id = f"ESC-{conversation_context.session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Determine assigned team based on business unit
            assigned_team = getattr(issue_details.business_unit, 'value', 'general') if issue_details.business_unit else 'general'
            
            escalation_protocol = EscalationProtocol(
                protocol_id=protocol_id,
                escalation_analysis=escalation_analysis,
                customer_info=customer_info,
                issue_details=issue_details,
                assigned_team=assigned_team
            )
            
            # Step 5: Send WhatsApp notification if enabled (async)
            notification_sent = False
            notification_details = None
            
            if self.whatsapp_enabled and self.mcp_tools:
                logger.info("Step 5: Sending WhatsApp notification via MCP...")
                try:
                    message = self._format_notification_message(escalation_protocol)
                    notification_result = await self._send_via_mcp_agent_async(message)
                    notification_sent = notification_result["success"]
                    notification_details = notification_result.get("details")
                    logger.info(f"✅ WhatsApp notification sent: {notification_sent}")
                except Exception as e:
                    logger.error(f"❌ WhatsApp notification failed: {str(e)}")
                    notification_sent = False
                    notification_details = {"error": str(e)}
                    # Continue workflow even if notification fails
            elif self.whatsapp_enabled:
                logger.warning("⚠️  WhatsApp enabled but no MCP tools provided")
                notification_sent = False
                notification_details = {"error": "No MCP tools"}
            
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
            
            # Return final response
            response = RunResponse(
                run_id=self.run_id,
                content=f"""✅ Transferência para atendimento humano concluída com sucesso!

📋 **Protocolo:** {protocol_id}
🎯 **Prioridade:** {escalation_analysis.urgency_level.value.upper()}
⏰ **Tempo de resposta esperado:** 15-30 minutos
📞 **Notificação enviada:** {'Sim' if notification_sent else 'Não'}

Um atendente especializado da equipe {assigned_team} entrará em contato em breve.
Mantenha este protocolo para referência.

🙏 Obrigado pela paciência!"""
            )
            # Add metadata if supported
            if hasattr(response, 'metadata'):
                response.metadata = {
                    "workflow_type": "human_handoff",
                    "protocol_id": protocol_id,
                    "escalation_reason": escalation_analysis.escalation_reason.value,
                    "urgency_level": escalation_analysis.urgency_level.value,
                    "assigned_team": assigned_team,
                    "notification_sent": notification_sent,
                    "duration_seconds": duration
                }
            yield response
            
        except Exception as e:
            logger.error(f"Human handoff workflow failed: {str(e)}")
            error_response = RunResponse(
                run_id=self.run_id,
                content=f"❌ Erro na transferência para atendimento humano: {str(e)}. Por favor, tente novamente ou contate nosso suporte."
            )
            # Add metadata if supported
            if hasattr(error_response, 'metadata'):
                error_response.metadata = {
                    "workflow_type": "human_handoff",
                    "status": "failed",
                    "error": str(e)
                }
            yield error_response
    
    def _send_whatsapp_notification_sync(self, protocol: EscalationProtocol) -> Dict:
        """Send WhatsApp notification using MCP tools"""
        
        try:
            # MCP WhatsApp tool uses preset recipient numbers
            # No need to specify target_phone as it's configured in the tool
            
            # Format notification message
            message = self._format_notification_message(protocol)
            
            # Create WhatsApp notification object  
            notification = WhatsAppNotification(
                instance=self.whatsapp_instance,
                target_number="EVOLUTION_API_FIXED_RECIPIENT",  # Uses env var from MCP config
                message=message,
                priority=protocol.escalation_analysis.urgency_level,
                protocol_id=protocol.protocol_id
            )
            
            # Send via MCP WhatsApp tools (synchronous version)
            # Use the MCP tool function directly
            # This requires the mcp__send_whatsapp_message server to be available
            
            # For proper integration, we'll create a specialized notification agent
            # with MCP tools configured
            result = self._send_via_mcp_agent_sync(message)
            
            if result.get("success", False):
                logger.info(f"📱 WhatsApp notification sent to preset recipient")
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
            "low": "🟢",
            "medium": "🟡", 
            "high": "🟠",
            "critical": "🔴"
        }
        
        urgency_str = getattr(protocol.escalation_analysis.urgency_level, 'value', str(protocol.escalation_analysis.urgency_level))
        emoji = urgency_emoji.get(urgency_str, "⚪")
        
        return dedent(f"""\
        🚨 *Escalação para Atendimento Humano* {emoji}
        
        📋 *Protocolo:* {protocol.protocol_id}
        👤 *Cliente:* {protocol.customer_info.customer_name or 'Não informado'}
        📱 *CPF:* {protocol.customer_info.customer_cpf or 'Não informado'}
        ⚠️ *Motivo:* {getattr(protocol.escalation_analysis.escalation_reason, 'value', str(protocol.escalation_analysis.escalation_reason))}
        🎯 *Urgência:* {getattr(protocol.escalation_analysis.urgency_level, 'value', str(protocol.escalation_analysis.urgency_level)).upper()}
        🕐 *Horário:* {protocol.timestamp.strftime('%d/%m/%Y %H:%M')}
        
        📝 *Descrição:*
        {protocol.issue_details.issue_description or protocol.issue_details.summary}
        
        💬 *Resumo da Conversa:*
        {protocol.issue_details.conversation_summary or protocol.issue_details.conversation_history[:200] + '...' if len(protocol.issue_details.conversation_history) > 200 else protocol.issue_details.conversation_history}
        
        🎯 *Ação Recomendada:*
        {protocol.issue_details.recommended_action or 'Avaliar situação e fornecer suporte personalizado'}
        
        📊 *Confiança na Escalação:* {protocol.escalation_analysis.confidence:.1%}
        """).strip()
    
    def _send_via_mcp_agent_sync(self, message: str) -> Dict:
        """Send WhatsApp message via MCP tools using synchronous wrapper"""
        import asyncio
        
        try:
            # Run the async method in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._send_via_mcp_agent_async(message))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Synchronous MCP WhatsApp call failed: {str(e)}")
            return {
                "success": False,
                "error": f"Sync wrapper error: {str(e)}",
                "method": "mcp_sync_wrapper"
            }
    
    def _save_handoff_result(self, result: HandoffResult):
        """Save handoff result to session state"""
        if not hasattr(self, 'session_state'):
            self.session_state = {}
        
        self.session_state.setdefault('handoff_results', [])
        self.session_state['handoff_results'].append(result.model_dump(mode="json"))
        
        logger.info(f"Saved handoff result: Protocol {result.protocol.protocol_id}")
    
    async def _send_via_mcp_agent_async(self, message: str) -> Dict:
        """Send WhatsApp message via MCP tools using pre-initialized tools"""
        try:
            if not self.mcp_tools:
                logger.error("📱 No MCP tools available for WhatsApp notifications")
                return {
                    "success": False,
                    "error": "No MCP tools provided to workflow",
                    "method": "mcp_evolution_api"
                }
            
            # Create an agent with the pre-initialized MCP tools
            whatsapp_agent = Agent(
                name="WhatsApp Notifier",
                model=Claude(id="claude-sonnet-4-20250514"),
                instructions=[
                    "You are a WhatsApp notification agent.",
                    "Use the send_whatsapp_message MCP tools to send notifications.",
                    f"Always use instance: {self.whatsapp_instance}",
                    "Format messages clearly and confirm when sent successfully."
                ],
                tools=[self.mcp_tools],  # Use pre-initialized MCP tools
                markdown=False
            )
            
            # Use the agent to send the WhatsApp message
            response = await whatsapp_agent.arun(
                f"Send this WhatsApp message:\n\n{message}\n\n"
                f"Use the send_text_message tool with instance '{self.whatsapp_instance}'"
            )
            
            if response and response.content:
                logger.info(f"📱 WhatsApp notification sent via MCP agent")
                logger.info(f"📄 Agent response: {response.content[:200]}...")
                return {
                    "success": True,
                    "message": "Notification sent successfully via MCP agent",
                    "target_phone": "configured_recipient", 
                    "method": "mcp_evolution_api",
                    "agent_response": response.content
                }
            else:
                logger.error(f"📱 MCP WhatsApp agent failed: No response")
                return {
                    "success": False,
                    "error": "MCP WhatsApp agent returned no response",
                    "method": "mcp_evolution_api"
                }
                
        except Exception as e:
            logger.error(f"WhatsApp notification via MCP failed: {str(e)}")
            return {
                "success": False,
                "error": f"MCP notification error: {str(e)}",
                "method": "mcp_evolution_api"
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
    mcp_tools=None,
    debug_mode: bool = False,
    whatsapp_enabled: bool = True,
    whatsapp_instance: str = "SofIA"  # Updated to match the actual instance
) -> HumanHandoffWorkflow:
    """Factory function to create a configured human handoff workflow"""
    
    logger.info(f"Creating human handoff workflow (WhatsApp: {whatsapp_enabled}, MCP: {mcp_tools is not None})")
    
    return HumanHandoffWorkflow(
        workflow_id="human-handoff",
        storage=PostgresStorage(
            table_name="human_handoff_workflows",
            db_url=db_url,
            auto_upgrade_schema=True,
        ),
        mcp_tools=mcp_tools,
        debug_mode=debug_mode,
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_instance=whatsapp_instance
    )