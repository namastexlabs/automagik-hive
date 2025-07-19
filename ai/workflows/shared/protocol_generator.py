
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from agno.utils.log import logger


class UnifiedProtocol(BaseModel):
    """
    Unified protocol model for all workflows.
    
    Consolidates protocol generation from human handoff and typification workflows
    into a single, consistent format.
    """
    protocol_id: str = Field(..., description="Unique protocol identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Protocol creation timestamp")
    protocol_type: str = Field(..., description="Type of protocol: escalation, typification, or finalization")
    
    # Customer information
    customer_info: Dict[str, Any] = Field(default_factory=dict, description="Customer details")
    
    # Workflow-specific data
    workflow_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow-specific information")
    
    # Status tracking
    status: str = Field(default="active", description="Protocol status")
    assigned_team: Optional[str] = Field(None, description="Assigned team or department")
    
    # Metadata
    created_by: str = Field(default="system", description="Entity that created the protocol")
    notes: Optional[str] = Field(None, description="Additional notes or comments")


def generate_protocol(
    session_id: str,
    protocol_type: str,
    customer_info: Optional[Dict[str, Any]] = None,
    workflow_data: Optional[Dict[str, Any]] = None,
    assigned_team: Optional[str] = None,
    notes: Optional[str] = None
) -> UnifiedProtocol:
    """
    Generate a unified protocol for any workflow type.
    
    Args:
        session_id: Session identifier
        protocol_type: Type of protocol (escalation, typification, finalization)
        customer_info: Customer details dictionary
        workflow_data: Workflow-specific data
        assigned_team: Team assignment
        notes: Additional notes
        
    Returns:
        UnifiedProtocol: Generated protocol object
    """
    
    # Generate consistent protocol ID format
    timestamp = datetime.now()
    protocol_id = f"PROTO-{session_id}-{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    logger.info(f"🎟️ Generating protocol: {protocol_id} (type: {protocol_type})")
    
    # Create unified protocol
    protocol = UnifiedProtocol(
        protocol_id=protocol_id,
        session_id=session_id,
        timestamp=timestamp,
        protocol_type=protocol_type,
        customer_info=customer_info or {},
        workflow_data=workflow_data or {},
        assigned_team=assigned_team,
        notes=notes
    )
    
    logger.info(f"✅ Protocol generated successfully: {protocol_id}")
    return protocol


def save_protocol_to_session_state(
    protocol: UnifiedProtocol,
    session_state: Dict[str, Any]
) -> None:
    """
    Save protocol to session state for agent access.
    
    Args:
        protocol: Protocol object to save
        session_state: Session state dictionary to update
    """
    
    if "protocols" not in session_state:
        session_state["protocols"] = {}
    
    session_state["protocols"][protocol.protocol_id] = {
        "protocol_id": protocol.protocol_id,
        "protocol_type": protocol.protocol_type,
        "timestamp": protocol.timestamp.isoformat(),
        "customer_info": protocol.customer_info,
        "workflow_data": protocol.workflow_data,
        "assigned_team": protocol.assigned_team,
        "status": protocol.status,
        "notes": protocol.notes
    }
    
    # Keep track of the latest protocol
    session_state["latest_protocol"] = protocol.protocol_id
    
    logger.info(f"💾 Protocol saved to session state: {protocol.protocol_id}")


def get_protocol_from_session_state(
    session_state: Dict[str, Any],
    protocol_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve protocol from session state.
    
    Args:
        session_state: Session state dictionary
        protocol_id: Specific protocol ID to retrieve (optional, defaults to latest)
        
    Returns:
        Protocol data or None if not found
    """
    
    if "protocols" not in session_state:
        return None
    
    # Use latest protocol if no specific ID provided
    if protocol_id is None:
        protocol_id = session_state.get("latest_protocol")
        
    if protocol_id is None:
        return None
    
    return session_state["protocols"].get(protocol_id)


def format_protocol_for_user(protocol_data: Dict[str, Any]) -> str:
    """
    Format protocol information for user display.
    
    Args:
        protocol_data: Protocol data dictionary
        
    Returns:
        Formatted protocol string for user
    """
    
    protocol_id = protocol_data.get("protocol_id", "N/A")
    protocol_type = protocol_data.get("protocol_type", "")
    
    # Basic protocol information
    if protocol_type == "escalation":
        return f"Seu atendimento foi encaminhado para nossa equipe especializada. Protocolo: {protocol_id}"
    elif protocol_type == "typification":
        return f"Sua solicitação foi registrada e tipificada. Protocolo: {protocol_id}"
    elif protocol_type == "finalization":
        return f"Seu atendimento foi finalizado com sucesso. Protocolo: {protocol_id}"
    elif protocol_type == "finalization_with_typification":
        return f"Seu atendimento foi finalizado e tipificado automaticamente. Protocolo: {protocol_id}"
    else:
        return f"Protocolo gerado: {protocol_id}"


def generate_protocol_id(session_id: str, protocol_type: str) -> str:
    """
    Generate a simple protocol ID for quick use.
    
    Args:
        session_id: Session identifier
        protocol_type: Type of protocol
        
    Returns:
        Generated protocol ID
    """
    timestamp = datetime.now()
    return f"PROTO-{session_id}-{timestamp.strftime('%Y%m%d%H%M%S')}"