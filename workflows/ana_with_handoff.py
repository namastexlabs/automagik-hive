"""
Ana Integration Workflow - Complete User Interaction with Human Handoff
=====================================================================

Workflow that integrates Ana team routing with human handoff processing.
Follows the pattern from TeamWorkflow example to execute teams within workflows.
"""

from datetime import datetime
from textwrap import dedent
from typing import Iterator, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.run.team import TeamRunResponse
from agno.storage.postgres import PostgresStorage
from agno.team.team import Team
from agno.workflow import RunResponse, Workflow
from db.session import db_url

from .human_handoff.models import ConversationContext, CustomerInfo, IssueDetails


class AnaWithHandoffWorkflow(Workflow):
    """
    Complete customer service workflow integrating Ana team with human handoff.
    
    Flow:
    1. Ana team processes user query and routes appropriately
    2. If human escalation is needed, continues with human handoff workflow
    3. Returns final result to user
    
    This eliminates the need for external execution handlers.
    """
    
    description: str = dedent("""\
    Workflow completo de atendimento com Ana e escalação humana.
    
    Integra o roteamento inteligente da equipe Ana com o processo
    estruturado de transferência para atendimento humano.
    """)
    
    def __init__(self, **kwargs):
        # Extract custom parameters
        self.debug_mode = kwargs.pop('debug_mode', False)
        self.whatsapp_enabled = kwargs.pop('whatsapp_enabled', True)
        
        super().__init__(**kwargs)
        
        # Initialize Ana team (dynamically imported to avoid circular imports)
        self._ana_team = None
        self._human_handoff_workflow = None
    
    @property
    def ana_team(self) -> Team:
        """Lazy load Ana team to avoid circular imports"""
        if self._ana_team is None:
            from teams.ana.team import get_ana_team
            self._ana_team = get_ana_team(
                debug_mode=self.debug_mode
            )
        return self._ana_team
    
    @property 
    def human_handoff_workflow(self):
        """Lazy load human handoff workflow"""
        if self._human_handoff_workflow is None:
            from .human_handoff.workflow import get_human_handoff_workflow
            self._human_handoff_workflow = get_human_handoff_workflow(
                whatsapp_enabled=self.whatsapp_enabled
            )
        return self._human_handoff_workflow
    
    # Context extractor agent for building conversation context
    context_extractor: Agent = Agent(
        name="Context Extractor",
        model=Claude(id="claude-sonnet-4-20250514"),
        description="Extract and structure conversation context for handoff",
        instructions=dedent("""\
        Analise a conversa e extraia informações estruturadas.
        
        EXTRAIR:
        - Mensagem atual do usuário
        - Histórico da conversa
        - Motivo da escalação
        - Informações do cliente mencionadas
        - Contexto do problema
        
        FORMATO DE SAÍDA:
        - session_id: ID da sessão
        - customer_message: Mensagem atual
        - escalation_reason: Motivo da escalação
        - conversation_history: Histórico completo
        - customer_info: Informações do cliente
        """),
        response_model=ConversationContext,
        structured_outputs=True
    )
    
    def run(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Iterator[RunResponse]:
        """
        Execute complete workflow: Ana routing + human handoff if needed
        
        Args:
            user_message: Current user message
            session_id: Session identifier  
            conversation_history: Previous conversation context
            user_id: User identifier
        """
        
        if self.debug_mode:
            print(f"🔄 Ana Workflow starting for message: {user_message[:50]}...")
        
        # Step 1: Execute Ana team for intelligent routing
        print("Step 1: Ana team processing user message...")
        
        try:
            # Ana team processes the user message
            ana_response: TeamRunResponse = self.ana_team.run(user_message)
            
            if not ana_response or not ana_response.content:
                yield RunResponse(
                    run_id=self.run_id,
                    content="Desculpe, ocorreu um erro no atendimento. Tente novamente."
                )
                return
            
            # Check if Ana decided to escalate to human handoff
            ana_content = ana_response.content.lower()
            
            # Detection patterns for human escalation
            escalation_indicators = [
                "transferência para atendimento humano",
                "conectando você com atendimento humano",
                "protocolo de atendimento",
                "atendente humano",
                "escalação",
                "handoff"
            ]
            
            escalation_detected = any(indicator in ana_content for indicator in escalation_indicators)
            
            if escalation_detected:
                print("Step 2: Human escalation detected, continuing with handoff workflow...")
                
                # Step 2: Extract conversation context for handoff
                full_conversation = f"{conversation_history or ''}\n\nUsuário: {user_message}\nAna: {ana_response.content}"
                
                context_input = f"""
                Sessão: {session_id or 'new-session'}
                Mensagem atual: {user_message}
                Resposta da Ana: {ana_response.content}
                Histórico: {conversation_history or 'Início da conversa'}
                """
                
                context_response = self.context_extractor.run(context_input)
                
                # Step 3: Execute human handoff workflow
                print("Step 3: Executing human handoff workflow...")
                
                # Build conversation context
                if isinstance(context_response.content, ConversationContext):
                    conversation_context = context_response.content
                else:
                    # Fallback: create basic context
                    conversation_context = ConversationContext(
                        session_id=session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        customer_info=CustomerInfo(
                            customer_id=user_id or "unknown",
                            session_id=session_id or "unknown"
                        ),
                        issue_details=IssueDetails(
                            summary=user_message,
                            conversation_history=full_conversation
                        ),
                        conversation_history=full_conversation,
                        current_message=user_message,
                        start_time=datetime.now(),
                        last_interaction=datetime.now(),
                        interaction_count=1
                    )
                
                # Execute human handoff workflow
                handoff_results = list(self.human_handoff_workflow.run(
                    conversation_context=conversation_context,
                    escalation_trigger="ana_team_decision"
                ))
                
                if handoff_results:
                    # Return the handoff result (protocol and confirmation)
                    yield handoff_results[-1]
                else:
                    yield RunResponse(
                        run_id=self.run_id,
                        content="Erro na transferência para atendimento humano. Tente novamente."
                    )
            
            else:
                # Ana handled the query normally - return Ana's response
                print("Ana handled query normally, returning response...")
                yield RunResponse(
                    run_id=self.run_id,
                    content=ana_response.content,
                    metadata={
                        "workflow_type": "ana_routing",
                        "escalation_occurred": False,
                        "handled_by": "ana_team"
                    }
                )
        
        except Exception as e:
            print(f"❌ Workflow error: {str(e)}")
            yield RunResponse(
                run_id=self.run_id,
                content=f"Desculpe, ocorreu um erro no atendimento: {str(e)}. Tente novamente ou contate nosso suporte.",
                metadata={
                    "workflow_type": "ana_with_handoff",
                    "error": True,
                    "exception": str(e)
                }
            )


def get_ana_with_handoff_workflow(
    debug_mode: bool = False,
    whatsapp_enabled: bool = True
) -> AnaWithHandoffWorkflow:
    """Factory function to create the complete Ana + handoff workflow"""
    
    return AnaWithHandoffWorkflow(
        workflow_id="ana-with-handoff",
        storage=PostgresStorage(
            table_name="ana_handoff_workflows",
            db_url=db_url,
            auto_upgrade_schema=True
        ),
        debug_mode=debug_mode,
        whatsapp_enabled=whatsapp_enabled
    )