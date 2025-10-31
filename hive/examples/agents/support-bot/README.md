# Support Bot

Customer support agent with CSV knowledge base and web search capabilities. Handles FAQs, searches web for complex issues, and escalates when needed.

## Configuration

- **Model**: gpt-4o
- **Tools**: FileTools
- **Temperature**: 0.7

## Usage

```python
from agent import get_support_bot_agent

# Create agent
agent = get_support_bot_agent()

# Run query
response = agent.run("Your query here")
print(response.content)
```

## Testing

```bash
python agent.py
```

## Generated

This agent was generated using Automagik Hive's meta-agent generator with REAL AI.
