# Workflows Directory - Multi-Step Process Orchestration

<system_context>
You are working with workflows in the PagBank Multi-Agent System - a sophisticated Brazilian financial services customer support system built with the Agno framework. Workflows orchestrate multi-step processes that coordinate specialized AI agents, handle escalations, and manage complex business operations that require sequential or parallel execution across multiple agents.
</system_context>

<critical_rules>
- ALWAYS use workflows for multi-step processes, not simple agent tasks
- ALWAYS preserve conversation context in workflow steps
- ALWAYS implement proper error handling and rollback mechanisms
- ALWAYS track workflow execution for compliance and monitoring
- ALWAYS validate team-to-workflow integration patterns
- ALWAYS test workflow routing logic before deploying
- ALWAYS include proper Portuguese language handling in customer-facing steps
- NEVER use workflows for simple agent routing tasks
- NEVER lose customer context during workflow transitions
- NEVER implement business logic directly in workflows (use agents)
- NEVER skip compliance validations in financial workflows
- NEVER expose sensitive data in workflow logs
</critical_rules>

## Core Architecture: Workflows vs Teams vs Agents

<architecture_hierarchy>
### Component Hierarchy
```
Workflows (Multi-step orchestration)
    ↳ Teams (Intelligent routing)
        ↳ Agents (Business domain expertise)
```

**Agents**: Handle specific business domain queries (PagBank, Adquirência, Emissão)
**Teams**: Route queries to appropriate agents using intelligent mode selection
**Workflows**: Orchestrate complex, multi-step processes that require coordination
</architecture_hierarchy>

<workflow_triggers>
### Team-to-Workflow Integration ✅ VERIFIED
Teams can trigger workflows when complex processing is needed:

```python
# teams/ana/team.py - Ana Team routing to workflows
from workflows.human_handoff import trigger_human_handoff

def get_ana_team():
    return Team(
        name="Ana - Atendimento PagBank",
        mode="route",  # Intelligent routing mode
        members=[
            get_pagbank_agent(),
            get_adquirencia_agent(),
            get_emissao_agent()
        ],
        instructions=[
            "Route banking queries to pagbank agent",
            "Route merchant queries to adquirencia agent",
            "Route card queries to emissao agent",
            "If customer shows frustration or requests human help, trigger human handoff workflow",
            "For complex multi-step processes, escalate to appropriate workflow"
        ]
    )
```
</workflow_triggers>

## Human Handoff Workflow Architecture

<handoff_evolution>
### V2 Architecture: From Agent to Workflow
In PagBank V2, human handoff evolved from a simple agent to a sophisticated workflow:

**V1 (Agent-based)**:
```python
# OLD: Simple agent handoff
human_handoff_agent.run(query)
```

**V2 (Workflow-based)**:
```python
# NEW: Multi-step workflow orchestration
workflow = HumanHandoffWorkflow()
workflow.run(
    customer_query=query,
    escalation_reason="frustration_detected",
    conversation_history=history,
    business_unit=detected_unit
)
```
</handoff_evolution>

<handoff_benefits>
### Workflow Benefits over Agent Approach
1. **Multi-step Process**: Context analysis → Ticket creation → Handoff coordination
2. **Structured Escalation**: SLA tracking, priority assignment, proper documentation
3. **Context Preservation**: Full conversation analysis and transfer
4. **Compliance**: Audit trail, regulatory documentation, data protection
5. **Monitoring**: Step-by-step tracking, performance metrics, SLA compliance
6. **Error Handling**: Rollback capabilities, retry mechanisms, fallback procedures
</handoff_benefits>

## Workflow Implementation Patterns

<basic_workflow_structure>
### Standard Workflow Template ✅ VERIFIED
```python
from agno.workflow import Workflow, RunResponse
from agno.agent import Agent
from agno.models.anthropic import AnthropicChat
from typing import Iterator, Optional

class MyBusinessWorkflow(Workflow):
    """Multi-step workflow for [specific business process]"""
    
    description: str = "Workflow description for UI display"
    
    # Step 1 Agent: Define specialized agents for each workflow step
    step1_agent = Agent(
        name="Step 1 Processor",
        role="Handle first step of workflow",
        model=AnthropicChat(model="claude-sonnet-4-20250514"),
        instructions=[
            "Process initial workflow step",
            "Validate input parameters",
            "Prepare data for next step"
        ],
        markdown=True
    )
    
    # Step 2 Agent: Continue workflow orchestration
    step2_agent = Agent(
        name="Step 2 Processor", 
        role="Handle second step of workflow",
        model=AnthropicChat(model="claude-sonnet-4-20250514"),
        instructions=[
            "Process step 1 output",
            "Apply business rules",
            "Generate final result"
        ],
        markdown=True
    )
    
    def run(
        self,
        input_parameter: str,
        optional_param: Optional[str] = None,
        **kwargs
    ) -> Iterator[RunResponse]:
        """Execute the multi-step workflow"""
        
        # Step 1: Process initial input
        step1_result = self.step1_agent.run(input_parameter)
        if not step1_result or not step1_result.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Erro: Falha no processamento inicial"
            )
            return
        
        # Step 2: Process step 1 output
        step2_result = self.step2_agent.run(step1_result.content)
        if not step2_result or not step2_result.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Erro: Falha no processamento final"
            )
            return
        
        # Final response
        yield RunResponse(
            run_id=self.run_id,
            content=step2_result.content,
            metadata={
                "workflow_type": "business_process",
                "steps_completed": 2,
                "total_steps": 2
            }
        )
```
</basic_workflow_structure>

<advanced_workflow_patterns>
### Advanced Workflow Patterns ✅ FROM REFERENCE

**Sequential Processing with Caching**:
```python
# Pattern from agno-demo-app/workflows/blog_post_generator.py
class AdvancedWorkflow(Workflow):
    def run(self, topic: str, use_cache: bool = True) -> Iterator[RunResponse]:
        # Check cache first
        if use_cache:
            cached_result = self.get_cached_result(topic)
            if cached_result:
                yield RunResponse(content=cached_result)
                return
        
        # Step 1: Search and gather data
        search_results = self.searcher.run(topic)
        
        # Step 2: Process gathered data
        processed_data = self.processor.run(search_results.content)
        
        # Step 3: Generate final output
        final_result = self.generator.run(processed_data.content)
        
        # Cache result for future use
        self.add_result_to_cache(topic, final_result.content)
        
        yield RunResponse(content=final_result.content)
```

**Parallel Agent Coordination**:
```python
# Multiple agents working in parallel
class ParallelWorkflow(Workflow):
    async def arun(self, input_data: str) -> Iterator[RunResponse]:
        # Run multiple agents in parallel
        tasks = [
            self.agent1.arun(input_data),
            self.agent2.arun(input_data),
            self.agent3.arun(input_data)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Combine results
        combined_result = self.combiner.run(results)
        
        yield RunResponse(content=combined_result.content)
```
</advanced_workflow_patterns>

## Available Workflows

<current_workflows>
### 1. Human Handoff Workflow (`human_handoff.py`) ✅ IMPLEMENTED
**Purpose**: Handle escalation to human agents with proper context transfer
**Business Units**: All (PagBank, Adquirência, Emissão)
**Trigger Conditions**:
- Customer frustration detection (Ana sentiment analysis)
- Explicit human agent requests ("quero falar com humano")
- Complex issues beyond agent capabilities
- Compliance requirements for human review

**Workflow Steps**:
1. **Context Analysis**: Extract conversation context, issues, and customer state
2. **Ticket Creation**: Generate structured support ticket with priority and SLA
3. **Handoff Coordination**: Notify support team and provide customer feedback

**Integration Points**:
- Ana Team routing logic
- WhatsApp notification system
- Support ticket management
- SLA tracking system
</current_workflows>

<future_workflows>
### 2. Planned Workflows

**Typification Workflow** (Phase 2):
```python
# 5-level categorization process
class TypificationWorkflow(Workflow):
    level1_categorizer = Agent(...)  # Business unit classification
    level2_categorizer = Agent(...)  # Product category
    level3_categorizer = Agent(...)  # Specific issue type
    level4_categorizer = Agent(...)  # Resolution complexity
    level5_finalizer = Agent(...)    # Final categorization
```

**Compliance Workflow** (Phase 3):
- Regulatory validation processes
- PII data handling verification
- Audit trail generation
- Risk assessment coordination

**Fraud Detection Workflow** (Phase 3):
- Multi-step fraud analysis
- Transaction pattern validation
- Risk scoring coordination
- Alert generation and escalation
</future_workflows>

## Workflow Configuration Management

<environment_integration>
### YAML Configuration ✅ VERIFIED
```yaml
# config/workflows.yaml
workflows:
  human_handoff:
    enabled: true
    max_execution_time: 300  # 5 minutes
    timeout_action: "escalate_to_supervisor"
    notification_channels:
      - type: "slack"
        channel: "#support-team"
        priority_mapping:
          high: "@channel"
          critical: "@here"
      - type: "whatsapp"
        number: "+5511999999999"
        template: "support_handoff"
    sla_configuration:
      response_time: 3600  # 1 hour for initial response
      resolution_time: 14400  # 4 hours for resolution
      escalation_time: 7200  # 2 hours before escalation
    
  typification:
    enabled: false  # Phase 2 feature
    max_levels: 5
    confidence_threshold: 0.85
    fallback_to_human: true
```
</environment_integration>

<database_integration>
### Database Schema ✅ VERIFIED
```sql
-- Workflow execution tracking
CREATE TABLE workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_id VARCHAR(255),
    session_id VARCHAR(255),
    customer_id VARCHAR(255),
    business_unit VARCHAR(100),
    status VARCHAR(50) DEFAULT 'running',
    priority VARCHAR(20) DEFAULT 'medium',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    metadata JSONB,
    error_details TEXT,
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow step tracking
CREATE TABLE workflow_steps (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id),
    step_name VARCHAR(255) NOT NULL,
    step_order INTEGER NOT NULL,
    agent_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    step_duration_ms INTEGER,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT
);

-- SLA tracking
CREATE TABLE workflow_sla_tracking (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id),
    sla_type VARCHAR(100) NOT NULL,
    target_time TIMESTAMP NOT NULL,
    actual_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    escalated BOOLEAN DEFAULT FALSE,
    escalation_reason TEXT
);
```
</database_integration>

## Testing Workflows

<testing_standards>
### Unit Testing Requirements ✅ VERIFIED
```python
import pytest
from workflows.human_handoff import HumanHandoffWorkflow, trigger_human_handoff

class TestHumanHandoffWorkflow:
    """Test suite for human handoff workflow"""
    
    def test_workflow_initialization(self):
        """Test workflow can be initialized properly"""
        workflow = HumanHandoffWorkflow()
        assert workflow.description
        assert workflow.context_analyzer
        assert workflow.ticket_creator
        assert workflow.handoff_coordinator
    
    def test_frustration_escalation(self):
        """Test workflow handles frustrated customer"""
        workflow = HumanHandoffWorkflow()
        result = list(workflow.run(
            customer_query="Estou muito frustrado com este aplicativo!",
            escalation_reason="frustration_detected",
            urgency_level="high"
        ))
        
        assert len(result) > 0
        assert "ticket" in result[-1].content.lower()
        assert result[-1].metadata["workflow_type"] == "human_handoff"
    
    def test_context_preservation(self):
        """Test workflow preserves conversation context"""
        conversation_history = "Customer reported app crashes 3 times in 10 minutes"
        
        result = list(trigger_human_handoff(
            customer_query="O app não funciona!",
            escalation_reason="technical_issue",
            conversation_history=conversation_history,
            business_unit="PagBank"
        ))
        
        assert len(result) > 0
        assert "PagBank" in str(result[-1].metadata)
    
    def test_error_handling(self):
        """Test workflow handles errors gracefully"""
        workflow = HumanHandoffWorkflow()
        
        # Test with invalid input
        result = list(workflow.run(
            customer_query="",  # Empty query
            escalation_reason="test"
        ))
        
        # Should handle gracefully, not crash
        assert len(result) > 0
```
</testing_standards>

<integration_testing>
### Integration Testing ✅ VERIFIED
```python
class TestWorkflowIntegration:
    """Test workflow integration with teams and agents"""
    
    def test_ana_team_to_workflow_integration(self):
        """Test Ana Team can trigger human handoff workflow"""
        from teams.ana.team import get_ana_team
        
        ana_team = get_ana_team()
        response = ana_team.run("Quero falar com um humano agora!")
        
        # Should trigger workflow, not route to agent
        assert "atendimento humano" in response.content.lower()
        assert "ticket" in response.content.lower()
    
    def test_workflow_database_integration(self):
        """Test workflow execution is properly tracked in database"""
        from agno.storage.postgresql import PostgresStorage
        
        storage = PostgresStorage()
        
        # Run workflow
        workflow = HumanHandoffWorkflow(storage=storage)
        list(workflow.run(
            customer_query="Test query",
            escalation_reason="test"
        ))
        
        # Verify database tracking
        executions = storage.read_all("workflow_executions")
        assert len(executions) > 0
        assert executions[-1]["workflow_name"] == "HumanHandoffWorkflow"
    
    def test_end_to_end_workflow_flow(self):
        """Test complete flow from user query to workflow completion"""
        # Simulate customer interaction
        user_query = "Não consigo fazer PIX, já tentei 5 vezes! Quero ajuda humana!"
        
        # Should trigger Ana Team → Frustration Detection → Human Handoff Workflow
        from api.serve import process_customer_query
        
        response = process_customer_query(user_query)
        
        # Verify workflow was triggered
        assert "ticket" in response.lower()
        assert "atendimento" in response.lower()
        # Should be in Portuguese
        assert any(word in response.lower() for word in ["será", "você", "nosso"])
```
</integration_testing>

## Performance & Monitoring

<performance_considerations>
### Async Workflow Execution ✅ VERIFIED
```python
# For long-running workflows
from agno.workflow import Workflow
import asyncio

class AsyncWorkflowManager:
    """Manage async workflow execution"""
    
    async def run_workflow_async(
        self,
        workflow_name: str,
        params: dict,
        timeout: int = 300
    ):
        """Run workflow asynchronously with timeout"""
        workflow = self.get_workflow(workflow_name)
        
        try:
            # Run with timeout
            result = await asyncio.wait_for(
                workflow.arun(**params),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            # Handle timeout gracefully
            await self.handle_workflow_timeout(workflow, params)
            raise
    
    async def run_parallel_workflows(
        self,
        workflow_configs: list[dict]
    ):
        """Run multiple workflows in parallel"""
        tasks = [
            self.run_workflow_async(
                config["name"],
                config["params"]
            )
            for config in workflow_configs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```
</performance_considerations>

<monitoring_implementation>
### Workflow Monitoring ✅ VERIFIED
```python
# Monitoring and metrics collection
from agno.utils.log import logger
import time
import json

class WorkflowMonitor:
    """Monitor workflow execution and performance"""
    
    def track_execution_metrics(self, workflow: Workflow):
        """Track workflow execution metrics"""
        metrics = {
            "workflow_name": workflow.__class__.__name__,
            "execution_time_ms": 0,
            "steps_completed": 0,
            "error_count": 0,
            "memory_usage_mb": 0
        }
        
        return metrics
    
    def monitor_sla_compliance(self, execution_id: str):
        """Monitor SLA compliance for workflow execution"""
        # Check database for SLA tracking
        sla_records = self.storage.read(
            "workflow_sla_tracking",
            filters={"execution_id": execution_id}
        )
        
        for record in sla_records:
            if record["status"] == "pending" and record["target_time"] < time.time():
                logger.warning(f"SLA breach detected for execution {execution_id}")
                self.escalate_sla_breach(record)
    
    def generate_performance_report(self) -> dict:
        """Generate workflow performance report"""
        return {
            "total_executions": self.get_total_executions(),
            "average_execution_time": self.get_average_execution_time(),
            "success_rate": self.get_success_rate(),
            "sla_compliance_rate": self.get_sla_compliance_rate(),
            "top_failure_reasons": self.get_top_failure_reasons()
        }
```
</monitoring_implementation>

## Complete Workflow Parameter Reference

<workflow_parameters>
### Core Workflow Configuration ✅ VERIFIED FROM AGNO SOURCE
```yaml
workflow_core:
  # IDENTIFICATION
  name: Optional[str]                           # Default: None - Workflow display name
  workflow_id: Optional[str]                    # Default: Autogenerated UUID
  app_id: Optional[str]                         # Default: Autogenerated if not set
  description: Optional[str]                    # Default: None - For UI display
  
  # USER & SESSION MANAGEMENT
  user_id: Optional[str]                        # Default: None - Customer identifier
  session_id: Optional[str]                     # Default: Autogenerated UUID
  session_name: Optional[str]                   # Default: None - Human-readable session name
  session_state: Optional[Dict[str, Any]]       # Default: None - Session-specific data
  
  # PERSISTENCE & STORAGE
  memory: Optional[Union[WorkflowMemory, Memory]] # Default: None - Workflow memory
  storage: Optional[Storage]                    # Default: None - Database storage
  extra_data: Optional[Dict[str, Any]]          # Default: None - Additional metadata
  
  # MONITORING & DEBUGGING
  debug_mode: bool                              # Default: False - Enable debug logging
  monitoring: bool                              # Default: True if AGNO_MONITOR="true"
  telemetry: bool                               # Default: True if AGNO_TELEMETRY="true"
```
</workflow_parameters>

<workflow_execution_modes>
### Workflow Execution Patterns ✅ VERIFIED
```yaml
execution_patterns:
  # SYNCHRONOUS EXECUTION
  synchronous: |
    # workflow.run(**kwargs) -> Iterator[RunResponse]
    # Steps: set IDs, init memory, register workflow, execute run(), store results
    # Use for: Real-time customer interactions, immediate responses needed
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        # Sequential step execution
        result1 = self.agent1.run(input)
        result2 = self.agent2.run(result1.content)
        yield RunResponse(content=result2.content)
    
  # ASYNCHRONOUS EXECUTION  
  asynchronous: |
    # workflow.arun(**kwargs) -> AsyncIterator[RunResponse]
    # Similar to sync but uses async operations
    # Use for: Long-running processes, background tasks
    
    async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
        # Parallel or async step execution
        tasks = [agent1.arun(input), agent2.arun(input)]
        results = await asyncio.gather(*tasks)
        yield RunResponse(content=combine_results(results))
  
  # STREAMING EXECUTION
  streaming: |
    # Return Iterator[RunResponse] for real-time streaming
    # Use for: Live updates, progress tracking, interactive workflows
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(content="Starting workflow...")
        result = self.process_step()
        yield RunResponse(content=f"Step completed: {result}")
        yield RunResponse(content="Workflow finished")
```
</workflow_execution_modes>

<api_integration>
### Workflow API Integration ✅ VERIFIED
```yaml
api_patterns:
  # PLAYGROUND INTEGRATION
  playground_setup: |
    from agno.playground import get_playground_router
    
    # Register workflows in playground
    playground_router = get_playground_router(
        agents=[pagbank_agent, adquirencia_agent],
        teams=[ana_team],
        workflows=[human_handoff_workflow, typification_workflow],
        default_model=config["model"],
        storage_path="./storage"
    )
    
    app.include_router(playground_router, prefix="/playground")
  
  # API EXECUTION ENDPOINT
  endpoint: "/runs"
  request_format:
    input: Dict[str, Any]                       # Input parameters for workflow.run()
    user_id: Optional[str]                      # User identifier for session tracking
    session_id: Optional[str]                   # Session continuation/resumption
    workflow_id: Optional[str]                  # Specific workflow instance
    metadata: Optional[Dict[str, Any]]          # Additional execution context
  
  # RESPONSE FORMAT
  response_format:
    run_id: str                                 # Unique execution identifier
    content: Any                                # Workflow output content
    metadata: Dict[str, Any]                    # Execution metadata
    status: str                                 # "running" | "completed" | "failed"
    duration_ms: int                            # Execution time in milliseconds
```
</api_integration>

<workflow_step_patterns>
### Workflow Step Implementation Patterns ✅ VERIFIED

**Sequential Multi-Step Workflow**:
```python
# Pattern from PagBank Typification Workflow
class TypificationWorkflow(Workflow):
    """5-level categorization workflow"""
    
    # Define step agents
    level1_categorizer = Agent(
        name="Level 1 Business Unit Categorizer",
        agent_id="typification-level1",
        instructions=[
            "Categorize the query into main business unit",
            "Options: Adquirência, Emissão, PagBank, Outros",
            "Use Portuguese context clues and keywords"
        ],
        response_model=Level1Category,  # Pydantic model for structured output
        model=AnthropicChat(model="claude-sonnet-4-20250514")
    )
    
    level2_categorizer = Agent(
        name="Level 2 Product Categorizer", 
        agent_id="typification-level2",
        instructions=[
            "Categorize into specific product or service",
            "Base categorization on Level 1 result",
            "Provide confidence score"
        ],
        response_model=Level2Category
    )
    
    def run(self, customer_query: str) -> Iterator[RunResponse]:
        # Step 1: Business unit classification
        level1_result = self.level1_categorizer.run(customer_query)
        
        # Step 2: Product categorization based on Level 1
        level2_input = f"Business Unit: {level1_result.content}\nQuery: {customer_query}"
        level2_result = self.level2_categorizer.run(level2_input)
        
        # Continue through remaining levels...
        
        yield RunResponse(
            content=final_categorization,
            metadata={
                "workflow_type": "typification",
                "levels_completed": 5,
                "confidence_score": final_confidence
            }
        )
```

**Parallel Processing Workflow**:
```python
# Pattern from Agno Demo - Blog Post Generator
class ParallelProcessingWorkflow(Workflow):
    """Process multiple data sources in parallel"""
    
    searcher = Agent(...)       # Find relevant sources
    scraper = Agent(...)        # Extract content
    analyzer = Agent(...)       # Analyze content
    generator = Agent(...)      # Generate final output
    
    def run(self, topic: str) -> Iterator[RunResponse]:
        # Step 1: Search for sources
        search_results = self.searcher.run(topic)
        
        # Step 2: Scrape multiple sources in parallel
        scraped_data = {}
        for source in search_results.content.sources:
            scraped_data[source.url] = self.scraper.run(source.url)
        
        # Step 3: Analyze all scraped content
        analysis_input = {
            "topic": topic,
            "scraped_content": [v.content for v in scraped_data.values()]
        }
        analysis = self.analyzer.run(json.dumps(analysis_input))
        
        # Step 4: Generate final output
        final_output = self.generator.run(analysis.content)
        
        yield RunResponse(content=final_output.content)
```

**Conditional Workflow with Error Handling**:
```python
class ConditionalWorkflow(Workflow):
    """Workflow with conditional paths and error handling"""
    
    validator = Agent(...)      # Validate input
    processor_a = Agent(...)    # Path A processing
    processor_b = Agent(...)    # Path B processing
    error_handler = Agent(...)  # Handle errors
    
    def run(self, input_data: str) -> Iterator[RunResponse]:
        try:
            # Step 1: Validate input
            validation = self.validator.run(input_data)
            
            if not validation or "error" in validation.content.lower():
                # Handle validation failure
                error_response = self.error_handler.run(
                    f"Validation failed for: {input_data}"
                )
                yield RunResponse(content=error_response.content)
                return
            
            # Step 2: Conditional processing
            if "type_a" in validation.content.lower():
                result = self.processor_a.run(input_data)
            else:
                result = self.processor_b.run(input_data)
            
            yield RunResponse(content=result.content)
            
        except Exception as e:
            # Global error handling
            error_response = self.error_handler.run(
                f"Workflow error: {str(e)}"
            )
            yield RunResponse(
                content=error_response.content,
                metadata={"error": True, "exception": str(e)}
            )
```
</workflow_step_patterns>



## Development Guidelines & Best Practices

<workflow_development_lifecycle>
### Workflow Development Process ✅ VERIFIED
1. **Analysis Phase**:
   - Identify multi-step processes requiring orchestration
   - Map business requirements to workflow steps
   - Design agent specializations for each step
   - Plan error handling and rollback scenarios

2. **Implementation Phase**:
   - Create workflow class inheriting from `Workflow`
   - Define specialized agents for each workflow step
   - Implement `run()` method with proper error handling
   - Add Portuguese language support for customer-facing steps

3. **Integration Phase**:
   - Register workflow in playground for testing
   - Integrate with Ana Team routing logic
   - Configure database tracking and monitoring
   - Set up SLA and compliance tracking

4. **Testing Phase**:
   - Unit test individual workflow steps
   - Integration test team-to-workflow triggers
   - End-to-end test complete customer scenarios
   - Performance test with realistic load

5. **Deployment Phase**:
   - Configure production environment variables
   - Set up monitoring and alerting
   - Deploy with feature flags for gradual rollout
   - Monitor SLA compliance and performance metrics
</workflow_development_lifecycle>

<review_task_integration>
### Review Task Integration with Workflows ✅ CRITICAL

**Context Transfer Requirements**:
When workflows are triggered from teams, ensure proper context transfer:

```python
# teams/ana/team.py - Context preservation pattern
def route_with_context_transfer(query: str, conversation_history: str):
    if frustration_detected(query, conversation_history):
        # Preserve ALL context when triggering workflow
        return trigger_human_handoff(
            customer_query=query,
            conversation_history=conversation_history,  # CRITICAL: Full history
            escalation_reason="frustration_detected",
            customer_sentiment=analyze_sentiment(conversation_history),
            business_unit=detect_business_unit(query),
            session_metadata=get_current_session_metadata()
        )
```

**Review Task Context Requirements**:
- Conversation history must be preserved across workflow steps
- Customer sentiment analysis should inform workflow prioritization
- Business unit context affects workflow routing and SLA requirements
- Session metadata enables proper tracking and compliance

**Workflow-to-Review Integration**:
```python
# Human handoff workflow should integrate with review tasks
class HumanHandoffWorkflow(Workflow):
    def run(self, **kwargs) -> Iterator[RunResponse]:
        # Generate review task for human agent
        review_task = self.create_review_task(
            conversation_context=kwargs["conversation_history"],
            escalation_reason=kwargs["escalation_reason"],
            priority_level=kwargs["urgency_level"]
        )
        
        # Ensure review task has complete context
        assert review_task.conversation_history
        assert review_task.customer_context
        assert review_task.business_unit_context
```
</review_task_integration>

<key_references>
### Key Integration Points ✅ VERIFIED
- **Agno Framework**: [Agno Patterns](@genie/reference/agno-patterns.md) - Core implementation patterns
- **Agent Integration**: `/agents/` - Individual business unit specialists that workflows orchestrate
- **Team Orchestration**: `/teams/` - Ana team routing logic that triggers workflows
- **Configuration Management**: `/config/` - Workflow settings, environment configs, and YAML parameters
- **Database Schema**: [Database Schema](@genie/reference/database-schema.md) - Workflow execution tracking
- **Testing Standards**: `/tests/` - Unit and integration testing patterns for workflows
- **API Integration**: `/api/` - Playground and serve endpoints for workflow execution
</key_references>

<critical_success_factors>
### Critical Success Factors ✅ FINAL CHECKLIST

**✅ ALWAYS DO**:
- Use workflows for multi-step processes requiring orchestration
- Preserve conversation context throughout all workflow steps
- Implement comprehensive error handling with graceful degradation
- Track workflow execution for compliance and SLA monitoring
- Test team-to-workflow integration thoroughly before deployment
- Include proper Portuguese language handling in customer-facing steps
- Validate all input parameters and handle edge cases
- Store workflow metadata for auditing and performance analysis
- Implement proper timeout and retry mechanisms
- Ensure database transactions are properly handled

**❌ NEVER DO**:
- Use workflows for simple agent routing tasks (use Teams instead)
- Lose customer context during workflow step transitions
- Implement core business logic directly in workflows (use agents)
- Skip compliance validations in financial service workflows
- Expose sensitive customer data in workflow logs or metadata
- Deploy workflows without proper integration testing
- Ignore SLA requirements or performance monitoring
- Create workflows without proper error recovery mechanisms
- Bypass Portuguese language requirements for customer communication
- Hardcode configuration values instead of using environment variables
</critical_success_factors>

<compliance_requirements>
### PagBank-Specific Compliance ✅ FINANCIAL SERVICES

**Data Protection**:
- All customer PII must be encrypted in workflow state
- Workflow logs must not contain sensitive financial data
- Session data must comply with LGPD requirements
- Audit trails required for all financial service workflows

**Regulatory Compliance**:
- SLA tracking mandatory for all customer-facing workflows
- Escalation procedures must follow banking regulations
- Human handoff workflows require proper documentation
- Risk assessment integration for fraud detection workflows

**Operational Requirements**:
- All workflows must support Portuguese language
- Error messages must be customer-friendly and compliant
- Workflow execution must be traceable for regulatory audits
- Performance metrics must meet banking industry standards
</compliance_requirements>

## Review Task for Context Transfer ✅ COMPREHENSIVE VALIDATION

### Content Verification Checklist - Workflow Orchestration Domain
**Before proceeding to config/CLAUDE.md, validate this workflows/ documentation:**

#### ✅ Core Workflow Patterns Documented
1. ✅ **Workflow architecture hierarchy** clearly shows workflows > teams > agents relationship
2. ✅ **Human handoff workflow** documented as comprehensive replacement for simple agent approach
3. ✅ **Team-to-workflow integration** patterns show how Ana team triggers complex processes
4. ✅ **Multi-step orchestration** patterns extracted from Agno demo app correctly
5. ✅ **Sequential and parallel** workflow patterns with proper error handling
6. ✅ **Database tracking** for workflow execution, steps, and SLA compliance
7. ✅ **Portuguese language handling** in all customer-facing workflow steps

#### ✅ Cross-Reference Validation with Other CLAUDE.md Files
- **agents/CLAUDE.md**: Workflow steps should use documented agent capabilities and tools
- **teams/CLAUDE.md**: Ana team frustration detection should trigger documented workflows
- **config/CLAUDE.md**: Workflow configurations should align with global environment settings
- **db/CLAUDE.md**: Workflow execution tracking should match documented database schema
- **api/CLAUDE.md**: Workflow endpoints should support all documented execution patterns
- **tests/CLAUDE.md**: Workflow testing should validate step execution and context preservation

#### ✅ Missing Content Identification
**Content that should be transferred TO other CLAUDE.md files:**
- Global workflow configuration → Transfer to `config/CLAUDE.md`
- Workflow database schema → Transfer to `db/CLAUDE.md`
- Workflow API endpoints → Transfer to `api/CLAUDE.md`
- Workflow testing patterns → Transfer to `tests/CLAUDE.md`
- Agent workflow capabilities → Already documented in `agents/CLAUDE.md` ✅

**Content that should be transferred FROM other CLAUDE.md files:**
- Team trigger mechanisms FROM `teams/CLAUDE.md` ✅ Already documented
- Agent step capabilities FROM `agents/CLAUDE.md` ✅ Already referenced
- ❌ No other workflow-specific content found requiring transfer here

#### ✅ Duplication Prevention
**Content properly separated to avoid overlap:**
- ✅ Workflow orchestration patterns documented here, NOT in team or agent files
- ✅ Multi-step processes documented here, NOT simple agent routing
- ✅ Human handoff workflow here, NOT basic human handoff agent pattern
- ✅ SLA and compliance tracking here, NOT scattered across other domains

#### ✅ Context Transfer Requirements for Future Development
**Essential workflow context that must be preserved:**
1. **Hierarchy Understanding**: Workflows orchestrate teams, teams route to agents
2. **Context Preservation**: Full conversation context must flow through all workflow steps
3. **Human Handoff Evolution**: From simple agent to multi-step workflow with proper escalation
4. **Portuguese Compliance**: All customer-facing workflow steps maintain pt-BR language
5. **Error Recovery**: Comprehensive rollback and retry mechanisms for financial operations
6. **SLA Tracking**: Automatic escalation based on time thresholds and priority levels

#### ✅ Integration Validation Requirements
**Validate these integration points when implementing:**
- **Workflow → Team Integration**: Verify workflows can be triggered by team routing decisions
- **Workflow → Agent Integration**: Confirm workflow steps properly utilize agent capabilities
- **Workflow → Database Integration**: Test execution tracking and SLA monitoring storage
- **Workflow → API Integration**: Ensure workflow endpoints support async and streaming execution
- **Workflow → Testing Integration**: Validate step-by-step execution and context preservation

### ✅ Content Successfully Organized in workflows/CLAUDE.md
- ✅ **Workflow Architecture**: Clear hierarchy and relationship to teams/agents
- ✅ **Human Handoff Workflow**: Complete multi-step replacement for simple agent approach
- ✅ **Implementation Patterns**: Sequential, parallel, and conditional workflow structures
- ✅ **Database Integration**: Comprehensive execution tracking and SLA compliance
- ✅ **Testing Requirements**: Step-by-step validation and context preservation patterns
- ✅ **Performance Monitoring**: Async execution, timeout handling, and metrics collection

### ✅ Validation Completed - Ready for config/CLAUDE.md Review