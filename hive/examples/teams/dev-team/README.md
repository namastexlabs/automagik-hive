# Development Team

**Collaborative development team that works together to plan, implement, and review features.**

## Overview

The Development Team is a collaborative team where multiple agents work together on the same problem. Unlike routing teams that send queries to one specialist, collaborative teams have all members contribute their expertise to produce a comprehensive solution.

## Team Mode

**Mode**: `collaborate`

This team uses Agno's collaborative mode where all team members work together on the same task. The framework orchestrates their interactions to produce a unified, high-quality result.

## Team Members

1. **Planner**
   - Analyzes requirements and user stories
   - Breaks down work into actionable tasks
   - Identifies dependencies, risks, and edge cases
   - Suggests architecture and design patterns

2. **Coder**
   - Implements features following the plan
   - Writes clean, maintainable, tested code
   - Follows best practices and coding standards
   - Handles edge cases and error conditions

3. **Reviewer**
   - Reviews code for correctness and quality
   - Validates test coverage
   - Checks security and performance
   - Provides constructive feedback

## When to Use Collaborative Teams

✅ **Use collaborative teams when:**
- Multiple perspectives improve the solution
- You need consensus or validation from multiple experts
- Work benefits from planning, execution, and review phases
- Quality requires multiple checkpoints
- All agents should contribute to a single deliverable

❌ **Don't use collaborative teams when:**
- Only one specialist is needed (use routing instead)
- Tasks are independent and can run in parallel (use workflows)
- Immediate response is needed (collaboration adds latency)
- Query has a single clear answer (use single agent)

## Usage

```python
from my_test_project.ai.teams.examples.dev_team.team import get_dev_team

# Create the collaborative team
team = get_dev_team()

# All team members work together on the feature
response = team.run("""
Build a user authentication system with:
- Email/password login
- JWT token management
- Password reset flow
- Rate limiting
""")

# Response includes:
# - Planner's implementation plan and architecture
# - Coder's implementation with tests
# - Reviewer's quality assessment and suggestions
```

## How Collaboration Works

1. **Shared Context**: All team members see the full conversation
2. **Sequential Contribution**: Members contribute in logical order
3. **Iterative Refinement**: Team iterates based on feedback
4. **Unified Output**: Framework combines contributions into coherent result
5. **Quality Assurance**: Multiple perspectives catch issues early

## Collaboration Workflow

```
User Request
    ↓
Planner → Analyzes requirements, creates implementation plan
    ↓
Coder → Implements feature following the plan
    ↓
Reviewer → Reviews quality, suggests improvements
    ↓
Team → Iterates if needed
    ↓
Final Output → Complete, reviewed, production-ready feature
```

## Configuration

See `config.yaml` for:
- Team metadata and collaboration mode
- Model configuration (default: gpt-4o-mini)
- Team instructions and workflow
- Storage configuration for session persistence

## Benefits

- **Higher Quality**: Multiple checkpoints catch issues early
- **Comprehensive Solutions**: Planning + implementation + review
- **Knowledge Sharing**: Team members learn from each other
- **Reduced Rework**: Catch problems before they reach production
- **Consistent Standards**: Reviewer ensures quality across all work

## Comparison: Routing vs Collaboration

| Aspect | Routing Team | Collaborative Team |
|--------|--------------|-------------------|
| **Members** | One agent responds | All agents contribute |
| **Use Case** | Distinct domains | Shared problem |
| **Speed** | Fast (single agent) | Slower (multiple agents) |
| **Quality** | Specialist expertise | Multi-perspective validation |
| **Output** | Single expert answer | Comprehensive solution |
| **Example** | Support routing | Feature development |

## Real-World Use Cases

**Collaborative Teams** (like this one):
- Feature development with planning and review
- Architecture decisions requiring multiple perspectives
- Complex troubleshooting needing different expertise
- Document creation with technical and editorial review

**Routing Teams** (see `support-router`):
- Customer support with domain specialists
- Question answering with topic experts
- Request triage and forwarding
- Department-specific inquiries

## Testing

```python
# Test collaborative workflow
team = get_dev_team()

response = team.run("Build a REST API endpoint for user registration")

# Validate all team members contributed
assert "plan" in response.content.lower()  # Planner contribution
assert "implement" in response.content.lower()  # Coder contribution
assert "review" in response.content.lower()  # Reviewer contribution
```

## Related Patterns

- For routing to specialists, see: `support-router` (routing example)
- For sequential workflows, see: Agno Workflows
- For single-agent development, see: `agents/examples/support-bot`

## Extension Ideas

Enhance this team by adding:
- **Tester**: Dedicated test engineer for comprehensive QA
- **Security Expert**: Security-focused code review
- **DevOps Engineer**: Deployment and infrastructure considerations
- **Documentation Writer**: User-facing documentation
