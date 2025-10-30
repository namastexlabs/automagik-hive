# Teams Guide

Build intelligent multi-agent teams with automatic routing.

## What is a Team?

A team is a group of specialized agents that work together. The team automatically routes queries to the best agent based on the question.

**Example**: A support team routes billing questions to a billing agent, technical issues to a technical agent, and sales inquiries to a sales agent.

## Quick Start

### 1. Create Team Directory

```bash
mkdir -p ai/teams/my-team
cd ai/teams/my-team
```

### 2. Create config.yaml

```yaml
team:
  name: "My Support Team"
  team_id: "my-support-team"
  mode: "route"  # Auto-routes to best member

members:
  - "billing-agent"
  - "technical-agent"
  - "sales-agent"

instructions: |
  You are the support team router.

  Route questions:
  - Billing issues → billing-agent
  - Technical problems → technical-agent
  - Sales inquiries → sales-agent
```

### 3. Create team.py

```python
"""My team factory."""
import yaml
from pathlib import Path
from agno.team import Team
from hive.scaffolder.generator import generate_agent_from_yaml

def get_my_team(**kwargs) -> Team:
    """Create team with agent members."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Load member agents
    members = []
    for member_id in config.get("members", []):
        # Assuming agents are in ../agents/
        agent_path = f"ai/agents/{member_id}/config.yaml"
        try:
            agent = generate_agent_from_yaml(agent_path)
            members.append(agent)
        except:
            print(f"Warning: Could not load agent {member_id}")

    team = Team(
        name=config["team"]["name"],
        members=members,
        instructions=config.get("instructions"),
        mode=config["team"].get("mode", "route"),
        **kwargs
    )

    return team
```

## Directory Structure

```
ai/teams/
├── my-team/
│   ├── config.yaml    # Team configuration
│   └── team.py        # Factory function
└── README.md          # This file
```

## Team Modes

### "route" - Intelligent Routing

Automatically sends queries to the most appropriate team member.

```yaml
team:
  mode: "route"

instructions: |
  Route billing questions to billing-agent.
  Route technical issues to technical-agent.
```

**Use when**: You have specialized agents and want automatic routing.

### "coordinate" - Collaborative Solving

All agents collaborate to solve the problem together.

```yaml
team:
  mode: "coordinate"

instructions: |
  Work together to solve this problem.
  Each agent should share their perspective.
```

**Use when**: You need multiple viewpoints or complex multi-step solutions.

## Configuration

### Team Metadata

```yaml
team:
  name: "Support Team"
  team_id: "support-team"  # Used in API calls
  description: "Handles customer support"
  mode: "route"             # "route" or "coordinate"
```

### Team Instructions

```yaml
instructions: |
  You are the support team router.

  Team members:
  1. billing-agent: Handles billing and payment issues
  2. technical-agent: Solves technical problems
  3. sales-agent: Answers sales questions

  Route based on the customer's issue type.
```

## Adding Team Members

### Simple Registration

```yaml
members:
  - "billing-agent"
  - "technical-agent"
  - "sales-agent"
```

Each member must be an agent with the corresponding `agent_id`.

### With Descriptions

```yaml
members:
  - agent_id: "billing-agent"
    description: "Billing and payment support"

  - agent_id: "technical-agent"
    description: "Technical troubleshooting"

  - agent_id: "sales-agent"
    description: "Sales and product questions"
```

## Testing Your Team

### Python

```python
from hive.scaffolder.generator import generate_team_from_yaml

# Load team
team = generate_team_from_yaml("ai/teams/my-team/config.yaml")

# Test it
response = team.run("I can't pay my invoice")
print(response)
```

### API

```bash
# Start server: hive dev

# Call the team
curl -X POST http://localhost:8886/teams/my-support-team/run \
  -H "Content-Type: application/json" \
  -d '{"message":"I have a billing question"}'
```

## Real-World Examples

### E-Commerce Support Team

```yaml
team:
  name: "E-Commerce Support"
  team_id: "ecommerce-support"
  mode: "route"

members:
  - "orders-agent"
  - "shipping-agent"
  - "returns-agent"
  - "accounts-agent"

instructions: |
  Route customer inquiries:
  - "Where's my order?" → orders-agent
  - "Shipping question" → shipping-agent
  - "Want to return?" → returns-agent
  - "Account issues" → accounts-agent
```

### Technical Support Team

```yaml
team:
  name: "Technical Support"
  team_id: "tech-support"
  mode: "route"

members:
  - "frontend-expert"
  - "backend-expert"
  - "devops-expert"
  - "database-expert"

instructions: |
  Route technical issues:
  - UI/UX problems → frontend-expert
  - API/Server issues → backend-expert
  - Deployment problems → devops-expert
  - Database problems → database-expert
```

### Content Review Team

```yaml
team:
  name: "Content Review"
  team_id: "content-review"
  mode: "coordinate"  # Collaborative

members:
  - "grammar-checker"
  - "tone-analyzer"
  - "plagiarism-detector"
  - "quality-reviewer"

instructions: |
  Review content collaboratively:
  1. Check grammar and spelling
  2. Analyze tone and clarity
  3. Verify originality
  4. Provide overall quality assessment

  Each expert should contribute their findings.
```

## Advanced Features

### Weighted Routing

You can add metadata to influence routing decisions:

```yaml
members:
  - agent_id: "expert-agent"
    weight: 2  # Higher priority
    description: "Expert-level support"

  - agent_id: "general-agent"
    weight: 1
    description: "General support"
```

### Conditional Routing

Add business logic for complex routing:

```python
def get_smart_team(**kwargs) -> Team:
    config = yaml.safe_load(open("config.yaml"))

    # Load agents based on time of day
    members = []
    hour = datetime.now().hour

    if 9 <= hour <= 17:  # Business hours
        members.append(generate_agent_from_yaml("ai/agents/expert-agent/config.yaml"))
    else:  # Off-hours
        members.append(generate_agent_from_yaml("ai/agents/basic-agent/config.yaml"))

    return Team(
        name=config["team"]["name"],
        members=members,
        **kwargs
    )
```

## Best Practices

### 1. Clear Routing Instructions

**Bad:**
```yaml
instructions: |
  Route appropriately
```

**Good:**
```yaml
instructions: |
  Route based on:
  - "billing" or "payment" → billing-agent
  - "bug" or "error" → technical-agent
  - "buy" or "pricing" → sales-agent
  - Unknown → general-agent
```

### 2. Meaningful Team IDs

```yaml
# Good
team_id: "customer-support"
team_id: "technical-issue-resolver"
team_id: "content-review-board"

# Avoid
team_id: "team1"
team_id: "my-team"
```

### 3. Comprehensive Agent Coverage

Ensure team members cover all common query types:

```yaml
members:
  - "billing-agent"
  - "technical-agent"
  - "sales-agent"
  - "general-agent"  # Catch-all for unknown queries
```

### 4. Agent Dependencies

Verify all referenced agents exist and are loaded:

```bash
# Check agents directory
ls -la ai/agents/

# Verify agent_id in each config.yaml
grep "agent_id:" ai/agents/*/config.yaml
```

## Troubleshooting

### Team Not Routing Correctly

```yaml
# Check instructions are explicit
instructions: |
  Route "refund" to billing-agent
  Route "crash" to technical-agent

# Add more specific keywords
mode: "route"  # Make sure mode is set
```

### Member Agent Not Found

```bash
# Verify agent exists
ls ai/agents/billing-agent/

# Check agent_id matches exactly
cat ai/agents/billing-agent/config.yaml | grep agent_id

# Update team.py to load correctly
```

### Performance Issues

```yaml
# Limit team members (5-7 is ideal)
members:
  - "billing-agent"
  - "technical-agent"
  - "sales-agent"
  # Don't add too many

# Use simpler instructions for faster routing
instructions: |
  Short, direct routing logic
```

## See Also

- [Agents Guide](../agents/README.md) - Create individual agents
- [Workflows Guide](../workflows/README.md) - Sequential multi-agent processes
- [Main README](../../README.md) - Project overview

Happy building! 🚀
