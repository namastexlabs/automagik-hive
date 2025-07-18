# Workflow Refactor Plan - Agno Workflows 2.0 (v1.7.4+)

## 🎯 Executive Summary

This document outlines a comprehensive refactor plan to transition current workflows to the official Agno Workflows 2.0 patterns. The current implementation uses a hybrid approach that needs alignment with the official v1.7.4+ APIs.

## 🔍 Current State Analysis

### Current Implementation
- ✅ **Factory Functions**: Already using proper factory function patterns
- ✅ **Step-based Structure**: Using standalone executor functions
- ✅ **Registry Pattern**: Clean workflow registry implementation
- ❌ **API Imports**: Using non-existent `agno.workflow.v2` imports
- ❌ **Step Definitions**: Using custom `StepInput`/`StepOutput` instead of official APIs
- ❌ **Session State**: Custom session state management vs official patterns

### Key Discrepancies
1. **Import Statements**: Current code imports from `agno.workflow.v2` which doesn't exist
2. **Step Structure**: Using custom step executor patterns vs official `Step` class
3. **Data Flow**: Custom `StepInput`/`StepOutput` vs official session state patterns
4. **Storage Integration**: Needs alignment with official storage APIs

## 📋 Refactor Plan

### Phase 1: API Alignment (Priority: Critical)

#### 1.1 Update Import Statements
**Current:**
```python
from agno.workflow.v2 import Workflow, Step, Steps, Parallel
from agno.workflow.v2.types import StepInput, StepOutput
```

**Target:**
```python
from agno.workflow.v2 import Workflow, Step, Parallel, Condition, Loop, Router
from agno.storage.postgres import PostgresStorage
```

#### 1.2 Convert Step Executor Functions
**Current Pattern:**
```python
def execute_business_unit_classification(step_input: StepInput) -> StepOutput:
    conversation_text = step_input.message
    # ... processing
    return StepOutput(content=json.dumps(result))
```

**Target Pattern:**
```python
def business_unit_classifier(step_input):
    conversation_text = step_input.message
    # ... processing
    # Use workflow_session_state for data sharing
    step_input.workflow_session_state["business_unit"] = result
    return StepOutput(content=result)
```

#### 1.3 Update Workflow Factory Functions
**Current:**
```python
def get_conversation_typification_workflow(**kwargs):
    workflow = Workflow(
        name="conversation_typification_v2",
        steps=[
            Step(
                name="business_unit_classification",
                executor=execute_business_unit_classification,
                max_retries=3
            ),
            # ...
        ],
        **kwargs
    )
```

**Target:**
```python
def get_conversation_typification_workflow(**kwargs):
    return Workflow(
        name="conversation_typification_v2",
        description="Hierarchical conversation classification",
        storage=PostgresStorage(
            table_name="conversation_workflows",
            db_url=os.getenv("DATABASE_URL")
        ),
        steps=[
            Step(name="Business Unit", function=business_unit_classifier),
            Step(name="Product Classification", agent=product_agent),
            Parallel(
                Step(name="Validation", function=validate_hierarchy),
                Step(name="Protocol Generation", agent=protocol_agent),
                name="Final Processing"
            )
        ],
        **kwargs
    )
```

### Phase 2: Data Flow Refactoring (Priority: High)

#### 2.1 Session State Migration
**Current Approach:**
```python
def execute_product_classification(step_input: StepInput) -> StepOutput:
    previous_output = step_input.get_step_output("business_unit_classification")
    previous_data = json.loads(previous_output.content)
    business_unit = previous_data["business_unit"]
```

**Target Approach:**
```python
def product_classifier(step_input):
    # Access data from session state
    business_unit = step_input.workflow_session_state.get("business_unit")
    conversation_text = step_input.message
    
    # Store results in session state
    step_input.workflow_session_state["product"] = result
    return StepOutput(content=result)
```

#### 2.2 Remove Custom StepInput/StepOutput Classes
- Replace custom `StepInput` with official step input patterns
- Replace custom `StepOutput` with official return patterns
- Update all executor functions to use official APIs

### Phase 3: Storage Integration (Priority: High)

#### 3.1 PostgreSQL Storage Setup
```python
# Update workflow creation to use official storage
from agno.storage.postgres import PostgresStorage

workflow = get_conversation_typification_workflow(
    storage=PostgresStorage(
        table_name="conversation_workflows",
        db_url=os.getenv("DATABASE_URL")
    ),
    session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
)
```

#### 3.2 Development Storage Configuration
```python
from agno.storage.sqlite import SqliteStorage

# Development configuration
workflow = get_human_handoff_workflow(
    storage=SqliteStorage(
        table_name="handoff_workflows",
        db_file="tmp/workflows.db"
    )
)
```

### Phase 4: Advanced Features Implementation (Priority: Medium)

#### 4.1 Add Parallel Processing
**Current Sequential:**
```python
steps=[
    Step(name="protocol_generation", executor=execute_protocol_generation),
    Step(name="whatsapp_notification", executor=execute_whatsapp_notification),
]
```

**Target Parallel:**
```python
steps=[
    Parallel(
        Step(name="protocol_generation", agent=protocol_agent),
        Step(name="whatsapp_notification", function=whatsapp_notifier),
        name="parallel_processing"
    )
]
```

#### 4.2 Add Conditional Logic
```python
def should_escalate(step_input) -> bool:
    urgency = step_input.workflow_session_state.get("urgency_level")
    return urgency == "high"

# Add to workflow
Condition(
    name="Escalation Check",
    evaluator=should_escalate,
    steps=[Step(name="Human Escalation", agent=escalation_agent)]
)
```

#### 4.3 Add Loop Processing for Quality
```python
def quality_check(step_input) -> bool:
    confidence = step_input.workflow_session_state.get("confidence", 0)
    return confidence < 0.8

Loop(
    name="Quality Loop",
    steps=[Step(name="Refinement", agent=refinement_agent)],
    exit_condition=quality_check,
    max_iterations=3
)
```

## 📝 Implementation Steps

### Step 1: Backup Current Implementation
```bash
# Create backup branch
git checkout -b backup-pre-refactor-$(date +%Y%m%d)
git add -A && git commit -m "Backup: Pre-refactor state"
git checkout v2
```

### Step 2: Update Imports and Dependencies
```python
# Update all workflow files
find ai/workflows -name "*.py" -exec sed -i 's/from agno.workflow.v2 import/from agno.workflow.v2 import/g' {} \;
find ai/workflows -name "*.py" -exec sed -i 's/from agno.workflow.v2.types import//g' {} \;
```

### Step 3: Refactor Conversation Typification Workflow
```python
# File: ai/workflows/conversation_typification/workflow.py

from agno.workflow.v2 import Workflow, Step, Parallel
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage

def business_unit_classifier(step_input):
    """Business unit classification step"""
    conversation_text = step_input.message
    if not conversation_text:
        raise ValueError("conversation_text is required")
    
    # Use existing agent creation logic
    agent = create_business_unit_classifier()
    response = agent.run(conversation_text)
    
    if not response.content:
        raise ValueError("Invalid classification response")
    
    # Store in session state
    step_input.workflow_session_state["business_unit"] = response.content.unidade_negocio.value
    step_input.workflow_session_state["confidence"] = response.content.confidence
    
    return StepOutput(content=response.content.model_dump())

def product_classifier(step_input):
    """Product classification step"""
    business_unit = step_input.workflow_session_state.get("business_unit")
    conversation_text = step_input.message
    
    agent = create_product_classifier(business_unit)
    classifier_input = f"Business Unit: {business_unit}\n\nConversation: {conversation_text}"
    response = agent.run(classifier_input)
    
    # Update session state
    step_input.workflow_session_state["product"] = response.content.produto
    
    return StepOutput(content=response.content.model_dump())

def get_conversation_typification_workflow(**kwargs):
    """Factory function for conversation typification workflow"""
    
    return Workflow(
        name="conversation_typification_v2",
        description="Hierarchical conversation classification with official v2 patterns",
        storage=PostgresStorage(
            table_name="conversation_workflows",
            db_url=os.getenv("DATABASE_URL")
        ),
        steps=[
            Step(
                name="business_unit_classification",
                function=business_unit_classifier
            ),
            Step(
                name="product_classification",
                function=product_classifier
            ),
            Step(
                name="motive_classification",
                function=motive_classifier
            ),
            Step(
                name="submotive_classification", 
                function=submotive_classifier
            ),
            Parallel(
                Step(name="validation", function=validate_hierarchy),
                Step(name="protocol_generation", agent=protocol_agent),
                name="final_processing"
            )
        ],
        **kwargs
    )
```

### Step 4: Refactor Human Handoff Workflow
```python
# File: ai/workflows/human_handoff/workflow.py

def escalation_analyzer(step_input):
    """Escalation analysis step"""
    customer_message = step_input.message
    analyst = create_escalation_analyst()
    
    response = analyst.run(f"Analyze escalation: {customer_message}")
    
    # Store in session state
    step_input.workflow_session_state.update({
        "escalation_reason": response.content.escalation_reason.value,
        "urgency_level": response.content.urgency_level.value,
        "customer_emotion": response.content.customer_emotion.value,
        "should_escalate": response.content.should_escalate
    })
    
    return StepOutput(content=response.content.model_dump())

def whatsapp_notifier(step_input):
    """WhatsApp notification step"""
    escalation_data = step_input.workflow_session_state
    
    try:
        notification_result = send_whatsapp_notification(escalation_data)
        step_input.workflow_session_state["notification_sent"] = notification_result["success"]
        return StepOutput(content=notification_result)
    except Exception as e:
        step_input.workflow_session_state["notification_error"] = str(e)
        raise

def get_human_handoff_workflow(**kwargs):
    """Factory function for human handoff workflow"""
    
    return Workflow(
        name="human_handoff_v2",
        description="Human escalation with parallel processing",
        storage=PostgresStorage(
            table_name="handoff_workflows",
            db_url=os.getenv("DATABASE_URL")
        ),
        steps=[
            Step(name="escalation_analysis", function=escalation_analyzer),
            Step(name="customer_info_collection", agent=customer_info_agent),
            Step(name="issue_details_creation", agent=issue_details_agent),
            Parallel(
                Step(name="protocol_generation", agent=protocol_agent),
                Step(name="whatsapp_notification", function=whatsapp_notifier),
                name="parallel_processing"
            ),
            Step(name="handoff_completion", agent=completion_agent)
        ],
        **kwargs
    )
```

### Step 5: Update Registry
```python
# File: ai/workflows/registry.py

from agno.workflow.v2 import Workflow
from typing import Dict, Callable

from .conversation_typification.workflow import get_conversation_typification_workflow
from .human_handoff.workflow import get_human_handoff_workflow

WORKFLOW_REGISTRY: Dict[str, Callable[..., Workflow]] = {
    "conversation-typification": get_conversation_typification_workflow,
    "human-handoff": get_human_handoff_workflow,
}

def get_workflow(workflow_id: str, **kwargs) -> Workflow:
    """Get workflow instance by ID with official v2 patterns"""
    if workflow_id not in WORKFLOW_REGISTRY:
        available_workflows = ", ".join(sorted(WORKFLOW_REGISTRY.keys()))
        raise ValueError(
            f"Workflow '{workflow_id}' not found. "
            f"Available: {available_workflows}"
        )
    
    factory = WORKFLOW_REGISTRY[workflow_id]
    return factory(**kwargs)
```

### Step 6: Testing and Validation
```python
# Test script to validate refactored workflows
def test_workflow_refactor():
    """Test refactored workflows"""
    
    # Test conversation typification
    conv_workflow = get_conversation_typification_workflow(
        session_id="test-conv-session"
    )
    
    response = conv_workflow.run(
        message="Customer asking about credit card fees"
    )
    
    assert response.content is not None
    print("✅ Conversation typification workflow test passed")
    
    # Test human handoff
    handoff_workflow = get_human_handoff_workflow(
        session_id="test-handoff-session"
    )
    
    response = handoff_workflow.run(
        message="Escalate this issue to human support"
    )
    
    assert response.content is not None
    print("✅ Human handoff workflow test passed")

# Run tests
if __name__ == "__main__":
    test_workflow_refactor()
```

## 🛡️ Risk Mitigation

### 1. Backward Compatibility Strategy
- Maintain old API endpoints during transition period
- Gradual rollout with feature flags
- Comprehensive testing before full deployment

### 2. Data Migration
- Ensure session state data compatibility
- Backup existing workflow executions
- Plan rollback strategy if needed

### 3. Performance Monitoring
- Monitor workflow execution times before/after refactor
- Track memory usage and resource consumption
- Validate parallel execution performance gains

## 📊 Success Metrics

### Technical Metrics
- ✅ All workflows using official Agno v1.7.4+ APIs
- ✅ Zero custom API implementations
- ✅ Parallel execution reducing total workflow time by 30%+
- ✅ Session state properly managed across all steps

### Quality Metrics
- ✅ 100% test coverage for refactored workflows
- ✅ Zero breaking changes to external APIs
- ✅ Documentation updated to reflect new patterns
- ✅ All examples working with official APIs

## 🚀 Timeline

### Week 1: Planning and Preparation
- [ ] Complete analysis of current implementation
- [ ] Create detailed refactor specifications
- [ ] Set up testing environment

### Week 2: Core API Refactoring
- [ ] Update imports and dependencies
- [ ] Refactor step executor functions
- [ ] Implement session state management

### Week 3: Advanced Features
- [ ] Add parallel processing
- [ ] Implement conditional logic
- [ ] Add storage integration

### Week 4: Testing and Validation
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] Documentation updates

## 📋 Checklist

### Pre-Refactor
- [ ] Backup current implementation
- [ ] Document current behavior
- [ ] Identify breaking changes
- [ ] Plan rollback strategy

### During Refactor
- [ ] Update imports to official APIs
- [ ] Convert step executors to official patterns
- [ ] Implement session state management
- [ ] Add storage configuration
- [ ] Test each component individually

### Post-Refactor
- [ ] Validate all workflows work with official APIs
- [ ] Test parallel execution performance
- [ ] Update documentation
- [ ] Remove custom implementations
- [ ] Deploy to production

## 🎯 Expected Outcomes

### Technical Benefits
1. **Standards Compliance**: 100% alignment with official Agno v1.7.4+ APIs
2. **Performance**: 30%+ improvement from parallel execution
3. **Maintainability**: Reduced custom code, easier debugging
4. **Scalability**: Official storage backends support enterprise scale

### Business Benefits
1. **Reliability**: Official APIs are battle-tested and maintained
2. **Support**: Access to official Agno community and documentation
3. **Future-Proofing**: Automatic compatibility with future Agno releases
4. **Development Speed**: Faster development with official patterns

---

**This refactor plan ensures seamless transition to official Agno Workflows 2.0 patterns while maintaining all current functionality and improving performance through parallel execution capabilities.**