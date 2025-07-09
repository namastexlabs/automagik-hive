# Task 5: Simplify Frustration Detection

## Objective
Make frustration detection silent and immediate. When users ask for human assistance, yell, or use bad words, transfer should happen immediately without escalation levels.

## Current Issues
- Complex frustration levels (0-3)
- Gradual escalation process
- Delays in human transfer
- Over-engineered detection system

## New Approach
- **Silent detection**: No visible frustration tracking
- **Immediate action**: Transfer on detection
- **Direct triggers**: Bad words, CAPS, "quero humano" = instant transfer
- **No escalation**: Direct handoff when triggered

## Implementation Plan

### Phase 1: Simplify Frustration Detector

#### Current Logic (Remove)
```python
# Complex levels and gradual escalation
frustration_level = 0-3
escalation_threshold = 3
tracking history, patterns, etc.
```

#### New Logic (Implement)
```python
def detect_human_handoff_needed(message: str) -> bool:
    """Simple boolean check for immediate handoff"""
    
    # Direct human request
    human_phrases = ["quero humano", "falar com atendente", "quero falar com alguem"]
    
    # Frustration indicators
    bad_words = ["droga", "merda", "porra", "caralho"]
    
    # Check conditions
    if any(phrase in message.lower() for phrase in human_phrases):
        return True
    
    if any(word in message.lower() for word in bad_words):
        return True
        
    if message.isupper() and len(message) > 10:  # CAPS LOCK yelling
        return True
        
    return False
```

### Phase 2: Update Orchestrator

Remove:
- Frustration level tracking
- Frustration history
- Complex escalation logic
- State updates for frustration

Add:
- Simple handoff check
- Direct routing to human handoff agent

### Phase 3: Simplify State

Remove from team_session_state:
```python
'frustration_level': int,
'frustration_history': List[Dict],
```

Keep only:
```python
'awaiting_human': bool,  # If human handoff is in progress
```

### Phase 4: Update Routing Logic

```python
# In main orchestrator
if detect_human_handoff_needed(message):
    # Route directly to human handoff agent
    return route_to_human_handoff_agent()
```

## Benefits
- Faster human transfers
- Simpler codebase
- Better user experience
- No frustration tracking overhead

## Notes
- Escalation for "unclear communication" should be handled differently
- This is about immediate triggers, not gradual escalation
- Keep it simple and direct

Co-Authored-By: Automagik Genie <genie@namastex.ai>