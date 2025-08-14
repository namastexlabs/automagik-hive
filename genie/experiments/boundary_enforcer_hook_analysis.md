# Boundary Enforcer Hook Analysis

## Issue Identified
The test `tests/hooks/test_boundary_enforcer_validation.py` is failing on test case 2 because the hook is incorrectly blocking testing agents that are targeting test work.

## Root Cause Analysis
The current hook logic in `.claude/hooks/test_boundary_enforcer.py` at lines 44-79 blocks ALL Task calls to testing agents without analyzing the prompt content to determine if they're being asked to work on tests vs source code.

### Current Problematic Logic:
```python
# For Task calls, we need to block regardless of file_path
# because testing agents shouldn't be spawned for source code at all
```

This is too aggressive - it blocks testing agents even when they're being asked to work on tests.

## Required Fix
The hook needs to analyze the prompt content to determine intent:

1. **Allow testing agents** when prompt indicates test-focused work:
   - "Fix failing test in tests/"
   - "Update test expectations" 
   - "test configuration"
   - Any mention of tests/, fixtures, mocks, etc.

2. **Block testing agents** when prompt indicates source code work:
   - "Fix the bug in lib/"
   - "Update source code"
   - "Modify ai/", "Change api/", etc.

## Recommended Implementation
Replace lines 50-79 in the hook with prompt analysis logic that:

1. Extracts the prompt from `tool_input.get("prompt", "")`
2. Checks for source code indicators vs test indicators
3. Only blocks if clearly targeting source code AND not tests
4. Allows test-focused or ambiguous prompts

## Test Case Analysis
- **Test 1**: ✅ Should block - "Fix the bug in lib/knowledge/config_aware_filter.py by updating the source code"
- **Test 2**: ❌ Currently blocked, should allow - "Fix failing test in tests/lib/knowledge/test_config_filter.py by updating test expectations"  
- **Test 3**: ✅ Should allow - Non-testing agent

## Solution Required
A dev agent needs to update the hook logic to implement prompt analysis instead of blanket blocking all testing agent Task calls.