# Claude Hooks Documentation

## Overview
This directory contains hooks that enforce coding standards and protect critical files in the Automagik Hive project.

## Active Hooks

### 1. **pyproject_protection.py** 🛡️
**Purpose**: Prevents unauthorized modification of `pyproject.toml` to avoid dependency corruption.

**Background**: Previous incidents where subagents incorrectly modified dependencies (e.g., adding self-referential `automagik-hive>=0.1.0`) require human oversight.

**Behavior**:
- Blocks ALL attempts to edit `pyproject.toml` by default
- Only allows edits when `PYPROJECT_EDIT_APPROVED=true` environment variable is set
- Provides clear instructions to report the need to human

**To Allow Edits** (for main Claude only):
```bash
export PYPROJECT_EDIT_APPROVED=true
# Make your edits
unset PYPROJECT_EDIT_APPROVED
```

### 2. **naming_validation.py** ✅
**Purpose**: Enforces naming conventions across the codebase.

**Rules**:
- Prevents files/functions with names like "fixed", "enhanced", "improved", etc.
- Ensures clean, descriptive naming without temporary markers

### 3. **tdd_hook.py** 🧪
**Purpose**: Enforces Test-Driven Development practices.

**Features**:
- Ensures tests are created in proper mirror structure
- Validates test files exist before modifying source code
- Enforces Red-Green-Refactor cycle

### 4. **test_boundary_enforcer.py** 🚧
**Purpose**: Prevents testing agents from modifying source code.

**Rules**:
- Testing agents (`hive-testing-fixer`, `hive-testing-maker`) can only modify files in `tests/`
- Blocks Task tool spawning of testing agents for source code work

## Hook Configuration

Hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 $CLAUDE_PROJECT_DIR/.claude/hooks/pyproject_protection.py"
          },
          // ... other hooks
        ]
      }
    ]
  }
}
```

## Debug Logging

Most hooks write debug logs to `/tmp/` for troubleshooting:
- `/tmp/pyproject_hook_debug.log` - PyProject protection events
- `/tmp/hook_debug.log` - Test boundary enforcer events
- `/tmp/tdd_debug.log` - TDD validation events

## Important Notes

1. **Hook Priority**: PyProject protection runs first to catch critical file modifications early
2. **Subagent Detection**: Hooks attempt to detect subagent context but may not be 100% accurate
3. **Fail-Safe**: If hooks fail, they exit gracefully without blocking operations (except for explicit denials)
4. **Human Override**: The human can always bypass hooks by setting appropriate environment variables

## For Subagent Developers

If you're a subagent and need to modify protected files:
1. **DON'T** try to bypass the hooks
2. **DO** report the need to the human with clear justification
3. **DO** provide exact changes needed
4. **DO** wait for human approval or manual implementation

Remember: These hooks exist to protect the project from accidental corruption. Respect them!