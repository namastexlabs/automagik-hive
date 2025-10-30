# Automagik Hive Examples

Production-ready examples of agents, teams, and workflows built with YAML configs.

## 📚 What's Included

### Agents

- **[support-bot](agents/support-bot/)** - Customer support with CSV knowledge base
- **[code-reviewer](agents/code-reviewer/)** - Code quality and security reviews
- **[researcher](agents/researcher/)** - Web research and synthesis

### Teams

Coming soon! Examples of multi-agent teams for:
- Customer support routing
- Code review pipeline
- Research coordination

### Workflows

Coming soon! Examples of step-based workflows for:
- Blog post creation
- Code review pipeline
- Customer onboarding

## 🚀 Quick Start

### 1. Pick an Example

```bash
cd examples/agents/support-bot
cat README.md  # Read the guide
```

### 2. Configure Environment

Create `.env` in project root:

```bash
# Required
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/hive
OPENAI_API_KEY=your_key_here

# Optional (depending on agent)
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
```

### 3. Run the Agent

```python
from hive.scaffolder import generate_agent_from_yaml

# Load agent from YAML config
agent = generate_agent_from_yaml("examples/agents/support-bot/config.yaml")

# Chat with agent
response = agent.run("How do I install Automagik Hive?")
print(response.content)
```

Or use CLI:

```bash
hive chat examples/agents/support-bot/config.yaml
```

## 📖 Example Structure

Each example includes:

```
example-name/
├── config.yaml       # Agent configuration (the heart of it!)
├── README.md         # Complete guide with examples
├── data/            # Knowledge base, sample files (if needed)
└── tests/           # Example tests (coming soon)
```

## 🎯 Use Cases by Example

### Customer Support
→ **support-bot** - Answers FAQs using knowledge base, searches web for complex issues

### Code Quality
→ **code-reviewer** - Reviews code for bugs, security, and best practices

### Research & Analysis
→ **researcher** - Finds and synthesizes information from multiple sources

## 🛠️ Customization Guide

### Change the Model

All examples use different models based on use case:

```yaml
# Fast and cheap (support, simple tasks)
agent:
  model: "gpt-4o-mini"

# Balanced (research, analysis)
agent:
  model: "gpt-4o"

# Best for code (reviews, technical)
agent:
  model: "claude-sonnet-4"
```

### Add More Tools

```yaml
tools:
  - "web_search"      # Already included
  - "slack_api"       # Add Slack notifications
  - "email_tools"     # Add email capabilities
  - "github_api"      # Add GitHub integration
```

See full list:
```python
from hive.config import print_tool_catalog
print_tool_catalog()
```

### Modify Instructions

```yaml
instructions: |
  You are a [personality].

  Your responsibilities:
  - [Task 1]
  - [Task 2]

  Guidelines:
  - [Guideline 1]
  - [Guideline 2]
```

### Add Knowledge Base

```yaml
knowledge:
  source: "./data/my_knowledge.csv"
  type: "csv"
  hot_reload: true
  num_documents: 5
```

CSV format:
```csv
query,context,category
"Question 1","Answer 1","category1"
"Question 2","Answer 2","category2"
```

## 🔍 Validation

Validate configs before running:

```bash
# Validate single config
hive validate examples/agents/support-bot/config.yaml

# Validate all examples
hive validate examples/
```

Or in Python:

```python
from hive.scaffolder import validate_yaml

is_valid = validate_yaml("examples/agents/support-bot/config.yaml")
```

## 📊 Performance Comparison

| Agent | Model | Response Time | Cost/Query | Best For |
|-------|-------|---------------|------------|----------|
| support-bot | gpt-4o-mini | <2s | $0.001 | High volume, simple queries |
| code-reviewer | claude-sonnet-4 | 5-10s | $0.02 | Code understanding, security |
| researcher | gpt-4o | 30-60s | $0.05 | Comprehensive research |

## 🎓 Learning Path

### Beginner
1. **Start with support-bot** - Simple, clear example
2. **Modify instructions** - Change personality/tone
3. **Add to knowledge base** - Add your own FAQs
4. **Test different models** - See performance differences

### Intermediate
1. **Try code-reviewer** - More complex instructions
2. **Add custom tools** - Integrate your APIs
3. **Create your own agent** - Use templates as guide
4. **Deploy to production** - Docker, cloud platforms

### Advanced
1. **Build a team** - Coordinate multiple agents
2. **Create workflows** - Multi-step processes
3. **Custom knowledge sources** - Databases, APIs
4. **Build MCP integrations** - External services

## 💡 Tips for Great Agents

### 1. Clear Instructions

❌ BAD: "You help with stuff"
✅ GOOD: "You are a customer support agent that answers questions using the knowledge base first, then searches the web if needed"

### 2. Right Model for the Task

- **gpt-4o-mini** - Fast, cheap, good enough (90% of cases)
- **gpt-4o** - Balanced speed and capability
- **claude-sonnet-4** - Best for code, complex reasoning
- **o1-mini** - Deep reasoning (math, logic)

### 3. Appropriate Tools

Only include tools the agent actually needs:
- Too few → Agent can't complete tasks
- Too many → Agent confused about when to use what

### 4. Good Knowledge Bases

- Curate quality over quantity
- Keep information current (hot reload!)
- Organize by category
- Test retrieval accuracy

### 5. Iteration

Start simple, then:
1. Run agent on test queries
2. Identify failures
3. Improve instructions/knowledge
4. Repeat

## 🔧 Troubleshooting

### Agent Not Using Knowledge Base

**Fix**: Make instructions explicit:

```yaml
instructions: |
  ALWAYS check the knowledge base FIRST.
  Only search the web if knowledge base has no answer.
```

### Tool Not Being Used

**Fix**: Add tool-specific instructions:

```yaml
instructions: |
  When you need to [specific task], use [tool_name].
  Example: "When searching the web, use web_search tool"
```

### Responses Too Long/Short

**Fix**: Adjust max_tokens:

```yaml
settings:
  max_tokens: 300   # Brief responses
  max_tokens: 1000  # Balanced
  max_tokens: 2000  # Comprehensive
```

### Inconsistent Behavior

**Fix**: Lower temperature:

```yaml
settings:
  temperature: 0.3  # More consistent
  temperature: 0.7  # Balanced
  temperature: 1.0  # More creative
```

## 🚢 Deployment

### Development

```bash
# Run locally with hot reload
hive dev examples/agents/support-bot/config.yaml
```

### Production

```bash
# Set environment
export HIVE_ENVIRONMENT=production

# Use production database
export HIVE_DATABASE_URL=postgresql://prod-db:5432/hive

# Deploy (Docker example)
docker build -t my-agent .
docker run -p 8886:8886 my-agent
```

### Monitoring

```python
# Track usage
agent.run(message, metadata={
    "user_id": "123",
    "session_id": "abc",
    "source": "web"
})

# Monitor metrics
print(agent.metrics.total_queries)
print(agent.metrics.avg_response_time)
print(agent.metrics.error_rate)
```

## 📚 Next Steps

1. **Run Examples** - Try each agent, see what they do
2. **Modify Configs** - Change instructions, tools, models
3. **Create Your Own** - Use templates in `hive/scaffolder/templates/`
4. **Share Back** - Submit your examples as PRs!

## 🤝 Contributing

Have a great example agent? Share it!

```bash
# 1. Create your example
cp -r examples/agents/support-bot examples/agents/my-agent

# 2. Customize config and README
# ... make your changes ...

# 3. Test and validate
hive validate examples/agents/my-agent/config.yaml

# 4. Submit PR
git add examples/agents/my-agent
git commit -m "Add my-agent example"
git push
```

## 📖 Learn More

- [Agent Configuration Guide](../docs/agents.md)
- [Tool Integration](../docs/tools.md)
- [Knowledge Bases](../docs/knowledge.md)
- [Teams & Workflows](../docs/teams-workflows.md)
- [Deployment Guide](../docs/deployment.md)

---

**Built something cool?** Share it! Open a PR or discussion.

**Need help?** Check the docs or open an issue.

**Have feedback?** We'd love to hear it!
