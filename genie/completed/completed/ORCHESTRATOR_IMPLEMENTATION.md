# PagBank Main Orchestrator Implementation

## Overview
The Main Orchestrator has been successfully implemented as the central routing system for the PagBank Multi-Agent System. It uses Agno's Team routing mode to intelligently direct customer queries to appropriate specialist teams.

## Components Implemented

### 1. Frustration Detection System (`frustration_detector.py`)
- **Portuguese Keywords**: Categorized into high/medium/low severity
- **Explicit Escalation**: Detects phrases like "quero falar com humano"
- **Giving Up Detection**: Identifies when customers are about to leave
- **Emotional Indicators**: CAPS LOCK, repeated punctuation, repeated characters
- **Frustration Scoring**: 0-3 scale with automatic escalation at level 3

### 2. Text Normalization (`text_normalizer.py`)
- **Common Misspellings**: vc→você, nao→não, pra→para, etc.
- **Banking Terms**: cartao→cartão, credito→crédito, etc.
- **Internet Slang**: blz→beleza, vlw→valeu, etc.
- **Punctuation Fixes**: Multiple spaces, repeated punctuation
- **Accent Restoration**: Handles missing accents in Portuguese

### 3. Routing Logic Engine (`routing_logic.py`)
- **7 Specialist Teams**: Cards, Digital Account, Investments, Credit, Insurance, Technical, Feedback
- **Keyword-Based Routing**: Extensive keyword lists for each team
- **Pattern Matching**: Regex patterns for complex queries
- **Confidence Scoring**: Determines routing certainty
- **Ambiguity Detection**: Identifies queries needing clarification

### 4. Clarification Handler (`clarification_handler.py`)
- **Ambiguous Term Detection**: Handles vague terms like "problema", "ajuda"
- **Missing Information**: Identifies incomplete queries
- **Context-Specific Questions**: Generates targeted clarification questions
- **Natural Language Prompts**: Creates conversational clarification requests

### 5. Main Orchestrator (`main_orchestrator.py`)
- **Team Mode="route"**: Uses Agno's routing team functionality
- **Integrated Preprocessing**: Normalizes text and detects frustration before routing
- **Session State Management**: Tracks customer interactions and context
- **Memory Integration**: Uses existing memory system for pattern detection
- **Human Escalation**: Automatic triggers based on frustration or explicit request

## Key Features

### Frustration Management
- Real-time frustration level tracking (0-3 scale)
- Automatic human escalation at level 3
- Empathetic response recommendations
- Portuguese-specific frustration keywords

### Language Processing
- Handles common Portuguese typos and informal language
- Banking-specific term normalization
- Preserves acronyms (CPF, RG, PIX)
- Smart punctuation correction

### Intelligent Routing
- Confidence-based team selection
- Alternative team suggestions
- Ambiguity detection and resolution
- Context-aware routing decisions

### Session Management
- Persistent session state across interactions
- Interaction history tracking
- Failed attempt monitoring
- Quality metrics collection

## Integration Points

### Memory System
- Uses `memory_manager` for pattern detection
- Stores interaction history
- Tracks user preferences and behavior

### Specialist Teams
- Routes to 7 different specialist teams
- Each team has specific expertise areas
- Supports both Team and Agent routing

### Configuration
- Uses `settings.py` for configuration
- Debug mode support
- Customizable thresholds

## Usage Example

```python
from orchestrator import create_main_orchestrator

# Create orchestrator
orchestrator = create_main_orchestrator()

# Process a message
result = orchestrator.process_message(
    message="vc pode me ajudar com o cartao pq nao ta funcionando",
    user_id="customer_123"
)

# Access results
print(f"Frustration Level: {result['team_session_state']['frustration_level']}")
print(f"Normalized Text: {result['preprocessing']['normalized']}")
print(f"Should Escalate: {result['preprocessing']['should_escalate']}")
```

## Testing

A comprehensive test suite has been created in `tests/test_orchestrator.py` covering:
- Frustration detection accuracy
- Text normalization effectiveness
- Routing logic validation
- Clarification generation
- Integration testing

## Performance Metrics

The orchestrator tracks:
- Total interactions
- Frustration incidents
- Clarification requests
- Average frustration levels
- Human escalation rate

## Next Steps

1. **Integration with Specialist Teams**: Connect actual specialist team implementations
2. **Advanced NLU**: Implement more sophisticated intent detection
3. **Learning System**: Add pattern learning from successful resolutions
4. **Performance Optimization**: Optimize for high-volume scenarios
5. **A/B Testing**: Test different routing strategies

## Completion Status

✅ All requested features have been implemented:
- Main routing Team with mode="route"
- Integrated clarification logic (no separate agent)
- Frustration detection with Portuguese keywords
- Message normalization for Portuguese errors
- team_session_state management
- Routing to all specialist teams
- Human escalation triggers (3 interactions or high frustration)

The Main Orchestrator is ready for integration with the specialist teams in Phase 3 of the project.