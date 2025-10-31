# {PROJECT_NAME}

Hive V2 AI agent project.

## Getting Started

1. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

2. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Add your API keys

3. **Start development server**:
   ```bash
   hive dev
   ```

## Project Structure

```
{PROJECT_NAME}/
├── ai/                    # AI components
│   ├── agents/           # Agent definitions
│   ├── teams/            # Team definitions
│   ├── workflows/        # Workflow definitions
│   └── tools/            # Custom tools
├── data/                 # Knowledge bases
│   ├── csv/             # CSV knowledge
│   └── documents/       # Document stores
├── .env                 # Environment config
└── hive.yaml           # Project config
```

## Creating Components

Create new agents, teams, or workflows:

```bash
# Create an agent
hive create agent my-agent --description "My custom agent"

# Create a team
hive create team my-team --mode route

# Create a workflow
hive create workflow my-workflow
```

## Development

### Start Dev Server
```bash
hive dev
```

### Test Components
```bash
# Test via API
curl http://localhost:8886/docs

# Test via Python
python -c "from ai.agents.my_agent.agent import get_my_agent; agent = get_my_agent(); print(agent.run('Hello'))"
```

## Documentation

- [Hive V2 Docs](https://docs.automagik-hive.dev)
- [Agno Framework](https://docs.agno.com)

## Support

For issues and questions:
- GitHub Issues: https://github.com/namastexlabs/automagik-hive/issues
- Documentation: https://docs.automagik-hive.dev
