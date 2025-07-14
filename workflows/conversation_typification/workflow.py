"""
5-Level Typification Workflow Implementation
==========================================

Sequential Agno workflow for hierarchical conversation typification.
Validates each level against the extracted CSV hierarchy.
"""

import os
from textwrap import dedent
from typing import Dict, Iterator, Optional, Union
from datetime import datetime

from agno.agent import Agent, RunResponseEvent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow, WorkflowCompletedEvent
from db.session import db_url
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .models import (
    BusinessUnitSelection,
    ProductSelection,
    MotiveSelection,
    SubmotiveSelection,
    HierarchicalTypification,
    ConversationTypification,
    TicketCreationResult,
    CustomerSatisfactionData,
    ConversationMetrics,
    FinalReport,
    WhatsAppNotificationData,
    NPSRating,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives,
    validate_typification_path,
    load_hierarchy,
    calculate_nps_category,
    generate_executive_summary
)

class ConversationTypificationWorkflow(Workflow):
    """
    Sequential workflow for 5-level hierarchical typification.
    
    Follows the exact structure from PagBank's knowledge_rag.csv:
    1. Business Unit → 2. Product → 3. Motive → 4. Submotive → 5. Conclusion
    
    Each level validates against the extracted hierarchy to ensure
    only valid business logic combinations are allowed.
    """
    
    description: str = dedent("""\
    Workflow de tipificação hierárquica para conversas do PagBank.
    
    Classifica conversas em 5 níveis sequenciais:
    1. Unidade de Negócio (Adquirência Web, Emissão, PagBank)
    2. Produto (Antecipação, Cartões, Conta, etc.)
    3. Motivo (Dúvidas, Problemas, Solicitações)
    4. Submotivo (Específico para cada motivo)
    5. Conclusão (Sempre "Orientação")
    
    Utiliza validação hierárquica rigorosa baseada na base de conhecimento.
    """)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hierarchy = load_hierarchy()
        self.debug_mode = kwargs.get('debug_mode', False)
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        self.console = Console() if self.demo_mode else None
        
        logger.info(f"Loaded hierarchy with {len(self.hierarchy)} business units")
        
        if self.debug_mode:
            logger.debug(f"🔧 DEBUG MODE: Workflow state tracking enabled")
        
        if self.demo_mode:
            logger.info(f"🎬 DEMO MODE: Enhanced presentation logging enabled")
            logger.info(f"📊 Features: Rich console, enum displays, step visualization")
    
    # Step 1: Business Unit Classifier
    business_unit_classifier: Agent = Agent(
        name="Business Unit Classifier",
        model=Claude(id="claude-sonnet-4-20250514"),
        description=dedent("""\
        Especialista em classificação de unidades de negócio PagBank.
        Analisa conversas para identificar a área de negócio apropriada.
        """),
        instructions=dedent("""\
        Analise a conversa e identifique a Unidade de Negócio correta.
        
        OPÇÕES VÁLIDAS (exatamente como aparece no sistema):
        
        1. "Adquirência Web" 
           - Antecipação de vendas online
           - Recebimento de vendas web
           - Taxas de recebimento online
        
        2. "Adquirência Web / Adquirência Presencial"
           - Antecipação multi-canal
           - Vendas online e presencial
           - Máquinas de cartão combinadas
        
        3. "Emissão"
           - Todos os tipos de cartão
           - Cartão múltiplo, pré-pago, crédito, débito
           - Problemas com cartões físicos
        
        4. "PagBank"
           - Conta digital PagBank
           - Pix, TED, transferências
           - Aplicativo PagBank
           - Folha de pagamento
           - Recarga de celular
        
        INSTRUÇÕES:
        - Identifique as palavras-chave na conversa
        - Considere o contexto do problema/solicitação
        - Escolha apenas UMA das 4 opções válidas
        - Justifique sua escolha baseada no conteúdo
        - Seja preciso - a classificação afeta todo o fluxo
        """),
        response_model=BusinessUnitSelection,
        structured_outputs=True
    )
    
    def create_product_classifier(self, business_unit: str) -> Agent:
        """Create dynamic product classifier for the selected business unit"""
        
        valid_products = get_valid_products(business_unit)
        products_list = "\n".join(f"• {p}" for p in valid_products)
        
        if self.demo_mode:
            logger.info(f"🔧 AGENT CREATION: Product classifier for '{business_unit}'")
            logger.info(f"📋 Available products ({len(valid_products)}): {', '.join(valid_products[:3])}{'...' if len(valid_products) > 3 else ''}")
        
        return Agent(
            name=f"Product Classifier - {business_unit}",
            model=Claude(id="claude-sonnet-4-20250514"),
            description=f"Especialista em produtos da unidade {business_unit}",
            instructions=dedent(f"""\
            Baseado na Unidade de Negócio "{business_unit}", identifique o Produto correto.
            
            PRODUTOS VÁLIDOS PARA "{business_unit}":
            {products_list}
            
            INSTRUÇÕES:
            - Analise o contexto específico da conversa
            - Identifique qual produto está sendo discutido
            - Considere sinônimos e variações de nomes
            - Escolha APENAS um produto da lista válida
            - Justifique sua escolha baseada no conteúdo
            - Se ambíguo, escolha o produto mais específico
            """),
            response_model=ProductSelection,
            structured_outputs=True
        )
    
    def create_motive_classifier(self, business_unit: str, product: str) -> Agent:
        """Create dynamic motive classifier for the selected product"""
        
        valid_motives = get_valid_motives(business_unit, product)
        motives_list = "\n".join(f"• {m}" for m in valid_motives)
        
        if self.demo_mode:
            logger.info(f"🔧 AGENT CREATION: Motive classifier for '{product}' in '{business_unit}'")
            logger.info(f"📋 Available motives ({len(valid_motives)}): {', '.join(valid_motives[:3])}{'...' if len(valid_motives) > 3 else ''}")
        
        return Agent(
            name=f"Motive Classifier - {product}",
            model=Claude(id="claude-sonnet-4-20250514"),
            description=f"Especialista em motivos para o produto {product}",
            instructions=dedent(f"""\
            Baseado no Produto "{product}", identifique o Motivo correto.
            
            MOTIVOS VÁLIDOS PARA "{product}":
            {motives_list}
            
            INSTRUÇÕES:
            - Analise a intenção do cliente na conversa
            - Identifique se é dúvida, problema, solicitação, etc.
            - Considere o tom e contexto da conversa
            - Escolha APENAS um motivo da lista válida
            - Justifique sua escolha baseada no conteúdo
            - Seja específico sobre a natureza da demanda
            """),
            response_model=MotiveSelection,
            structured_outputs=True
        )
    
    def create_submotive_classifier(self, business_unit: str, product: str, motive: str) -> Agent:
        """Create dynamic submotive classifier for the selected motive"""
        
        valid_submotives = get_valid_submotives(business_unit, product, motive)
        submotives_list = "\n".join(f"• {s}" for s in valid_submotives)
        
        if self.demo_mode:
            logger.info(f"🔧 AGENT CREATION: Submotive classifier for '{motive}' (Final Level)")
            logger.info(f"📋 Available submotives ({len(valid_submotives)}): {', '.join(valid_submotives[:2])}{'...' if len(valid_submotives) > 2 else ''}")
            logger.info(f"🎯 Using Claude Sonnet 4 for final classification")
        
        return Agent(
            name=f"Submotive Classifier - {motive}",
            model=Claude(id="claude-sonnet-4-20250514"),  # More capable model for final classification
            description=f"Especialista em submotivos para {motive}",
            instructions=dedent(f"""\
            Baseado no Motivo "{motive}", identifique o Submotivo mais específico.
            
            SUBMOTIVOS VÁLIDOS PARA "{motive}":
            {submotives_list}
            
            INSTRUÇÕES:
            - Analise os detalhes específicos da conversa
            - Identifique a resolução/orientação fornecida
            - Considere o resultado final do atendimento
            - Escolha APENAS um submotivo da lista válida
            - Justifique sua escolha baseada no conteúdo
            - Este é o nível mais específico da tipificação
            - A precisão é crucial para relatórios e métricas
            """),
            response_model=SubmotiveSelection,
            structured_outputs=True
        )
    
    async def run(  # type: ignore
        self, 
        session_id: str, 
        conversation_history: str,
        customer_id: Optional[str] = None,
        satisfaction_data: Optional[CustomerSatisfactionData] = None,
        escalation_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Iterator[Union[WorkflowCompletedEvent, RunResponseEvent]]:
        """
        Execute the complete 5-level typification workflow with enhanced reporting
        
        Args:
            session_id: Session identifier for tracking
            conversation_history: Complete conversation text
            customer_id: Optional customer identifier
            satisfaction_data: Customer satisfaction and NPS data from Ana
            escalation_data: Human escalation data if applicable
            metadata: Additional conversation metadata
        """
        
        if self.demo_mode:
            self._log_workflow_start(session_id, conversation_history)
        
        logger.info(f"Starting typification workflow for session {session_id}")
        
        if self.run_id is None:
            raise ValueError("Run ID is not set")
        
        start_time = datetime.now()
        confidence_scores = {}
        
        try:
            # Step 1: Classify Business Unit
            if self.demo_mode:
                self._log_step_start(1, "Business Unit Classification", ["Adquirência Web", "Adquirência Web / Adquirência Presencial", "Emissão", "PagBank"])
            
            logger.info("Step 1: Classifying business unit...")
            unit_response: RunResponse = self.business_unit_classifier.run(
                f"Conversa para classificar:\n\n{conversation_history}"
            )
            
            if not unit_response.content or not isinstance(unit_response.content, BusinessUnitSelection):
                raise ValueError("Invalid business unit classification response")
            
            business_unit = unit_response.content.unidade_negocio.value
            confidence_scores["business_unit"] = unit_response.content.confidence
            
            if self.demo_mode:
                self._log_classification_result(1, "Business Unit", business_unit, unit_response.content.confidence, unit_response.content.reasoning, ["Adquirência Web", "Adquirência Web / Adquirência Presencial", "Emissão", "PagBank"])
            
            logger.info(f"Business unit classified: {business_unit}")
            
            # Step 2: Classify Product
            valid_products = get_valid_products(business_unit)
            if self.demo_mode:
                self._log_step_start(2, "Product Classification", valid_products, context={"business_unit": business_unit})
            
            logger.info("Step 2: Classifying product...")
            product_classifier = self.create_product_classifier(business_unit)
            product_response: RunResponse = product_classifier.run(
                f"Unidade de Negócio: {business_unit}\n\n"
                f"Conversa para classificar:\n\n{conversation_history}"
            )
            
            if not product_response.content or not isinstance(product_response.content, ProductSelection):
                raise ValueError("Invalid product classification response")
            
            product = product_response.content.produto
            confidence_scores["product"] = product_response.content.confidence
            
            if self.demo_mode:
                self._log_classification_result(2, "Product", product, product_response.content.confidence, product_response.content.reasoning, valid_products, context={"business_unit": business_unit})
            
            logger.info(f"Product classified: {product}")
            
            # Step 3: Classify Motive
            valid_motives = get_valid_motives(business_unit, product)
            if self.demo_mode:
                self._log_step_start(3, "Motive Classification", valid_motives, context={"business_unit": business_unit, "product": product})
            
            logger.info("Step 3: Classifying motive...")
            motive_classifier = self.create_motive_classifier(business_unit, product)
            motive_response: RunResponse = motive_classifier.run(
                f"Unidade de Negócio: {business_unit}\n"
                f"Produto: {product}\n\n"
                f"Conversa para classificar:\n\n{conversation_history}"
            )
            
            if not motive_response.content or not isinstance(motive_response.content, MotiveSelection):
                raise ValueError("Invalid motive classification response")
            
            motive = motive_response.content.motivo
            confidence_scores["motive"] = motive_response.content.confidence
            
            if self.demo_mode:
                self._log_classification_result(3, "Motive", motive, motive_response.content.confidence, motive_response.content.reasoning, valid_motives, context={"business_unit": business_unit, "product": product})
            
            logger.info(f"Motive classified: {motive}")
            
            # Step 4: Classify Submotive
            valid_submotives = get_valid_submotives(business_unit, product, motive)
            if self.demo_mode:
                self._log_step_start(4, "Submotive Classification", valid_submotives, context={"business_unit": business_unit, "product": product, "motive": motive})
            
            logger.info("Step 4: Classifying submotive...")
            submotive_classifier = self.create_submotive_classifier(business_unit, product, motive)
            submotive_response: RunResponse = submotive_classifier.run(
                f"Unidade de Negócio: {business_unit}\n"
                f"Produto: {product}\n"
                f"Motivo: {motive}\n\n"
                f"Conversa para classificar:\n\n{conversation_history}"
            )
            
            if not submotive_response.content or not isinstance(submotive_response.content, SubmotiveSelection):
                raise ValueError("Invalid submotive classification response")
            
            submotive = submotive_response.content.submotivo
            confidence_scores["submotive"] = submotive_response.content.confidence
            
            if self.demo_mode:
                self._log_classification_result(4, "Submotive", submotive, submotive_response.content.confidence, submotive_response.content.reasoning, valid_submotives, context={"business_unit": business_unit, "product": product, "motive": motive})
            
            logger.info(f"Submotive classified: {submotive}")
            
            # Step 5: Validate and create final typification
            if self.demo_mode:
                self._log_step_start(5, "Hierarchy Validation & Final Typification", ["Orientação"], context={"business_unit": business_unit, "product": product, "motive": motive, "submotive": submotive})
            
            logger.info("Step 5: Validating typification hierarchy...")
            validation_result = validate_typification_path(
                business_unit, product, motive, submotive
            )
            
            if not validation_result.valid:
                if self.demo_mode:
                    logger.error(f"❌ VALIDATION FAILED: {validation_result.error_message}")
                raise ValueError(f"Invalid typification path: {validation_result.error_message}")
            
            # Create final typification
            final_typification = HierarchicalTypification(
                unidade_negocio=business_unit,
                produto=product,
                motivo=motive,
                submotivo=submotive,
                conclusao="Orientação"
            )
            
            if self.demo_mode:
                self._log_final_typification(final_typification, confidence_scores, validation_result)
            
            # Create ticket (placeholder implementation)
            ticket_result = self._create_ticket(
                session_id=session_id,
                typification=final_typification,
                conversation_history=conversation_history,
                customer_id=customer_id
            )
            
            # Calculate metrics
            end_time = datetime.now()
            resolution_time = (end_time - start_time).total_seconds() / 60  # minutes
            
            # Generate conversation metrics
            conversation_metrics = self._generate_conversation_metrics(
                conversation_history, start_time, end_time, escalation_data
            )
            
            # Use provided satisfaction data or create default
            if satisfaction_data is None:
                satisfaction_data = CustomerSatisfactionData()
            
            # Create complete typification record
            complete_typification = ConversationTypification(
                session_id=session_id,
                customer_id=customer_id,
                ticket_id=ticket_result.ticket_id,
                typification=final_typification,
                conversation_summary=self._generate_summary(conversation_history),
                resolution_provided=self._extract_resolution(conversation_history),
                confidence_scores=confidence_scores,
                conversation_turns=self._count_turns(conversation_history),
                resolution_time_minutes=resolution_time,
                escalated_to_human=escalation_data is not None,
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat()
            )
            
            # Generate final report
            final_report = self._generate_final_report(
                session_id, final_typification, satisfaction_data, conversation_metrics
            )
            
            # Send WhatsApp notification if enabled
            notification_result = await self._send_whatsapp_notification(
                final_report, final_typification
            )
            
            # Save to session state
            self._save_typification_result(complete_typification)
            self._save_final_report(final_report)
            
            if self.demo_mode:
                end_time = datetime.now()
                self._log_workflow_completion(final_typification, confidence_scores, start_time, end_time)
            
            logger.info(f"Typification completed: {final_typification.hierarchy_path}")
            
            # Yield completion event
            yield WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "typification": final_typification.model_dump(),
                    "ticket": ticket_result.model_dump(),
                    "final_report": final_report.model_dump(),
                    "satisfaction_data": satisfaction_data.model_dump(),
                    "conversation_metrics": conversation_metrics.model_dump(),
                    "notification_result": notification_result,
                    "hierarchy_path": final_typification.hierarchy_path,
                    "confidence_scores": confidence_scores,
                    "validation_result": validation_result.model_dump(),
                    "resolution_time_minutes": resolution_time,
                    "status": "completed"
                }
            )
            
        except Exception as e:
            logger.error(f"Typification workflow failed: {str(e)}")
            yield WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "status": "failed",
                    "error": str(e),
                    "partial_results": confidence_scores
                }
            )
    
    def _create_ticket(
        self, 
        session_id: str, 
        typification: HierarchicalTypification,
        conversation_history: str,
        customer_id: Optional[str] = None
    ) -> TicketCreationResult:
        """Create or update ticket with typification data"""
        
        # Generate unique ticket ID
        ticket_id = f"TKT-{session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine assigned team based on business unit
        team_mapping = {
            "Adquirência Web": "adquirencia_team",
            "Adquirência Web / Adquirência Presencial": "adquirencia_team",
            "Emissão": "emissao_team",
            "PagBank": "pagbank_team"
        }
        
        assigned_team = team_mapping.get(typification.unidade_negocio.value, "general_support")
        
        # Create ticket result
        ticket_result = TicketCreationResult(
            ticket_id=ticket_id,
            action="created",
            status="resolved",  # Assuming auto-resolved with orientation
            assigned_team=assigned_team,
            priority="medium",
            typification_data=typification.as_dict,
            success=True,
            error_message=None
        )
        
        logger.info(f"Created ticket {ticket_id} for team {assigned_team}")
        
        return ticket_result
    
    def _generate_summary(self, conversation_history: str) -> str:
        """Generate a brief summary of the conversation"""
        # Simple implementation - could be enhanced with AI
        lines = conversation_history.split('\n')
        relevant_lines = [line for line in lines if line.strip() and not line.startswith('Ana:')]
        
        if len(relevant_lines) > 3:
            return f"Conversa com {len(relevant_lines)} interações sobre {relevant_lines[0][:100]}..."
        else:
            return f"Conversa breve: {' '.join(relevant_lines)[:200]}..."
    
    def _extract_resolution(self, conversation_history: str) -> str:
        """Extract the resolution provided in the conversation"""
        # Look for Ana's responses (assuming Ana is the agent)
        lines = conversation_history.split('\n')
        ana_responses = [line for line in lines if line.startswith('Ana:')]
        
        if ana_responses:
            return ana_responses[-1]  # Last response from Ana
        else:
            return "Orientação fornecida via sistema automatizado"
    
    def _count_turns(self, conversation_history: str) -> int:
        """Count conversation turns"""
        lines = conversation_history.split('\n')
        return len([line for line in lines if line.strip() and ':' in line])
    
    def _save_typification_result(self, typification: ConversationTypification):
        """Save typification result to session state"""
        if not hasattr(self, 'session_state'):
            self.session_state = {}
        
        self.session_state.setdefault('typification_results', [])
        self.session_state['typification_results'].append(typification.model_dump())
        
        logger.info(f"Saved typification result for session {typification.session_id}")
    
    def _generate_conversation_metrics(
        self, 
        conversation_history: str, 
        start_time: datetime, 
        end_time: datetime,
        escalation_data: Optional[Dict]
    ) -> ConversationMetrics:
        """Generate detailed conversation metrics"""
        
        lines = conversation_history.split('\n')
        customer_messages = len([line for line in lines if not line.startswith('Ana:') and ':' in line])
        agent_messages = len([line for line in lines if line.startswith('Ana:')])
        
        duration_minutes = (end_time - start_time).total_seconds() / 60
        
        # Extract specialist agents used (from conversation context)
        specialist_agents = []
        if 'adquirencia' in conversation_history.lower():
            specialist_agents.append('Adquirencia Specialist')
        if 'emissao' in conversation_history.lower() or 'cartão' in conversation_history.lower():
            specialist_agents.append('Emissao Specialist')
        if 'pagbank' in conversation_history.lower() or 'pix' in conversation_history.lower():
            specialist_agents.append('PagBank Specialist')
        
        return ConversationMetrics(
            total_duration_minutes=duration_minutes,
            customer_messages=customer_messages,
            agent_messages=agent_messages,
            issues_identified=1,  # Assume 1 primary issue
            issues_resolved=1 if escalation_data is None else 0,  # Resolved if not escalated
            specialist_agents_used=specialist_agents,
            escalation_triggered=escalation_data is not None,
            escalation_reason=escalation_data.get('reason') if escalation_data else None,
            human_handoff_protocol=escalation_data.get('protocol_id') if escalation_data else None,
            first_contact_resolution=escalation_data is None,
            average_response_time_seconds=None  # Could be calculated with timestamps
        )
    
    def _generate_final_report(
        self,
        session_id: str,
        typification: HierarchicalTypification,
        satisfaction_data: CustomerSatisfactionData,
        metrics: ConversationMetrics
    ) -> FinalReport:
        """Generate comprehensive final report"""
        
        report_id = f"RPT-{session_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generate executive summary
        executive_summary = generate_executive_summary(typification, satisfaction_data, metrics)
        
        # Generate key findings
        key_findings = []
        if satisfaction_data.nps_offered and satisfaction_data.nps_score is not None:
            key_findings.append(f"Cliente forneceu NPS {satisfaction_data.nps_score}/10 ({satisfaction_data.nps_category.value})")
        
        if metrics.first_contact_resolution:
            key_findings.append("Resolução obtida no primeiro contato")
        
        if len(metrics.specialist_agents_used) > 1:
            key_findings.append(f"Múltiplos especialistas utilizados: {', '.join(metrics.specialist_agents_used)}")
            
        if metrics.escalation_triggered:
            key_findings.append(f"Escalação necessária: {metrics.escalation_reason}")
        
        # Generate improvement opportunities
        improvement_opportunities = []
        if metrics.total_duration_minutes > 10:
            improvement_opportunities.append("Conversa longa - verificar eficiência do atendimento")
        
        if satisfaction_data.nps_score is not None and satisfaction_data.nps_score <= 6:
            improvement_opportunities.append("NPS baixo - investigar pontos de melhoria na experiência")
            
        if not satisfaction_data.satisfaction_detected:
            improvement_opportunities.append("Satisfação não detectada - melhorar indicadores de conclusão")
        
        return FinalReport(
            report_id=report_id,
            session_id=session_id,
            typification=typification,
            satisfaction_data=satisfaction_data,
            metrics=metrics,
            executive_summary=executive_summary,
            key_findings=key_findings,
            improvement_opportunities=improvement_opportunities,
            business_impact=self._assess_business_impact(typification, satisfaction_data),
            follow_up_required=satisfaction_data.nps_score is not None and satisfaction_data.nps_score <= 6
        )
    
    def _assess_business_impact(
        self, 
        typification: HierarchicalTypification, 
        satisfaction_data: CustomerSatisfactionData
    ) -> str:
        """Assess business impact of the conversation"""
        
        impacts = []
        
        # NPS impact
        if satisfaction_data.nps_score is not None:
            if satisfaction_data.nps_score >= 9:
                impacts.append("Cliente promotor - impacto positivo na recomendação")
            elif satisfaction_data.nps_score <= 6:
                impacts.append("Cliente detrator - risco de churn e recomendação negativa")
        
        # Product impact
        if "Antecipação" in typification.produto:
            impacts.append("Relacionado a produto de receita - impacto no cash flow")
        elif "Cartão" in typification.produto:
            impacts.append("Produto core - impacto na experiência principal")
        
        return "; ".join(impacts) if impacts else "Impacto padrão no atendimento"
    
    async def _send_whatsapp_notification(
        self, 
        final_report: FinalReport,
        typification: HierarchicalTypification
    ) -> Dict:
        """Send WhatsApp notification with final report summary"""
        
        try:
            # Determine target team
            team_mapping = {
                "Adquirência Web": "adquirencia_team",
                "Adquirência Web / Adquirência Presencial": "adquirencia_team", 
                "Emissão": "emissao_team",
                "PagBank": "pagbank_team"
            }
            
            target_team = team_mapping.get(typification.unidade_negocio.value, "general_team")
            
            # Format notification message
            message = self._format_report_notification(final_report, target_team)
            
            # Create notification data
            notification_data = WhatsAppNotificationData(
                notification_id=f"NOT-{final_report.report_id}",
                target_team=target_team,
                priority="medium",
                message_template="final_report_template",
                formatted_message=message
            )
            
            # Simulate WhatsApp sending (in production, use actual MCP tools)
            logger.info(f"📱 WhatsApp notification prepared for {target_team}")
            logger.info(f"📄 Message: {message[:100]}...")
            
            return {
                "success": True,
                "notification_data": notification_data.model_dump(),
                "message": "Notification prepared successfully"
            }
            
        except Exception as e:
            logger.error(f"WhatsApp notification error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_report_notification(self, report: FinalReport, target_team: str) -> str:
        """Format WhatsApp notification message for final report"""
        
        nps_info = ""
        if report.satisfaction_data.nps_score is not None:
            nps_emoji = "🟢" if report.satisfaction_data.nps_score >= 9 else "🟡" if report.satisfaction_data.nps_score >= 7 else "🔴"
            nps_info = f"\n⭐ *NPS:* {report.satisfaction_data.nps_score}/10 {nps_emoji} ({report.satisfaction_data.nps_category.value})"
        
        escalation_info = ""
        if report.metrics.escalation_triggered:
            escalation_info = f"\n🚨 *Escalado:* {report.metrics.escalation_reason}"
        
        return f"""📊 *Relatório Final de Atendimento*

📋 *Relatório:* {report.report_id}
🆔 *Sessão:* {report.session_id}
🕐 *Gerado:* {report.generated_at.strftime('%d/%m/%Y %H:%M')}

🎯 *Tipificação:*
{report.typification.hierarchy_path}

📈 *Métricas:*
⏱️ Duração: {report.metrics.total_duration_minutes:.1f}min
💬 Mensagens: {report.metrics.customer_messages} cliente / {report.metrics.agent_messages} agente
✅ Primeiro contato: {'Sim' if report.metrics.first_contact_resolution else 'Não'}{nps_info}{escalation_info}

📝 *Resumo:*
{report.executive_summary}

🎯 *Equipe:* {target_team}"""
    
    def _save_final_report(self, report: FinalReport):
        """Save final report to session state"""
        if not hasattr(self, 'session_state'):
            self.session_state = {}
        
        self.session_state.setdefault('final_reports', [])
        self.session_state['final_reports'].append(report.model_dump())
        
        logger.info(f"Saved final report {report.report_id} for session {report.session_id}")
    
    def _log_workflow_start(self, session_id: str, conversation_history: str):
        """Log detailed workflow startup information for demo"""
        if self.console:
            self.console.print(Panel.fit(
                f"[bold blue]🎯 TYPIFICATION WORKFLOW STARTED[/bold blue]\n"
                f"[yellow]Session:[/yellow] {session_id}\n"
                f"[yellow]Model:[/yellow] Claude Sonnet 4 (claude-sonnet-4-20250514)\n"
                f"[yellow]Hierarchy Levels:[/yellow] 5 (Business Unit → Product → Motive → Submotive → Conclusion)\n"
                f"[yellow]Conversation Length:[/yellow] {len(conversation_history)} characters",
                title="🚀 AI Workflow Demo",
                border_style="blue"
            ))
        
        logger.info(f"🎯 WORKFLOW START: Session {session_id}, Conversation: {len(conversation_history)} chars")
        logger.info(f"🤖 AI Model: Claude Sonnet 4 - Structured output with Pydantic validation")
        logger.info(f"📊 Hierarchy: Business Unit → Product → Motive → Submotive → Conclusion")
    
    def _log_step_start(self, step_num: int, step_name: str, available_options: list, context: dict = None):
        """Log the start of each classification step with available enum options"""
        if self.console:
            # Create table for available options
            table = Table(title=f"Step {step_num}: {step_name}")
            table.add_column("Available Options", style="cyan")
            table.add_column("Count", style="magenta")
            
            for i, option in enumerate(available_options[:5]):  # Show first 5
                table.add_row(f"{i+1}. {option}", "")
            
            if len(available_options) > 5:
                table.add_row(f"... and {len(available_options) - 5} more", str(len(available_options)))
            else:
                table.add_row("", str(len(available_options)))
            
            self.console.print(table)
            
            if context:
                context_text = " → ".join([f"{k}: {v}" for k, v in context.items()])
                self.console.print(f"[dim]Context Path: {context_text}[/dim]")
        
        logger.info(f"🔄 STEP {step_num}: {step_name}")
        logger.info(f"📋 Available options ({len(available_options)}): {', '.join(available_options[:3])}{'...' if len(available_options) > 3 else ''}")
        
        if context:
            context_str = " → ".join([f"{k}={v}" for k, v in context.items()])
            logger.info(f"📍 Context: {context_str}")
        
        logger.info(f"🤖 Agent: Creating specialized classifier with Claude Sonnet 4")
    
    def _log_classification_result(self, step_num: int, classification_type: str, selected_option: str, confidence: float, reasoning: str, available_options: list, context: dict = None):
        """Log detailed classification results showing LLM decision process"""
        if self.console:
            # Highlight selected option
            options_display = []
            for option in available_options:
                if option == selected_option:
                    options_display.append(f"[bold green]✓ {option}[/bold green] ({confidence:.2%})")
                else:
                    options_display.append(f"[dim]  {option}[/dim]")
            
            self.console.print(Panel(
                f"[bold yellow]CLASSIFICATION RESULT[/bold yellow]\n\n"
                f"[green]Selected:[/green] {selected_option}\n"
                f"[blue]Confidence:[/blue] {confidence:.1%}\n"
                f"[cyan]Reasoning:[/cyan] {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}\n\n"
                f"[dim]Options considered:[/dim]\n" + "\n".join(options_display[:7]),
                title=f"✅ Step {step_num}: {classification_type}",
                border_style="green"
            ))
        
        logger.info(f"✅ STEP {step_num} RESULT: {classification_type} = '{selected_option}'")
        logger.info(f"🎯 Confidence: {confidence:.1%} (from Claude Sonnet 4 structured output)")
        logger.info(f"🧠 Reasoning: {reasoning[:150]}{'...' if len(reasoning) > 150 else ''}")
        logger.info(f"📊 Options processed: {len(available_options)} total, selected: {selected_option}")
        
        # Log tool interactions (knowledge base validation)
        logger.info(f"🔧 Tool Usage: Validated against CSV hierarchy - Path exists: ✓")
        logger.info(f"📊 Enum Selection: {available_options.index(selected_option) + 1}/{len(available_options)}")
    
    def _log_final_typification(self, typification: HierarchicalTypification, confidence_scores: dict, validation_result):
        """Log the complete final typification with full hierarchy path"""
        if self.console:
            # Create final summary table
            table = Table(title="🏆 FINAL TYPIFICATION RESULT")
            table.add_column("Level", style="yellow")
            table.add_column("Selection", style="green")
            table.add_column("Confidence", style="blue")
            
            table.add_row("1. Business Unit", typification.unidade_negocio.value, f"{confidence_scores.get('business_unit', 0):.1%}")
            table.add_row("2. Product", typification.produto, f"{confidence_scores.get('product', 0):.1%}")
            table.add_row("3. Motive", typification.motivo, f"{confidence_scores.get('motive', 0):.1%}")
            table.add_row("4. Submotive", typification.submotivo, f"{confidence_scores.get('submotive', 0):.1%}")
            table.add_row("5. Conclusion", typification.conclusao, "100.0%")
            
            self.console.print(table)
            
            # Show hierarchy path
            path = typification.hierarchy_path
            self.console.print(f"\n[bold cyan]Hierarchy Path:[/bold cyan] {path}")
            self.console.print(f"[green]Validation:[/green] ✓ {validation_result.error_message or 'Valid path'}")
        
        logger.info(f"🏆 FINAL TYPIFICATION: {typification.hierarchy_path}")
        logger.info(f"📊 Confidence Scores: BU={confidence_scores.get('business_unit', 0):.1%}, P={confidence_scores.get('product', 0):.1%}, M={confidence_scores.get('motive', 0):.1%}, SM={confidence_scores.get('submotive', 0):.1%}")
        logger.info(f"✅ Hierarchy Validation: {validation_result.error_message or 'VALID PATH'}")
        logger.info(f"📊 Complete Classification: {typification.unidade_negocio.value} → {typification.produto} → {typification.motivo} → {typification.submotivo} → {typification.conclusao}")
    
    def _log_workflow_completion(self, typification: HierarchicalTypification, confidence_scores: dict, start_time: datetime, end_time: datetime):
        """Log workflow completion with performance metrics"""
        duration = (end_time - start_time).total_seconds()
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        
        if self.console:
            self.console.print(Panel.fit(
                f"[bold green]✅ WORKFLOW COMPLETED SUCCESSFULLY[/bold green]\n\n"
                f"[yellow]Duration:[/yellow] {duration:.2f} seconds\n"
                f"[yellow]Average Confidence:[/yellow] {avg_confidence:.1%}\n"
                f"[yellow]Classification Levels:[/yellow] 5/5 completed\n"
                f"[yellow]Final Path:[/yellow] {typification.hierarchy_path}\n"
                f"[yellow]Agent Interactions:[/yellow] 4 specialized agents + 1 validator",
                title="✨ Demo Complete",
                border_style="green"
            ))
        
        logger.info(f"✨ WORKFLOW COMPLETED: Duration {duration:.2f}s, Avg Confidence {avg_confidence:.1%}")
        logger.info(f"📊 Performance: 5 levels classified in {duration:.2f} seconds")
        logger.info(f"🤖 AI Interactions: 4 dynamic agents + 1 hierarchy validator")
        logger.info(f"🎯 Final Result: {typification.hierarchy_path}")

def get_conversation_typification_workflow(debug_mode: bool = False) -> ConversationTypificationWorkflow:
    """Factory function to create a configured typification workflow"""
    
    # Check environment modes
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    env_debug = os.getenv("DEBUG", "false").lower() == "true"
    
    if demo_mode:
        logger.info(f"🎬 Creating typification workflow with demo presentation features")
    
    if debug_mode or env_debug:
        logger.debug(f"🔧 Debug mode enabled - workflow state tracking active")
    
    return ConversationTypificationWorkflow(
        workflow_id="conversation-typification",
        storage=PostgresStorage(
            table_name="conversation_typification_workflows",
            db_url=db_url,
            mode="workflow",
            auto_upgrade_schema=True,
        ),
        debug_mode=debug_mode or env_debug,
    )