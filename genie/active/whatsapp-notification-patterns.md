# WhatsApp Notification Patterns

## Simple Notification Function

```python
def notify(message, context=""):
    """Send WhatsApp notification to user"""
    notification = f"🤖 Genie Update\n\n{message}"
    if context:
        notification += f"\n\n💡 {context}"
    
    mcp__send_whatsapp_message__send_text_message(
        instance="SofIA", 
        message=notification
    )
```

## Notification Triggers

### 1. Task Completion
```python
# When finishing a task
notify(
    f"✅ {task_id} Complete: {summary}",
    "Check memory: memory.search('TASK {task_id}')"
)
```

### 2. Epic Milestones
```python
# When reaching epic milestones
notify(
    f"🎯 Epic Milestone: {milestone}",
    f"Progress: {completed}/{total} tasks done"
)
```

### 3. Blockers Resolved
```python
# When blockers are resolved
notify(
    f"🔓 Blocker Resolved: {blocker_description}",
    "Dependent tasks can now proceed"
)
```

### 4. Discoveries
```python
# When finding something important
notify(
    f"💡 Discovery: {finding}",
    "Added to memory with FOUND: prefix"
)
```

### 5. Errors Need Attention
```python
# When human intervention needed
notify(
    f"⚠️ Need Help: {error_description}",
    "Manual intervention required"
)
```

## Notification Schedule

- **Always**: Task completions, epic milestones, errors
- **Important**: New patterns discovered, blockers resolved
- **Optional**: Progress updates (every 30min for long tasks)

## Message Templates

### Task Complete
```
🤖 Genie Update

✅ T-005 Complete: WhatsApp notifications working

📝 Summary: Created notification system with hooks and patterns
📍 Files: .claude/hooks/whatsapp-notifier.sh
🔍 Memory: search('TASK T-005') for details
```

### Epic Progress
```
🤖 Epic Progress

🎯 genie-framework-completion
✅ Phase 1: 3/4 tasks done
🔄 Next: T-005 (interactive CLAUDE.md refactoring)

📊 Overall: 60% complete
```

### Discovery
```
🤖 New Discovery

💡 Found: Memory can replace all reference files
🧠 Pattern: Use PATTERN/TASK/FOUND prefixes
✨ Impact: Reduces file bloat, increases discoverability
```

## Usage in Workflows

```python
# Start of epic
notify("🎯 Started Epic: genie-framework-completion")

# During work
memory.add("TASK T-006: Working on WhatsApp notifications - Claude")

# Important finding
memory.add("FOUND: WhatsApp async working perfectly")
notify("💡 WhatsApp integration successful", "One-way notifications ready")

# Task completion
memory.add("TASK T-006: DONE - WhatsApp notifications active")
notify("✅ T-006 Complete: WhatsApp notifications", "You'll get updates when away from screen")

# Epic completion
notify("🎉 Epic Complete: genie-framework-completion", "Framework ready for self-enhancement!")
```

## Best Practices

✅ Keep messages concise but informative
✅ Use emojis for quick visual parsing
✅ Include memory search hints
✅ Only notify for meaningful events
✅ Test notifications before epic work

❌ Don't spam with minor updates
❌ Don't send without context
❌ Don't rely on notifications for critical coordination