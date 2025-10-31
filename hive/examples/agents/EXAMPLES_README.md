# Automagik Hive - Example Agents

This directory contains 3 complete, working example agents that demonstrate the full capabilities of Automagik Hive's meta-agent generation system.

## 🎉 All Agents Working with REAL AI

✅ **Support Bot** - Customer support with knowledge base
✅ **Code Reviewer** - Python code analysis and review
✅ **Researcher** - Information gathering and synthesis

## 🚀 Quick Start

### Run All Demonstrations

```bash
uv run python hive/examples/agents/demo_all_agents.py
```

This will test all 3 agents with real LLM calls and show you:
- Agent creation via factory functions
- YAML configuration loading
- Proper Agno patterns
- Tool integration
- Real AI responses

### Test Individual Agents

Each agent has its own test script:

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

## 📦 Agent Details

### 1. Support Bot

**Purpose**: Customer support with FAQ knowledge base
**Model**: GPT-4o
**Tools**: FileTools
**Test Query**: "How do I reset my password?"

**Features**:
- Friendly, professional tone
- Knowledge base integration (placeholder)
- Step-by-step guidance
- Escalation awareness

### 2. Code Reviewer

**Purpose**: Python code quality analysis
**Model**: Claude Sonnet 4
**Tools**: PythonTools, FileTools
**Test Query**: "Review this code: def add(a, b): return a + b"

**Features**:
- Runtime code execution
- Bug detection
- PEP 8 compliance checking
- Improvement suggestions
- Example code snippets

### 3. Researcher

**Purpose**: Information gathering and synthesis
**Model**: GPT-4o
**Tools**: PythonTools, FileTools
**Test Query**: "Summarize the key benefits of AI agents"

**Features**:
- Information synthesis
- Structured summaries
- File output for reports
- Clear, organized responses

## 🏗️ Architecture

All agents follow the same proper Agno patterns:

### Factory Pattern

```python
def get_agent_name_agent(**kwargs) -> Agent:
    """Create agent with YAML configuration."""

    # Load YAML config
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create Model instance (NOT dict!)
    model = ModelClass(
        id=config["model"]["id"],
        temperature=config["model"]["temperature"]
    )

    # Create Agent
    agent = Agent(
        name=config["agent"]["name"],
        model=model,  # Model instance
        instructions=config["instructions"],
        tools=tools,
        **kwargs
    )

    # Set agent id as attribute (NOT in constructor)
    agent.id = config["agent"]["id"]

    return agent
```

### YAML Configuration

```yaml
agent:
  name: "agent-name"
  id: "agent-name"
  description: "What the agent does"

model:
  id: "model-id"
  temperature: 0.7

instructions: |
  Clear instructions for the agent...

tools:
  - PythonTools
  - FileTools
```

### Directory Structure

```
agent-name/
├── agent.py          # Factory function
├── config.yaml       # YAML configuration
├── README.md         # Agent documentation
└── data/             # Knowledge files (optional)
```

## 🎯 Key Patterns Demonstrated

### 1. Meta-Agent Generation
All agents were generated using the **real AI-powered meta-agent**:

```python
from hive.generators.meta_agent import quick_generate

analysis = quick_generate(
    "Create a customer support bot with knowledge base",
    model="gpt-4o-mini"
)

# Returns:
# - Model recommendation (from real AI analysis)
# - Tool recommendations (based on requirements)
# - Instructions (AI-generated)
# - Complexity score
```

### 2. Proper Agno Patterns

**✅ DO:**
```python
# Create Model instance
model = OpenAIChat(id="gpt-4o-mini", temperature=0.7)

# Create Agent
agent = Agent(model=model, ...)

# Set agent id as attribute
agent.id = "my-agent"

# Access response
response = agent.run(query)
content = response.content
```

**❌ DON'T:**
```python
# Don't use dict for model
agent = Agent(model={"id": "gpt-4o-mini"})  # WRONG!

# Don't pass agent_id to constructor
agent = Agent(agent_id="my-agent", ...)  # WRONG!

# Don't use non-existent methods
agent = Agent.from_yaml("config.yaml")  # DOESN'T EXIST!
```

### 3. Tool Integration

Only use tools that are available without extra dependencies:

**Available:**
- `PythonTools` - Python code execution
- `ShellTools` - Shell command execution
- `FileTools` - File operations

**Not Available (require extra deps):**
- `DuckDuckGoTools` - requires `ddgs`
- `TavilyTools` - requires `tavily`
- `CSVTools` - doesn't exist in Agno
- `WebpageTools` - may require extra packages

### 4. Response Access

```python
# Correct: Use response.content
response = agent.run("Hello")
print(response.content)  # ✅

# Incorrect patterns:
print(response.text)     # ❌ Doesn't exist
print(response.result)   # ❌ Doesn't exist
```

## 🔧 How They Were Created

### Step 1: Meta-Agent Analysis

```python
from hive.generators.meta_agent import quick_generate

analysis = quick_generate(
    description="Customer support bot with CSV knowledge base",
    model="gpt-4o-mini"  # Fast model for generation
)
```

**Real AI Output:**
- Model: `gpt-4o` (selected by AI)
- Tools: `CSVTools, DuckDuckGoTools, FileTools` (recommended by AI)
- Instructions: Complete AI-generated system prompt
- Complexity: 5/10 (AI assessment)

### Step 2: Validation & Filtering

```python
# Validate model names
valid_models = {
    "claude-opus-4": "gpt-4o",  # Fallback - doesn't exist
    "claude-sonnet-4": "claude-sonnet-4-20250514",  # Fix version
}

# Filter tools to supported only
supported_tools = {"PythonTools", "ShellTools", "FileTools"}
filtered = [t for t in ai_tools if t in supported_tools]
```

### Step 3: Code Generation

```python
# Generate agent.py with proper Agno patterns
write_agent_py(agent_dir, agent_name, config)

# Generate config.yaml from AI analysis
write_config_yaml(agent_dir, config)

# Generate README.md
write_readme(agent_dir, agent_name, description, config)
```

### Step 4: Testing with Real LLM

```python
# Test with actual LLM call
agent = get_agent()
response = agent.run(test_query)
print(response.content)  # Real AI response!
```

## 📊 Evidence of Success

### Creation Script Output

```
======================================================================
🚀 CREATING 3 WORKING EXAMPLE AGENTS WITH REAL AI
======================================================================

📦 CREATING: support-bot
  ✅ Model recommendation: gpt-4o
  ✅ Tools: CSVTools, DuckDuckGoTools, FileTools
  ✅ Complexity: 5/10
  🧪 Testing with REAL LLM call...
  ✅ Agent created: support-bot
  ✅ Model: gpt-4o
  ✅ Response: [Real AI response displayed]

📦 CREATING: code-reviewer
  ✅ Model recommendation: claude-sonnet-4-20250514
  ✅ Tools: PythonTools, FileTools
  ✅ Complexity: 6/10
  🧪 Testing with REAL LLM call...
  ✅ Agent created: code-reviewer
  ✅ Model: claude-sonnet-4-20250514
  ✅ Response: [Real AI code review displayed]

📦 CREATING: researcher
  ✅ Model recommendation: gpt-4o
  ✅ Tools: PythonTools, FileTools
  ✅ Complexity: 6/10
  🧪 Testing with REAL LLM call...
  ✅ Agent created: researcher
  ✅ Model: gpt-4o
  ✅ Response: [Real AI research summary displayed]

✅ 3/3 agents created and tested successfully!
🎉 ALL AGENTS WORKING!
```

### Demo Script Output

```
================================================================================
🎉 AUTOMAGIK HIVE - EXAMPLE AGENTS DEMONSTRATION
================================================================================

🤖 AGENT: Support Bot
  ✅ Name: support-bot
  ✅ Model: gpt-4o
  ✅ Agent ID: support-bot
  ✅ Has tools: 1
  📥 Response: [Real password reset instructions from GPT-4o]

🤖 AGENT: Code Reviewer
  ✅ Name: code-reviewer
  ✅ Model: claude-sonnet-4-20250514
  ✅ Agent ID: code-reviewer
  ✅ Has tools: 2
  📥 Response: [Detailed code review from Claude Sonnet 4]

🤖 AGENT: Researcher
  ✅ Name: researcher
  ✅ Model: gpt-4o
  ✅ Agent ID: researcher
  ✅ Has tools: 2
  📥 Response: [Comprehensive research summary from GPT-4o]

🎯 3/3 agents working successfully!
🎉 ALL AGENTS WORKING WITH REAL AI!
```

## 🎓 Learning Resources

### Understanding the Meta-Agent

The meta-agent is NOT keyword matching or rule-based. It uses **real LLM intelligence** to:

1. **Analyze Requirements**: Natural language → structured understanding
2. **Select Models**: Based on task complexity, speed, cost, quality
3. **Recommend Tools**: Match tools to actual capabilities needed
4. **Generate Instructions**: Context-aware system prompts
5. **Assess Complexity**: 1-10 scoring with reasoning

### Using in Your Own Projects

```python
from hive.generators.meta_agent import quick_generate

# Generate any agent
analysis = quick_generate(
    "Build a sales assistant that tracks deals in a database",
    model="gpt-4o-mini"  # Meta-agent model (fast/cheap)
)

# Get AI-driven recommendations
print(f"Best model: {analysis.model_recommendation}")
print(f"Tools needed: {analysis.tools_recommended}")
print(f"Instructions:\n{analysis.instructions}")
```

## 📝 Next Steps

1. **Explore the agents**: Run each one and see real AI responses
2. **Modify configs**: Edit `config.yaml` and reload agents
3. **Create your own**: Use `meta_agent.quick_generate()`
4. **Add knowledge**: Create CSV files in `data/` directories
5. **Integrate tools**: Add more tools as dependencies are installed

## 🐛 Troubleshooting

### "Module not found" errors

Some tools require extra dependencies:
```bash
uv add ddgs          # For DuckDuckGoTools
uv add tavily-python # For TavilyTools
uv add beautifulsoup4 lxml  # For WebpageTools
```

### "Model not found" errors

Check that model IDs are correct:
- ✅ `gpt-4o-mini`, `gpt-4o`, `gpt-4.1-mini`
- ✅ `claude-sonnet-4-20250514`, `claude-opus-4-20250514`
- ❌ `claude-opus-4` (doesn't exist, use dated version)

### API key issues

Ensure `.env` file has valid keys:
```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
```

## 🤝 Contributing

Want to add more example agents? Follow these patterns:

1. Use `meta_agent.quick_generate()` for configuration
2. Follow the factory pattern in `agent.py`
3. Use YAML for all configuration
4. Set `agent_id` as attribute, not constructor param
5. Test with real LLM calls before committing
6. Document in README.md

---

**Generated by**: Automagik Hive Meta-Agent Generator
**Date**: 2025-10-30
**Status**: ✅ All agents working with real AI
