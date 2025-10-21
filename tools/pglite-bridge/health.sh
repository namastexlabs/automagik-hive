#!/bin/bash
# Check PGlite Bridge Health

set -e

PORT="${PGLITE_PORT:-5532}"

if curl -f -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
    echo "✓ PGlite bridge is healthy (port $PORT)"
    exit 0
else
    echo "✗ PGlite bridge is not responding (port $PORT)"
    exit 1
fi
