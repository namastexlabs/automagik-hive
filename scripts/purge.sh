#!/bin/bash
set -e

echo "🗑️ Enhanced full purge script started - main + agent infrastructure"

# Stop main services
echo "🐳 Stopping main Docker containers..."
docker compose -f docker-compose.yml down 2>/dev/null || true

# Stop agent services  
echo "🤖 Stopping agent Docker containers..."
docker compose -f docker-compose-agent.yml down 2>/dev/null || true

echo "🗑️ Removing all containers..."
docker container rm hive-agents hive-postgres hive-agents-agent hive-agent-postgres 2>/dev/null || true

echo "🖼️ Removing Docker images..."
docker image rm automagik-hive-app 2>/dev/null || true

echo "💾 Removing all volumes..."
docker volume rm automagik-hive_app_logs 2>/dev/null || true
docker volume rm automagik-hive_app_data 2>/dev/null || true
docker volume rm automagik-hive_agent_app_logs 2>/dev/null || true
docker volume rm automagik-hive_agent_app_data 2>/dev/null || true

echo "🔄 Stopping all local processes..."
if pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then
    pkill -f "python.*api/serve.py" 2>/dev/null || true
    echo "  Stopped development server"
else
    echo "  No development server running"
fi

# Stop agent background processes
if [ -f "logs/agent-server.pid" ]; then
    PID=$(cat logs/agent-server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill -TERM $PID 2>/dev/null || true
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            kill -KILL $PID 2>/dev/null || true
        fi
        echo "  Stopped agent server (PID: $PID)"
    fi
    rm -f logs/agent-server.pid
else
    echo "  No agent server running"
fi

echo "📁 Removing directories and environment files..."
rm -rf .venv/ logs/ 2>/dev/null || true

echo "🗑️ Removing PostgreSQL data (with Docker)..."
if [ -d "./data/postgres" ]; then
    # Use Docker to remove data with proper permissions
    docker run --rm -v "$(pwd)/data:/data" --entrypoint="" postgres:16 sh -c "rm -rf /data/*" 2>/dev/null || true
    rmdir ./data 2>/dev/null || true
    echo "  Removed main database data (agent uses ephemeral storage)"
else
    rm -rf ./data/ 2>/dev/null || true
    echo "  Removed data directory"
fi

echo "✅ Enhanced full purge complete - all main and agent infrastructure deleted"