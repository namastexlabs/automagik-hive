# TDD Hooks Comparison Report

## Overview
There are 3 TDD-related files in `.claude/`:
1. **tdd_hook.py** - Currently active (used in settings.json)
2. **tdd_validator.py** - More sophisticated but not active
3. **tdd_hook.sh** - Shell wrapper for tdd_validator.py

## Detailed Comparison

### 1. `.claude/tdd_hook.py` (CURRENTLY ACTIVE)

**Purpose**: Simple test existence checker  
**Activation**: Direct Python execution via settings.json  
**Exit Codes**: 0 (pass), 2 (warning - blocks with message)

**Features**:
- ✅ Checks if test files exist for implementation files
- ✅ Skips non-Python files and test files
- ✅ Skips certain directories (docs, .claude, genie, etc.)
- ✅ Warns but blocks when no test found (exit code 2)
- ❌ Does NOT run tests
- ❌ Does NOT check test status (passing/failing)
- ❌ Does NOT enforce Red-Green-Refactor cycle

**Test Detection Patterns**:
```python
# Looks for tests in these locations:
1. Same directory: test_<filename>.py
2. Tests subdirectory: tests/test_<filename>.py  
3. Project-level: tests/<path>/test_<filename>.py
```

**Behavior**:
- **Blocks with warning** when writing implementation without tests
- **Allows** writing test files always
- **Allows** writing non-Python files always

---

### 2. `.claude/tdd_validator.py` (NOT ACTIVE)

**Purpose**: Full TDD cycle enforcer with test execution  
**Activation**: Not currently used (but has shell wrapper)  
**Exit Codes**: 0 (pass), 1 (block)

**Features**:
- ✅ Checks if test files exist
- ✅ **RUNS ACTUAL TESTS** via `uv run pytest`
- ✅ Enforces Red-Green-Refactor cycle
- ✅ Validates TDD phases based on test status
- ✅ More sophisticated phase detection
- ❌ Requires pytest to be working
- ❌ Could slow down development if tests are slow

**TDD Phase Detection**:
```python
# RED PHASE: Tests must exist before implementation
if not file_exists and not has_tests:
    return "RED PHASE VIOLATION: Create tests first!"

# GREEN PHASE: Tests failing, implementation allowed
if test_results["has_failures"]:
    return "GREEN PHASE: Tests failing, implementation allowed"

# REFACTOR PHASE: Tests passing, warn about new features
if all_tests_pass:
    return "REFACTOR PHASE: Ensure new functionality has tests"
```

**Key Differences**:
- **Actually runs pytest** to check test status
- **Enforces proper TDD cycle** (Red → Green → Refactor)
- **More intelligent** about when to allow changes
- **Performance impact** from running tests on every edit

---

### 3. `.claude/tdd_hook.sh` (WRAPPER SCRIPT)

**Purpose**: Shell wrapper to run tdd_validator.py with uv  
**Usage**: Could be used if settings.json supported shell scripts

```bash
#!/bin/bash
# Simply changes to project root and runs tdd_validator.py via uv
cd "$PROJECT_ROOT"
uv run python "$SCRIPT_DIR/tdd_validator.py"
```

---

## Key Differences Summary

| Feature | tdd_hook.py (ACTIVE) | tdd_validator.py | 
|---------|---------------------|------------------|
| **Currently Active** | ✅ Yes | ❌ No |
| **Checks test existence** | ✅ Yes | ✅ Yes |
| **Runs actual tests** | ❌ No | ✅ Yes (pytest) |
| **Enforces TDD cycle** | ❌ No | ✅ Yes |
| **Performance impact** | ✅ Minimal | ⚠️ Runs pytest |
| **Blocks on missing tests** | ✅ Yes (warning) | ✅ Yes (error) |
| **Intelligence** | Basic | Advanced |
| **Dependencies** | None | pytest must work |
| **Exit behavior** | Exit 2 (warning) | Exit 1 (error) |

---

## Current Configuration

**`.claude/settings.json`**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 $CLAUDE_PROJECT_DIR/.claude/tdd_hook.py"
          }
        ]
      }
    ]
  }
}
```

---

## Recommendations

### Current Issues with Active Hook (tdd_hook.py):
1. **Too simplistic** - Only checks file existence, not test quality
2. **No cycle enforcement** - Doesn't understand Red-Green-Refactor
3. **Can be bypassed** - Just create empty test file to satisfy it

### Why tdd_validator.py Might Be Better:
1. **Enforces real TDD** - Actually runs tests and checks status
2. **Smarter decisions** - Allows implementation when tests are failing (GREEN phase)
3. **Catches more issues** - Empty or broken tests won't bypass it

### Why tdd_hook.py Might Be Preferred:
1. **Faster** - No pytest execution overhead
2. **Simpler** - Less can go wrong
3. **Non-blocking** for refactoring (when tests might temporarily break)

### Suggested Improvement:
Create a **hybrid approach**:
- Quick existence check (like tdd_hook.py)
- Optional test execution (like tdd_validator.py) 
- Configurable strictness level
- Better test structure validation (using our new analyzer)

---

## Test Structure Integration

Given our test structure analysis showing:
- 95 orphaned tests
- 83 missing tests  
- 56 misplaced root-level tests

**Neither hook addresses**:
- Test file location/structure validation
- Orphaned test detection
- Test naming convention enforcement

**Proposed Enhancement**:
Integrate our `test_structure_analyzer.py` logic into the TDD hook to:
1. Ensure tests follow mirror structure
2. Warn about orphaned tests
3. Enforce proper test placement
4. Block creation of tests in wrong locations