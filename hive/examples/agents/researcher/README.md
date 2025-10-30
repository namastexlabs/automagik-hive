# Researcher

Web research agent that searches for information, synthesizes findings, and provides comprehensive summaries with sources.

## Configuration

- **Model**: gpt-4o
- **Tools**: PythonTools, FileTools
- **Temperature**: 0.7

## Usage

```python
from agent import get_researcher_agent

# Create agent
agent = get_researcher_agent()

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
