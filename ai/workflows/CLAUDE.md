# Agno Workflows 2.0 - Enterprise Implementation Guide (v1.7.4+)

## 🚀 Overview

Agno Workflows 2.0 represents a complete redesign of the workflow system introduced in v1.7.4, featuring a **step-based architecture** that provides better structure, flexibility, and control over multi-stage AI agent processes.

**Official Documentation**: 
- [Overview](https://docs.agno.com/workflows_2/overview)
- [Workflow Types](https://docs.agno.com/workflows_2/types_of_workflows)
- [Running Workflows](https://docs.agno.com/workflows_2/run_workflow)
- [Session State](https://docs.agno.com/workflows_2/workflow_session_state)
- [Advanced Features](https://docs.agno.com/workflows_2/advanced)
- [Migration Guide](https://docs.agno.com/workflows_2/migration)

### Key Architectural Changes

| Feature | Workflows 1.0 | Workflows 2.0 |
|---------|---------------|---------------|
| **Execution Model** | Linear only | Multiple patterns (sequential, parallel, conditional, loop) |
| **Components** | Agent-focused | Mixed components (agents, teams, functions) |
| **Routing** | Basic | Smart routing with dynamic step selection |
| **State Management** | Limited | Full session state management |
| **Flexibility** | Monolithic run method | Modular step-based design |

### Core Concepts

1. **Flexible Execution**: Sequential, parallel, conditional, and loop-based execution
2. **Smart Routing**: Dynamic step selection based on content analysis or user intent
3. **Mixed Components**: Combine agents, teams, and functions seamlessly
4. **State Management**: Share data across steps with workflow session state

## 🏗️ Architecture Components

### 1. Core Workflow Structure

```python
from agno.workflow.v2 import Workflow, Step, Parallel, Condition, Loop, Router
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage

# Basic workflow structure
workflow = Workflow(
    name="Mixed Execution Pipeline",
    storage=SqliteStorage(
        table_name="workflow_v2",
        db_file="tmp/workflow_v2.db"
    ),
    steps=[
        research_team,      # Team
        data_preprocessor,  # Function
        content_agent,      # Agent
    ]
)
```

### 2. Step Types and Building Blocks

#### Sequential Steps (Default)
```python
def data_preprocessor(step_input):
    return StepOutput(content=f"Processed: {step_input.message}")

workflow = Workflow(
    name="Sequential Pipeline",
    steps=[
        Step(name="Research", agent=research_agent),
        data_preprocessor,  # Function step
        Step(name="Analysis", agent=analysis_agent),
    ]
)
```

#### Parallel Execution
```python
workflow = Workflow(
    name="Parallel Research Pipeline",
    steps=[
        Parallel(
            Step(name="HackerNews Research", agent=hn_researcher),
            Step(name="Web Research", agent=web_researcher),
            Step(name="Academic Research", agent=academic_researcher),
            name="Research Step"
        ),
        Step(name="Synthesis", agent=synthesizer),
    ]
)
```

#### Conditional Steps
```python
def is_tech_topic(step_input) -> bool:
    topic = step_input.message.lower()
    return any(keyword in topic for keyword in ["ai", "tech", "software"])

workflow = Workflow(
    name="Conditional Research",
    steps=[
        Condition(
            name="Tech Topic Check",
            evaluator=is_tech_topic,
            steps=[Step(name="Tech Research", agent=tech_researcher)]
        ),
        Step(name="General Analysis", agent=general_analyst),
    ]
)
```

#### Loop Execution
```python
def quality_check(outputs) -> bool:
    return any(len(output.content) > 500 for output in outputs)

workflow = Workflow(
    name="Quality-Driven Research",
    steps=[
        Loop(
            name="Research Loop",
            steps=[Step(name="Deep Research", agent=researcher)],
            exit_condition=quality_check,
            max_iterations=3
        ),
        Step(name="Final Report", agent=reporter),
    ]
)
```

#### Router (Dynamic Routing)
```python
def route_by_topic(step_input) -> str:
    topic = step_input.message.lower()
    if "tech" in topic:
        return "tech_path"
    elif "business" in topic:
        return "business_path"
    return "general_path"

workflow = Workflow(
    name="Dynamic Routing Workflow",
    steps=[
        Router(
            name="Topic Router",
            evaluator=route_by_topic,
            routes={
                "tech_path": [tech_specialist],
                "business_path": [business_analyst],
                "general_path": [general_agent]
            }
        )
    ]
)
```

### 3. Session State Management

```python
# Workflow session state is automatically managed
# Access via workflow_session_state in agents/functions

def add_to_shared_state(agent, item):
    # Initialize state if needed
    if agent.workflow_session_state is None:
        agent.workflow_session_state = {}
    
    # Add to shared list
    if "items" not in agent.workflow_session_state:
        agent.workflow_session_state["items"] = []
    
    agent.workflow_session_state["items"].append(item)
    return f"Added {item} to shared state"

# State persists across all workflow steps
workflow = Workflow(
    name="Stateful Workflow",
    steps=[
        Step(name="Collector", function=add_to_shared_state),
        Step(name="Processor", agent=processor_agent),  # Can access shared state
    ]
)
```

## 🔄 Migration from Workflows 1.0

### Current Architecture (1.0)
```python
class ConversationTypificationWorkflow(Workflow):
    def run(self, conversation_text: str) -> Iterator[RunResponse]:
        # Linear execution
        business_unit = self.business_unit_agent.run(conversation_text)
        product = self.product_agent.run(business_unit, conversation_text)
        motive = self.motive_agent.run(product, conversation_text)
        submotive = self.submotive_agent.run(motive, conversation_text)
        final_report = self.validate_and_finalize(submotive)
        
        yield RunResponse(content=final_report)
```

### Migrated Architecture (2.0)
```python
from agno.workflow.v2 import Workflow, Step, Parallel
from agno.storage.postgres import PostgresStorage

def business_unit_classifier(step_input):
    # Custom function step
    conversation = step_input.message
    # Process and return classification
    return StepOutput(content={"business_unit": "credit_cards"})

def validate_hierarchy(step_input):
    # Access previous step outputs
    business_unit = step_input.workflow_session_state.get("business_unit")
    product = step_input.workflow_session_state.get("product")
    # Validation logic
    return StepOutput(content={"valid": True})

workflow = Workflow(
    name="conversation_typification_v2",
    description="Step-based hierarchical conversation typification",
    storage=PostgresStorage(
        table_name="conversation_workflows",
        db_url=os.getenv("DATABASE_URL")
    ),
    steps=[
        Step(name="Business Unit", function=business_unit_classifier),
        Step(name="Product Classification", agent=product_agent),
        Step(name="Motive Classification", agent=motive_agent),
        Step(name="Submotive Classification", agent=submotive_agent),
        Parallel(
            Step(name="Validation", function=validate_hierarchy),
            Step(name="Protocol Generation", agent=protocol_agent),
            Step(name="Report Generation", agent=report_agent),
            name="Final Processing"
        )
    ]
)
```

## 🎯 Workflow Creation Patterns

### 1. Factory Function Pattern (Current Standard)

```python
from agno.workflow.v2 import Workflow, Step, Parallel
from agno.agent import Agent
from agno.models.anthropic import Claude
from typing import Dict, Any

def get_conversation_typification_workflow(**kwargs) -> Workflow:
    """Factory function to create conversation typification workflow"""
    
    # Create specialized agents
    business_unit_agent = Agent(
        name="Business Unit Classifier",
        model=Claude(id="claude-sonnet-4-20250514"),
        description="Classify business unit from conversation",
        response_model=BusinessUnitSelection,
    )
    
    product_agent = Agent(
        name="Product Classifier", 
        model=Claude(id="claude-sonnet-4-20250514"),
        description="Classify product based on business unit",
        response_model=ProductSelection,
    )
    
    # Define step executor functions
    def execute_business_unit_classification(step_input):
        conversation_text = step_input.message
        if not conversation_text:
            raise ValueError("conversation_text is required")
        
        response = business_unit_agent.run(conversation_text)
        if not response.content:
            raise ValueError("Invalid classification response")
        
        # Store in session state for next steps
        step_input.workflow_session_state["business_unit"] = response.content.unidade_negocio.value
        step_input.workflow_session_state["confidence"] = response.content.confidence
        
        return StepOutput(content=response.content.model_dump())
    
    def execute_product_classification(step_input):
        # Access previous step data from session state
        business_unit = step_input.workflow_session_state.get("business_unit")
        conversation_text = step_input.message
        
        classifier_input = f"Business Unit: {business_unit}\n\nConversation: {conversation_text}"
        response = product_agent.run(classifier_input)
        
        # Update session state
        step_input.workflow_session_state["product"] = response.content.produto
        
        return StepOutput(content=response.content.model_dump())
    
    # Create workflow with steps
    return Workflow(
        name="conversation_typification_v2",
        description="Hierarchical conversation classification with parallel processing",
        steps=[
            Step(
                name="business_unit_classification",
                function=execute_business_unit_classification,
                max_retries=3
            ),
            Step(
                name="product_classification", 
                function=execute_product_classification,
                max_retries=3
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

### 2. Human Handoff Workflow Pattern

```python
def get_human_handoff_workflow(**kwargs) -> Workflow:
    """Factory function for human escalation workflow"""
    
    def execute_escalation_analysis(step_input):
        customer_message = step_input.message
        analyst = create_escalation_analyst()
        
        response = analyst.run(f"Analyze escalation: {customer_message}")
        
        # Store escalation data in session state
        step_input.workflow_session_state.update({
            "escalation_reason": response.content.escalation_reason.value,
            "urgency_level": response.content.urgency_level.value,
            "customer_emotion": response.content.customer_emotion.value,
            "should_escalate": response.content.should_escalate
        })
        
        return StepOutput(content=response.content.model_dump())
    
    def execute_whatsapp_notification(step_input):
        # Access escalation data from session state
        escalation_data = step_input.workflow_session_state
        
        # Send WhatsApp notification using MCP integration
        notification_result = send_whatsapp_notification(escalation_data)
        
        return StepOutput(content=notification_result)
    
    return Workflow(
        name="human_handoff_v2",
        description="Step-based human escalation with parallel notifications",
        steps=[
            Step(
                name="escalation_analysis",
                function=execute_escalation_analysis,
                max_retries=3
            ),
            Step(
                name="customer_info_collection",
                agent=customer_info_agent,
                max_retries=2
            ),
            Step(
                name="issue_details_creation", 
                agent=issue_details_agent,
                max_retries=2
            ),
            Parallel(
                Step(name="protocol_generation", agent=protocol_agent),
                Step(name="whatsapp_notification", function=execute_whatsapp_notification),
                name="parallel_processing"
            ),
            Step(
                name="handoff_completion",
                agent=completion_agent,
                max_retries=1
            )
        ],
        **kwargs
    )
```

## 🚀 Execution Patterns

### 1. Basic Execution
```python
# Synchronous execution
response = workflow.run(
    message="Customer inquiry about credit card fees",
    markdown=True
)

# Asynchronous execution
response = await workflow.arun(
    message="Escalate this issue to human support"
)
```

### 2. Streaming Execution
```python
# Stream workflow execution with intermediate steps
for response in workflow.run(
    message="Process this customer conversation",
    stream=True,
    stream_intermediate_steps=True
):
    print(f"Step: {response.step_name}")
    print(f"Content: {response.content}")
```

### 3. Storage Configuration
```python
from agno.storage.postgres import PostgresStorage

# Production setup with PostgreSQL
workflow = get_conversation_typification_workflow(
    storage=PostgresStorage(
        table_name="conversation_workflows",
        db_url=os.getenv("DATABASE_URL")
    ),
    session_id="conversation-analysis-session"
)

# Development setup with SQLite
from agno.storage.sqlite import SqliteStorage

workflow = get_human_handoff_workflow(
    storage=SqliteStorage(
        table_name="handoff_workflows", 
        db_file="tmp/workflows.db"
    )
)
```

## 🔧 Best Practices

### 1. Step Design Principles
- **Single Responsibility**: Each step should have one clear purpose
- **Stateless Functions**: Use session state for data sharing, not function state
- **Error Handling**: Implement proper error handling and validation
- **Type Safety**: Use Pydantic models for structured data

### 2. Session State Management
```python
def step_executor(step_input):
    # Always check if session state exists
    if step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}
    
    # Use descriptive keys
    step_input.workflow_session_state["analysis_results"] = results
    step_input.workflow_session_state["processing_timestamp"] = datetime.now()
    
    # Clean up unnecessary data
    if "temp_data" in step_input.workflow_session_state:
        del step_input.workflow_session_state["temp_data"]
    
    return StepOutput(content=processed_data)
```

### 3. Performance Optimization
- **Parallel Processing**: Use `Parallel` for independent operations
- **Caching**: Leverage session state for expensive computations
- **Early Stopping**: Implement condition checks to avoid unnecessary processing
- **Resource Management**: Use appropriate storage backends for scale

### 4. Error Handling and Retry Logic
```python
def robust_step_executor(step_input):
    try:
        # Main processing logic
        result = expensive_operation(step_input.message)
        
        # Store result in session state
        step_input.workflow_session_state["operation_result"] = result
        
        return StepOutput(content=result)
        
    except Exception as e:
        logger.error(f"Step execution failed: {str(e)}")
        
        # Store error info for debugging
        step_input.workflow_session_state["last_error"] = str(e)
        
        # Re-raise to trigger retry mechanism
        raise

# Configure retry in workflow
Step(
    name="robust_processing",
    function=robust_step_executor,
    max_retries=3  # Automatic retry on failure
)
```

## 📊 Advanced Features

### 1. Custom Functions with Media Support
```python
def process_image_data(step_input):
    """Custom function that handles media artifacts"""
    # Access uploaded images/media
    media_files = step_input.media or []
    
    for media in media_files:
        # Process each media file
        processed_data = analyze_image(media)
        
        # Store results in session state
        step_input.workflow_session_state[f"analysis_{media.name}"] = processed_data
    
    return StepOutput(
        content="Image analysis complete",
        media=processed_media_files
    )
```

### 2. Dynamic Workflow Routing
```python
def intelligent_router(step_input) -> str:
    """Route based on content analysis"""
    content = step_input.message.lower()
    confidence = analyze_content_confidence(content)
    
    if confidence > 0.9:
        return "high_confidence_path"
    elif confidence > 0.5:
        return "medium_confidence_path"
    else:
        return "human_review_path"

workflow = Workflow(
    name="Intelligent Processing",
    steps=[
        Router(
            name="Confidence Router",
            evaluator=intelligent_router,
            routes={
                "high_confidence_path": [automated_processor],
                "medium_confidence_path": [validation_agent, automated_processor],
                "human_review_path": [human_handoff_workflow]
            }
        )
    ]
)
```

### 3. Early Stopping Conditions
```python
def quality_gate(step_input) -> bool:
    """Check if quality standards are met"""
    results = step_input.workflow_session_state.get("analysis_results", {})
    confidence_score = results.get("confidence", 0)
    
    # Stop early if confidence is too low
    return confidence_score < 0.7

workflow = Workflow(
    name="Quality-Gated Processing",
    steps=[
        Step(name="Initial Analysis", agent=analysis_agent),
        Condition(
            name="Quality Gate",
            evaluator=quality_gate,
            steps=[
                Step(name="Human Review", agent=human_reviewer),
                Step(name="Retry Analysis", agent=enhanced_analyzer)
            ]
        ),
        Step(name="Final Processing", agent=processor)
    ]
)
```

## 📈 Monitoring and Event Tracking

### 1. Workflow Events
```python
# Events are automatically tracked during execution:
# - WorkflowStarted, WorkflowCompleted
# - StepStarted, StepCompleted  
# - ConditionExecutionStarted
# - ParallelExecutionStarted
# - LoopExecutionStarted
# - RouterExecutionStarted

# Access events after execution
for event in workflow.events:
    print(f"Event: {event.type} at {event.timestamp}")
    print(f"Details: {event.data}")
```

### 2. Performance Monitoring
```python
def monitored_step(step_input):
    start_time = time.time()
    
    try:
        result = process_data(step_input.message)
        
        # Record metrics in session state
        execution_time = time.time() - start_time
        step_input.workflow_session_state["metrics"] = {
            "execution_time": execution_time,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
        
        return StepOutput(content=result)
        
    except Exception as e:
        execution_time = time.time() - start_time
        step_input.workflow_session_state["metrics"] = {
            "execution_time": execution_time,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        raise
```

## 🎯 Integration with Genie Agents Project

### 1. Registry Integration
```python
# ai/workflows/registry.py
from typing import Dict, Callable
from agno.workflow.v2 import Workflow

from .conversation_typification.workflow import get_conversation_typification_workflow
from .human_handoff.workflow import get_human_handoff_workflow

WORKFLOW_REGISTRY: Dict[str, Callable[..., Workflow]] = {
    "conversation-typification": get_conversation_typification_workflow,
    "human-handoff": get_human_handoff_workflow,
}

def get_workflow(workflow_id: str, **kwargs) -> Workflow:
    """Get workflow instance by ID"""
    if workflow_id not in WORKFLOW_REGISTRY:
        raise ValueError(f"Workflow '{workflow_id}' not found")
    
    factory = WORKFLOW_REGISTRY[workflow_id]
    return factory(**kwargs)
```

### 2. Configuration Management
```python
# Load workflow-specific configuration
config = config_loader.load_workflow_config('conversation_typification')

workflow = get_conversation_typification_workflow(
    storage=PostgresStorage(
        table_name=config.get('storage', {}).get('table_name'),
        db_url=os.getenv("DATABASE_URL")
    ),
    session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
)
```

### 3. MCP Server Integration
```python
def whatsapp_notification_step(step_input):
    """Integration with WhatsApp MCP server"""
    escalation_data = step_input.workflow_session_state
    
    try:
        # Use MCP WhatsApp integration
        from mcp_integration import send_whatsapp_notification
        
        result = send_whatsapp_notification(
            instance="pagbank-instance",
            message=format_escalation_message(escalation_data),
            number=escalation_data.get("customer_phone")
        )
        
        step_input.workflow_session_state["notification_sent"] = result["success"]
        return StepOutput(content=result)
        
    except Exception as e:
        logger.error(f"WhatsApp notification failed: {str(e)}")
        step_input.workflow_session_state["notification_error"] = str(e)
        raise
```

## 📚 Reference Documentation

### Official Agno Documentation
- **Overview**: https://docs.agno.com/workflows_2/overview
- **Workflow Types**: https://docs.agno.com/workflows_2/types_of_workflows  
- **Execution**: https://docs.agno.com/workflows_2/run_workflow
- **Session State**: https://docs.agno.com/workflows_2/workflow_session_state
- **Advanced Features**: https://docs.agno.com/workflows_2/advanced
- **Migration Guide**: https://docs.agno.com/workflows_2/migration

### Key API Components
```python
# Core imports for Workflows 2.0
from agno.workflow.v2 import (
    Workflow,      # Main workflow class
    Step,          # Basic step wrapper
    Parallel,      # Parallel execution
    Condition,     # Conditional execution
    Loop,          # Loop execution
    Router,        # Dynamic routing
    StepOutput     # Step return value
)

from agno.storage.postgres import PostgresStorage
from agno.storage.sqlite import SqliteStorage
from agno.agent import Agent
from agno.models.anthropic import Claude
```

## 🚀 Migration Checklist

### From v1 to v2 Workflows

1. **✅ Assessment Phase**
   - [ ] Identify parallel execution opportunities
   - [ ] Map current if/else logic to Condition components
   - [ ] Extract custom logic into function-based steps
   - [ ] Plan session state management strategy

2. **✅ Implementation Phase**
   - [ ] Convert linear workflow to step-based structure
   - [ ] Implement factory function pattern
   - [ ] Add session state management
   - [ ] Configure appropriate storage backend

3. **✅ Enhancement Phase**
   - [ ] Add parallel processing where beneficial
   - [ ] Implement conditional routing
   - [ ] Add retry logic and error handling
   - [ ] Enable streaming for real-time feedback

4. **✅ Testing Phase**
   - [ ] Test individual step execution
   - [ ] Validate session state persistence
   - [ ] Test parallel execution scenarios
   - [ ] Verify error handling and retries

---

## ✨ Current Status

**Agno Workflows 2.0 (v1.7.4+) is now available!** This documentation reflects the official release patterns and APIs. All workflows in this project have been successfully migrated to the step-based architecture.

**Key Benefits Achieved:**
- ⚡ **Performance**: Parallel execution capabilities reduce total workflow time
- 🔧 **Maintainability**: Modular step-based design improves code organization  
- 🛡️ **Reliability**: Enhanced error handling and retry mechanisms
- 📈 **Scalability**: Advanced routing and state management support complex scenarios
- 🎯 **Standards Compliance**: Full adherence to official Agno v1.7.4+ patterns

All workflows are production-ready and follow the latest Agno Workflows 2.0 best practices.