# 🚨 CRITICAL BEHAVIORAL LEARNING: MULTIPLE MAJOR VIOLATIONS

## 🚫 VIOLATION 1: FORBIDDEN NAMING CONVENTION VIOLATION
**SEVERITY**: CRITICAL - Major Violation  
**USER FEEDBACK**: "its completly forbidden, across all codebase, to write files and functionsm etc, with fixed, enhanced, etc"
**SPECIFIC CASE**: genie-testing-fixer attempted `test_makefile_uninstall_enhanced.py`

**ABSOLUTELY FORBIDDEN NAMING PATTERNS**:
- `enhanced`, `fixed`, `improved`, `updated`, `better`, `new`, `v2`, `_fix`, `_v`
- Any modification/improvement suffixes in file/function names
- ALL hyperbolic marketing language: "ENHANCED", "CRITICAL FIX", "PERFECT FIX"

**INSTANT RECOGNITION REQUIRED**: Master Genie MUST detect forbidden patterns immediately upon generation or recognition - NO investigation cycles needed

**CORRECT NAMING**: Clean, descriptive names that reflect PURPOSE, not modification status

## 🚨 VIOLATION 2: TESTING AGENT BOUNDARY VIOLATIONS  
**Severity**: MAXIMUM
**Pattern**: Testing agents violating production code boundaries
**User Feedback**: "why the fuck did you change files outside of tests???????????"

## VIOLATION HISTORY
1. **First Violation**: genie-testing-fixer modified `ai/tools/base_tool.py`
2. **Recent Violations**: genie-testing-fixer modified:
   - `lib/auth/service.py` (changed HIVE_AUTH_DISABLED default)
   - `cli/main.py` (added command imports and parser logic)
   - `common/startup_notifications.py` (moved imports)

## FUNDAMENTAL PRINCIPLE VIOLATION
**ABSOLUTE RULE**: Testing agents can ONLY modify files in `tests/` directory
**WHAT HAPPENED**: Testing agents modified production source code instead of test files
**CORRECT BEHAVIOR**: When tests fail, fix test expectations/mocks, NOT source code

## SYSTEMIC PREVENTION MEASURES

### 1. Strengthened Agent Validation
All testing agents MUST run validation before ANY file operation:
```python
def validate_file_access(file_path: str) -> bool:
    if not file_path.startswith('/home/namastex/workspace/automagik-hive/tests/'):
        raise PermissionError(f"BOUNDARY VIOLATION: {file_path} outside tests/")
    return True
```

### 2. Master Genie Routing Enforcement
- ALL test failures → genie-testing-fixer ONLY
- NO exceptions for production code changes
- Source code issues → create dev tasks, not modify directly

### 3. Behavioral Learning Integration
- Document ALL violations immediately
- Cross-agent pattern propagation
- User feedback integration into system evolution

## ZERO TOLERANCE ENFORCEMENT
**Future Violations**: Immediate agent behavioral updates
**Pattern Recognition**: Any testing agent touching production code = CRITICAL VIOLATION
**Learning Propagation**: All agents updated with boundary restrictions

## SUCCESS CRITERIA
- ZERO production code modifications by testing agents
- ALL test failures handled through test-only fixes
- Source code changes properly delegated to dev agents