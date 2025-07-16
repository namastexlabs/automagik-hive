"""
Validation Schemas for Agno Standard Contract
=============================================

Pydantic schemas for validating workflow_input parameters according to Agno standards.
Provides type safety and validation for the migration process.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class UrgencyLevel(str, Enum):
    """Supported urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BusinessUnit(str, Enum):
    """Supported business units"""
    PAGBANK = "pagbank"
    EMISSAO = "emissao"
    ADQUIRENCIA = "adquirencia"
    ADQUIRENCIA_WEB = "adquirencia_web"
    GENERAL = "general"


class ConversationData(BaseModel):
    """Standard conversation data structure"""
    message: str = Field(..., description="Primary message content")
    history: Optional[str] = Field(None, description="Previous conversation history")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    urgency_level: UrgencyLevel = Field(UrgencyLevel.MEDIUM, description="Priority level")
    business_unit: BusinessUnit = Field(BusinessUnit.GENERAL, description="Target business unit")
    summary: Optional[str] = Field(None, description="Conversation summary")
    
    @validator('message')
    def validate_message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()
    
    @validator('history')
    def validate_history_length(cls, v):
        if v and len(v) > 10000:  # 10K character limit
            raise ValueError("Conversation history too long (max 10,000 characters)")
        return v


class CustomerData(BaseModel):
    """Standard customer data structure"""
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    customer_name: Optional[str] = Field(None, description="Customer full name")
    customer_cpf: Optional[str] = Field(None, description="Customer CPF document")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    customer_email: Optional[str] = Field(None, description="Customer email address")
    account_type: Optional[str] = Field(None, description="Account type classification")
    satisfaction_data: Optional[Dict[str, Any]] = Field(None, description="Customer satisfaction metrics")
    
    @validator('customer_cpf')
    def validate_cpf_format(cls, v):
        if v and not cls._is_valid_cpf_format(v):
            raise ValueError("Invalid CPF format (expected XXX.XXX.XXX-XX or XXXXXXXXXXX)")
        return v
    
    @validator('customer_phone')
    def validate_phone_format(cls, v):
        if v and not cls._is_valid_phone_format(v):
            raise ValueError("Invalid phone format (expected +55XXXXXXXXXXX or similar)")
        return v
    
    @validator('customer_email')
    def validate_email_format(cls, v):
        if v and '@' not in v:
            raise ValueError("Invalid email format")
        return v
    
    @staticmethod
    def _is_valid_cpf_format(cpf: str) -> bool:
        """Validate CPF format (Brazilian tax ID)"""
        import re
        # Accept both XXX.XXX.XXX-XX and XXXXXXXXXXX formats
        pattern = r'^(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})$'
        return bool(re.match(pattern, cpf))
    
    @staticmethod
    def _is_valid_phone_format(phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Accept international format +55XXXXXXXXXXX or local XXXXXXXXXXX
        pattern = r'^(\+55\d{10,11}|\d{10,11})$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


class SessionData(BaseModel):
    """Standard session data structure"""
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp: Optional[str] = Field(None, description="Session timestamp")
    
    @validator('session_id')
    def validate_session_id_format(cls, v):
        if v and len(v) < 3:
            raise ValueError("Session ID too short (minimum 3 characters)")
        return v
    
    @validator('timestamp')
    def validate_timestamp_format(cls, v):
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Invalid timestamp format (expected ISO format)")
        return v


class ProcessData(BaseModel):
    """Standard process metadata structure"""
    escalation_data: Optional[Dict[str, Any]] = Field(None, description="Escalation metadata")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional process metadata")
    timestamp: Optional[str] = Field(None, description="Process timestamp")
    migration_source: Optional[str] = Field(None, description="Source of parameter migration")
    workflow_version: Optional[str] = Field("2.0", description="Workflow version")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now().isoformat()


class HumanHandoffWorkflowInput(BaseModel):
    """Complete workflow input schema for Human Handoff"""
    conversation: ConversationData = Field(..., description="Conversation information")
    customer: Optional[CustomerData] = Field(None, description="Customer information")
    session: Optional[SessionData] = Field(None, description="Session information")
    process: Optional[ProcessData] = Field(None, description="Process metadata")
    
    @root_validator
    def validate_required_fields(cls, values):
        """Validate that required fields are present"""
        conversation = values.get('conversation')
        if not conversation:
            raise ValueError("conversation is required")
        
        # Auto-generate session_id if not provided
        session = values.get('session') or SessionData()
        if not session.session_id:
            session.session_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        values['session'] = session
        
        # Initialize process data if not provided
        if not values.get('process'):
            values['process'] = ProcessData()
        
        return values


class ConversationTypificationWorkflowInput(BaseModel):
    """Complete workflow input schema for Conversation Typification"""
    conversation: ConversationData = Field(..., description="Conversation to typify")
    customer: Optional[CustomerData] = Field(None, description="Customer information")
    session: Optional[SessionData] = Field(None, description="Session information")
    process: Optional[ProcessData] = Field(None, description="Process metadata")
    
    @validator('conversation')
    def validate_typification_conversation(cls, v):
        """Validate conversation data for typification"""
        # For typification, we need either 'message' or 'text' field
        if not hasattr(v, 'message') and not hasattr(v, 'text'):
            raise ValueError("conversation must have either 'message' or 'text' field for typification")
        return v
    
    @root_validator
    def validate_typification_fields(cls, values):
        """Validate fields specific to typification workflow"""
        conversation = values.get('conversation')
        if conversation and hasattr(conversation, 'text'):
            # Ensure text is not empty for typification
            if not conversation.text or not conversation.text.strip():
                raise ValueError("conversation.text cannot be empty for typification")
        
        # Auto-generate session_id if not provided
        session = values.get('session') or SessionData()
        if not session.session_id:
            session.session_id = f"typify-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        values['session'] = session
        
        return values


class StandardWorkflowResponse(BaseModel):
    """Standard response format for workflows"""
    status: str = Field(..., description="Execution status (completed/failed)")
    protocol_id: Optional[str] = Field(None, description="Generated protocol ID")
    user_message: str = Field(..., description="Message to display to user")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    migration_info: Optional[Dict[str, Any]] = Field(None, description="Migration tracking information")


class LegacyParameterMapping(BaseModel):
    """Mapping configuration for legacy parameter translation"""
    workflow_type: str = Field(..., description="Type of workflow")
    parameter_mappings: Dict[str, str] = Field(..., description="Legacy to standard parameter mappings")
    required_fields: List[str] = Field(..., description="Required fields for this workflow type")
    deprecated_fields: List[str] = Field(..., description="Fields that are deprecated")


# Validation functions for common use cases
def validate_human_handoff_input(workflow_input: Dict[str, Any]) -> HumanHandoffWorkflowInput:
    """
    Validate workflow input for human handoff workflow.
    
    Args:
        workflow_input: Raw workflow input dictionary
        
    Returns:
        HumanHandoffWorkflowInput: Validated and normalized input
        
    Raises:
        ValidationError: If input is invalid
    """
    return HumanHandoffWorkflowInput(**workflow_input)


def validate_typification_input(workflow_input: Dict[str, Any]) -> ConversationTypificationWorkflowInput:
    """
    Validate workflow input for conversation typification workflow.
    
    Args:
        workflow_input: Raw workflow input dictionary
        
    Returns:
        ConversationTypificationWorkflowInput: Validated and normalized input
        
    Raises:
        ValidationError: If input is invalid
    """
    return ConversationTypificationWorkflowInput(**workflow_input)


def create_workflow_input_template(workflow_type: str) -> Dict[str, Any]:
    """
    Create a template workflow_input structure for a given workflow type.
    
    Args:
        workflow_type: Type of workflow ('human_handoff' or 'conversation_typification')
        
    Returns:
        Dict[str, Any]: Template structure with example values
    """
    
    if workflow_type == "human_handoff":
        return {
            "conversation": {
                "message": "Customer needs assistance",
                "history": "Previous conversation context...",
                "escalation_reason": "Complex technical issue",
                "urgency_level": "medium",
                "business_unit": "general"
            },
            "customer": {
                "customer_id": "CUS123456",
                "customer_name": "João Silva",
                "customer_cpf": "123.456.789-00",
                "customer_phone": "+5511999999999",
                "customer_email": "joao@email.com"
            },
            "session": {
                "session_id": "sess_20250716_001",
                "user_id": "CUS123456"
            },
            "process": {
                "metadata": {
                    "source": "whatsapp",
                    "channel": "customer_service"
                }
            }
        }
    elif workflow_type == "conversation_typification":
        return {
            "conversation": {
                "text": "Customer asking about payment methods and transaction fees...",
                "summary": "Payment inquiry conversation"
            },
            "customer": {
                "customer_id": "CUS123456",
                "satisfaction_data": {
                    "nps_score": 8,
                    "feedback": "Helpful service"
                }
            },
            "session": {
                "session_id": "typify_20250716_001"
            },
            "process": {
                "escalation_data": None,
                "metadata": {
                    "source": "chat",
                    "agent_id": "ana_assistant"
                }
            }
        }
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")


# Example usage and testing
if __name__ == "__main__":
    print("🔍 Testing Workflow Input Validation")
    print("=" * 40)
    
    # Test 1: Valid human handoff input
    print("\n1. Testing Human Handoff Input Validation:")
    try:
        valid_input = create_workflow_input_template("human_handoff")
        validated = validate_human_handoff_input(valid_input)
        print(f"✅ Valid input: {validated.conversation.message}")
        print(f"📋 Session ID: {validated.session.session_id}")
        print(f"👤 Customer: {validated.customer.customer_name}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    # Test 2: Invalid input (missing required field)
    print("\n2. Testing Invalid Input:")
    try:
        invalid_input = {"customer": {"customer_id": "123"}}  # Missing conversation
        validate_human_handoff_input(invalid_input)
        print("❌ Should have failed validation")
    except Exception as e:
        print(f"✅ Correctly caught validation error: {e}")
    
    # Test 3: Typification input validation
    print("\n3. Testing Typification Input Validation:")
    try:
        typification_input = create_workflow_input_template("conversation_typification")
        validated = validate_typification_input(typification_input)
        print(f"✅ Valid typification input: {len(validated.conversation.text)} chars")
        print(f"📋 Session ID: {validated.session.session_id}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    # Test 4: Schema serialization
    print("\n4. Testing Schema Serialization:")
    try:
        input_data = create_workflow_input_template("human_handoff")
        validated = validate_human_handoff_input(input_data)
        
        # Convert to JSON and back
        json_data = validated.json()
        print(f"✅ JSON serialization successful: {len(json_data)} chars")
        
        # Parse back from JSON
        parsed = HumanHandoffWorkflowInput.parse_raw(json_data)
        print(f"✅ JSON parsing successful: {parsed.conversation.message}")
        
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
    
    print("\n✨ Validation testing completed!")