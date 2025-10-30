# Team Examples Index

Two production-ready team examples demonstrating different coordination patterns.

## Available Examples

### 1. Support Router Team (`support-router/`)

**Pattern**: Routing Team
**Mode**: `route`
**Purpose**: Automatically routes customer queries to specialist agents

**Team Members**:
- Billing Specialist - Payment and account inquiries
- Technical Specialist - Bug reports and technical issues
- Sales Specialist - Product features and pricing questions

**When to Use**:
- Customer support and help desk systems
- Query triage and specialist routing
- Domain-specific expert systems
- Fast single-expert responses needed

**Key Files**:
- `team.py` - Factory function with inline specialist agents
- `config.yaml` - Team configuration and routing logic
- `README.md` - Complete documentation and usage guide

---

### 2. Development Team (`dev-team/`)

**Pattern**: Collaborative Team
**Mode**: `collaborate`
**Purpose**: Multiple agents work together on complex development tasks

**Team Members**:
- Planner - Requirements analysis and implementation planning
- Coder - Feature implementation with tests
- Reviewer - Quality assurance and feedback

**When to Use**:
- Feature development requiring multiple phases
- Complex problem solving with multiple perspectives
- Quality assurance through multiple checkpoints
- Iterative refinement workflows

**Key Files**:
- `team.py` - Factory function with collaborative agents
- `config.yaml` - Team configuration and workflow
- `README.md` - Complete documentation and usage guide

---

## Quick Start

### Import and Use

```python
# Support Router Team
from my_test_project.ai.teams.examples.support_router.team import get_support_router_team
router = get_support_router_team()
response = router.run("I need help with a refund")

# Development Team
from my_test_project.ai.teams.examples.dev_team.team import get_dev_team
dev = get_dev_team()
response = dev.run("Build a user authentication system")
```

### Copy and Customize

```bash
# Copy routing team pattern
cp -r support-router/ ../my-routing-team/

# Copy collaborative team pattern
cp -r dev-team/ ../my-collaborative-team/

# Edit config.yaml and team.py to customize
```

---

## Pattern Comparison

| Aspect | Routing Team | Collaborative Team |
|--------|--------------|-------------------|
| **Members** | One agent responds | All agents contribute |
| **Use Case** | Distinct domains | Shared problem |
| **Speed** | Fast (single agent) | Slower (multiple agents) |
| **Quality** | Specialist expertise | Multi-perspective validation |
| **Output** | Single expert answer | Comprehensive solution |
| **Example** | `support-router` | `dev-team` |

---

## Decision Guide

### Choose Routing Team When:
- ✓ Query needs ONE specialist
- ✓ Domain boundaries are clear
- ✓ Fast response is critical
- ✓ Single expert answer is sufficient

### Choose Collaborative Team When:
- ✓ Multiple perspectives improve solution
- ✓ Work needs planning + execution + review
- ✓ Quality requires multiple checkpoints
- ✓ Consensus or validation needed

---

## Extending Examples

### Add Members to Routing Team

```python
# In support-router/team.py, add new specialist
hr_specialist = Agent(
    name="HR Specialist",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="Handle employee and HR inquiries...",
    description="Handles HR and employee questions"
)

# Add to members list
members=[billing_specialist, technical_specialist, sales_specialist, hr_specialist]
```

### Add Members to Collaborative Team

```python
# In dev-team/team.py, add new role
tester = Agent(
    name="Tester",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="Create comprehensive test strategies...",
    description="Develops test plans and QA strategies"
)

# Add to members list
members=[planner, coder, reviewer, tester]
```

---

## Technical Notes

### Agno Team API

These examples use Agno's Team class with:
- `role` parameter for coordination behavior (not `mode`)
- `mode` stored as instance attribute for metadata
- `members` list with Agent instances
- `instructions` for team-level coordination logic

### Factory Pattern

Both examples follow the factory pattern:
1. Load configuration from `config.yaml`
2. Create Model instance for the team
3. Create member Agent instances inline
4. Instantiate Team with all components
5. Set team_id and mode as attributes
6. Return configured team instance

### Configuration-Driven

All team behavior configured via YAML:
- Team metadata (name, id, version)
- Model selection and parameters
- Instructions for coordination
- Storage configuration

---

## Related Resources

- **Agent Examples**: See `../agents/examples/` for single-agent patterns
- **Workflows**: See `../workflows/` for step-based orchestration
- **Documentation**: Each example has detailed README.md

---

## Support

For questions or issues:
1. Read the example README.md files
2. Check configuration in config.yaml
3. Review factory function in team.py
4. Refer to Agno documentation for Team API

Both examples are production-ready and can be used as-is or customized for your specific needs.
