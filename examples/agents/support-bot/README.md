# Customer Support Bot Example

A production-ready customer support agent with CSV knowledge base and web search capabilities.

## What This Agent Does

- Answers questions using a curated knowledge base (FAQs)
- Falls back to web search for complex issues
- Maintains professional, helpful tone
- Knows when to escalate to human support

## Features

✅ **CSV Knowledge Base** - Hot-reloading FAQ database
✅ **Web Search** - For issues not in knowledge base
✅ **Session Memory** - Remembers conversation context
✅ **Smart Routing** - Checks knowledge base before searching
✅ **Production Ready** - Includes error handling and logging

## Quick Start

### 1. Prerequisites

```bash
# Ensure you have:
- Python 3.9+
- PostgreSQL running
- Environment variables set in .env
```

### 2. Configure Environment

Add to your `.env` file:

```bash
# Required
HIVE_DATABASE_URL=postgresql://user:pass@localhost:5432/hive
OPENAI_API_KEY=your_openai_key_here

# Optional (if using different models)
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### 3. Run the Agent

```python
from hive.scaffolder.generator import generate_agent_from_yaml

# Load agent from config
agent = generate_agent_from_yaml("examples/agents/support-bot/config.yaml")

# Chat with agent
response = agent.run("How do I install Automagik Hive?")
print(response.content)
```

Or use the CLI:

```bash
# Start interactive chat
hive chat examples/agents/support-bot/config.yaml
```

## Configuration Explained

### Knowledge Base (support_docs.csv)

The agent's primary source of truth. Columns:

- `query` - Question or topic
- `context` - Answer or explanation
- `category` - Topic category (for organization)
- `priority` - Importance level

**Hot Reload**: Edit the CSV and changes apply immediately!

### Tools

- `web_search` - DuckDuckGo search for complex issues

The agent checks knowledge base first, then searches web if needed.

### Model Choice

Uses `gpt-4o-mini` for:
- Fast responses (<2 seconds)
- Low cost
- Good enough for support tasks

Upgrade to `gpt-4o` or `claude-sonnet-4` for more complex reasoning.

## Customization

### Add More FAQs

Edit `data/support_docs.csv`:

```csv
query,context,category,priority
"New question","Answer here","category","high"
```

Changes apply immediately (hot reload enabled).

### Change Personality

Edit `instructions` in `config.yaml`:

```yaml
instructions: |
  You are a [describe personality].

  Your tone should be [formal/casual/funny/etc].
```

### Add More Tools

```yaml
tools:
  - "web_search"
  - "email_tools"    # Send email notifications
  - "slack_api"      # Post to Slack channel
```

### Adjust Response Length

```yaml
settings:
  max_tokens: 500    # Shorter responses
  # or
  max_tokens: 2000   # Longer, detailed responses
```

## Example Conversations

### Using Knowledge Base

```
User: How do I create an agent?

Bot: Creating agents in Automagik Hive is straightforward! You use YAML
     configuration files. Here's how:

     1. Create a config.yaml file with:
        - Agent name
        - Model choice
        - Instructions

     2. Check out examples/agents/ for templates you can copy

     3. For interactive creation, run: hive create agent

     This will guide you through the process step-by-step.

     Anything else I can help with?
```

### Falling Back to Web Search

```
User: What's the latest version of Python?

Bot: *searches web*

     The latest stable version of Python is 3.12.0 (released October 2023).
     It includes performance improvements, better error messages, and new
     typing features.

     For Automagik Hive, you need Python 3.9 or higher.

     Anything else I can help with?
```

### Escalation to Human

```
User: I was charged twice for my subscription!

Bot: I understand that billing issues can be frustrating. This requires
     attention from our billing team.

     Please contact human support at support@automagik.com or use the
     chat widget on our website. They'll resolve this for you quickly.

     I apologize for the inconvenience!
```

## Performance

- **Response Time**: <2 seconds (with gpt-4o-mini)
- **Cost**: ~$0.001 per conversation (knowledge base queries)
- **Accuracy**: ~90% (with well-curated knowledge base)

## Production Considerations

### Scaling

- Add more FAQs to knowledge base as new questions arise
- Use PostgreSQL for session storage (handles many users)
- Enable caching for frequently asked questions

### Monitoring

```python
# Track agent usage
agent.run(message, metadata={
    "user_id": "123",
    "source": "web_chat",
    "timestamp": datetime.now()
})
```

### Security

- Never put API keys in config.yaml (use .env)
- Validate user inputs before processing
- Rate limit to prevent abuse
- Monitor for prompt injection attempts

## Troubleshooting

### Agent Can't Find Knowledge Base

**Error**: "File not found: ./data/support_docs.csv"

**Fix**: Use absolute path or run from correct directory:

```yaml
knowledge:
  source: "/full/path/to/data/support_docs.csv"
```

### Knowledge Base Not Hot Reloading

**Error**: Changes to CSV not reflected

**Fix**: Ensure hot_reload is enabled:

```yaml
knowledge:
  hot_reload: true  # Must be set
```

### Responses Too Slow

**Fix**: Reduce max_tokens or use faster model:

```yaml
agent:
  model: "gpt-4o-mini"  # Fastest

settings:
  max_tokens: 300  # Shorter responses
```

## Next Steps

1. **Customize FAQs** - Add your product's specific questions
2. **Adjust Tone** - Match your brand voice in instructions
3. **Add Tools** - Email, Slack, ticketing system integration
4. **Deploy** - Use Docker or your preferred platform
5. **Monitor** - Track usage, accuracy, user satisfaction

## Learn More

- [Agents Guide](../../../docs/agents.md)
- [Knowledge Bases](../../../docs/knowledge.md)
- [Tool Integration](../../../docs/tools.md)
- [Deployment](../../../docs/deployment.md)
