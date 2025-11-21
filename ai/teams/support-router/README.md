# Support Router Team

**Intelligent routing team that automatically directs customer queries to specialist agents.**

## Overview

The Support Router is a routing team that analyzes customer questions and automatically forwards them to the most appropriate specialist. This eliminates manual triage and ensures customers reach the right expert immediately.

## Team Mode

**Mode**: `route`

This team uses Agno's intelligent routing to automatically select the best agent based on query content. No manual orchestration needed - the framework handles everything.

## Team Members

1. **Billing Specialist**
   - Handles: Payments, invoices, charges, refunds, subscriptions
   - Best for: Financial and account-related questions

2. **Technical Specialist**
   - Handles: Bugs, errors, performance, integrations, configurations
   - Best for: Technical troubleshooting and support

3. **Sales Specialist**
   - Handles: Pricing, features, demos, upgrades, comparisons
   - Best for: Pre-sales and product inquiries

## When to Use Routing Teams

✅ **Use routing teams when:**
- You have distinct specialist domains (billing, tech, sales)
- Query intent is clear and distinct
- You want automatic, intelligent routing
- Customer should interact with ONE expert at a time
- Response needs to come from a single source

❌ **Don't use routing teams when:**
- Multiple agents need to work together on the same problem
- You need consensus or collaboration between specialists
- The workflow requires sequential steps
- All agents need to contribute to a single response

## Usage

```python
from my_test_project.ai.teams.examples.support_router.team import get_support_router_team

# Create the routing team
team = get_support_router_team()

# The team automatically routes queries to the right specialist
response = team.run("I need help with a refund")  # → Billing Specialist
response = team.run("The API is returning 500 errors")  # → Technical Specialist
response = team.run("What features are in the Pro plan?")  # → Sales Specialist
```

## How Routing Works

1. **Query Analysis**: Team analyzes the customer's message
2. **Intent Detection**: Determines primary topic (billing, technical, sales)
3. **Automatic Routing**: Forwards to the most appropriate specialist
4. **Specialist Response**: Selected agent processes and responds
5. **Seamless Experience**: Customer gets expert answer immediately

## Routing Logic

The team routes based on primary intent:

- **Billing Keywords**: payment, invoice, charge, refund, subscription, billing
- **Technical Keywords**: bug, error, performance, integration, API, configuration
- **Sales Keywords**: pricing, feature, demo, upgrade, plan, comparison

Default routing: If unclear, routes to Technical Specialist.

## Configuration

See `config.yaml` for:
- Team metadata and mode settings
- Model configuration (default: gpt-4o-mini)
- Routing instructions and guidelines
- Storage configuration for session persistence

## Benefits

- **Instant Expertise**: Customers reach the right specialist immediately
- **No Manual Triage**: Framework handles routing automatically
- **Specialist Focus**: Each agent focuses on their domain
- **Scalable**: Add new specialists without changing routing logic
- **Session Context**: Maintains conversation state across interactions

## Related Patterns

- For collaborative work, see: `dev-team` (collaboration example)
- For sequential workflows, see: Agno Workflows
- For single-agent use cases, see: `agents/examples/support-bot`

## Testing

```python
# Test routing behavior
team = get_support_router_team()

# Billing route
assert "billing" in team.run("I was charged twice").content.lower()

# Technical route
assert "technical" in team.run("Getting 404 errors").content.lower()

# Sales route
assert "sales" in team.run("What's included in Enterprise?").content.lower()
```
