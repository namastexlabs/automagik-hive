# Genie Local CLI

A TypeScript-based CLI chat application for interacting with local multi-agent APIs, built using the Gemini CLI as a boilerplate and stripped down to focus on local API integration.

## Features

- 🎯 **Multi-Target Support**: Connect to agents, teams, and workflows
- 🔄 **Real-time Streaming**: Live response streaming with visual indicators
- 💾 **Session Management**: Persistent conversation history
- ⚙️ **Environment Configuration**: All settings via .env files
- 🎨 **Rich UI**: Beautiful terminal interface with React components
- 🔌 **Hot Reload**: Development mode with instant feedback

## Prerequisites

- Node.js >= 20
- Local multi-agent API server running (default: http://localhost:9888)

## Installation

```bash
# Clone or navigate to the project
cd /path/to/genie-agents/chat/genie-local-cli

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Edit configuration as needed
nano .env
```

## Configuration

All configuration is done via environment variables in the `.env` file:

```bash
# API Server Configuration
API_BASE_URL=http://localhost:9888
API_TIMEOUT=30000
API_RETRY_ATTEMPTS=3

# WebSocket Configuration
WS_URL=ws://localhost:9888/ws
WS_RECONNECT_ATTEMPTS=5
WS_RECONNECT_DELAY=1000

# CLI Configuration
CLI_NAME=genie-cli
CLI_VERSION=0.1.0
CLI_DEBUG=false

# Session Configuration
SESSION_DIR=~/.genie-cli/sessions
SESSION_MAX_HISTORY=100
SESSION_AUTO_SAVE=true

# Display Configuration
ENABLE_COLORS=true
ENABLE_SPINNER=true
STREAM_DELAY=50
MAX_DISPLAY_WIDTH=120
```

## Usage

### Development Mode

```bash
# Start in development mode with hot reload
npm run dev

# Or manually
npm run start
```

### Production Mode

```bash
# Build the application
npm run build

# Run in production mode
NODE_ENV=production npm run start

# Or run the bundle directly
./bundle/genie-cli.js
```

### CLI Controls

- **Type messages**: Chat with the selected agent/team/workflow
- **Ctrl+H**: Toggle help
- **Ctrl+L**: Clear screen
- **Ctrl+C or Ctrl+D** (twice): Exit
- **Enter**: Send message
- **Arrow keys**: Navigate input history

## API Integration

The CLI automatically discovers and connects to:

- **Agents**: Individual AI agents at `/agents`
- **Teams**: Agent teams with routing at `/teams`  
- **Workflows**: Automated workflows at `/workflows`

### Required API Endpoints

Your local API server should provide:

```
GET  /openapi.json       # OpenAPI schema
GET  /health             # Health check
GET  /agents             # List available agents
GET  /teams              # List available teams
GET  /workflows          # List available workflows

POST /agents/{id}/runs   # Invoke agent
POST /teams/{id}/runs    # Invoke team
POST /workflows/{id}/runs # Execute workflow
```

### Response Format

Expected response format:

```json
{
  "data": "response content",
  "error": null,
  "session_id": "session-123"
}
```

## Development

### Project Structure

```
src/
├── config/
│   ├── settings.ts      # Environment configuration
│   └── localClient.ts   # API client
├── ui/
│   ├── App.tsx          # Main application
│   ├── types.ts         # Type definitions
│   ├── components/      # React components
│   ├── contexts/        # React contexts
│   └── hooks/           # Custom hooks
└── index.ts             # Entry point
```

### Building

```bash
# Clean build
npm run clean

# TypeScript compilation
npm run typecheck

# Create bundle
npm run bundle

# Full build process
npm run build
```

### Key Components

- **App.tsx**: Main application with session management
- **localClient.ts**: HTTP client for API communication
- **useLocalAPIStream**: Streaming hook for real-time responses
- **SessionContext**: Persistent conversation management
- **StreamingContext**: Real-time state management

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check API server is running at configured URL
   - Verify `.env` configuration
   - Check network connectivity

2. **Build Errors**
   - Ensure Node.js >= 20
   - Run `npm install` to update dependencies
   - Check TypeScript compilation with `npm run typecheck`

3. **Streaming Issues**
   - Verify API supports streaming responses
   - Check WebSocket URL configuration
   - Enable debug mode for detailed logs

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env file
CLI_DEBUG=true

# Or via environment variable
CLI_DEBUG=true npm run dev
```

## Session Management

Sessions are automatically saved to `~/.genie-cli/sessions/` as JSON files:

```json
{
  "id": "session-123",
  "messages": [...],
  "createdAt": 1641234567890,
  "updatedAt": 1641234567890,
  "metadata": {
    "totalMessages": 10,
    "lastTarget": {
      "type": "agent",
      "id": "emissao"
    }
  }
}
```

## Contributing

This CLI was built by stripping down the Gemini CLI and replacing Gemini-specific functionality with local API integration. Key changes:

- Removed Google authentication
- Replaced Gemini API with local HTTP client
- Simplified command system
- Added environment-based configuration
- Preserved React-based UI framework

## License

Based on the Gemini CLI (Apache 2.0), modified for local API integration.