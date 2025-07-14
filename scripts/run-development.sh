#!/bin/bash
# Start the server in development mode

echo "🎮 Starting PagBank Development Server..."
echo "📍 URL: http://localhost:9888"
echo "📋 Mode: Development"
echo ""

# Set development environment
export ENVIRONMENT=development

# Run unified server
uv run python api/serve.py