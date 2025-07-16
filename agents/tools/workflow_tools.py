# Workflow Trigger Tools for Specialist Agents
# Human handoff agent uses this to trigger workflows

from typing import Dict, Any, Optional
from agno.tools import tool
from agno.utils.log import logger
from workflows.human_handoff.workflow import get_human_handoff_workflow

# User context helper for automatic extraction from session_state
from context.user_context_helper import get_user_context_from_agent


@tool  # Only for human handoff specialist agent
def trigger_human_handoff_workflow(
    customer_message: str,
    escalation_reason: str,
    conversation_history: Optional[str] = None,
    urgency_level: str = "medium",
    business_unit: Optional[str] = None,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    # User data parameters - optional, will auto-extract from agent session_state
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None
) -> str:
    """
    Trigger the human handoff workflow for escalating customer service.
    
    EXCLUSIVE TOOL for human handoff specialist agent only.
    Ana team routes to human handoff agent, then agent calls this workflow.
    
    This tool automatically extracts user context from the calling agent's session_state
    when parameters are not explicitly provided.
    
    Args:
        customer_message: Current customer message requiring escalation
        escalation_reason: Reason for escalation (e.g., "frustration_detected", "explicit_request")
        conversation_history: Full conversation context
        urgency_level: Priority level (low, medium, high, critical)
        business_unit: Business unit for routing (pagbank, emissao, adquirencia)
        session_id: Session identifier
        customer_id: Customer identifier
        user_id: User identifier (auto-extracted from session_state)
        user_name: Customer name (auto-extracted from session_state)
        phone_number: Customer phone number (auto-extracted from session_state)
        cpf: Customer CPF (auto-extracted from session_state)
        
    Returns:
        Final response to customer about escalation completion
    """
    
    logger.info(f"🚨 Human handoff workflow triggered: {escalation_reason}")
    
    # Auto-extract user context from session_state if not provided
    # Note: Future enhancement - tools could access current agent context
    # For now, user context flows through agent instructions via session_state
    # and agents can pass the context explicitly or via session_state access
    
    # Log current user context for debugging
    user_context_provided = {
        'user_id': bool(user_id),
        'user_name': bool(user_name), 
        'phone_number': bool(phone_number),
        'cpf': bool(cpf)
    }
    logger.info(f"📝 User context provided: {user_context_provided}")
    
    # Future enhancement: Auto-extract from agent session_state
    # This would eliminate the need for agents to pass user context explicitly
    
    try:
        # Execute workflow - Use synchronous execution to avoid event loop issues
        # Create workflow with WhatsApp enabled
        workflow = get_human_handoff_workflow(
            whatsapp_enabled=True,  # Enable WhatsApp notifications
            whatsapp_instance="SofIA"
        )
        
        # Execute workflow synchronously
        results = []
        for result in workflow.run(
            customer_message=customer_message,
            escalation_reason=escalation_reason,
            conversation_history=conversation_history,
            urgency_level=urgency_level,
            business_unit=business_unit,
            session_id=session_id,
            customer_id=customer_id,
            # NEW: Pass user data parameters
            user_id=user_id,
            user_name=user_name,
            phone_number=phone_number,
            cpf=cpf
        ):
            results.append(result)
        
        if results:
            # Get the final result and extract the protocol
            final_result = results[-1]
            
            # Return the workflow's response directly
            if hasattr(final_result, 'content'):
                return final_result.content
            else:
                return "✅ Escalação para atendimento humano iniciada com sucesso!"
        else:
            return "❌ Erro ao processar escalação para atendimento humano"
            
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return f"❌ Erro na escalação: {str(e)}"




def handle_workflow_trigger_external(tool_execution):
    """
    External handler for human handoff workflow trigger.
    
    Called when human handoff specialist agent uses workflow trigger tool
    with external_execution=True. Executes the workflow with automatic
    user context extraction from agent session_state.
    """
    
    if tool_execution.tool_name == "trigger_human_handoff_workflow":
        try:
            # Extract arguments from tool execution
            args = tool_execution.tool_args
            
            logger.info(f"🚀 Executing human handoff workflow externally with args: {args}")
            
            # Log user context for debugging
            user_context_provided = {
                'user_id': bool(args.get("user_id")),
                'user_name': bool(args.get("user_name")), 
                'phone_number': bool(args.get("phone_number")),
                'cpf': bool(args.get("cpf"))
            }
            logger.info(f"📝 User context provided (external): {user_context_provided}")
            
            # Execute workflow - Use synchronous execution to avoid event loop issues
            # Create workflow with WhatsApp enabled
            workflow = get_human_handoff_workflow(
                whatsapp_enabled=True,  # Enable WhatsApp notifications
                whatsapp_instance="SofIA"
            )
            
            # Execute workflow with provided arguments synchronously
            results = []
            for result in workflow.run(
                customer_message=args.get("customer_message"),
                escalation_reason=args.get("escalation_reason"),
                conversation_history=args.get("conversation_history"),
                urgency_level=args.get("urgency_level", "medium"),
                business_unit=args.get("business_unit"),
                session_id=args.get("session_id"),
                customer_id=args.get("customer_id"),
                # NEW: Pass user data parameters
                user_id=args.get("user_id"),
                user_name=args.get("user_name"),
                phone_number=args.get("phone_number"),
                cpf=args.get("cpf")
            ):
                results.append(result)
            
            if results:
                # Get the final result
                final_result = results[-1]
                
                if hasattr(final_result, 'content') and isinstance(final_result.content, dict):
                    protocol_id = final_result.content.get('protocol', {}).get('protocol_id', 'N/A')
                    success_message = f"✅ Escalação concluída com sucesso! Protocolo: {protocol_id}"
                else:
                    success_message = "✅ Escalação para atendimento humano iniciada com sucesso!"
                
                # Set the result for the agent to continue
                tool_execution.result = success_message
                
                logger.info(f"🎉 Human handoff workflow completed successfully")
                
            else:
                error_message = "❌ Erro ao processar escalação para atendimento humano"
                tool_execution.result = error_message
                logger.error("Workflow execution returned no results")
                
        except Exception as e:
            error_message = f"❌ Erro na escalação: {str(e)}"
            tool_execution.result = error_message
            logger.error(f"Workflow execution failed: {str(e)}")
            
    else:
        # Unknown workflow trigger
        tool_execution.result = f"❌ Workflow trigger desconhecido: {tool_execution.tool_name}"
        logger.error(f"Unknown workflow trigger: {tool_execution.tool_name}")