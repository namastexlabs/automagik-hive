"""
5-Level Typification Workflow Implementation
==========================================

Sequential Agno workflow for hierarchical conversation typification.
Validates each level against the extracted CSV hierarchy.
Uses shared protocol generator for consistent protocol format.
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

# YAML configuration loader
from ai.workflows.config_loader import config_loader

# Shared protocol generator
from ai.workflows.shared.protocol_generator import (
    generate_protocol, 
    save_protocol_to_session_state,
    format_protocol_for_user
)

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
    UnidadeNegocio,
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
        
        # Load workflow configuration
        self.workflow_config = config_loader.load_workflow_config('conversation-typification')
        
        logger.info(f"Loaded hierarchy with {len(self.hierarchy)} business units")
        
        if self.debug_mode:
            logger.debug(f"🔧 DEBUG MODE: Workflow state tracking enabled")
    
    def _create_model_from_config(self, agent_key: str) -> Claude:
        """
        Create Claude model from YAML configuration.
        
        Args:
            agent_key: Key for agent configuration in YAML
            
        Returns:
            Configured Claude model instance
        """
        model_config = config_loader.get_model_config('conversation-typification', agent_key)
        
        return Claude(
            id=model_config.get('id', 'claude-sonnet-4-20250514'),
            temperature=model_config.get('temperature', 0.7),
            max_tokens=model_config.get('max_tokens', 2000)
        )
        
    
    def _create_business_unit_classifier(self) -> Agent:
        """Create business unit classifier from configuration"""
        return Agent(
            name="Business Unit Classifier",
            model=self._create_model_from_config('business_unit_classifier'),
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
        
        
        return Agent(
            name=f"Product Classifier - {business_unit}",
            model=self._create_model_from_config('product_classifier'),
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
        
        
        return Agent(
            name=f"Motive Classifier - {product}",
            model=self._create_model_from_config('motive_classifier'),
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
        
        
        return Agent(
            name=f"Submotive Classifier - {motive}",
            model=self._create_model_from_config('submotive_classifier'),
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
    
    def run(  # type: ignore
        self, 
        conversation_text: str,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        satisfaction_data: Optional[CustomerSatisfactionData] = None,
        escalation_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Iterator[Union[WorkflowCompletedEvent, RunResponseEvent]]:
        """
        Execute the complete 5-level typification workflow with enhanced reporting
        
        Args:
            conversation_text: Complete conversation text to classify
            session_id: Optional session identifier for tracking
            customer_id: Optional customer identifier
            satisfaction_data: Customer satisfaction and NPS data from Ana
            escalation_data: Human escalation data if applicable
            metadata: Additional conversation metadata
        """
        
        # Generate session_id if not provided
        if session_id is None:
            session_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conversation_history = conversation_text  # Use the input parameter
        
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
            business_unit_classifier = self._create_business_unit_classifier()
            unit_response: RunResponse = business_unit_classifier.run(
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
            # Convert business_unit string back to enum
            business_unit_enum = UnidadeNegocio(business_unit)
            
            final_typification = HierarchicalTypification(
                unidade_negocio=business_unit_enum,
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
            import asyncio
            notification_result = asyncio.run(self._send_whatsapp_notification_sync(
                final_report, final_typification
            ))
            
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
                    "typification": final_typification.model_dump(mode="json"),
                    "ticket": ticket_result.model_dump(mode="json"),
                    "final_report": final_report.model_dump(mode="json"),
                    "satisfaction_data": satisfaction_data.model_dump(mode="json"),
                    "conversation_metrics": conversation_metrics.model_dump(mode="json"),
                    "notification_result": notification_result,
                    "hierarchy_path": final_typification.hierarchy_path,
                    "confidence_scores": confidence_scores,
                    "validation_result": validation_result.model_dump(mode="json"),
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
        """Create or update ticket with typification data using shared protocol generator"""
        
        # Determine assigned team based on business unit
        team_mapping = {
            "Adquirência Web": "adquirencia_team",
            "Adquirência Web / Adquirência Presencial": "adquirencia_team",
            "Emissão": "emissao_team",
            "PagBank": "pagbank_team"
        }
        
        assigned_team = team_mapping.get(typification.unidade_negocio.value, "general_support")
        
        # Generate unified protocol
        workflow_data = {
            "typification_data": typification.as_dict,
            "conversation_summary": self._generate_summary(conversation_history),
            "business_unit": typification.unidade_negocio.value,
            "product": typification.produto,
            "motive": typification.motivo,
            "submotive": typification.submotivo,
            "conclusion": typification.conclusao
        }
        
        unified_protocol = generate_protocol(
            session_id=session_id,
            protocol_type="typification",
            customer_info={"customer_id": customer_id} if customer_id else {},
            workflow_data=workflow_data,
            assigned_team=assigned_team,
            notes=f"Typification completed for {typification.unidade_negocio.value}"
        )
        
        # Save protocol to session state for access by other agents
        if hasattr(self, 'session_state') and self.session_state:
            save_protocol_to_session_state(unified_protocol, self.session_state)
        
        # Create ticket result using unified protocol ID
        ticket_result = TicketCreationResult(
            ticket_id=unified_protocol.protocol_id,
            action="created",
            status="resolved",  # Assuming auto-resolved with orientation
            assigned_team=assigned_team,
            priority="medium",
            typification_data=typification.as_dict,
            success=True,
            error_message=None
        )
        
        logger.info(f"Created ticket {unified_protocol.protocol_id} for team {assigned_team}")
        
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
        self.session_state['typification_results'].append(typification.model_dump(mode="json"))
        
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
    
    def _get_target_team(self, typification: HierarchicalTypification) -> str:
        """Get target team based on business unit"""
        team_mapping = {
            "Adquirência Web": "adquirencia_team",
            "Adquirência Web / Adquirência Presencial": "adquirencia_team", 
            "Emissão": "emissao_team",
            "PagBank": "pagbank_team"
        }
        return team_mapping.get(typification.unidade_negocio.value, "general_team")
    
    async def _send_whatsapp_notification_sync(
        self, 
        final_report: FinalReport,
        typification: HierarchicalTypification
    ) -> Dict:
        """Send WhatsApp notification with final report summary using Evolution API via MCP"""
        
        try:
            # Import the WhatsApp notification service
            from ai.workflows.shared.whatsapp_notification import get_whatsapp_notification_service
            
            # Get the WhatsApp service
            whatsapp_service = get_whatsapp_notification_service(debug_mode=self.debug_mode)
            
            # Prepare report data for WhatsApp formatting
            report_data = {
                "report_id": final_report.report_id,
                "session_id": final_report.session_id,
                "typification": final_report.typification.model_dump(mode="json"),
                "satisfaction_data": final_report.satisfaction_data.model_dump(mode="json"),
                "metrics": final_report.metrics.model_dump(mode="json"),
                "executive_summary": final_report.executive_summary
            }
            
            # Send via WhatsApp service using Evolution API
            notification_result = await whatsapp_service.send_typification_report(report_data)
            
            if notification_result["success"]:
                logger.info(f"📱 WhatsApp typification report sent successfully")
                
                # Create notification data for compatibility
                notification_data = WhatsAppNotificationData(
                    notification_id=f"NOT-{final_report.report_id}",
                    target_team=self._get_target_team(typification),
                    priority="medium",
                    message_template="final_report_template",
                    formatted_message=notification_result.get("agent_response", "Report sent")
                )
                
                return {
                    "success": True,
                    "notification_data": notification_data.model_dump(mode="json"),
                    "message": "WhatsApp notification sent successfully",
                    "agent_response": notification_result.get("agent_response"),
                    "method": "agno_whatsapp_tools"
                }
            else:
                logger.error(f"WhatsApp notification failed: {notification_result.get('error')}")
                return {
                    "success": False,
                    "error": notification_result.get("error"),
                    "method": "agno_whatsapp_tools"
                }
            
        except Exception as e:
            logger.error(f"WhatsApp notification error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "agno_whatsapp_tools"
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
🕐 *Gerado:* {datetime.fromisoformat(report.generated_at).strftime('%d/%m/%Y %H:%M')}

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
        self.session_state['final_reports'].append(report.model_dump(mode="json"))
        
        logger.info(f"Saved final report {report.report_id} for session {report.session_id}")
    
    def _log_workflow_start(self, session_id: str, conversation_history: str):
        """Log workflow startup"""
        logger.info(f"Typification started | Session: {session_id} | Length: {len(conversation_history)} chars")
    
    def _log_step_start(self, step_num: int, step_name: str, available_options: list, context: dict = None):
        """Log classification step start"""
        pass  # Silent for concise mode
    
    def _log_classification_result(self, step_num: int, classification_type: str, selected_option: str, confidence: float, reasoning: str, available_options: list, context: dict = None):
        """Log classification result"""
        logger.info(f"Step {step_num}/5: {selected_option} ({confidence:.0%})")
    
    def _log_final_typification(self, typification: HierarchicalTypification, confidence_scores: dict, validation_result):
        """Log final typification result with summary table"""
        if self.console:
            # Create final summary table (preserve this for data visibility)
            table = Table(title="FINAL TYPIFICATION RESULT")
            table.add_column("Level", style="yellow")
            table.add_column("Selection", style="green")
            table.add_column("Confidence", style="blue")
            
            table.add_row("1. Business Unit", typification.unidade_negocio.value, f"{confidence_scores.get('business_unit', 0):.1%}")
            table.add_row("2. Product", typification.produto, f"{confidence_scores.get('product', 0):.1%}")
            table.add_row("3. Motive", typification.motivo, f"{confidence_scores.get('motive', 0):.1%}")
            table.add_row("4. Submotive", typification.submotivo, f"{confidence_scores.get('submotive', 0):.1%}")
            table.add_row("5. Conclusion", typification.conclusao, "100.0%")
            
            self.console.print(table)
        
        logger.info(f"Typification complete: {typification.hierarchy_path}")
    
    def _log_workflow_completion(self, typification: HierarchicalTypification, confidence_scores: dict, start_time: datetime, end_time: datetime):
        """Log workflow completion"""
        duration = (end_time - start_time).total_seconds()
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        logger.info(f"Workflow completed in {duration:.1f}s | Avg confidence: {avg_confidence:.0%}")

def get_conversation_typification_workflow(debug_mode: bool = False) -> ConversationTypificationWorkflow:
    """Factory function to create a configured typification workflow"""
    
    # Check environment modes
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    env_debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Load storage configuration from YAML
    storage_config = config_loader.get_storage_config('conversation-typification')
    workflow_settings = config_loader.get_workflow_settings('conversation-typification')
    
    return ConversationTypificationWorkflow(
        workflow_id=workflow_settings.get('workflow_id', 'conversation-typification'),
        storage=PostgresStorage(
            table_name=storage_config.get('table_name', 'conversation-typification-workflows'),
            db_url=db_url,
            auto_upgrade_schema=storage_config.get('auto_upgrade_schema', True),
        ),
        debug_mode=debug_mode or env_debug,
    )