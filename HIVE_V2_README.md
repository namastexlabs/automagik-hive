# Hive V2 - Foundation Infrastructure

This document describes the new Hive V2 infrastructure built from scratch.

## What's New

Hive V2 is a complete redesign focusing on:
- **UVX CLI**: Install and run with `uvx automagik-hive`
- **Project Scaffolding**: `hive init` creates new projects
- **AI-Powered Generation**: `hive create` generates components
- **Hot Reload Dev Server**: `hive dev` with automatic reloading
- **Minimal Dependencies**: 20 essential environment variables (not 145!)
- **YAML-First Config**: Simple, declarative configuration

## Installation

### As a Tool (Recommended)
```bash
# Run directly with uvx (no installation needed)
uvx automagik-hive init my-project

# Or install globally
uv pip install automagik-hive
```

### Development
```bash
# Clone and install
git clone https://github.com/namastexlabs/automagik-hive
cd automagik-hive
uv sync
```

## Quick Start

### 1. Create a New Project
```bash
# Initialize new project
hive init my-project

# Navigate to project
cd my-project
```

### 2. Configure Environment
```bash
# Copy example environment
cp .env.example .env

# Add your API keys
# Edit .env and add:
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### 3. Start Development Server
```bash
# Start with hot reload
hive dev

# API available at: http://localhost:8886
# Docs available at: http://localhost:8886/docs
```

### 4. Create Components
```bash
# Create an agent
hive create agent customer-support --description "Helpful customer support agent"

# Create a team
hive create team support-team --mode route

# Create a workflow
hive create workflow onboarding --description "User onboarding workflow"

# Create a tool
hive create tool slack-notifier --description "Send Slack notifications"
```

## Project Structure

```
my-project/
├── ai/                           # All AI components
│   ├── agents/
│   │   ├── examples/             # Built-in examples
│   │   │   └── support-bot/
│   │   └── customer-support/     # Your agents
│   ├── teams/
│   │   └── support-team/         # Your teams
│   ├── workflows/
│   │   └── onboarding/           # Your workflows
│   └── tools/
│       └── slack-notifier/       # Your tools
├── data/
│   ├── csv/                      # CSV knowledge bases
│   ├── documents/                # Document stores
│   └── embeddings/               # Vector embeddings
├── .env                          # Environment config
├── hive.yaml                     # Project config
└── README.md
```

## CLI Commands

### Project Management
```bash
hive init <project-name>          # Create new project
hive init <name> --path /custom   # Custom location
```

### Component Creation
```bash
# Agents
hive create agent <name> --description "..." --model gpt-4o-mini

# Teams
hive create team <name> --mode route|coordinate|collaborate

# Workflows
hive create workflow <name> --description "..."

# Tools
hive create tool <name> --description "..."
```

### Development
```bash
hive dev                          # Start dev server (default port 8886)
hive dev --port 3000              # Custom port
hive dev --no-reload              # Disable hot reload
```

### Utilities
```bash
hive version show                 # Show version info
```

## Configuration

### Environment Variables (20 Core Settings)

```bash
# Environment
HIVE_ENVIRONMENT=development
HIVE_DEBUG=true

# API
HIVE_API_PORT=8886
HIVE_API_HOST=0.0.0.0
HIVE_CORS_ORIGINS=*

# Database
HIVE_DATABASE_URL=postgresql+psycopg://hive:hive@localhost:5532/automagik_hive

# AI Providers (at least one required)
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
COHERE_API_KEY=your_key

# Models
HIVE_DEFAULT_MODEL=gpt-4o-mini
HIVE_EMBEDDER_MODEL=text-embedding-3-small

# Logging
HIVE_LOG_LEVEL=INFO
AGNO_LOG_LEVEL=WARNING

# Features
HIVE_ENABLE_METRICS=true
HIVE_ENABLE_AGUI=false
```

### Project Config (hive.yaml)

```yaml
project:
  name: "my-project"
  version: "1.0.0"

agents:
  discovery_path: "ai/agents"
  examples_enabled: true

teams:
  discovery_path: "ai/teams"

workflows:
  discovery_path: "ai/workflows"

knowledge:
  csv_path: "data/csv"
  auto_reload: true
```

## Agent Example

### Create Agent
```bash
hive create agent support-bot --description "Customer support agent"
```

### Generated Files

**ai/agents/support-bot/config.yaml**:
```yaml
agent:
  name: "Support Bot"
  agent_id: "support-bot"
  version: "1.0.0"

model:
  provider: "openai"
  id: "gpt-4o-mini"
  temperature: 0.7

instructions: |
  You are a helpful customer support agent...

storage:
  table_name: "support_bot_sessions"
```

**ai/agents/support-bot/agent.py**:
```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_support_bot_agent(**kwargs) -> Agent:
    # Load config and create agent
    ...
```

## Development Workflow

### 1. Local Development
```bash
# Start dev server
hive dev

# Server watches for changes in ai/
# Automatically reloads on file changes
```

### 2. Test Components
```bash
# Via API
curl http://localhost:8886/docs

# Via Python
python -c "from ai.agents.support_bot.agent import get_support_bot_agent; agent = get_support_bot_agent(); print(agent.run('Hello'))"
```

### 3. Iterate
- Edit config.yaml to update instructions
- Modify agent.py for custom logic
- Add tools, knowledge bases, etc.

## Hive Package Structure

The core `hive` package provides:

```
hive/
├── cli/              # CLI commands
│   ├── init.py       # Project initialization
│   ├── create.py     # Component generation
│   ├── dev.py        # Dev server
│   └── version.py    # Version info
├── api/              # FastAPI app
│   └── app.py        # Minimal API with health check
├── config/           # Configuration
│   ├── settings.py   # 20 essential env vars
│   └── defaults.py   # Sensible defaults
└── scaffolder/       # Templates
    └── templates/
        └── project/  # Project scaffold
```

## Next Steps

After setting up your project:

1. **Add Knowledge**: Place CSV files in `data/csv/` for RAG
2. **Customize Agents**: Edit `config.yaml` and instructions
3. **Create Tools**: Build reusable tools in `ai/tools/`
4. **Build Teams**: Coordinate multiple agents with routing
5. **Design Workflows**: Create multi-step processes

## Migration from V1

If you're using the old Automagik Hive:
1. Both versions can coexist
2. V1 code is in `ai/`, `api/`, `lib/`
3. V2 code is in `hive/` package
4. Projects created with `hive init` are V2-native

## Testing

```bash
# Run V2 infrastructure tests
uv run pytest tests/hive_v2/ -v

# Test CLI commands
uv run python -c "from hive.cli import app; app(['version', 'show'], standalone_mode=False)"
```

## Documentation

- **Full Docs**: https://docs.automagik-hive.dev
- **Agno Framework**: https://docs.agno.com
- **Examples**: See `hive/scaffolder/templates/project/`

## Support

- **GitHub Issues**: https://github.com/namastexlabs/automagik-hive/issues
- **Documentation**: https://docs.automagik-hive.dev

## License

MIT License - See LICENSE file for details
