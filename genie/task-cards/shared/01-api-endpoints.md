# Task Card: API Endpoints Reference

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### Complete API Endpoints (from agent-api + demo-app)

```python
# Core Agent API (from agent-api)
GET  /v1/agents                           # List all agents
POST /v1/agents/{agent_id}/runs           # Run specific agent
POST /v1/agents/{agent_id}/knowledge/load # Load agent knowledge

# Team API (enhanced from demo-app)
GET  /v1/teams                            # List all teams  
POST /v1/teams/{team_id}/runs             # Run specific team
GET  /v1/teams/{team_id}/sessions         # Team sessions

# NEW: Workflow API (TO BE CREATED - Not in demo-app)
# Note: These endpoints don't exist in the demo-app, they're proposed
GET  /v1/workflows                        # List all workflows
POST /v1/workflows/{workflow_id}/runs     # Execute workflow

# Future Workflow Management (proposed)
GET  /v1/workflows/{workflow_id}/config   # Get workflow config
PUT  /v1/workflows/{workflow_id}/config   # Update workflow config

# Simple Agent Versioning (PagBank Style)
GET  /v1/agents/{agent_id}/versions       # List all versions (25, 26, 27...)
POST /v1/agents/{agent_id}/versions       # Create new version

# Run Any Version Directly
POST /v1/agents/{agent_id}/v25/runs       # Run version 25 specifically  
POST /v1/agents/{agent_id}/v26/runs       # Run version 26 specifically
POST /v1/agents/{agent_id}/v27/runs       # Run version 27 specifically
POST /v1/agents/{agent_id}/runs           # Run latest version

# Advanced Analytics & Monitoring
GET  /v1/analytics/agents                 # Agent performance metrics
GET  /v1/analytics/teams                  # Team performance metrics  
GET  /v1/analytics/workflows              # Workflow execution stats
GET  /v1/analytics/customers              # Customer satisfaction metrics

# Playground & Testing
GET  /playground                          # Web UI for testing
POST /playground/agents/{agent_id}        # Test agent in playground
POST /playground/teams/{team_id}          # Test team in playground
POST /playground/workflows/{workflow_id}  # Test workflow in playground

# Health & Status
GET  /health                              # System health check
GET  /status                              # Detailed system status
GET  /metrics                             # Prometheus metrics
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
