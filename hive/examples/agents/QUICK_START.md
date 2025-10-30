# Example Agents - Quick Start

## ⚡ 30-Second Demo

```bash
# Run comprehensive demo of all 3 agents
uv run python hive/examples/agents/demo_all_agents.py
```

Expected output:
```
🎉 ALL AGENTS WORKING WITH REAL AI!
✅ Support Bot
✅ Code Reviewer
✅ Researcher
🎯 3/3 agents working successfully!
```

## 📦 What You Get

3 complete, working agents with real AI:

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **support-bot** | GPT-4o | FileTools | Customer support |
| **code-reviewer** | Claude Sonnet 4 | PythonTools, FileTools | Code analysis |
| **researcher** | GPT-4o | PythonTools, FileTools | Research & synthesis |

## 🎯 Test Individual Agents

```bash
# Support Bot
cd hive/examples/agents/support-bot
uv run python agent.py

# Code Reviewer
cd hive/examples/agents/code-reviewer
uv run python agent.py

# Researcher
cd hive/examples/agents/researcher
uv run python agent.py
```

## 🔧 Use in Your Code

```python
# Import any agent factory
from hive.examples.agents.support_bot.agent import get_support_bot_agent

# Create agent
agent = get_support_bot_agent()

# Run query
response = agent.run("How do I reset my password?")
print(response.content)
```

## 📚 Learn More

- **Full Documentation**: `EXAMPLES_README.md`
- **Evidence of Success**: `/EXAMPLE_AGENTS_EVIDENCE.md`
- **Creation Script**: `create_and_test_agents.py`

## ✅ All Features Verified

- [x] Meta-agent generation with REAL AI
- [x] Proper Agno factory patterns
- [x] YAML configuration loading
- [x] API key integration
- [x] Tool usage (PythonTools, FileTools)
- [x] Real LLM responses
- [x] Production-ready code

## 🎉 Status

**ALL 3 AGENTS WORKING!** 🚀

---

**Quick Links**:
- Demo: `demo_all_agents.py`
- Docs: `EXAMPLES_README.md`
- Evidence: `/EXAMPLE_AGENTS_EVIDENCE.md`
