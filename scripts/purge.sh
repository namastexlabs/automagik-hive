#!/bin/bash
set -e

echo "🗑️ Full purge script started - main infrastructure"

# Stop main services
echo "🐳 Stopping main Docker containers..."
docker compose -f docker-compose.yml down 2>/dev/null || true


echo "🗑️ Removing all containers..."
docker container rm hive-api hive-postgres 2>/dev/null || true

echo "🖼️ Removing Docker images..."
docker image rm hive-api 2>/dev/null || true

echo "💾 Removing all volumes..."
docker volume rm automagik-hive_app_logs 2>/dev/null || true
docker volume rm automagik-hive_app_data 2>/dev/null || true

echo "🔄 Stopping all local processes..."
if pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then
    pkill -f "python.*api/serve.py" 2>/dev/null || true
    echo "  Stopped development server"
else
    echo "  No development server running"
fi


echo "📁 Removing directories and environment files..."
rm -rf .venv/ logs/ 2>/dev/null || true

echo "🗑️ Removing PostgreSQL data (with Docker)..."
if [ -d "./data/postgres" ]; then
    # Use Docker to remove data with proper permissions
    docker run --rm -v "$(pwd)/data:/data" --entrypoint="" postgres:16 sh -c "rm -rf /data/*" 2>/dev/null || true
    rmdir ./data 2>/dev/null || true
    echo "  Removed main database data"
else
    rm -rf ./data/ 2>/dev/null || true
    echo "  Removed data directory"
fi

echo "✅ Full purge complete - all main infrastructure deleted"