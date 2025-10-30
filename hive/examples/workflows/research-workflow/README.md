# Sequential Research Workflow

A complete example of a multi-step research workflow that demonstrates sequential processing with state passing between steps.

## Overview

This workflow executes research tasks in four sequential steps:

1. **Planning** - Analyzes the topic and creates a structured research plan
2. **Research** - Gathers information based on the plan
3. **Analysis** - Processes and analyzes collected data
4. **Summary** - Generates comprehensive final summary

## When to Use This Pattern

Use sequential workflows when:

- Steps must execute in order (each depends on previous results)
- You need to pass state/data between steps
- Building complex pipelines with multiple stages
- Each step has a distinct responsibility

**Examples:**
- Research and reporting pipelines
- Data processing workflows
- Multi-stage content generation
- Document analysis with synthesis

## Structure

```
research-workflow/
├── config.yaml     # Workflow configuration
├── workflow.py     # Implementation with step functions
└── README.md       # This file
```

## Configuration (config.yaml)

```yaml
workflow:
  name: "Sequential Research Workflow"
  workflow_id: "research-workflow"
  version: "1.0.0"

steps:
  - name: "Planning"
    type: "agent"
  - name: "Research"
    type: "agent"
  - name: "Analysis"
    type: "function"
  - name: "Summary"
    type: "agent"
```

## Usage

### Basic Usage

```python
from my_test_project.ai.workflows.examples.research_workflow.workflow import get_research_workflow

# Create workflow instance
workflow = get_research_workflow()

# Run with a research topic
response = workflow.run(message="The impact of AI on software development")

print(response.content)  # Final summary
```

### Async Usage

```python
import asyncio

async def run_research():
    workflow = get_research_workflow()
    response = await workflow.arun(message="Climate change impact on agriculture")
    return response.content

result = asyncio.run(run_research())
```

### Streaming Results

```python
# Stream each step's output
for response in workflow.run(message="Blockchain in healthcare", stream=True):
    print(f"Step: {response.step_name}")
    print(f"Output: {response.content}\n")
```

### Accessing Workflow State

```python
response = workflow.run(message="Machine learning in medicine")

# Access complete workflow state
if hasattr(response, 'workflow_session_state'):
    state = response.workflow_session_state
    print(f"Topic: {state['topic']}")
    print(f"Plan: {state['plan']}")
    print(f"Findings: {state['findings']}")
    print(f"Analysis: {state['analysis']}")
    print(f"Summary: {state['summary']}")
```

## Step Functions

### 1. Planning Step (Agent-based)

Creates a structured research plan:
- Key questions to answer
- Areas to explore
- Expected outcomes

### 2. Research Step (Agent-based)

Executes research based on plan:
- Gathers information
- Collects supporting evidence
- Documents key insights

### 3. Analysis Step (Function-based)

Processes findings (pure function):
- Analyzes data points
- Identifies themes
- Assesses confidence

### 4. Summary Step (Agent-based)

Creates final deliverable:
- Executive summary
- Key findings
- Recommendations
- Conclusion

## State Passing Pattern

```python
def step_function(step_input) -> StepOutput:
    # Initialize state if needed
    if step_input.workflow_session_state is None:
        step_input.workflow_session_state = {}

    # Access previous step data
    previous_data = step_input.workflow_session_state.get("key", "")

    # Do work...
    result = process(previous_data)

    # Store for next step
    step_input.workflow_session_state["new_key"] = result

    return StepOutput(content=result)
```

## Testing

Run the standalone test:

```bash
cd /home/cezar/automagik/automagik-hive/my-test-project
python -m ai.workflows.examples.research_workflow.workflow
```

Expected output:
- Workflow creation confirmation
- Step-by-step execution logs
- Final research summary
- Workflow state summary

## Customization

### Modify Steps

Edit `workflow.py` to:
- Add/remove steps
- Change step logic
- Adjust agent instructions
- Modify state handling

### Change Model

Edit `config.yaml`:
```yaml
model:
  provider: "anthropic"
  id: "claude-sonnet-4-20250514"
  temperature: 0.7
```

### Add Storage

Enable session persistence:
```python
from agno.storage.postgres import PgStorage

workflow = get_research_workflow(
    storage=PgStorage(
        table_name="research_workflow_sessions",
        db_url="postgresql://..."
    )
)
```

## Key Features

- **Sequential Execution**: Steps run in order
- **State Management**: Data flows between steps
- **Mixed Step Types**: Agents + pure functions
- **Configurable**: YAML-driven configuration
- **Testable**: Standalone test included
- **Production-Ready**: Storage support included

## Integration with Your Project

1. Copy this directory to your project
2. Adjust config.yaml for your needs
3. Modify step functions as needed
4. Add to your workflow registry:

```python
from ai.workflows.examples.research_workflow.workflow import get_research_workflow

# In your registry
workflows = {
    "research-workflow": get_research_workflow,
    # ... other workflows
}
```

## Related Examples

- **parallel-workflow** - For concurrent step execution
- **support-bot** (agent) - For single-agent interactions
- **csv-analyzer** (tool) - For data analysis tools

## Best Practices

1. **Keep steps focused** - Single responsibility per step
2. **Name state keys clearly** - Use descriptive names
3. **Handle missing state** - Always check for None
4. **Document state schema** - What each step expects/produces
5. **Test each step** - Unit test step functions independently
6. **Use type hints** - Makes code clearer and safer

## Troubleshooting

**State not persisting?**
- Add storage parameter when creating workflow
- Check workflow_session_state initialization

**Steps executing out of order?**
- Sequential workflows guarantee order
- Use Parallel() for concurrent execution

**Agent responses too long?**
- Adjust model temperature
- Refine agent instructions
- Add output length constraints

## Learn More

- [Agno Workflows Documentation](https://docs.agno.com)
- [Workflow Best Practices](../../README.md)
- [Agent Examples](../../agents/examples/)
- [Tool Examples](../../tools/examples/)
