# Workflows Guide

Build multi-step processes with sequential and parallel execution.

## What is a Workflow?

A workflow is a series of steps that execute in a defined order. Each step can be:
- An agent task
- A team decision
- A custom function
- Parallel branches

**Example**: Analyze support request → Generate response → Send notification

## Quick Start

### 1. Create Workflow Directory

```bash
mkdir -p ai/workflows/my-workflow
cd ai/workflows/my-workflow
```

### 2. Create config.yaml

```yaml
workflow:
  name: "Support Flow"
  description: "Customer support processing"

steps:
  - name: "Analyze Request"
    agent: "analyzer-agent"
    description: "Understand customer issue"

  - name: "Generate Response"
    agent: "responder-agent"
    description: "Create helpful response"

  - name: "Send Notification"
    function: "send_email"
    description: "Notify customer"
```

### 3. Create workflow.py

```python
"""My workflow factory."""
import yaml
from pathlib import Path
from agno.workflow import Workflow, Step
from hive.scaffolder.generator import generate_agent_from_yaml

def get_my_workflow(**kwargs) -> Workflow:
    """Create workflow."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Build steps
    steps = []
    for step_config in config.get("steps", []):
        if "agent" in step_config:
            agent_path = f"ai/agents/{step_config['agent']}/config.yaml"
            agent = generate_agent_from_yaml(agent_path)
            step = Step(
                name=step_config["name"],
                agent=agent,
                description=step_config.get("description")
            )
        elif "function" in step_config:
            step = Step(
                name=step_config["name"],
                function=None,  # Implement separately
                description=step_config.get("description")
            )
        steps.append(step)

    return Workflow(
        name=config["workflow"]["name"],
        steps=steps,
        **kwargs
    )
```

## Directory Structure

```
ai/workflows/
├── my-workflow/
│   ├── config.yaml    # Workflow configuration
│   └── workflow.py    # Factory function
└── README.md          # This file
```

## Step Types

### Sequential Steps

Run one after another:

```yaml
steps:
  - name: "Step 1"
    agent: "agent-1"

  - name: "Step 2"
    agent: "agent-2"

  - name: "Step 3"
    agent: "agent-3"
```

### Parallel Steps

Run simultaneously:

```yaml
steps:
  - name: "Parallel Work"
    type: "parallel"
    steps:
      - name: "Task A"
        agent: "agent-a"

      - name: "Task B"
        agent: "agent-b"

      - name: "Task C"
        agent: "agent-c"
```

**Use when**: Tasks are independent and can run together.

### Conditional Steps

Execute based on conditions:

```yaml
steps:
  - name: "Analyze"
    agent: "analyzer"

  - name: "Conditional Action"
    type: "conditional"
    condition: "analysis.is_complex"
    steps:
      - name: "Expert Review"
        agent: "expert-agent"
```

## Configuration

### Workflow Metadata

```yaml
workflow:
  name: "My Workflow"
  description: "What this workflow does"
  version: "1.0.0"  # Optional
```

### Step Configuration

```yaml
- name: "Step Name"
  agent: "agent-id"              # Run an agent
  description: "What this does"
  timeout: 30                    # Max 30 seconds
  retry: 2                       # Retry 2 times
```

## Testing Your Workflow

### Python

```python
from hive.scaffolder.generator import generate_workflow_from_yaml

# Load workflow
workflow = generate_workflow_from_yaml("ai/workflows/my-workflow/config.yaml")

# Execute workflow
result = workflow.run(message="Start processing")
print(result)
```

### API

```bash
# Start server: hive dev

# Call the workflow
curl -X POST http://localhost:8886/workflows/my-workflow/run \
  -H "Content-Type: application/json" \
  -d '{"message":"Process this request"}'
```

## Real-World Examples

### Customer Support Workflow

```yaml
workflow:
  name: "Support Processing"
  description: "Handle customer support requests"

steps:
  - name: "Classify Issue"
    agent: "classifier-agent"
    description: "Determine issue type"

  - name: "Generate Response"
    agent: "responder-agent"
    description: "Create helpful response"

  - name: "Quality Check"
    agent: "qa-agent"
    description: "Verify response quality"

  - name: "Send Response"
    function: "send_email"
    description: "Email customer"
```

### Content Publishing Workflow

```yaml
workflow:
  name: "Content Publishing"

steps:
  - name: "Write Content"
    agent: "writer-agent"

  - name: "Review Stage"
    type: "parallel"
    steps:
      - name: "Grammar Check"
        agent: "grammar-agent"

      - name: "Fact Check"
        agent: "fact-checker"

      - name: "Tone Analysis"
        agent: "tone-agent"

  - name: "Finalize"
    agent: "editor-agent"

  - name: "Publish"
    function: "publish_to_website"
```

### Data Processing Workflow

```yaml
workflow:
  name: "Data Processing Pipeline"

steps:
  - name: "Extract Data"
    function: "extract_data"

  - name: "Transform Data"
    agent: "transformer-agent"

  - name: "Validate & Load"
    type: "parallel"
    steps:
      - name: "Validation"
        agent: "validator-agent"

      - name: "Load to DB"
        function: "load_database"

  - name: "Report Results"
    function: "send_report"
```

## Advanced Features

### Workflow State

Pass data between steps:

```python
def get_workflow(**kwargs) -> Workflow:
    steps = [
        Step(
            name="Process",
            agent=agent,
            output_key="processing_result"  # Save output
        ),
        Step(
            name="Analyze",
            agent=analyzer,
            input_from="processing_result"  # Use saved output
        )
    ]

    return Workflow(name="Advanced", steps=steps)
```

### Error Handling

```yaml
steps:
  - name: "Process"
    agent: "processor"
    retry: 3           # Retry up to 3 times
    timeout: 60        # Timeout after 60 seconds
    on_error: "continue"  # Skip if fails
```

### Conditional Logic

```python
def get_smart_workflow(**kwargs) -> Workflow:
    from agno.workflow import Condition

    steps = [
        Step(name="Analyze", agent=analyzer),
        Condition(
            name="Route by Complexity",
            evaluator=lambda x: x.get("is_complex", False),
            steps=[
                Step(name="Expert Review", agent=expert)
            ]
        )
    ]

    return Workflow(name="Smart", steps=steps)
```

## Best Practices

### 1. Linear Workflows

Keep workflows simple and linear when possible:

```yaml
# Good: Clear flow
steps:
  - name: "Step 1"
  - name: "Step 2"
  - name: "Step 3"

# Bad: Complex nesting
steps:
  - name: "Complex"
    steps:
      - steps:
          - steps:
              - ...
```

### 2. Meaningful Step Names

```yaml
# Good
- name: "Classify Customer Issue"
- name: "Generate Response"
- name: "Quality Assurance"

# Avoid
- name: "Step 1"
- name: "Do Processing"
```

### 3. Reusable Agents

Use existing agents instead of creating new ones:

```yaml
# Good: Reuse agents from other workflows
steps:
  - name: "Analyze"
    agent: "shared-analyzer"  # Exists elsewhere

# Avoid: Creating agents just for this workflow
steps:
  - name: "Analyze"
    agent: "this-workflow-only-analyzer"
```

### 4. Timeout Management

Set reasonable timeouts for each step:

```yaml
steps:
  - name: "Quick Task"
    timeout: 10      # 10 seconds

  - name: "Long Task"
    timeout: 300     # 5 minutes

  - name: "Analysis"
    timeout: 60      # 1 minute
```

## Troubleshooting

### Workflow Not Executing

```bash
# Check step agent IDs exist
ls -la ai/agents/

# Check workflow syntax
cat ai/workflows/my-workflow/config.yaml

# Enable debug mode
# Add debug_mode: true to workflow config
```

### Steps Executing Out of Order

```yaml
# Make sure you're not using parallel by accident
steps:
  - name: "First"
    agent: "agent-1"

  - name: "Second"
    agent: "agent-2"

  # Not:
  # - name: "Parallel"
  #   type: "parallel"
```

### Timeout Issues

```yaml
# Increase timeout for slow agents
steps:
  - name: "Analysis"
    agent: "slow-analyzer"
    timeout: 120  # 2 minutes instead of default
```

### Data Not Passing Between Steps

```python
# Make sure to use output_key and input_from:
Step(name="First", agent=agent1, output_key="result1"),
Step(name="Second", agent=agent2, input_from="result1")
```

## See Also

- [Agents Guide](../agents/README.md) - Create agents for workflow steps
- [Teams Guide](../teams/README.md) - Use teams in workflows
- [Main README](../../README.md) - Project overview

Happy building! 🚀
