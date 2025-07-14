"""
5-Level Typification Workflow Implementation
==========================================

Sequential Agno workflow for hierarchical conversation typification.
Validates each level against the extracted CSV hierarchy.
"""

import json
import logging
from textwrap import dedent
from typing import Dict, Iterator, Optional, Union
from datetime import datetime

from agno.agent import Agent, RunResponseEvent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.utils.log import logger
from agno.workflow import RunResponse, Workflow, WorkflowCompletedEvent
from db.session import db_url

from .models import (
    BusinessUnitSelection,
    ProductSelection,
    MotiveSelection,
    SubmotiveSelection,
    HierarchicalTypification,
    ConversationTypification,
    TicketCreationResult,
    ValidationResult,
    get_valid_products,
    get_valid_motives,
    get_valid_submotives,
    validate_typification_path,
    load_hierarchy,
    HIERARCHY
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
        logger.info(f"Loaded hierarchy with {len(self.hierarchy)} business units")
    
    # Step 1: Business Unit Classifier
    business_unit_classifier: Agent = Agent(
        name="Business Unit Classifier",
        model=Claude(id="claude-haiku-4-20250514"),
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
            model=Claude(id="claude-haiku-4-20250514"),
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
            model=Claude(id="claude-haiku-4-20250514"),
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
    
    def run(  # type: ignore
        self, 
        session_id: str, 
        conversation_history: str,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Iterator[Union[WorkflowCompletedEvent, RunResponseEvent]]:
        """
        Execute the complete 5-level typification workflow
        
        Args:
            session_id: Session identifier for tracking
            conversation_history: Complete conversation text
            customer_id: Optional customer identifier
            metadata: Additional conversation metadata
        """
        
        logger.info(f"Starting typification workflow for session {session_id}")
        
        if self.run_id is None:
            raise ValueError("Run ID is not set")
        
        start_time = datetime.now()
        confidence_scores = {}
        
        try:
            # Step 1: Classify Business Unit
            logger.info("Step 1: Classifying business unit...")
            unit_response: RunResponse = self.business_unit_classifier.run(
                f"Conversa para classificar:\n\n{conversation_history}"
            )
            
            if not unit_response.content or not isinstance(unit_response.content, BusinessUnitSelection):
                raise ValueError("Invalid business unit classification response")
            
            business_unit = unit_response.content.unidade_negocio.value
            confidence_scores["business_unit"] = unit_response.content.confidence
            
            logger.info(f"Business unit classified: {business_unit}")
            
            # Step 2: Classify Product
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
            
            logger.info(f"Product classified: {product}")
            
            # Step 3: Classify Motive
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
            
            logger.info(f"Motive classified: {motive}")
            
            # Step 4: Classify Submotive
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
            
            logger.info(f"Submotive classified: {submotive}")
            
            # Step 5: Validate and create final typification
            logger.info("Step 5: Validating typification hierarchy...")
            validation_result = validate_typification_path(
                business_unit, product, motive, submotive
            )
            
            if not validation_result.valid:
                raise ValueError(f"Invalid typification path: {validation_result.error_message}")
            
            # Create final typification
            final_typification = HierarchicalTypification(
                unidade_negocio=business_unit,
                produto=product,
                motivo=motive,
                submotivo=submotive,
                conclusao="Orientação"
            )
            
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
                escalated_to_human=False,  # Set based on actual escalation
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat()
            )
            
            # Save to session state
            self._save_typification_result(complete_typification)
            
            logger.info(f"Typification completed: {final_typification.hierarchy_path}")
            
            # Yield completion event
            yield WorkflowCompletedEvent(
                run_id=self.run_id,
                content={
                    "typification": final_typification.model_dump(),
                    "ticket": ticket_result.model_dump(),
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

def get_conversation_typification_workflow(debug_mode: bool = False) -> ConversationTypificationWorkflow:
    """Factory function to create a configured typification workflow"""
    
    return ConversationTypificationWorkflow(
        workflow_id="conversation-typification",
        storage=PostgresStorage(
            table_name="conversation_typification_workflows",
            db_url=db_url,
            mode="workflow",
            auto_upgrade_schema=True,
        ),
        debug_mode=debug_mode,
    )