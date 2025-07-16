# Parameter Standardization Strategy
## Migrating from Custom Parameters to Agno Standard Contract

### Executive Summary

This document outlines a comprehensive migration strategy to transition from custom workflow parameters to Agno framework standards while maintaining backward compatibility. The strategy ensures existing clients continue working during the transition period with a clear deprecation timeline.

### Current State Analysis

#### Existing Custom Parameters

**Human Handoff Workflow:**
```python
def run(
    customer_message: Optional[str] = None,
    escalation_reason: Optional[str] = None,
    conversation_history: Optional[str] = None,
    urgency_level: str = "medium",
    business_unit: Optional[str] = None,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
)
```

**Conversation Typification Workflow:**
```python
def run(
    conversation_text: str,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    satisfaction_data: Optional[CustomerSatisfactionData] = None,
    escalation_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None
)
```

#### Agno Standard Contract

- **Agents/Teams**: Use `message` parameter (string, dict, or structured message)
- **Workflows**: Use `workflow_input` parameter (structured dictionary)

### 1. Parameter Mapping Strategy

#### 1.1 Core Mapping Structure

```python
# Standard Agno contract for workflows
def run(
    self,
    workflow_input: Dict[str, Any],
    **kwargs
) -> Iterator[WorkflowCompletedEvent]:
    """
    Standard Agno workflow signature
    
    Args:
        workflow_input: Structured input containing all workflow parameters
        **kwargs: Additional optional parameters
    """
```

#### 1.2 Parameter Mapping Schema

**Human Handoff Workflow Mapping:**
```yaml
standard_parameter: workflow_input
structure:
  # Core conversation data
  conversation:
    message: customer_message || customer_query || "Default message"
    history: conversation_history
    escalation_reason: escalation_reason
    urgency_level: urgency_level
    business_unit: business_unit
  
  # Customer identification
  customer:
    customer_id: customer_id || user_id
    customer_name: user_name || customer_name
    customer_cpf: cpf || customer_cpf
    customer_phone: phone_number || customer_phone
    customer_email: customer_email
  
  # Session management
  session:
    session_id: session_id
    user_id: user_id || customer_id
```

**Conversation Typification Workflow Mapping:**
```yaml
standard_parameter: workflow_input
structure:
  # Primary content
  conversation:
    text: conversation_text
    summary: derived_from_conversation_text
  
  # Customer context
  customer:
    customer_id: customer_id
    satisfaction_data: satisfaction_data
  
  # Process metadata
  process:
    session_id: session_id
    escalation_data: escalation_data
    metadata: metadata
```

### 2. Backward Compatibility Implementation

#### 2.1 Parameter Translation Layer

Create a `ParameterTranslator` class to handle legacy parameter mapping:

```python
# workflows/shared/parameter_translator.py
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import warnings

@dataclass
class StandardWorkflowInput:
    """Standard workflow input structure"""
    conversation: Dict[str, Any]
    customer: Dict[str, Any]
    session: Dict[str, Any]
    process: Dict[str, Any]

class ParameterTranslator:
    """Handles translation between legacy and standard parameters"""
    
    @staticmethod
    def translate_human_handoff(
        # Legacy parameters
        customer_message: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        conversation_history: Optional[str] = None,
        urgency_level: str = "medium",
        business_unit: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        cpf: Optional[str] = None,
        # Standard parameter
        workflow_input: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> StandardWorkflowInput:
        """Translate legacy human handoff parameters to standard format"""
        
        # If workflow_input provided, use it (new standard)
        if workflow_input:
            return StandardWorkflowInput(
                conversation=workflow_input.get('conversation', {}),
                customer=workflow_input.get('customer', {}),
                session=workflow_input.get('session', {}),
                process=workflow_input.get('process', {})
            )
        
        # Legacy parameter warning
        warnings.warn(
            "Legacy parameters are deprecated. Use 'workflow_input' parameter. "
            "Legacy support will be removed in v3.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Map legacy parameters to standard structure
        return StandardWorkflowInput(
            conversation={
                "message": customer_message or kwargs.get('customer_query', 'Human assistance requested'),
                "history": conversation_history or "",
                "escalation_reason": escalation_reason,
                "urgency_level": urgency_level,
                "business_unit": business_unit or "general"
            },
            customer={
                "customer_id": customer_id or user_id or "unknown",
                "customer_name": user_name or kwargs.get('customer_name'),
                "customer_cpf": cpf or kwargs.get('customer_cpf'),
                "customer_phone": phone_number or kwargs.get('customer_phone'),
                "customer_email": kwargs.get('customer_email')
            },
            session={
                "session_id": session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "user_id": user_id or customer_id or "unknown"
            },
            process={
                "timestamp": datetime.now().isoformat(),
                "migration_source": "legacy_parameters"
            }
        )
    
    @staticmethod
    def translate_conversation_typification(
        # Legacy parameters
        conversation_text: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        satisfaction_data: Optional[Any] = None,
        escalation_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        # Standard parameter
        workflow_input: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> StandardWorkflowInput:
        """Translate legacy typification parameters to standard format"""
        
        if workflow_input:
            return StandardWorkflowInput(
                conversation=workflow_input.get('conversation', {}),
                customer=workflow_input.get('customer', {}),
                session=workflow_input.get('session', {}),
                process=workflow_input.get('process', {})
            )
        
        # Legacy parameter warning
        warnings.warn(
            "Legacy parameters are deprecated. Use 'workflow_input' parameter. "
            "Legacy support will be removed in v3.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        
        return StandardWorkflowInput(
            conversation={
                "text": conversation_text or "",
                "summary": f"Conversation for typification: {len(conversation_text or '')} chars"
            },
            customer={
                "customer_id": customer_id or "unknown",
                "satisfaction_data": satisfaction_data
            },
            session={
                "session_id": session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            },
            process={
                "escalation_data": escalation_data,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "migration_source": "legacy_parameters"
            }
        )
```

#### 2.2 Updated Workflow Signatures

**Human Handoff Workflow V2:**
```python
def run(
    self,
    # Standard Agno parameter (NEW)
    workflow_input: Optional[Dict[str, Any]] = None,
    
    # Legacy parameters (DEPRECATED - remove in v3.0.0)
    customer_message: Optional[str] = None,
    escalation_reason: Optional[str] = None,
    conversation_history: Optional[str] = None,
    urgency_level: str = "medium",
    business_unit: Optional[str] = None,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    cpf: Optional[str] = None,
    **kwargs
) -> Iterator[WorkflowCompletedEvent]:
    """
    Execute human handoff workflow with standard Agno contract.
    
    Args:
        workflow_input: Standard workflow input (PREFERRED)
            {
                "conversation": {
                    "message": str,
                    "history": str,
                    "escalation_reason": str,
                    "urgency_level": str,
                    "business_unit": str
                },
                "customer": {
                    "customer_id": str,
                    "customer_name": str,
                    "customer_cpf": str,
                    "customer_phone": str,
                    "customer_email": str
                },
                "session": {
                    "session_id": str,
                    "user_id": str
                }
            }
        
        Legacy parameters (DEPRECATED):
            customer_message: Use workflow_input.conversation.message
            escalation_reason: Use workflow_input.conversation.escalation_reason
            [... other legacy parameters ...]
    """
    
    # Use parameter translator for backward compatibility
    standard_input = ParameterTranslator.translate_human_handoff(
        workflow_input=workflow_input,
        customer_message=customer_message,
        escalation_reason=escalation_reason,
        conversation_history=conversation_history,
        urgency_level=urgency_level,
        business_unit=business_unit,
        session_id=session_id,
        customer_id=customer_id,
        user_id=user_id,
        user_name=user_name,
        phone_number=phone_number,
        cpf=cpf,
        **kwargs
    )
    
    # Continue with standard workflow logic using standard_input
    # ...existing workflow implementation using standard_input...
```

### 3. Migration Timeline

#### Phase 1: Preparation (Weeks 1-2)
- [ ] Implement `ParameterTranslator` class
- [ ] Update workflow signatures to accept both legacy and standard parameters
- [ ] Add deprecation warnings for legacy parameters
- [ ] Create migration utilities and documentation

#### Phase 2: Soft Migration (Weeks 3-4)
- [ ] Deploy workflows with dual parameter support
- [ ] Monitor deprecation warnings in logs
- [ ] Create migration scripts for existing clients
- [ ] Update API documentation with new standard

#### Phase 3: Client Migration (Weeks 5-8)
- [ ] Migrate internal clients to use `workflow_input`
- [ ] Provide migration support for external clients
- [ ] Track usage metrics for legacy vs standard parameters
- [ ] Increase warning frequency for legacy usage

#### Phase 4: Deprecation (Weeks 9-12)
- [ ] Remove legacy parameter support
- [ ] Deploy final standardized workflows
- [ ] Update all documentation
- [ ] Announce completion of migration

### 4. Implementation Examples

#### 4.1 Standard Workflow Input Examples

**Human Handoff - Standard Format:**
```python
workflow_input = {
    "conversation": {
        "message": "I need help with my payment issue",
        "history": "Customer: Having trouble with payment\nAna: Let me help you",
        "escalation_reason": "Complex payment dispute",
        "urgency_level": "high",
        "business_unit": "pagbank"
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
    }
}

# Call workflow with standard parameter
result = human_handoff_workflow.run(workflow_input=workflow_input)
```

**Conversation Typification - Standard Format:**
```python
workflow_input = {
    "conversation": {
        "text": "Customer asking about payment methods...",
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
        "session_id": "sess_20250716_002"
    },
    "process": {
        "escalation_data": None,
        "metadata": {
            "source": "whatsapp",
            "channel": "customer_service"
        }
    }
}

# Call workflow with standard parameter
result = typification_workflow.run(workflow_input=workflow_input)
```

#### 4.2 API Endpoint Updates

**Before (Legacy):**
```python
@app.post("/workflows/human-handoff")
async def trigger_human_handoff(
    customer_message: str,
    escalation_reason: Optional[str] = None,
    urgency_level: str = "medium",
    customer_id: Optional[str] = None,
    # ... other legacy parameters
):
    return await human_handoff_workflow.run(
        customer_message=customer_message,
        escalation_reason=escalation_reason,
        urgency_level=urgency_level,
        customer_id=customer_id
    )
```

**After (Standard with Backward Compatibility):**
```python
from pydantic import BaseModel
from typing import Optional, Union

class ConversationData(BaseModel):
    message: str
    history: Optional[str] = None
    escalation_reason: Optional[str] = None
    urgency_level: str = "medium"
    business_unit: Optional[str] = None

class CustomerData(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_cpf: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None

class SessionData(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class HumanHandoffInput(BaseModel):
    conversation: ConversationData
    customer: Optional[CustomerData] = None
    session: Optional[SessionData] = None

class LegacyHumanHandoffRequest(BaseModel):
    """Legacy request format (DEPRECATED)"""
    customer_message: str
    escalation_reason: Optional[str] = None
    urgency_level: str = "medium"
    customer_id: Optional[str] = None
    # ... other legacy fields

@app.post("/workflows/human-handoff")
async def trigger_human_handoff(
    # Standard format (PREFERRED)
    request: Union[HumanHandoffInput, LegacyHumanHandoffRequest]
):
    """
    Trigger human handoff workflow
    
    Supports both standard workflow_input format and legacy parameters.
    Legacy format is deprecated and will be removed in v3.0.0
    """
    
    if isinstance(request, HumanHandoffInput):
        # New standard format
        workflow_input = request.model_dump()
        return await human_handoff_workflow.run(workflow_input=workflow_input)
    else:
        # Legacy format with deprecation warning
        warnings.warn(
            "Legacy request format is deprecated. Use standard workflow_input format.",
            DeprecationWarning
        )
        return await human_handoff_workflow.run(
            customer_message=request.customer_message,
            escalation_reason=request.escalation_reason,
            urgency_level=request.urgency_level,
            customer_id=request.customer_id
        )
```

### 5. Validation and Testing Strategy

#### 5.1 Validation Schema

```python
# workflows/shared/validation.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class StandardWorkflowInputSchema(BaseModel):
    """Validation schema for standard workflow input"""
    
    conversation: Dict[str, Any] = Field(..., description="Conversation data")
    customer: Optional[Dict[str, Any]] = Field(None, description="Customer information")
    session: Optional[Dict[str, Any]] = Field(None, description="Session data")
    process: Optional[Dict[str, Any]] = Field(None, description="Process metadata")
    
    @validator('conversation')
    def validate_conversation(cls, v):
        required_fields = ['message']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"conversation.{field} is required")
        return v
    
    @validator('session')
    def validate_session(cls, v):
        if v and 'session_id' not in v:
            v['session_id'] = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return v

def validate_workflow_input(workflow_input: Dict[str, Any]) -> StandardWorkflowInputSchema:
    """Validate workflow input against standard schema"""
    return StandardWorkflowInputSchema(**workflow_input)
```

#### 5.2 Testing Strategy

```python
# tests/test_parameter_migration.py
import pytest
import warnings
from workflows.shared.parameter_translator import ParameterTranslator
from workflows.human_handoff.workflow import HumanHandoffWorkflow

class TestParameterMigration:
    
    def test_legacy_parameter_translation(self):
        """Test legacy parameters are correctly translated"""
        
        # Legacy call
        with warnings.catch_warnings(record=True) as w:
            result = ParameterTranslator.translate_human_handoff(
                customer_message="Help needed",
                escalation_reason="Complex issue",
                urgency_level="high",
                customer_id="CUS123"
            )
            
            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "Legacy parameters are deprecated" in str(w[0].message)
        
        # Validate translation
        assert result.conversation["message"] == "Help needed"
        assert result.conversation["escalation_reason"] == "Complex issue"
        assert result.conversation["urgency_level"] == "high"
        assert result.customer["customer_id"] == "CUS123"
    
    def test_standard_parameter_usage(self):
        """Test standard workflow_input parameter"""
        
        workflow_input = {
            "conversation": {
                "message": "Standard format message",
                "urgency_level": "medium"
            },
            "customer": {
                "customer_id": "CUS456"
            }
        }
        
        with warnings.catch_warnings(record=True) as w:
            result = ParameterTranslator.translate_human_handoff(
                workflow_input=workflow_input
            )
            
            # No deprecation warning for standard format
            assert len(w) == 0
        
        assert result.conversation["message"] == "Standard format message"
        assert result.customer["customer_id"] == "CUS456"
    
    def test_workflow_backward_compatibility(self):
        """Test workflow supports both parameter formats"""
        
        workflow = HumanHandoffWorkflow()
        
        # Test legacy format
        with warnings.catch_warnings(record=True):
            legacy_result = list(workflow.run(
                customer_message="Legacy test",
                customer_id="CUS789"
            ))
        
        # Test standard format
        standard_result = list(workflow.run(
            workflow_input={
                "conversation": {"message": "Standard test"},
                "customer": {"customer_id": "CUS789"}
            }
        ))
        
        # Both should succeed and produce similar results
        assert len(legacy_result) > 0
        assert len(standard_result) > 0
```

### 6. Documentation and Communication Plan

#### 6.1 Migration Guide

Create comprehensive migration documentation:

```markdown
# Migration Guide: Custom Parameters to Agno Standards

## Quick Start

### Before (Legacy)
```python
workflow.run(
    customer_message="Help request",
    customer_id="CUS123",
    urgency_level="high"
)
```

### After (Standard)
```python
workflow.run(
    workflow_input={
        "conversation": {
            "message": "Help request",
            "urgency_level": "high"
        },
        "customer": {
            "customer_id": "CUS123"
        }
    }
)
```

## Complete Migration Examples
[... detailed examples for each workflow ...]
```

#### 6.2 API Documentation Updates

Update OpenAPI/Swagger documentation to show both formats with deprecation notices:

```yaml
paths:
  /workflows/human-handoff:
    post:
      summary: "Human Handoff Workflow"
      description: |
        Triggers human handoff workflow.
        
        **MIGRATION NOTICE**: Legacy parameter format is deprecated.
        Use the standard `workflow_input` format for new implementations.
        Legacy support will be removed in v3.0.0.
      
      requestBody:
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/StandardWorkflowInput'
                - $ref: '#/components/schemas/LegacyHumanHandoffRequest'
                  deprecated: true
```

### 7. Monitoring and Metrics

#### 7.1 Migration Tracking

```python
# workflows/shared/migration_metrics.py
from typing import Dict
import logging
from datetime import datetime

class MigrationMetrics:
    """Track parameter migration progress"""
    
    def __init__(self):
        self.usage_counts = {
            "standard_format": 0,
            "legacy_format": 0
        }
        self.migration_logger = logging.getLogger("migration_metrics")
    
    def log_parameter_usage(self, format_type: str, workflow_name: str):
        """Log parameter format usage"""
        
        self.usage_counts[format_type] += 1
        
        self.migration_logger.info({
            "event": "parameter_usage",
            "format": format_type,
            "workflow": workflow_name,
            "timestamp": datetime.now().isoformat(),
            "total_standard": self.usage_counts["standard_format"],
            "total_legacy": self.usage_counts["legacy_format"],
            "migration_percentage": self.get_migration_percentage()
        })
    
    def get_migration_percentage(self) -> float:
        """Calculate migration completion percentage"""
        total = sum(self.usage_counts.values())
        if total == 0:
            return 0.0
        return (self.usage_counts["standard_format"] / total) * 100

# Global metrics instance
migration_metrics = MigrationMetrics()
```

#### 7.2 Dashboard Integration

Add migration progress to monitoring dashboard:

```python
# api/monitoring/migration_dashboard.py
@router.get("/migration/progress")
async def get_migration_progress():
    """Get migration progress metrics"""
    
    return {
        "migration_status": {
            "standard_usage": migration_metrics.usage_counts["standard_format"],
            "legacy_usage": migration_metrics.usage_counts["legacy_format"],
            "completion_percentage": migration_metrics.get_migration_percentage()
        },
        "timeline": {
            "current_phase": "Phase 2: Soft Migration",
            "legacy_removal_date": "2025-10-15",
            "days_remaining": calculate_days_remaining()
        }
    }
```

### 8. Risk Mitigation

#### 8.1 Rollback Strategy

Implement feature flags for parameter format support:

```python
# config/feature_flags.py
from typing import Dict
import os

class FeatureFlags:
    """Feature flags for migration control"""
    
    @staticmethod
    def legacy_parameters_enabled() -> bool:
        """Check if legacy parameter support is enabled"""
        return os.getenv("ENABLE_LEGACY_PARAMETERS", "true").lower() == "true"
    
    @staticmethod
    def strict_validation_enabled() -> bool:
        """Check if strict validation for new format is enabled"""
        return os.getenv("ENABLE_STRICT_VALIDATION", "false").lower() == "true"

# In workflow implementations
if not FeatureFlags.legacy_parameters_enabled():
    raise ValueError("Legacy parameters are no longer supported")
```

#### 8.2 Gradual Rollout

```python
# workflows/shared/gradual_rollout.py
import random
from typing import Dict, Any

class GradualRollout:
    """Manage gradual migration rollout"""
    
    @staticmethod
    def should_use_standard_format(user_id: str = None) -> bool:
        """Determine if user should use standard format"""
        
        # Priority users (internal testing)
        priority_users = ["internal_test_user", "admin_user"]
        if user_id in priority_users:
            return True
        
        # Gradual rollout percentage
        rollout_percentage = int(os.getenv("STANDARD_FORMAT_ROLLOUT", "25"))
        
        # Hash-based consistent assignment
        if user_id:
            hash_value = hash(user_id) % 100
            return hash_value < rollout_percentage
        
        # Random assignment for anonymous users
        return random.randint(0, 99) < rollout_percentage
```

### 9. Success Criteria

#### 9.1 Technical Metrics
- [ ] 100% of workflows support standard `workflow_input` parameter
- [ ] 0% of production traffic uses legacy parameters
- [ ] All API endpoints follow Agno standard contract
- [ ] Comprehensive test coverage for both formats during transition

#### 9.2 Business Metrics
- [ ] Zero breaking changes for existing clients during migration
- [ ] ≤5% performance impact during dual-format support phase
- [ ] ≤24 hours downtime for final migration
- [ ] 100% client satisfaction with migration process

### 10. Conclusion

This comprehensive migration strategy ensures a smooth transition from custom parameters to Agno standards while maintaining full backward compatibility. The phased approach allows for careful validation and testing at each step, minimizing risks to production systems.

Key benefits of this approach:
- **Zero Disruption**: Existing clients continue working unchanged
- **Gradual Migration**: Controlled rollout with monitoring and rollback capabilities
- **Future-Proof**: Full alignment with Agno framework standards
- **Maintainable**: Cleaner, more consistent parameter structure

The migration timeline of 12 weeks provides adequate time for thorough testing and client migration while maintaining system stability throughout the process.