# Ana Team - Clean Agno Implementation

This directory contains the refactored Ana team implementation following Agno framework best practices.

## Files Overview

### Core Implementation
- **`team.py`** - Main team factory function (123 lines)
- **`models.py`** - Clean Pydantic models for structured input (76 lines)
- **`config.yaml`** - Comprehensive Agno configuration (105 lines)
- **`__init__.py`** - Clean module exports (14 lines)

### Testing
- **`test_ana_refactor.py`** - Integration test suite

## Key Features

### ✅ All Agno Features Preserved
- Route mode for intelligent agent routing
- Memory with 10 conversation history
- Session summaries enabled
- Real-time streaming with intermediate steps
- Complete event storage for metrics
- Agentic context sharing
- Member interaction sharing
- PostgreSQL storage with auto-migrations
- Reasoning capabilities

### ✅ Clean Architecture
- Minimal implementation (62% reduction in team.py)
- Structured input via UserContext model
- No execution tracing or complex abstractions
- All configuration in YAML
- Frozen Pydantic models with validation

## Usage

```python
from ai.teams.ana import get_ana_team, UserContext

# Basic usage
team = get_ana_team()

# With user context
user_context = UserContext(
    pb_user_name="João Silva",
    pb_user_cpf="123.456.789-00",
    pb_phone_number="+5511999887766"
)
team = get_ana_team(user_context=user_context)

# With session management
team = get_ana_team(
    user_context=user_context,
    session_id="abc-123",
    user_id="user-456"
)
```

## Routing Logic

Ana routes users to appropriate specialists:
1. **PIX/conta/saldo** → pagbank
2. **Cartão/limite/fatura** → emissao  
3. **Máquina/antecipação** → adquirencia
4. **Humano/frustração** → human-escalation-agent
5. **Finalização** → finalizacao

## Testing

Run the test suite:
```bash
uv run python -m ai.teams.ana.test_ana_refactor
```

## Configuration

All configuration is in `config.yaml`:
- Team settings (name, mode, description)
- Model configuration with reasoning
- Memory and session settings
- Streaming and event configuration
- Storage and member definitions
- Routing instructions in Portuguese

## Benefits

- **Maintainability**: 62% code reduction, clear separation of concerns
- **Performance**: Minimal abstractions, efficient configuration loading
- **Reliability**: Strong typing, validation, comprehensive testing
- **Scalability**: Clean architecture supports easy extensions