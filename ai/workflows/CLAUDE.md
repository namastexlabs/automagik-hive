# CLAUDE.md - Workflows

🗺️ **Workflow Orchestration Domain**

## 🧭 Navigation

**🔙 AI Hub**: [/ai/CLAUDE.md](../CLAUDE.md) | **🔙 Main**: [/CLAUDE.md](../../CLAUDE.md)  
**🔗 Related**: [Agents](../agents/CLAUDE.md) | [Teams](../teams/CLAUDE.md) | [API](../../api/CLAUDE.md)

## Purpose

Step-based workflows using **Agno Workflows 2.0** (v1.7.4+) with parallel execution, conditional logic, and session state management.

## Workflow Components

**Step Types**:
- **`Step`** → Sequential execution
- **`Parallel`** → Concurrent execution
- **`Condition`** → Conditional branching
- **`Loop`** → Iterative execution  
- **`Router`** → Dynamic routing

## Quick Start

```bash
# Create workflow
cp -r ai/workflows/template-workflow ai/workflows/my-workflow

# Factory pattern
def get_my_workflow(**kwargs) -> Workflow:
    return Workflow(
        name="My Process",
        steps=[
            Step("Analysis", agent=analysis_agent),
            Parallel(
                Step("Testing", agent=qa_agent),
                Step("Docs", agent=doc_agent)
            ),
            Step("Deploy", function=deploy_function)
        ],
        **kwargs
    )
```

## Step Types

**Core building blocks**:
```python
# Sequential (default)
Step("Analysis", agent=analyst)

# Parallel execution
Parallel(
    Step("Testing", agent=qa_agent),
    Step("Docs", agent=doc_agent)
)

# Conditional branching
Condition(
    evaluator=is_complex_task,
    steps=[Step("Deep Analysis", agent=expert)]
)

# Loop execution
Loop(
    steps=[Step("Research", agent=researcher)],
    exit_condition=quality_check,
    max_iterations=3
)

# Dynamic routing
Router(
    evaluator=route_by_complexity,
    routes={
        "simple": [quick_agent],
        "complex": [expert_team]
    }
)
```

## Factory Pattern

**Standard implementation**:
```python
def get_my_workflow(**kwargs) -> Workflow:
    """Factory for workflow creation"""
    
    def step_function(step_input):
        # Access session state
        shared_data = step_input.workflow_session_state
        
        # Process data
        result = process_data(step_input.message)
        
        # Update state for next steps
        shared_data["results"] = result
        
        return StepOutput(content=result)
    
    return Workflow(
        name="My Process",
        storage=PostgresStorage(
            table_name="my_workflow",
            auto_upgrade_schema=True
        ),
        steps=[
            Step("Input", function=step_function),
            Step("Analysis", agent=analysis_agent),
            Parallel(
                Step("QA", agent=qa_agent),
                Step("Docs", agent=doc_agent)
            )
        ],
        **kwargs
    )
```

## Session State

**Share data across steps**:
```python
def step_with_state(step_input):
    # Access shared workflow state
    if step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}
    
    # Store data for next steps
    step_input.workflow_session_state["analysis"] = results
    
    return StepOutput(content=processed_data)
```

## Execution

**Run workflows**:
```python
# Sync execution
response = workflow.run(message="Process this data")

# Async execution  
response = await workflow.arun(message="Async process")

# Streaming
for response in workflow.run(message="Stream process", stream=True):
    print(f"Step: {response.step_name}, Content: {response.content}")
```

## Integration

- **Agents**: Use as workflow steps
- **Teams**: Teams can be workflow components
- **API**: Auto-exposed via `Playground(workflows=[...])`
- **MCP**: Integrate external services in steps
- **Storage**: PostgreSQL with session persistence

## Critical Rules

- **🚨 Version Bump**: ANY workflow change requires version increment
- **Factory Pattern**: Always use factory functions for creation
- **Session State**: Use for cross-step data sharing
- **Error Handling**: Implement retry logic with `max_retries`
- **Step Responsibility**: Each step should have single clear purpose

## Performance

- **Target**: <30s for complex multi-step processes
- **Parallel**: Use `Parallel` for independent operations
- **State**: Session state persists across steps
- **Storage**: PostgreSQL for production persistence
- **Retry**: Automatic retry on step failures

Navigate to [Agents](../agents/CLAUDE.md) for step components or [Teams](../teams/CLAUDE.md) for team-based steps.