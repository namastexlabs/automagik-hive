# Task Card: Advanced Playground Setup

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### Advanced Playground Configuration (from demo-app)

```python
# api/routes/playground.py
from agno.playground import Playground

# Import all components
from agents.registry import AgentRegistry
from teams.registry import TeamRegistry
from workflows.registry import WorkflowRegistry

# Create unified playground
playground = Playground(
    agents=AgentRegistry.list_all(),
    workflows=WorkflowRegistry.list_all(),
    teams=TeamRegistry.list_all(),
)

# Register with Agno platform (production feature)
if settings.runtime_env == "prd":
    playground.register_app_on_platform()

playground_router = playground.get_router()
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
