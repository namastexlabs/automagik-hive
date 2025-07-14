# Human Handoff Workflow
# Triggered when Ana Team routes to human escalation

from typing import Iterator, Optional
from agno.workflow import Workflow, RunResponse
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.utils.log import logger
from agno.storage.postgres import PostgresStorage

# V2 Database infrastructure
from db.session import db_url


class HumanHandoffWorkflow(Workflow):
    """
    Workflow for handling human escalation scenarios.
    
    This workflow is triggered when the Ana Team determines that human
    intervention is needed. It handles ticket creation, context preservation,
    and proper handoff to human agents.
    """
    
    description: str = "Human escalation workflow for complex or frustrated customer cases"
    
    # Context Analyzer: Analyzes conversation context for handoff
    context_analyzer = Agent(
        name="Context Analyzer",
        role="Analyze conversation context for human handoff",
        model=Claude(id="claude-sonnet-4-20250514"),
        instructions=[
            "Analyze the conversation context to extract key information for human agents.",
            "Identify the customer's main issue, frustration level, and priority.",
            "Summarize previous attempts to resolve the issue.",
            "Highlight any security or compliance concerns.",
            "Provide clear context for the human agent to continue the conversation."
        ],
        markdown=True
    )
    
    # Ticket Creator: Creates structured tickets for human agents
    ticket_creator = Agent(
        name="Ticket Creator", 
        role="Create structured support tickets",
        model=Claude(id="claude-sonnet-4-20250514"),
        instructions=[
            "Create a structured support ticket with all relevant information.",
            "Include customer details, issue summary, urgency level, and context.",
            "Format the ticket for easy consumption by human agents.",
            "Assign appropriate priority levels based on issue severity.",
            "Include any compliance or security flags if applicable."
        ],
        markdown=True
    )
    
    # Handoff Coordinator: Manages the actual handoff process
    handoff_coordinator = Agent(
        name="Handoff Coordinator",
        role="Coordinate handoff to human agents",
        model=Claude(id="claude-sonnet-4-20250514"),
        instructions=[
            "Coordinate the handoff process to human agents.",
            "Send appropriate notifications to the support team.",
            "Provide customer with handoff confirmation and expectations.",
            "Ensure all context is properly transferred.",
            "Set up monitoring for handoff completion."
        ],
        markdown=True
    )
    
    def run(
        self,
        customer_query: str,
        conversation_history: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None,
        urgency_level: str = "medium",
        business_unit: Optional[str] = None
    ) -> Iterator[RunResponse]:
        """
        Execute the human handoff workflow.
        
        Args:
            customer_query: The current customer query
            conversation_history: Previous conversation context
            escalation_reason: Why escalation was triggered
            customer_id: Customer identifier
            session_id: Session identifier
            urgency_level: Priority level (low, medium, high, critical)
            business_unit: Which business unit this relates to
        """
        
        logger.info(f"Starting human handoff workflow for session {session_id}")
        
        # Step 1: Analyze conversation context
        logger.info("Analyzing conversation context...")
        context_prompt = f"""
        Analyze this customer interaction for human handoff:
        
        Customer Query: {customer_query}
        Escalation Reason: {escalation_reason or 'Not specified'}
        Business Unit: {business_unit or 'General'}
        Urgency: {urgency_level}
        
        Conversation History:
        {conversation_history or 'No previous history'}
        
        Provide a comprehensive analysis including:
        1. Customer's main issue and pain points
        2. Escalation triggers that led to human handoff
        3. Key context human agents need to know
        4. Recommended approach for resolution
        5. Any compliance or security considerations
        """
        
        context_analysis = self.context_analyzer.run(context_prompt)
        if not context_analysis or not context_analysis.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Erro: Não foi possível analisar o contexto da conversa."
            )
            return
            
        # Step 2: Create structured ticket
        logger.info("Creating support ticket...")
        ticket_prompt = f"""
        Create a structured support ticket based on this analysis:
        
        {context_analysis.content}
        
        Customer ID: {customer_id or 'Unknown'}
        Session ID: {session_id or 'Unknown'}
        
        Format the ticket with:
        - Ticket ID (generate unique)
        - Priority Level
        - Business Unit
        - Issue Summary
        - Customer Details
        - Context Summary
        - Recommended Actions
        - SLA Requirements
        """
        
        ticket_response = self.ticket_creator.run(ticket_prompt)
        if not ticket_response or not ticket_response.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Erro: Não foi possível criar o ticket de suporte."
            )
            return
        
        # Step 3: Execute handoff coordination
        logger.info("Coordinating handoff to human agents...")
        handoff_prompt = f"""
        Coordinate the handoff process with this ticket information:
        
        {ticket_response.content}
        
        Tasks to complete:
        1. Send notification to appropriate support team
        2. Prepare customer communication about handoff
        3. Set up monitoring for response times
        4. Ensure context preservation
        5. Provide customer with next steps
        
        Respond with:
        - Customer notification message (in Portuguese)
        - Internal notification details
        - Expected response timeframes
        - Handoff completion confirmation
        """
        
        handoff_response = self.handoff_coordinator.run(handoff_prompt)
        if not handoff_response or not handoff_response.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Erro: Não foi possível coordenar a transferência para atendimento humano."
            )
            return
        
        # Final response with customer notification
        logger.info("Human handoff workflow completed successfully")
        yield RunResponse(
            run_id=self.run_id,
            content=handoff_response.content,
            metadata={
                "workflow_type": "human_handoff",
                "escalation_reason": escalation_reason,
                "urgency_level": urgency_level,
                "business_unit": business_unit,
                "session_id": session_id,
                "customer_id": customer_id
            }
        )


# Convenience function for triggering from Ana Team
def get_human_handoff_workflow(
    debug_mode: bool = False,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> HumanHandoffWorkflow:
    """
    Factory function to create HumanHandoffWorkflow instance.
    
    Args:
        debug_mode: Enable debug mode
        session_id: Session ID for tracking
        user_id: User ID for tracking
        
    Returns:
        Configured HumanHandoffWorkflow instance
    """
    return HumanHandoffWorkflow(
        workflow_id="human-handoff",
        name="Human Handoff Workflow",
        description="Escalate conversations to human agents with proper context transfer",
        session_id=session_id,
        user_id=user_id,
        storage=PostgresStorage(
            table_name="human_handoff_workflows",
            db_url=db_url,
            mode="workflow",
            auto_upgrade_schema=True,
        ),
        debug_mode=debug_mode,
    )


def trigger_human_handoff(
    customer_query: str,
    escalation_reason: str,
    conversation_history: Optional[str] = None,
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
    business_unit: Optional[str] = None,
    urgency_level: str = "medium"
) -> Iterator[RunResponse]:
    """
    Trigger human handoff workflow from Ana Team routing.
    
    This function can be called when Ana Team determines human
    escalation is needed, instead of routing to a human agent.
    """
    workflow = HumanHandoffWorkflow()
    return workflow.run(
        customer_query=customer_query,
        conversation_history=conversation_history,
        escalation_reason=escalation_reason,
        customer_id=customer_id,
        session_id=session_id,
        urgency_level=urgency_level,
        business_unit=business_unit
    )


if __name__ == "__main__":
    # Test the workflow
    test_response = trigger_human_handoff(
        customer_query="Estou muito frustrado, nada funciona no aplicativo!",
        escalation_reason="Customer frustration detected",
        conversation_history="Customer reported multiple app issues over 20 minutes",
        urgency_level="high",
        business_unit="PagBank"
    )
    
    for response in test_response:
        print(response.content)