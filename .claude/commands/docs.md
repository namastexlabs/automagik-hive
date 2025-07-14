# /docs

---
allowed-tools: mcp__zen__docgen(*), Read(*), Write(*), Edit(*)
description: Create or update documentation with optional model selection
---

Unified documentation command for creating and updating docs.

## Usage

```bash
# Create new documentation
/docs create "API reference for authentication system"

# Update existing documentation
/docs update "Add new endpoints to API docs"

# With specific model
/docs create "Architecture decision record" model="gemini"
```

## Automatic Execution

Based on the action (create/update), routes to appropriate tools.

---

**Smart Documentation**: One command for all documentation needs.
