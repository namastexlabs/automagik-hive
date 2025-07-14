# /chat

---
allowed-tools: mcp__zen__chat(*), WebSearch(*), Read(*), Glob(*)
description: General chat and collaborative thinking with optional model selection
---

Have a conversation with AI models for explanations, brainstorming, or general development questions.

## Usage

```bash
# Default (uses Claude)
/chat "How should I structure my authentication system?"

# With specific model
/chat "Explain SOLID principles" model="o3"
/chat "Compare React vs Vue for my project" model="grok"
/chat "Brainstorm API design patterns" model="gemini"
```

## Model Strengths

- **Claude** (default): Full project context, collaborative thinking
- **O3**: Logical explanations, structured reasoning
- **Grok**: Large context discussions (256K tokens)
- **Gemini**: Creative brainstorming, pattern recognition

## Features

- **Web Search**: Automatically enabled for current information
- **Continuation**: Maintains conversation context across multiple calls
- **Thinking Modes**: Adjust depth with thinking_mode parameter
- **Temperature**: Control creativity with temperature (0-1)

## Examples

```bash
# Brainstorming session
/chat "Let's explore different ways to implement real-time updates"

# Architecture discussion
/chat "What are the trade-offs between microservices and monolith?" model="gemini"

# Best practices research
/chat "Current best practices for API versioning" model="o3"
```

## Automatic Execution

/mcp__zen__chat "$ARGUMENTS" model="${MODEL:-claude}" use_websearch=true

---

**Collaborative Thinking**: Your AI thinking partner for any development question or discussion.