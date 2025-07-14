# Simple Memory Usage for Genie Framework

## Core Principle: Keep It Simple

Memory should make agent work EASIER, not harder. Here's how we'll use it:

## 1. Simple Discovery Sharing

```python
# Agent finds something useful
memory.add("Found: PagBank API requires auth token in header X-PagBank-Token")

# Any other agent can search
memory.search("PagBank API")  # Finds the discovery instantly
```

## 2. Simple Error Learning

```python
# Agent hits an error
memory.add("Error: 'uv sync' fixes ImportError for agno package")

# Next agent searches before panicking
memory.search("ImportError agno")  # Gets the solution
```

## 3. Simple Progress Tracking

```python
# Main agent notes progress
memory.add("Completed: Command consolidation reduced from 45 to 15 commands")

# Anyone can check status
memory.search("command consolidation")
```

## What NOT to Do

❌ Complex schemas and wrappers
❌ Elaborate locking mechanisms  
❌ Over-structured data formats
❌ Making agents think about memory

## What TO Do

✅ Plain text memories
✅ Natural language storage
✅ Simple searches
✅ Focus on the work, not the memory system

## Real Example

Instead of:
```python
GenieMemory.breadcrumb(
    agent_id="refactor-001",
    scope="utils/date.py", 
    note="Found unused parse_iso() helper"
)
```

Just do:
```python
memory.add("Found unused parse_iso() helper in utils/date.py")
```

## The Rule

If agents need documentation to use memory, we're doing it wrong.
Memory should be as simple as writing a note to yourself.