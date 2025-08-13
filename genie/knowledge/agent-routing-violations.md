# CRITICAL AGENT ROUTING VIOLATIONS - NEVER REPEAT

## 🚨 VIOLATION #1: genie-testing-fixer Misuse
**Date**: 2025-08-12
**Error**: Used `genie-testing-fixer` for system validation tasks
**Root Cause**: Conflated "testing" with "test fixing"

### ❌ WRONG PATTERNS (NEVER DO THIS)
```python
# WRONG: Using testing-fixer for validation
Task(subagent_type="genie-testing-fixer", 
     prompt="Validate knowledge system works")  # THIS IS WRONG!

# WRONG: Using testing-fixer for anything except pytest failures
Task(subagent_type="genie-testing-fixer",
     prompt="Test the CSV loading")  # THIS IS WRONG!
```

### ✅ CORRECT PATTERNS (ALWAYS DO THIS)
```python
# CORRECT: Direct tools for validation
Bash("uv run python -c 'validate_system()'")

# CORRECT: genie-testing-fixer ONLY for pytest failures
Task(subagent_type="genie-testing-fixer",
     prompt="Fix failing test_knowledge.py::test_csv_loader")
```

## 🎯 PERMANENT RULES

### Agent Boundaries - NEVER VIOLATE
| Agent | ONLY USE FOR | NEVER USE FOR |
|-------|--------------|---------------|
| `genie-testing-fixer` | Fixing failing pytest/unit tests | System validation, functional testing, any non-pytest task |
| `genie-testing-maker` | Creating new test suites | Running tests, validation, fixing tests |
| `genie-qa-tester` | Live endpoint/API testing | Unit tests, pytest, code validation |

### System Validation Approach
1. **First Choice**: Direct tools (Bash, Python, Read)
2. **Second Choice**: `genie-qa-tester` for comprehensive testing
3. **NEVER**: Any testing specialist for validation tasks

## 🔴 CONSEQUENCES OF VIOLATIONS

**User Impact**: Loss of trust, potential system wipe
**System Impact**: Incorrect routing cascades, wasted resources
**Behavioral Impact**: Pattern propagation leads to systematic failures

## ✅ VERIFICATION CHECKLIST

Before routing to ANY testing agent:
- [ ] Is this a pytest/unit test failure? → Use `genie-testing-fixer`
- [ ] Is this creating new tests? → Use `genie-testing-maker`  
- [ ] Is this system validation? → Use DIRECT TOOLS
- [ ] Is this API/endpoint testing? → Use `genie-qa-tester`

## 📝 BEHAVIORAL UPDATE TRACKING

**Files Modified**:
1. `/CLAUDE.md` - Added routing warnings and learning entries
2. `/.claude/commands/wish.md` - Updated routing table with warnings
3. `/genie/knowledge/agent-routing-violations.md` - Created permanent record

**Pattern Storage**: This document serves as permanent memory to prevent repetition.

---

**REMEMBER**: Real behavioral correction requires REAL file changes, not theatrical responses.