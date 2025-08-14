# KeyboardInterrupt Bug Analysis - CLI Docker Manager

**FORGE_TASK_ID:** 1161972c-9107-4c83-9aee-a13468eb33f0

## 🐛 Bug Summary

**Location:** `cli/docker_manager.py:625` in `_interactive_install` method  
**Issue:** Missing KeyboardInterrupt handling for interactive user prompts  
**Impact:** Critical UX issue - users cannot gracefully exit installation process  
**Severity:** High - affects user experience and system reliability  

## 🔍 Root Cause Analysis

The `_interactive_install` method contains multiple `input()` calls throughout the interactive installation flow but lacks proper exception handling for `KeyboardInterrupt`. When a user presses Ctrl+C during any prompt, the program terminates ungracefully instead of providing a clean exit.

### Affected Input Calls

1. **Line 625:** `hive_choice = input("Would you like to install Hive Core? (Y/n): ")`
2. **Line 644:** `db_choice = input("\nSelect database option (1-2): ")`  
3. **Line 658:** `db_action = input("Do you want to (r)euse existing database or (c)recreate it? (r/c): ")`
4. **Lines 683-687:** Multiple database credential inputs:
   - `host = input("Host (localhost): ")`
   - `port = input("Port (5432): ")`
   - `database = input("Database name (automagik_hive): ")`
   - `username = input("Username: ")`
   - `password = input("Password: ")`
5. **Line 701:** `genie_choice = input("Would you like to install Genie? (y/N): ")`
6. **Line 712:** `agent_choice = input("Would you like to install Agent Workspace? (y/N): ")`

## 🎯 Solution Strategy

### Approach 1: Individual Try-Catch Blocks (Recommended)

Wrap each `input()` call in its own try-catch block to provide immediate and contextual handling:

```python
try:
    user_input = input("Prompt: ").strip().lower()
except KeyboardInterrupt:
    print("\n👋 Installation cancelled by user")
    return False
```

**Advantages:**
- Immediate response to user interruption
- Clear context for each cancellation point
- Maintains existing code structure
- Easy to implement and understand

### Approach 2: Helper Function

Create a reusable helper function for all user input with built-in KeyboardInterrupt handling:

```python
def get_user_input(self, prompt: str, valid_options: list = None) -> str:
    try:
        user_input = input(prompt).strip().lower()
        return user_input
    except KeyboardInterrupt:
        print("\n👋 Installation cancelled by user")
        return None
```

**Advantages:**
- Consistent behavior across all inputs
- Reduced code duplication
- Centralized error handling
- Better maintainability

### Approach 3: Method-Level Wrapper

Wrap the entire method in a try-catch block:

```python
def _interactive_install(self) -> bool:
    try:
        # All existing code
        return True
    except KeyboardInterrupt:
        print("\n👋 Installation cancelled by user")
        return False
```

**Disadvantages:**
- Less granular control
- User might need to press Ctrl+C multiple times
- Doesn't provide immediate feedback

## 🏗️ Implementation Plan

**Recommended Implementation:** Approach 1 (Individual Try-Catch Blocks)

1. **Phase 1:** Add try-catch around the main flow inputs (lines 625, 644, 658, 701, 712)
2. **Phase 2:** Handle the database credential input block (lines 683-687) as a group
3. **Phase 3:** Add a method-level catch as a safety net
4. **Phase 4:** Test with actual user interruption scenarios

## 🧪 Testing Strategy

1. **Unit Tests:** Mock KeyboardInterrupt during each input call
2. **Integration Tests:** Test full installation flow with interruptions at different points
3. **Manual Testing:** Actual user testing with Ctrl+C at various prompts
4. **Edge Cases:** Test interruption during nested while loops

## 🔒 Error Handling Considerations

1. **Graceful Message:** Always display user-friendly cancellation message
2. **Return Value:** Consistently return `False` to indicate cancellation
3. **Cleanup:** Ensure no partial state is left after cancellation
4. **Logging:** Consider logging cancellation events for debugging

## 📋 Implementation Checklist

- [ ] Add try-catch around hive_choice input (line 625)
- [ ] Add try-catch around db_choice input (line 644)
- [ ] Add try-catch around db_action input (line 658)
- [ ] Add try-catch around database credential inputs (lines 683-687)
- [ ] Add try-catch around genie_choice input (line 701)
- [ ] Add try-catch around agent_choice input (line 712)
- [ ] Add method-level try-catch as safety net
- [ ] Test each interruption point
- [ ] Update documentation
- [ ] Add unit tests for KeyboardInterrupt handling

## 🚀 Expected Outcome

After implementation:
- Users can gracefully exit installation at any prompt with Ctrl+C
- Consistent "👋 Installation cancelled by user" message
- Method returns `False` to indicate cancellation
- No ungraceful program termination
- Better overall user experience

## 📖 Code Example

See `/genie/experiments/keyboard_interrupt_fix.py` for a complete prototype implementation demonstrating the recommended approach.