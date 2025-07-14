# Simple Memory Patterns - Keep It Simple!

## Just 3 Prefixes

### PATTERN: Reusable Solutions
```python
# Save a pattern
memory.add("PATTERN: Auth Flow - Use JWT with refresh tokens #auth #security")

# Find patterns
memory.search("PATTERN auth")
memory.search("PATTERN #security")
```

### TASK: What's Happening Now
```python
# Update task status
memory.add("TASK T-001: Working on API endpoints - Alice")
memory.add("TASK T-001: Found auth middleware at api/auth.py")
memory.add("TASK T-001: DONE - endpoints at /api/v2/*")

# Check status
memory.search("TASK T-001")      # Everything about T-001
memory.search("TASK Working")     # Who's working on what
memory.search("TASK DONE")        # What's completed
```

### FOUND: Project Knowledge
```python
# Share what you find
memory.add("FOUND: Run tests with 'uv run pytest'")
memory.add("FOUND: Database config in .env file")
memory.add("FOUND: Auth happens in middleware.py")

# Search knowledge
memory.search("FOUND tests")      # How to test
memory.search("FOUND database")   # Database info
```

## That's It!

No complex schemas. No structured fields. Just:
- Start with PATTERN:, TASK:, or FOUND:
- Write naturally after the prefix
- Use #tags if helpful
- Search with prefix + keywords

## Real Examples

```python
# Alice starts work
memory.add("TASK T-005: Starting WhatsApp integration - Alice")

# Alice finds something
memory.add("FOUND: WhatsApp API docs at docs/whatsapp.md")

# Alice hits an issue  
memory.add("FOUND: AsyncIO error - fix with nest_asyncio")

# Alice finishes
memory.add("TASK T-005: DONE - WhatsApp working")
memory.add("PATTERN: WhatsApp Integration - Use Evolution API v2 #whatsapp")

# Bob checks before starting
memory.search("TASK T-006")       # Is anyone on it?
memory.search("PATTERN whatsapp")  # Any WhatsApp patterns?
```

## Why This Works

1. **Natural Writing**: No schema to remember
2. **Natural Search**: Just prefix + what you want
3. **Real-Time Updates**: Everyone sees everything
4. **Pattern Library**: Builds itself as you work
5. **Zero Overhead**: Just add() and search()

## Update CLAUDE.md

Change:
```
- ALWAYS check `@genie/reference/` for patterns before implementing
```

To:
```
- ALWAYS search memory for patterns: memory.search("PATTERN [topic]")
```

Keep it simple. Ship it!