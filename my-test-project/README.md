# my-test-project

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
my-test-project/
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
hive create agent my-agent --description "My custom agent"
hive create team my-team --mode route
hive create workflow my-workflow
```

## Documentation

- [Hive V2 Docs](https://docs.automagik-hive.dev)
- [Agno Framework](https://docs.agno.com)
