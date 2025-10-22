#!/bin/bash
# Stop PGlite Bridge Server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f pglite-bridge.pid ]; then
    echo "PGlite bridge is not running (no PID file)"
    exit 0
fi

PID=$(cat pglite-bridge.pid)

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Stopping PGlite bridge (PID: $PID)..."
    kill -TERM "$PID"

    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "✓ PGlite bridge stopped"
            rm -f pglite-bridge.pid
            exit 0
        fi
        sleep 1
    done

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Force killing PGlite bridge..."
        kill -9 "$PID"
    fi
fi

rm -f pglite-bridge.pid
echo "✓ PGlite bridge stopped"
