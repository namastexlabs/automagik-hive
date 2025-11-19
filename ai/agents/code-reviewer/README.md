# Code Reviewer

Code review agent that analyzes code quality, suggests improvements, checks for bugs, and follows best practices. Focus on Python code.

## Configuration

- **Model**: claude-sonnet-4-20250514
- **Tools**: PythonTools, FileTools
- **Temperature**: 0.7

## Usage

```python
from agent import get_code_reviewer_agent

# Create agent
agent = get_code_reviewer_agent()

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
