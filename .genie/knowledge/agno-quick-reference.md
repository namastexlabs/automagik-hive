# Agno Teams & Workflows Quick Reference
**Last Updated:** 2025-10-30

---

## Teams Cheat Sheet

### Basic Team Creation
```python
from agno.team.team import Team
from agno.agent import Agent

team = Team(
    name="My Team",
    members=[agent1, agent2, agent3],
    instructions=["Coordinate tasks", "Share information"],
)
```

### Team Modes Quick Reference

| Mode | Config | When to Use |
|------|--------|-------------|
| **Router** | `respond_directly=True` | Route to specialists |
| **Cooperation** | `delegate_task_to_all_members=True` | Parallel research |
| **Coordinate** | Default | Sequential delegation |

### State Management Patterns

#### Shared Team History
```python
team = Team(
    db=SqliteDb(db_file="tmp/team.db"),
    add_team_history_to_members=True,  # All agents see history
)
```

#### Leader Context Awareness
```python
team = Team(
    add_history_to_context=True,  # Leader knows previous requests
)
```

#### Session State Variables
```python
team = Team(
    add_session_state_to_context=True,  # Inject variables
)

team.run(
    input="Help me",
    session_id="user_123",
    session_state={"user_name": "John", "age": 30}
)
```

#### Nested Shared State
```python
parent_team = Team(
    session_state={"shopping_list": []},  # Single source of truth
    members=[child_team1, child_team2],
)
```

---

## Workflows Cheat Sheet

### Basic Workflow
```python
from agno.workflow import Workflow, Step

workflow = Workflow(
    name="My Workflow",
    steps=[
        Step("Step1", agent=agent1),
        Step("Step2", agent=agent2),
    ],
)
```

### Five Core Patterns

#### 1. Sequential
```python
steps=[
    Step("Research", team=research_team),
    Step("Write", agent=writer),
    Step("Review", agent=reviewer),
]
```

#### 2. Parallel
```python
from agno.workflow import Parallel

steps=[
    Parallel(
        Step("Task A", agent=agent_a),
        Step("Task B", agent=agent_b),
        name="Parallel Phase"
    ),
]
```

#### 3. Conditional
```python
from agno.workflow import Condition

def should_run(step_input) -> bool:
    return "keyword" in step_input.message.lower()

steps=[
    Condition(
        evaluator=should_run,
        steps=[Step("Deep Analysis", agent=analyzer)],
    ),
]
```

#### 4. Loop
```python
from agno.workflow import Loop

def quality_check(step_input) -> bool:
    return len(str(step_input.previous_step_content)) > 500

steps=[
    Loop(
        steps=[Step("Research", agent=researcher)],
        end_condition=quality_check,
        max_iterations=3,
    ),
]
```

#### 5. Router
```python
from agno.workflow import Router

def route_logic(step_input) -> Step:
    if "tech" in step_input.message.lower():
        return Step("Tech Path", agent=tech_agent)
    return Step("General Path", agent=general_agent)

steps=[
    Router(evaluator=route_logic),
]
```

### Custom Function Steps

```python
from agno.workflow import StepInput, StepOutput

def my_function(step_input: StepInput) -> StepOutput:
    # Access previous step
    prev_data = step_input.previous_step_content

    # Access workflow state
    state = step_input.workflow_session_state
    if state is None:
        step_input.workflow_session_state = {}

    # Process and return
    result = process(step_input.message, prev_data)
    step_input.workflow_session_state["result"] = result

    return StepOutput(content=result)

steps=[
    Step("Custom", function=my_function),
]
```

---

## Common Patterns

### Multi-Lingual Router Team
```python
language_team = Team(
    members=[english_agent, spanish_agent, french_agent],
    instructions=["Detect language", "Route to specialist"],
    respond_directly=True,
    show_members_responses=True,
)
```

### Parallel Research Team
```python
research_team = Team(
    members=[reddit_agent, hn_agent, web_agent],
    delegate_task_to_all_members=True,  # All research simultaneously
    show_members_responses=True,
)
```

### Content Creation Workflow
```python
content_workflow = Workflow(
    steps=[
        Loop(
            steps=[
                Parallel(
                    Step("HN", agent=hn_agent),
                    Step("Web", agent=web_agent),
                ),
            ],
            end_condition=has_enough_data,
            max_iterations=3,
        ),
        Step("Write", agent=writer),
        Step("Review", agent=reviewer),
    ],
)
```

### Adaptive Research Workflow
```python
research_workflow = Workflow(
    steps=[
        Step("Quick Research", agent=quick_agent),
        Condition(
            evaluator=needs_deep_dive,
            steps=[
                Parallel(
                    Step("Deep", agent=deep_agent),
                    Step("Academic", agent=academic_agent),
                ),
            ],
        ),
    ],
)
```

---

## Database Configuration

### Development (SQLite)
```python
from agno.storage.db.sqlite import SqliteDb

db=SqliteDb(
    db_file="tmp/workflow.db",
    auto_upgrade_schema=True,
)
```

### Production (PostgreSQL)
```python
from agno.storage.db.postgres import PgDb

db=PgDb(
    db_url=os.getenv("DATABASE_URL"),
    schema="agno",
    pool_size=20,
    max_overflow=30,
    auto_upgrade_schema=True,
)
```

---

## Execution Modes

### Synchronous
```python
response = workflow.run(message="Process this")
print(response.content)
```

### Async
```python
response = await workflow.arun(message="Async process")
```

### Streaming
```python
for response in workflow.run(message="Stream", stream=True):
    print(f"Step: {response.step_name}")
    print(f"Content: {response.content}")
```

---

## StepInput Reference

```python
def custom_step(step_input: StepInput):
    # Current message
    message = step_input.message

    # Previous step outputs
    prev_content = step_input.previous_step_content

    # Workflow shared state
    state = step_input.workflow_session_state

    # Access specific step
    research = step_input.get_step_content("Research Step")

    # Additional metadata
    extra = step_input.additional_data
```

---

## StepOutput Reference

```python
# Return content
return StepOutput(content="Result")

# Stop workflow early
return StepOutput(content="Done", stop=True)

# With metadata
return StepOutput(
    content="Result",
    metadata={"processed": True}
)
```

---

## Common Evaluator Functions

### Keyword Detection
```python
def check_keywords(step_input) -> bool:
    keywords = ["tech", "startup", "AI"]
    return any(k in step_input.message.lower() for k in keywords)
```

### Content Length Check
```python
def has_enough_content(step_input) -> bool:
    if step_input.previous_step_content:
        total = sum(len(str(c)) for c in step_input.previous_step_content)
        return total > 500
    return False
```

### Topic Router
```python
def route_by_topic(step_input) -> Step:
    msg = step_input.message.lower()

    if "billing" in msg:
        return Step("Billing", agent=billing_agent)
    elif "technical" in msg:
        return Step("Tech", agent=tech_agent)
    else:
        return Step("General", agent=general_agent)
```

---

## Best Practices

### Teams
✅ **DO:**
- Keep teams focused (3-5 members)
- Use `show_members_responses=True` for transparency
- Enable history for multi-turn conversations
- Choose right mode for use case

❌ **DON'T:**
- Create teams with >7 members without nesting
- Mix incompatible tools across members
- Skip database configuration for production
- Ignore session management

### Workflows
✅ **DO:**
- Always set `max_iterations` on loops
- Implement clear exit conditions
- Use streaming for long workflows
- Combine patterns for complex needs

❌ **DON'T:**
- Create nested loops without limits
- Skip error handling in evaluators
- Use parallel for dependent tasks
- Forget session state initialization

### State Management
✅ **DO:**
- Use same `session_id` for related calls
- Initialize `workflow_session_state` properly
- Clean up old sessions periodically
- Document state structure

❌ **DON'T:**
- Mutate state without checking existence
- Store sensitive data in session state
- Forget to pass `session_id`
- Mix session contexts

---

## Performance Tips

### Team Optimization
- Use `add_member_tools_to_context=False` when not needed
- Implement tool caching
- Monitor database query patterns
- Use connection pooling for PostgreSQL

### Workflow Optimization
- Minimize sequential steps
- Use parallel for independent tasks
- Cache evaluation results
- Optimize custom functions

### Database Optimization
- SQLite: Development only
- PostgreSQL: Production with pooling
- Auto-upgrade schema in dev only
- Monitor connection counts

---

## Troubleshooting

### Teams Not Routing Correctly
- Check `respond_directly` setting
- Verify member instructions
- Test with `show_members_responses=True`
- Review routing logic

### Workflows Hanging
- Check loop `max_iterations`
- Verify exit conditions
- Review evaluator functions
- Enable streaming for visibility

### State Not Persisting
- Verify `session_id` consistency
- Check database configuration
- Confirm `add_history_to_context` setting
- Review state initialization

### Parallel Steps Not Working
- Verify tasks are truly independent
- Check resource availability
- Review agent tool configurations
- Monitor execution logs

---

## Quick Decision Matrix

### When to Use What?

| Requirement | Solution |
|-------------|----------|
| Route to specialists | Router team (`respond_directly=True`) |
| Parallel research | Cooperation team (`delegate_task_to_all_members=True`) |
| Sequential steps | Sequential workflow |
| Independent tasks | Parallel workflow |
| Topic-based routing | Conditional or Router workflow |
| Quality refinement | Loop workflow |
| Complex decisions | Router workflow |
| Mix patterns | Nested workflow steps |
| Multi-turn context | Team with history management |
| Custom logic + AI | Custom function steps |

---

## Example Recipes

### 1. Multi-Source Research
```python
workflow = Workflow(steps=[
    Loop(
        steps=[
            Parallel(
                Step("HN", agent=hn_agent),
                Step("Web", agent=web_agent),
            ),
        ],
        end_condition=lambda si: len(str(si.previous_step_content)) > 1000,
        max_iterations=3,
    ),
    Step("Summarize", agent=summarizer),
])
```

### 2. Adaptive Support System
```python
team = Team(
    members=[billing_agent, tech_agent, sales_agent],
    respond_directly=True,
    add_history_to_context=True,
    db=PgDb(db_url=os.getenv("DB_URL")),
)
```

### 3. Quality-Driven Content
```python
workflow = Workflow(steps=[
    Step("Research", team=research_team),
    Loop(
        steps=[Step("Write", agent=writer)],
        end_condition=lambda si: "quality" in str(si.previous_step_content).lower(),
        max_iterations=2,
    ),
    Step("Review", agent=reviewer),
])
```

### 4. Hierarchical Teams
```python
specialist_team = Team(members=[agent1, agent2])
generalist_team = Team(members=[agent3, agent4])

parent_team = Team(
    session_state={"context": {}},
    members=[specialist_team, generalist_team],
)
```

---

## Resources

- **Cookbook**: https://github.com/agno-agi/agno/tree/main/cookbook
- **Documentation**: https://docs.agno.com
- **Teams Examples**: cookbook/teams/
- **Workflows Examples**: cookbook/workflows/

---

**Quick Tips:**
- Start simple, add complexity as needed
- Use streaming for visibility
- Always set loop limits
- Test evaluators thoroughly
- Document state structure
- Monitor database growth
- Plan for scaling early
