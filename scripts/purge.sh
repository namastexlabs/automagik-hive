#!/bin/bash
set -e

echo "🗑️ Full purge script started"

# Stop services
echo "🐳 Stopping Docker containers..."
docker compose -f docker-compose.yml down 2>/dev/null || true

echo "🗑️ Removing containers..."
docker container rm hive-agents hive-postgres 2>/dev/null || true

echo "🗑️ Removing volumes..."
docker volume rm automagik-hive_app_logs 2>/dev/null || true
docker volume rm automagik-hive_app_data 2>/dev/null || true

echo "🗑️ Stopping local processes..."
if pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then
    pkill -f "python.*api/serve.py" 2>/dev/null || true
    echo "  Stopped development server"
else
    echo "  No development server running"
fi

echo "🗑️ Removing directories..."
rm -rf .venv/ logs/ 2>/dev/null || true

echo "🗑️ Removing PostgreSQL data (with Docker)..."
if [ -d "./data/postgres" ]; then
    docker run --rm -v "$(pwd)/data:/data" --entrypoint="" postgres:16 sh -c "rm -rf /data/*" 2>/dev/null || true
    rmdir ./data 2>/dev/null || true
else
    rm -rf ./data/ 2>/dev/null || true
fi

echo "✅ Full purge complete - all data deleted"