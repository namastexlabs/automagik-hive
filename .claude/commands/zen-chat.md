# /zen-chat

---
allowed-tools: mcp__zen__chat(*), Read(*), Glob(*), Bash(git *), Bash(find *), Bash(wc *), Bash(head *), Bash(tail *), Bash(grep *), Bash(ls *), Bash(du *), Bash(sort *), Bash(uniq *), Bash(cat *), mcp__search-repo-docs__*, mcp__ask-repo-agent__*
description: Collaborative thinking and brainstorming with intelligent context awareness
---

Collaborative thinking and brainstorming with intelligent context awareness for development decisions.

## Usage Examples

```bash
# Basic collaborative session
/zen-chat "How should we structure the agent routing logic?"

# Specific technical discussion  
/zen-chat "Evaluate tradeoffs between async/await vs traditional threading for agent communication"

# Architecture decisions
/zen-chat "What's the best pattern for managing state across multiple agents?"

# Include specific files for context
/zen-chat "Review the authentication flow in @agents/auth/handler.py and suggest improvements"
```

## Dynamic Context Collection

- Git status: !`git status --porcelain | wc -l` modified files, !`git status --porcelain | head -5`
- Active branch: !`git branch --show-current` 
- Recent commits: !`git log --oneline -5`
- Modified files: !`find . -name "*.py" -o -name "*.md" -o -name "*.yaml" -mtime -1 | head -10`
- System complexity: !`find . -name "*.py" | wc -l` Python files, !`find . -name "*.md" | wc -l` docs
- Active tasks: !`grep -r "\[ \]" genie/active/ 2>/dev/null | wc -l` pending todos
- Recent errors: !`find . -name "*.log" -mtime -1 | head -3`
- Code hotspots: !`git log --oneline --since="1 week ago" --name-only | grep "\.py$" | sort | uniq -c | sort -nr | head -5`

## Automatic Execution

/mcp__zen__chat "Context-driven brainstorming session. $ARGUMENTS

LIVE PROJECT CONTEXT:
- Current work: Above git analysis shows real-time project state
- Development focus: Based on modified files and pending tasks above
- System insights: Leveraging complexity metrics and code hotspots identified

Please provide collaborative insights and alternative approaches for the current development context."