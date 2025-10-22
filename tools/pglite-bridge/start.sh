#!/bin/bash
# Start PGlite Bridge Server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Node.js availability
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing PGlite bridge dependencies..."
    npm install --quiet
fi

# Start server in background
echo "Starting PGlite bridge on port ${PGLITE_PORT:-5532}..."
nohup node server.js > pglite-bridge.log 2>&1 &
echo $! > pglite-bridge.pid

# Wait for server to be ready
sleep 2

# Health check
if curl -f -s http://127.0.0.1:${PGLITE_PORT:-5532}/health > /dev/null 2>&1; then
    echo "✓ PGlite bridge started successfully (PID: $(cat pglite-bridge.pid))"
    exit 0
else
    echo "✗ PGlite bridge failed to start"
    if [ -f pglite-bridge.log ]; then
        echo "Last 10 lines of log:"
        tail -10 pglite-bridge.log
    fi
    exit 1
fi
