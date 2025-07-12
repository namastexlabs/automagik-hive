# Task Card: Project Folder Structure

## Overview
This task card is part of the PagBank Multi-Agent Platform V2 implementation.

## Reference
- Main strategy: `/genie/active/pagbank-agents-platform-strategy.md`
- Demo app reference: `/genie/agno-demo-app/`

---

### Folder Structure (UV-based, Scalable)

```
pagbank-multiagents/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app (copy from agent-api)
│   ├── routes/              # Scalable route structure
│   │   ├── __init__.py
│   │   ├── agents.py        # All agent endpoints (won't split)
│   │   ├── teams.py         # All team endpoints (won't split)
│   │   ├── sessions.py      # Session management
│   │   ├── knowledge.py     # Knowledge operations
│   │   └── health.py        # Health & monitoring
│   └── settings.py          # Pydantic settings
│
├── agents/                  # Agent implementations
│   ├── __init__.py
│   ├── registry.py          # Agent registry
│   ├── specialists/         # Specialist agents
│   │   ├── cards/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py     # CardsAgent class
│   │   │   └── config.yaml  # MANDATORY settings
│   │   ├── digital_account/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── config.yaml
│   │   ├── adquirencia/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── config.yaml
│   │   └── human_handoff/
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       └── config.yaml
│   ├── _template/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── config.yaml
│   └── base_agent.py       # Base class
│
├── teams/                   # Team configurations
│   ├── __init__.py
│   ├── registry.py          # Team registry
│   ├── ana/                 # Ana's team (atendimento renamed)
│   │   ├── __init__.py
│   │   ├── team.py          # Ana team logic (simple Team with mode=config["team"]["mode"])
│   │   └── config.yaml      # MANDATORY settings
│   └── _template/
│       ├── __init__.py
│       ├── team.py
│       └── config.yaml
│
# NEW: Workflows (from demo-app) - Currently None in Codebase
├── workflows/               # Multi-agent workflows (to be created)
│   ├── __init__.py
│   ├── registry.py          # Workflow registry
│   ├── settings.py          # Workflow-specific settings
│   ├── conversation_typification/
│   │   ├── __init__.py
│   │   ├── workflow.py      # Smart typification workflow
│   │   └── config.yaml      # Typification configuration
│   └── _template/
│       ├── __init__.py
│       ├── workflow.py
│       └── config.yaml
│
├── shared/                  # Shared components
│   ├── memory/              # Memory system
│   ├── knowledge/           # Knowledge base
│   └── tools/               # Shared tools
│
# NEW: Database Management (from demo-app)
├── db/
│   ├── __init__.py
│   ├── session.py           # SQLAlchemy session management
│   ├── settings.py          # Database settings
│   ├── alembic.ini          # Alembic configuration
│   ├── V2 implementations/          # Database V2 implementations
│   │   ├── README
│   │   ├── env.py           # V2 Implementation environment
│   │   ├── script.py.mako   # V2 Implementation template
│   │   └── versions/        # V2 Implementation versions
│   └── tables/
│       ├── __init__.py
│       ├── base.py          # SQLAlchemy base models
│       ├── agents.py        # Agent configuration tables
│       ├── teams.py         # Team configuration tables
│       ├── workflows.py     # Workflow configuration tables
│       └── config_history.py # Configuration audit trail
│
# NEW: Workspace Management (from demo-app)
├── workspace/
│   ├── __init__.py
│   ├── settings.py          # Workspace configuration
│   ├── dev_resources.py     # Development resources
│   ├── prd_resources.py     # Production resources
│   └── example_secrets/
│       ├── dev_api_secrets.yml
│       ├── prd_api_secrets.yml
│       └── prd_db_secrets.yml
│
# NEW: Utilities (from demo-app)
├── utils/
│   ├── __init__.py
│   ├── log.py               # Enhanced logging with Rich
│   └── dttm.py              # Date/time utilities
│
# NEW: Enhanced Testing (from demo-app)
├── tests/
│   ├── __init__.py
│   ├── evals/               # Evaluation tests
│   │   ├── __init__.py
│   │   ├── test_agent_accuracy.py
│   │   ├── test_workflow_performance.py
│   │   └── test_team_coordination.py
│   ├── unit/                # Unit tests
│   │   ├── test_agents.py
│   │   ├── test_teams.py
│   │   └── test_workflows.py
│   └── integration/         # Integration tests
│       ├── test_api.py
│       └── test_end_to_end.py
│
# NEW: Scripts (from demo-app)
├── scripts/
│   ├── _utils.sh            # Utility functions
│   ├── dev_setup.sh         # Development setup
│   ├── build_dev_image.sh   # Development Docker build
│   ├── build_prd_image.sh   # Production Docker build
│   ├── format.sh            # Code formatting
│   ├── test.sh              # Test runner
│   └── validate.sh          # Code validation
│
├── docker/
│   ├── Dockerfile
│   └── .dockerignore
│
├── docker-compose.yml
├── alembic.ini              # Database V2 implementations
├── example.env              # Environment variables template
└── pyproject.toml           # UV dependencies
```

---

## Validation Steps
TODO: Add specific validation steps for this task

## Dependencies
TODO: List dependencies on other task cards

Co-Authored-By: Automagik Genie <genie@namastex.ai>
