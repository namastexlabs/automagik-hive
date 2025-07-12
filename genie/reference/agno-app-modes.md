# Agno App Serving Modes

## Available App Types

Agno provides multiple app types for different deployment scenarios:

### 1. FastAPI App
- **Use Case**: REST API endpoints, production deployments
- **Features**: Full FastAPI integration, OpenAPI docs, async support
- **Example**: `serve.py` - Production API server

```python
from agno.app.fastapi.app import FastAPIApp

fastapi_app = FastAPIApp(
    agents=[agent1, agent2],  # Multiple agents
    teams=[team1],            # Multiple teams
    workflows=[workflow1],    # Multiple workflows
    name="My API",
    app_id="my_api",
    monitoring=True
)
```

### 2. Playground App
- **Use Case**: Development, testing, interactive UI
- **Features**: Built-in chat UI, session management, real-time updates
- **Example**: `playground.py` - Development environment

```python
from agno.app.playground.app import Playground

playground = Playground(
    agents=[agent],
    teams=[team],
    settings=PlaygroundSettings(...)
)
```

### 3. Slack App
- **Use Case**: Slack bot integration
- **Features**: Slack Events API, slash commands, interactive components

```python
from agno.app.slack.app import SlackApp

slack_app = SlackApp(
    agent=agent,
    slack_token="xoxb-...",
    signing_secret="..."
)
```

### 4. WhatsApp App
- **Use Case**: WhatsApp Business API integration
- **Features**: Message handling, media support, webhooks

```python
from agno.app.whatsapp.app import WhatsAppApp

whatsapp_app = WhatsAppApp(
    agent=agent,
    webhook_token="...",
    phone_number_id="..."
)
```

### 5. Discord App
- **Use Case**: Discord bot integration
- **Features**: Discord.py integration, slash commands, embeds

```python
from agno.app.discord.app import DiscordApp

discord_app = DiscordApp(
    agent=agent,
    bot_token="..."
)
```

### 6. AGUI (Agno UI)
- **Use Case**: Custom web UI with more control
- **Features**: Customizable frontend, WebSocket support

```python
from agno.app.agui.app import AGUIApp

agui_app = AGUIApp(
    agents=[agent],
    custom_theme={...}
)
```

## Key Differences

### Constructor Parameters
- **BaseAPIApp**: Single `agent` or `team`
- **FastAPIApp**: Multiple `agents`, `teams`, `workflows`
- **Playground**: Multiple `agents`, `teams`, `workflows`
- **Chat Apps** (Slack, WhatsApp, Discord): Single `agent` or `team`

### Deployment Patterns

1. **Production API** (FastAPI):
   ```bash
   uv run python serve.py
   ```

2. **Development** (Playground):
   ```bash
   uv run python playground.py
   ```

3. **Chat Integration** (Slack/WhatsApp/Discord):
   - Requires webhook configuration
   - Platform-specific authentication
   - Event handling setup

## PagBank Implementation

We use two modes:

1. **playground.py**: Development and testing
   - Port 7777
   - Interactive UI
   - Session persistence
   - Real-time updates

2. **serve.py**: Production API
   - Port 8880
   - REST endpoints
   - OpenAPI documentation
   - Monitoring enabled

Both use the same orchestrator but expose it differently for their use cases.