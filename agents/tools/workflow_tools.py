# Workflow Trigger Tools for Agents
# Allows agents to trigger workflows during their execution

from typing import Dict, Any, Optional
from agno.tools import tool
from agno.utils.log import logger
from workflows.human_handoff.workflow import get_human_handoff_workflow


@tool  # Remove external_execution=True - execute directly
def trigger_human_handoff_workflow(
    customer_message: str,
    escalation_reason: str,
    conversation_history: Optional[str] = None,
    urgency_level: str = "medium",
    business_unit: Optional[str] = None,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None
) -> str:
    """
    Trigger the human handoff workflow for escalating customer service.
    
    This tool allows agents to escalate conversations to human agents
    with proper context preservation and protocol generation.
    
    Args:
        customer_message: Current customer message requiring escalation
        escalation_reason: Reason for escalation (e.g., "frustration_detected", "explicit_request")
        conversation_history: Full conversation context
        urgency_level: Priority level (low, medium, high, critical)
        business_unit: Business unit for routing (pagbank, emissao, adquirencia)
        session_id: Session identifier
        customer_id: Customer identifier
        
    Returns:
        Status message about escalation initiation
    """
    
    logger.info(f"🚨 Human handoff workflow triggered: {escalation_reason}")
    
    try:
        # Execute the workflow directly within the tool
        workflow = get_human_handoff_workflow(debug_mode=True)
        
        # Execute workflow with provided arguments
        results = list(workflow.run(
            customer_message=customer_message,
            escalation_reason=escalation_reason,
            conversation_history=conversation_history,
            urgency_level=urgency_level,
            business_unit=business_unit,
            session_id=session_id,
            customer_id=customer_id
        ))
        
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
    External handler for workflow trigger tools.
    
    This function is called when an agent uses a workflow trigger tool
    with external_execution=True. It executes the actual workflow.
    """
    
    if tool_execution.tool_name == "trigger_human_handoff_workflow":
        try:
            # Extract arguments from tool execution
            args = tool_execution.tool_args
            
            logger.info(f"🚀 Executing human handoff workflow externally with args: {args}")
            
            # Create and run the workflow
            workflow = get_human_handoff_workflow(debug_mode=True)
            
            # Execute workflow with provided arguments
            results = list(workflow.run(
                customer_message=args.get("customer_message"),
                escalation_reason=args.get("escalation_reason"),
                conversation_history=args.get("conversation_history"),
                urgency_level=args.get("urgency_level", "medium"),
                business_unit=args.get("business_unit"),
                session_id=args.get("session_id"),
                customer_id=args.get("customer_id")
            ))
            
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