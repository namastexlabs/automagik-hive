# PyProject Protection Hook - Usage Guide

## Hook Purpose
The pyproject_protection.py hook prevents unauthorized modifications to `pyproject.toml` while allowing legitimate read-only operations and package management commands.

## ✅ ALLOWED Operations

### Package Management (Always Allowed)
- `uv add <package>`
- `uv add --dev <package>`
- `uv remove <package>`
- `uv sync`

### Read-Only Git Operations
- `git show HEAD:pyproject.toml`
- `git diff pyproject.toml`
- `git log pyproject.toml`
- `git blame pyproject.toml`
- `git cat-file blob HEAD:pyproject.toml`

### File Viewing Commands
- `cat pyproject.toml`
- `head -10 pyproject.toml`
- `tail pyproject.toml`
- `less pyproject.toml`
- `more pyproject.toml`

### Search Operations
- `grep 'pattern' pyproject.toml`
- `rg 'pattern' pyproject.toml`
- `ripgrep 'pattern' pyproject.toml`

## ❌ BLOCKED Operations

### Direct File Editing
- Edit tool with `file_path: pyproject.toml`
- Write tool with `file_path: pyproject.toml`
- MultiEdit tool targeting pyproject.toml

### Command-Line Modifications
- `sed -i 's/old/new/' pyproject.toml`
- `awk '{print $1}' pyproject.toml`
- `echo 'content' >> pyproject.toml`
- `vim pyproject.toml`
- `nano pyproject.toml`
- `emacs pyproject.toml`

### Git Modifications
- `git add pyproject.toml`
- `git commit -am "change"`
- `git checkout HEAD -- pyproject.toml`
- `git mv pyproject.toml other.toml`
- `git rm pyproject.toml`

## Configuration Location
- Hook script: `.claude/hooks/pyproject_protection.py`
- Hook configuration: `.claude/settings.json`

## Error Handling
When a blocked operation is attempted, the hook returns a JSON response with:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "🚫 PYPROJECT.TOML MODIFICATION BLOCKED..."
  }
}
```

This prevents the tool from executing and displays clear guidance to the user.