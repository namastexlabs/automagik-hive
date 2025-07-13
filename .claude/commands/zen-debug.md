# /zen-debug

---
allowed-tools: mcp__zen__debug(*), Read(*), Bash(*), Grep(*), Glob(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(ps *), Bash(netstat *), Bash(sort *), Bash(uniq *), Bash(cat *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Systematic investigation and root cause analysis for complex bugs and issues
---

Systematic investigation and root cause analysis for complex bugs and issues.

## Usage Examples

```bash
# Debug specific error
/zen-debug "Agent routing fails with 'NoneType' error in production"

# System-wide investigation
/zen-debug "Performance degradation after recent deployment"

# Include error logs for context  
/zen-debug "Analyze authentication failures in @logs/auth.log and @agents/auth/handler.py"

# Debug with specific symptoms
/zen-debug "Memory usage grows continuously, suspect memory leak in agent communication"
```

## Dynamic Context Collection

- Error logs: !`find . -name "*.log" -mtime -1 | head -5`
- Test failures: !`find . -name "test*.log" -o -name "pytest.log" | head -3`
- Recent bugs: !`git log --oneline -10 --grep="fix\|bug\|error"`
- Exception patterns: !`grep -r "Exception\|Error\|raise" --include="*.py" . | wc -l` error handlers
- Stack traces: !`grep -r "Traceback\|Exception\|Error:" --include="*.log" --include="*.py" . | tail -5`
- System health: !`ps aux | grep python | wc -l` Python processes
- Network issues: !`netstat -tuln 2>/dev/null | grep LISTEN | wc -l` listening ports
- Crash patterns: !`grep -r "crash\|abort\|fatal" --include="*.log" . | tail -3`
- Memory issues: !`grep -r "memory\|oom\|allocation" --include="*.log" . | tail -3`

## Automatic Execution

/mcp__zen__debug "Deep systematic debugging investigation. $ARGUMENTS

LIVE SYSTEM DIAGNOSIS:
- Error landscape: Above analysis shows current error patterns and system health
- Bug history: Recent fix patterns and crash/memory issues from logs
- System state: Process count, network status, and exception handler coverage
- Investigation leads: Stack traces and error logs identified above

Please conduct systematic root cause analysis considering the live diagnostic data above."