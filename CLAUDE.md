# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PagBank Multi-Agent System - A sophisticated Brazilian customer service multi-agent system built with the Agno framework. The system routes customer queries to specialized teams for cartões (cards), conta digital (digital account), investimentos (investments), crédito (credit), and seguros (insurance).

## Development Commands

### Python Operations (Required: Use UV)

**Install dependencies:**
```bash
uv sync
```

**Start backend system:**
```bash
uv run python playground.py
```


## Architecture Overview

### Core Components
- **Main Orchestrator** (`orchestrator/main_orchestrator.py`): Central routing system using Agno Team framework
- **Specialist Teams** (`teams/`): Five specialized agents for different banking domains
- **Memory System** (`memory/`): Persistent context and pattern detection using Agno Memory v2
- **Knowledge Base** (`knowledge/`): CSV-based knowledge with PgVector embeddings
- **Escalation Systems** (`escalation_systems/`): Human and technical escalation handling

### Key Architecture Patterns
- **Team-based Routing**: Main orchestrator routes queries to appropriate specialist teams
- **Shared State Management**: Teams coordinate through state synchronization
- **Memory Integration**: All interactions stored in SQLite with Agno Memory v2
- **Knowledge Filtering**: Team-specific knowledge base filtering
- **Escalation Flow**: Frustration detection triggers human escalation

### Request Flow
1. User message → Main Orchestrator
2. Text normalization and frustration detection
3. Team routing based on query classification
4. Specialist team processing with knowledge lookup
5. Memory update and response generation
6. Escalation handling if needed

## Development Configuration

### Environment Setup
- Python 3.12+ required
- SQLite databases in `data/` directory
- PgVector for embeddings (configurable)
- Agno framework for multi-agent orchestration

### Key Settings (`config/settings.py`)
- Session timeout: 30 minutes
- Max conversation turns: 20
- Team routing timeout: 30 seconds
- Frustration threshold: Level 3

### Database Structure
- `data/memory/pagbank_memory_dev.db`: Agno Memory v2 storage
- `data/memory/pagbank_sessions.db`: Session management
- `data/escalation_patterns.db`: Escalation pattern learning

## Testing Strategy

### Test Structure
- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Cross-team integration tests
- `tests/test_*.py`: Component-specific test files
- `conftest.py`: Shared test fixtures and configuration

### Key Test Areas
- Team routing accuracy
- Memory persistence
- Knowledge base filtering
- Escalation detection
- Cross-team coordination

## Specialist Teams

### Team Implementations
- **Cards Team** (`teams/cards_team.py`): Credit/debit cards, limits, billing
- **Digital Account Team** (`teams/digital_account_team.py`): PIX, transfers, balance
- **Investments Team** (`teams/investments_team.py`): CDB, investment products, compliance
- **Credit Team** (`teams/credit_team.py`): Loans, FGTS, fraud protection
- **Insurance Team** (`teams/insurance_team.py`): Insurance products, claims

### Team Framework
- All teams inherit from `BaseTeam` in `teams/base_team.py`
- Shared tools in `teams/team_tools.py`
- Team-specific prompts in `teams/team_prompts.py`


## Memory System

### Agno Memory v2 Integration
- Persistent user context across sessions
- Pattern detection for recurring issues
- Team coordination through shared memory
- Automatic memory cleanup and retention

### Memory Components
- `memory/memory_manager.py`: Main memory interface
- `memory/pattern_detector.py`: Pattern recognition
- `memory/session_manager.py`: Session lifecycle

## Knowledge Base

### CSV Knowledge Structure
- `knowledge/pagbank_knowledge.csv`: Main knowledge data
- Team-specific filtering through `agentic_filters.py`
- Embedding-based similarity search
- Category-based knowledge organization

## Escalation Systems

### Human Escalation Flow
- Frustration detection triggers escalation
- Ticket system integration
- Feedback collection and analysis
- Mock human agent for testing

### Technical Escalation
- Complex query routing
- Specialist consultation
- Knowledge gap identification

## Deployment

### Demo Setup
1. `uv sync` - Install dependencies
2. `uv run python playground.py` - Start backend (port 7777)
3. Database initialization automatic on startup

### Demo Environment
- Complete demo scripts in `docs/DEMO_SCRIPT.md`
- 6 distinct test scenarios
- Portuguese language support
- Frustration simulation cases

## Project-Specific Guidelines

### Code Style
- Follow Black formatting (88 char line length)
- Use isort for import organization
- Type hints required (mypy strict mode)
- Portuguese comments for domain-specific logic

### Team Development
- Each team is independent but uses shared tools
- Memory coordination through state synchronizer
- Knowledge base filtering by team scope
- Escalation patterns learned automatically

### Genie Framework Integration
- Create .md files ONLY in `genie/` folder
- Use TodoWrite for complex task coordination
- Parallel task execution with multiple Task calls
- Always include co-author: `Co-Authored-By: Automagik Genie <genie@namastex.ai>`

### Critical Requirements
- ALWAYS use UV for Python operations (never pip/python directly)
- All database operations use SQLite with Agno Memory v2
- Portuguese language support throughout
- Fraud detection and compliance warnings required

