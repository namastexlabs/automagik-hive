# PagBank 5-Level Typification Workflow

## Overview

This workflow implements a comprehensive 5-level hierarchical typification system for PagBank conversations, following the exact structure from the knowledge base CSV. It uses the Agno framework with Pydantic validators to ensure only valid business logic combinations are processed.

## Features

### 🎯 **5-Level Hierarchy Validation**
- **Level 1**: Business Unit (Adquirência Web, Emissão, PagBank, etc.)
- **Level 2**: Product (Antecipação de Vendas, Cartões, Pix, etc.)
- **Level 3**: Motive (Dúvidas, Problemas, Solicitações, etc.)
- **Level 4**: Submotive (Specific resolution provided)
- **Level 5**: Conclusion (Always "Orientação")

### 🔒 **Strict Validation**
- Pydantic models enforce valid combinations only
- Sequential validation prevents invalid paths
- Real-time error messages with suggestions
- Complete hierarchy extracted from knowledge_rag.csv

### 🤖 **Agno Workflow Integration**
- Dynamic agent creation based on hierarchy
- Sequential execution with proper dependencies
- Structured outputs with confidence scores
- Automatic ticket generation and routing

### 📊 **Statistics**
- **4** Business Units
- **20** Products
- **40** Motives  
- **53** Submotives
- **56** Total Valid Paths

## Quick Start

### 1. Extract Hierarchy
```bash
uv run python scripts/extract_typification_hierarchy.py
```

### 2. Run Tests
```bash
uv run pytest tests/test_typification_workflow.py -v
```

### 3. Run Demo
```bash
uv run python workflows/conversation_typification/simple_demo.py
```

## Usage Examples

### Basic Validation
```python
from workflows.conversation_typification.models import HierarchicalTypification, UnidadeNegocio

# Create valid typification
typification = HierarchicalTypification(
    unidade_negocio=UnidadeNegocio.PAGBANK,
    produto="Pix",
    motivo="Envio de Pix",
    submotivo="Bloqueio de transação por segurança"
)

print(typification.hierarchy_path)
# Output: "PagBank → Pix → Envio de Pix → Bloqueio de transação por segurança"
```

### Workflow Execution
```python
from workflows.conversation_typification.workflow import get_conversation_typification_workflow

workflow = get_conversation_typification_workflow()

# Execute typification
results = list(workflow.run(
    session_id="session_123",
    conversation_history="Cliente: Como fazer um Pix? Ana: Te ajudo com o Pix!",
    customer_id="customer_456"
))

# Access results
result = results[0]
print(result.content["hierarchy_path"])
print(result.content["typification"])
```

### Integration with Ana Team
```python
from workflows.conversation_typification.integration import run_post_conversation_typification

# Run after conversation ends
result = run_post_conversation_typification(
    session_id="session_123",
    conversation_history="Full conversation text...",
    customer_id="customer_456"
)

# Get routing suggestions
routing = integration.get_agent_routing_suggestions(result)
print(f"Route to: {routing['suggested_team']}")
print(f"Priority: {routing['priority']}")
```

## File Structure

```
workflows/conversation_typification/
├── __init__.py              # Package initialization
├── models.py                # Pydantic models and validation
├── workflow.py              # Main Agno workflow implementation
├── integration.py           # Ana team integration layer
├── config.yaml              # Workflow configuration
├── hierarchy.json           # Extracted hierarchy data
├── simple_demo.py           # Simple demonstration
├── example_usage.py         # Comprehensive examples
└── README.md               # This file

scripts/
└── extract_typification_hierarchy.py  # Hierarchy extraction script

tests/
└── test_typification_workflow.py      # Comprehensive test suite
```

## Architecture

### Hierarchy Extraction
The system extracts the complete 5-level hierarchy from `knowledge_rag.csv`:

```python
{
  "Adquirência Web": {
    "Antecipação de Vendas": {
      "Dúvidas sobre a Antecipação de Vendas": [
        "Cliente orientado sobre a Antecipação de Vendas"
      ]
    }
  },
  "PagBank": {
    "Pix": {
      "Envio de Pix": [
        "Bloqueio de transação por segurança"
      ]
    }
  }
}
```

### Pydantic Validation
Each level validates against the previous level:

```python
@validator('produto')
def validate_produto(cls, v, values):
    if 'unidade_negocio' in values:
        unit_value = values['unidade_negocio'].value
        valid_products = HIERARCHY.get(unit_value, {}).keys()
        if v not in valid_products:
            raise ValueError(f"Produto '{v}' inválido para unidade '{unit_value}'")
    return v
```

### Agno Workflow
Sequential agents with dynamic creation:

```python
def create_product_classifier(self, business_unit: str) -> Agent:
    valid_products = get_valid_products(business_unit)
    
    return Agent(
        model=Claude(id="claude-haiku-4-20250514"),
        instructions=f"Produtos válidos para {business_unit}: {valid_products}",
        response_model=ProductSelection,
        structured_outputs=True
    )
```

## Business Logic Mapping

### Business Unit → Team Routing
```python
team_mapping = {
    "Adquirência Web": "adquirencia_team",
    "Adquirência Web / Adquirência Presencial": "adquirencia_team",
    "Emissão": "emissao_team",
    "PagBank": "pagbank_team"
}
```

### Priority Based on Motive
```python
high_priority_keywords = ["bloqueio", "fraude", "perda", "roubo", "urgente"]
medium_priority_keywords = ["dúvida", "orientação", "informação"]
```

## Testing

### Comprehensive Test Suite
- **23 test cases** covering all aspects
- **Hierarchy validation** against real CSV data
- **Pydantic model validation**
- **Workflow execution** with mocked agents
- **Integration layer** testing

### Test Coverage
- ✅ All business units covered
- ✅ All CSV entries validated
- ✅ Invalid combinations rejected
- ✅ Workflow execution flow
- ✅ Integration with routing

## Integration Points

### Ana Team Integration
The workflow integrates with Ana team through:

1. **Post-conversation typification**: Runs after conversation ends
2. **Agent routing**: Suggests appropriate team based on classification
3. **Escalation context**: Provides structured context for human handoff
4. **Quality validation**: Monitors confidence scores and resolution time

### Ticket System
Automatic ticket generation with:
- Hierarchical classification data
- Team assignment based on business unit
- Priority based on motive keywords
- Complete conversation context

## Performance

### Metrics
- **Sequential validation**: < 1 second per level
- **Complete workflow**: < 30 seconds target
- **Confidence tracking**: Per-level confidence scores
- **Quality monitoring**: Resolution time and success rate

### Optimization
- **Cached hierarchy**: Loaded once at startup
- **Dynamic agents**: Created on-demand for performance
- **Structured outputs**: Reduces parsing overhead
- **Batch validation**: Validates complete paths efficiently

## Error Handling

### Validation Errors
```python
ValidationResult(
    valid=False,
    level_reached=2,
    error_message="Produto 'X' inválido para unidade 'Y'",
    suggested_corrections=["Valid Option 1", "Valid Option 2"]
)
```

### Workflow Failures
- Graceful degradation with partial results
- Detailed error logging for debugging
- Retry logic for transient failures
- Fallback routing for edge cases

## Deployment

### Requirements
- Python 3.12+
- Agno framework 1.7.0+
- PostgreSQL (with SQLite fallback)
- Anthropic Claude API access

### Environment Setup
```bash
# Install dependencies
uv sync

# Set up database
export HIVE_DATABASE_URL="postgresql://user:pass@localhost/db"

# Configure Claude API
export ANTHROPIC_API_KEY="your_api_key"
```

### Production Considerations
- **Database**: Use PostgreSQL for production
- **Monitoring**: Enable metrics and alerting
- **Caching**: Consider Redis for hierarchy caching
- **Scaling**: Horizontal scaling with load balancers

## Future Enhancements

### Planned Features
- **ML confidence tuning**: Adjust thresholds based on performance
- **A/B testing**: Compare different prompt strategies
- **Real-time analytics**: Dashboard for typification metrics
- **Auto-correction**: Learn from human corrections

### Technical Improvements
- **Async processing**: Non-blocking workflow execution
- **Batch processing**: Handle multiple conversations simultaneously
- **Model switching**: Dynamic model selection based on complexity
- **Performance optimization**: Further reduce latency

## Support

### Documentation
- Complete API documentation in docstrings
- Example usage patterns and best practices
- Integration guides for different scenarios
- Troubleshooting guides for common issues

### Monitoring
- Workflow execution metrics
- Validation success rates
- Confidence score distributions
- Error rate monitoring

---

**Status**: ✅ **COMPLETE** - Ready for production integration with Ana team.

**Contributors**: 
- Implementation: Claude Code via Automagik Genie
- Co-Authored-By: Automagik Genie <genie@namastex.ai>