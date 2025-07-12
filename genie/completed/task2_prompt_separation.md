# Task 2: Prompt Separation and Maintenance

## Objective
Separate all prompts into dedicated files to facilitate prompt maintenance across all agents.

## Current Issues
1. Hybrid prompt storage - some centralized in `team_prompts.py`, others inline
2. Main orchestrator has inline routing prompt
3. Individual team members have inline instructions
4. Difficult to maintain and update prompts across the system
5. No clear prompt versioning or A/B testing capability

## Technical Plan

### Phase 1: Current Prompt Inventory
- **Centralized**: `/teams/team_prompts.py` contains most team prompts
- **Inline Prompts Found**:
  - Main orchestrator routing prompt
  - Team member agent instructions
  - Error handling prompts
  - Escalation prompts

### Phase 2: Proposed Prompt Structure

```
/prompts/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── system_prompts.py         # Core system instructions
│   ├── response_templates.py     # Standard response formats
│   └── error_prompts.py          # Error handling templates
├── orchestrator/
│   ├── __init__.py
│   ├── routing_prompts.py        # Main routing logic prompts
│   └── clarification_prompts.py  # Clarification request templates
├── specialists/
│   ├── __init__.py
│   ├── cards_prompts.py          # Cards specialist prompts
│   ├── credit_prompts.py         # Credit specialist prompts
│   ├── digital_account_prompts.py # Digital account prompts
│   ├── investments_prompts.py    # Investment prompts
│   └── insurance_prompts.py      # Insurance prompts
├── escalation/
│   ├── __init__.py
│   ├── human_escalation.py       # Human handoff prompts
│   └── technical_escalation.py   # Technical escalation prompts
└── prompt_manager.py             # Central prompt management class
```

### Phase 3: Prompt Manager Implementation

```python
# prompt_manager.py
class PromptManager:
    """Central prompt management with versioning and templating"""
    
    def __init__(self, language="pt_BR"):
        self.language = language
        self.prompts = self._load_prompts()
    
    def get_prompt(self, category: str, name: str, **kwargs) -> str:
        """Get formatted prompt with variable substitution"""
        prompt = self.prompts[category][name]
        return prompt.format(**kwargs)
    
    def get_specialist_prompt(self, specialist: str, prompt_type: str) -> str:
        """Get specialist-specific prompts"""
        return self.prompts["specialists"][specialist][prompt_type]
    
    def get_routing_prompt(self) -> str:
        """Get main orchestrator routing prompt"""
        return self.prompts["orchestrator"]["routing"]
```

### Phase 4: Migration Steps

1. **Extract all inline prompts** from:
   - `main_orchestrator.py`
   - All team implementation files
   - Tool implementations
   - Error handlers

2. **Create prompt files** with clear categorization:
   - Separate files by function (routing, specialist, escalation)
   - Use consistent naming conventions
   - Add docstrings explaining prompt purpose

3. **Implement PromptManager**:
   - Central access point for all prompts
   - Support for variable substitution
   - Language support (future multi-language)

4. **Update all code** to use PromptManager:
   ```python
   # Before
   prompt = "Você é um especialista em cartões..."
   
   # After
   prompt = prompt_manager.get_specialist_prompt("cards", "base_instructions")
   ```

5. **Add prompt validation**:
   - Ensure all required prompts exist
   - Validate prompt templates
   - Check for missing variables

### Phase 5: Benefits Implementation

1. **Prompt Versioning**:
   ```python
   # prompts/versions/v1/cards_prompts.py
   # prompts/versions/v2/cards_prompts.py
   ```

2. **A/B Testing Support**:
   ```python
   prompt = prompt_manager.get_prompt_variant("cards", "greeting", variant="B")
   ```

3. **Easy Maintenance**:
   - Single location for each prompt
   - Clear categorization
   - Easy to update without touching code

4. **Prompt Documentation**:
   ```python
   CARDS_BASE_PROMPT = """
   Purpose: Base instructions for cards specialist
   Variables: {customer_name}, {session_id}
   Last Updated: 2024-01-15
   
   Você é um especialista em cartões...
   """
   ```

## Implementation Priority

1. **High Priority**:
   - Extract main orchestrator routing prompt
   - Create PromptManager class
   - Migrate specialist base prompts

2. **Medium Priority**:
   - Extract team member prompts
   - Implement prompt versioning
   - Add prompt validation

3. **Low Priority**:
   - Multi-language support
   - A/B testing framework
   - Prompt analytics

## Testing Strategy

1. **Unit Tests**:
   - Test PromptManager methods
   - Validate prompt loading
   - Test variable substitution

2. **Integration Tests**:
   - Ensure agents receive correct prompts
   - Test prompt updates don't break functionality
   - Validate all prompts are accessible

## Risks & Mitigation

- **Risk**: Missing prompts during migration
- **Mitigation**: Create comprehensive prompt inventory first

- **Risk**: Performance impact from file I/O
- **Mitigation**: Cache prompts in memory at startup

## Approval Required

1. Do you want versioning support from the start?
2. Should we implement multi-language support now?
3. Any specific prompt naming conventions?
4. Should prompts be in Python files or separate text/yaml files?

Co-Authored-By: Automagik Genie <genie@namastex.ai>