# PagBank Multi-Agents Folder Structure

## Current Structure (After Reorganization)

```
pagbank-multiagents/
├── agents/                  # All agent-related code
│   ├── orchestrator/       # Main orchestrator (routing logic)
│   ├── specialists/        # Business unit agents (4 agents)
│   ├── tools/             # Agent tools and utilities
│   └── prompts/           # Agent prompts and personas
│
├── context/                # Context management (data & intelligence)
│   ├── knowledge/         # Knowledge base (CSV + filters)
│   └── memory/            # Memory management & patterns
│
├── api/                    # Entry points
│   └── playground.py      # Web interface (Agno Playground)
│
├── config/                 # Configuration files
│   ├── settings.py        # System settings
│   ├── models.py          # Model configurations
│   └── database.py        # Database setup
│
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance tests
│
├── data/                   # Data storage
│   └── memory/            # SQLite databases
│
├── docs/                   # Documentation
│   └── knowledge_examples/ # Example knowledge documents
│
├── scripts/                # Utility scripts
│   ├── preprocessing/     # Knowledge preprocessing tools
│   └── *.py              # Other utility scripts
│
├── utils/                  # Helper utilities
└── genie/                  # Development workspace
```

## Key Benefits

1. **Clear Hierarchy**: Related components are grouped together
2. **Intuitive Names**: Folder purposes are obvious from their names
3. **Minimal Nesting**: Maximum 2 levels deep for easy navigation
4. **Logical Flow**: 
   - `agents/` contains all agent logic including orchestration
   - `context/` groups knowledge and memory (both handle context)
   - `api/` clearly shows entry points

## Import Examples

```python
# Orchestrator imports
from agents.orchestrator.main_orchestrator import create_main_orchestrator
from agents.orchestrator.routing_logic import BusinessUnit

# Specialist agent imports
from agents.specialists.pagbank_agent import PagBankAgent
from agents.specialists.human_handoff_agent import HumanHandoffAgent

# Context imports
from context.knowledge.csv_knowledge_base import PagBankCSVKnowledgeBase
from context.memory.memory_manager import MemoryManager

# API imports
from api.playground import orchestrator
```

## Running the System

```bash
# Start the playground
uv run python api/playground.py

# Or use the shortcut
uv run python playground.py  # symlink at root
```