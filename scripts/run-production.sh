#!/bin/bash
# Start the server in production mode

echo "🚀 Starting PagBank Production API Server..."
echo "📍 URL: http://0.0.0.0:9888"
echo "📋 Mode: Production (clean API)"
echo ""

# Set production environment
export ENVIRONMENT=production

# Run unified server
uv run python api/serve.py