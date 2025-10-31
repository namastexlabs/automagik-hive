# Parallel Processing Workflow

A complete example demonstrating concurrent execution of multiple steps using Agno's `Parallel()` feature for performance optimization.

## Overview

This workflow processes multiple data sources simultaneously:

1. **Preparation** - Set up data sources and parameters
2. **Parallel Processing** - Process 3 sources concurrently:
   - Source 1: User Database
   - Source 2: API Logs
   - Source 3: Analytics Data
3. **Aggregation** - Merge all parallel results
4. **Report** - Generate comprehensive final report

## When to Use This Pattern

Use parallel workflows when:

- Steps can execute independently (no dependencies)
- Processing multiple similar items
- Performance/speed is critical
- Working with multiple data sources
- Each step has similar completion time

**Examples:**
- Multi-source data processing
- Batch operations on independent items
- Concurrent API calls
- Parallel document processing
- Multi-channel notifications

## Structure

```
parallel-workflow/
├── config.yaml     # Workflow configuration
├── workflow.py     # Implementation with parallel steps
└── README.md       # This file
```

## Key Performance Benefits

**Sequential vs Parallel:**

```
Sequential Processing:
Step 1: 0.5s
Step 2: 0.8s  (waits for Step 1)
Step 3: 0.6s  (waits for Step 2)
Total: 1.9s

Parallel Processing:
Step 1: 0.5s ┐
Step 2: 0.8s ├─ Execute simultaneously
Step 3: 0.6s ┘
Total: 0.8s (longest step)

Time Saved: 1.1s (58% faster!)
```

## Configuration (config.yaml)

```yaml
workflow:
  name: "Parallel Processing Workflow"
  workflow_id: "parallel-workflow"
  version: "1.0.0"

steps:
  - name: "Preparation"
    type: "function"

  - name: "ParallelProcessing"
    type: "parallel"
    substeps:
      - name: "ProcessSource1"
      - name: "ProcessSource2"
      - name: "ProcessSource3"

  - name: "Aggregation"
    type: "function"

  - name: "Report"
    type: "agent"
```

## Usage

### Basic Usage

```python
from my_test_project.ai.workflows.examples.parallel_workflow.workflow import get_parallel_workflow
import time

# Create workflow
workflow = get_parallel_workflow()

# Run with processing request
start = time.time()
response = workflow.run(message="Process all data sources for monthly report")
elapsed = time.time() - start

print(f"Processing completed in {elapsed:.2f}s")
print(response.content)
```

### Streaming Each Step

```python
# Stream results from each parallel step
for response in workflow.run(message="Process data sources", stream=True):
    print(f"Step: {response.step_name}")
    print(f"Output: {response.content}\n")

    # Parallel steps complete concurrently
    if "ProcessSource" in response.step_name:
        print("  → Running in parallel!")
```

### Accessing Performance Metrics

```python
response = workflow.run(message="Process sources")

if hasattr(response, 'workflow_session_state'):
    state = response.workflow_session_state
    agg = state.get('aggregation', {})

    print(f"Sources Processed: {agg['total_sources']}")
    print(f"Records Processed: {agg['total_records']:,}")
    print(f"Time Saved: {agg['time_saved']:.2f}s")
    print(f"Efficiency: {(agg['time_saved'] / agg['total_time'] * 100):.1f}%")
```

## Parallel Step Pattern

### Defining Parallel Steps

```python
from agno.workflow import Workflow, Step, Parallel

workflow = Workflow(
    name="My Parallel Workflow",
    steps=[
        Step(name="Setup", function=setup_function),

        # Parallel execution block
        Parallel(
            Step(name="Task1", function=task1_function),
            Step(name="Task2", function=task2_function),
            Step(name="Task3", function=task3_function)
        ),

        Step(name="Merge", function=merge_function)
    ]
)
```

### Writing Parallel-Safe Functions

```python
def parallel_step_function(step_input) -> StepOutput:
    """
    Parallel steps must be thread-safe and independent.
    """
    # Access shared state (read-only is safest)
    data = step_input.workflow_session_state.get("data", [])

    # Do independent work
    result = process(data)

    # Store results (use lists for parallel writes)
    if "results" not in step_input.workflow_session_state:
        step_input.workflow_session_state["results"] = []

    step_input.workflow_session_state["results"].append(result)

    return StepOutput(content=result)
```

## State Management in Parallel Steps

### Safe Pattern (Append to List)

```python
# Each parallel step appends independently
if "results" not in step_input.workflow_session_state:
    step_input.workflow_session_state["results"] = []

step_input.workflow_session_state["results"].append(my_result)
```

### Unsafe Pattern (Direct Write)

```python
# ⚠️ DANGER: Parallel steps may overwrite each other
step_input.workflow_session_state["result"] = my_result  # BAD!
```

### Aggregating Parallel Results

```python
def aggregation_step(step_input) -> StepOutput:
    """Run after parallel steps complete."""
    results = step_input.workflow_session_state.get("results", [])

    # Merge results from all parallel steps
    merged = {
        "total_items": len(results),
        "combined_data": combine(results),
        "statistics": calculate_stats(results)
    }

    return StepOutput(content=merged)
```

## Testing

Run the standalone test:

```bash
cd /home/cezar/automagik/automagik-hive/my-test-project
python -m ai.workflows.examples.parallel_workflow.workflow
```

Expected output:
- Workflow creation confirmation
- Preparation step output
- Parallel processing (concurrent)
- Aggregation results with time saved
- Final report
- Performance metrics

## Customization

### Adjust Number of Parallel Steps

```python
# Add more parallel steps
workflow = Workflow(
    steps=[
        Step(name="Setup", function=setup),
        Parallel(
            Step(name="Task1", function=task1),
            Step(name="Task2", function=task2),
            Step(name="Task3", function=task3),
            Step(name="Task4", function=task4),  # Added
            Step(name="Task5", function=task5)   # Added
        ),
        Step(name="Merge", function=merge)
    ]
)
```

### Dynamic Parallel Steps

```python
def create_dynamic_parallel_workflow(num_sources: int) -> Workflow:
    """Create workflow with dynamic number of parallel steps."""

    # Create parallel steps dynamically
    parallel_steps = [
        Step(
            name=f"ProcessSource{i}",
            function=lambda si, idx=i: process_source(si, idx)
        )
        for i in range(1, num_sources + 1)
    ]

    return Workflow(
        name="Dynamic Parallel Workflow",
        steps=[
            Step(name="Setup", function=setup),
            Parallel(*parallel_steps),  # Unpack list
            Step(name="Merge", function=merge)
        ]
    )
```

### Add Error Handling

```python
def safe_parallel_step(step_input) -> StepOutput:
    """Parallel step with error handling."""
    try:
        result = risky_operation()
        return StepOutput(content=result)
    except Exception as e:
        # Store error, don't fail entire workflow
        if "errors" not in step_input.workflow_session_state:
            step_input.workflow_session_state["errors"] = []

        step_input.workflow_session_state["errors"].append({
            "step": "ProcessSource1",
            "error": str(e)
        })

        return StepOutput(content="Failed: " + str(e))
```

## Performance Tuning

### Optimal Parallel Step Count

```python
# Too few: Not utilizing parallelism
Parallel(
    Step(name="Task1", function=f1),
    Step(name="Task2", function=f2)
)  # Only 2 steps - minimal benefit

# Optimal: 3-10 concurrent tasks
Parallel(
    Step(name="Task1", function=f1),
    Step(name="Task2", function=f2),
    Step(name="Task3", function=f3),
    Step(name="Task4", function=f4),
    Step(name="Task5", function=f5)
)  # Good balance

# Too many: Diminishing returns
Parallel(
    *[Step(name=f"Task{i}", function=f) for i in range(100)]
)  # Overhead may exceed benefits
```

### Balance Step Duration

```python
# Balanced: All steps take similar time
Parallel(
    Step(name="Task1", function=task_500ms),
    Step(name="Task2", function=task_600ms),
    Step(name="Task3", function=task_550ms)
)  # Total time: ~600ms (longest)

# Unbalanced: One step much slower
Parallel(
    Step(name="Task1", function=task_500ms),
    Step(name="Task2", function=task_5000ms),  # 10x slower!
    Step(name="Task3", function=task_550ms)
)  # Total time: ~5000ms (negates benefit)
```

## Integration with Your Project

1. Copy this directory to your project
2. Modify data sources in `preparation_step()`
3. Adjust parallel step functions for your use case
4. Add to workflow registry:

```python
from ai.workflows.examples.parallel_workflow.workflow import get_parallel_workflow

workflows = {
    "parallel-workflow": get_parallel_workflow,
    # ... other workflows
}
```

## Related Examples

- **research-workflow** - For sequential step execution
- **support-bot** (agent) - For single-agent interactions
- **csv-analyzer** (tool) - For data processing tools

## Best Practices

1. **Keep steps independent** - No dependencies between parallel steps
2. **Use list appends** - Safest for parallel state writes
3. **Balance step duration** - Similar execution times optimize performance
4. **Limit parallel count** - 3-10 steps is usually optimal
5. **Handle errors gracefully** - Don't let one failure kill workflow
6. **Measure performance** - Track time saved vs sequential execution

## Troubleshooting

**Parallel steps not running concurrently?**
- Check that steps are truly independent
- Verify no shared resources causing locks
- Ensure using `Parallel()` wrapper correctly

**State corruption in parallel steps?**
- Use list appends instead of direct writes
- Make parallel functions read-only on shared state
- Add synchronization if absolutely necessary

**One step much slower than others?**
- Profile each step to find bottleneck
- Consider splitting slow step into smaller parallel units
- Move slow step out of parallel block if dependent

**Performance not improving?**
- Check if steps are actually independent
- Measure overhead vs time saved
- Consider if parallelism is appropriate for use case

## Learn More

- [Agno Workflows Documentation](https://docs.agno.com)
- [Parallel Execution Best Practices](../../README.md)
- [Sequential Workflow Example](../research-workflow/)
- [Agent Examples](../../agents/examples/)
