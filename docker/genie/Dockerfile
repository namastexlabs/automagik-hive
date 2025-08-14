# =============================================================================
# Genie All-in-One Container: PostgreSQL + FastAPI Multi-Stage Build
# =============================================================================
#
# Multi-stage build combining:
# 1. PostgreSQL with pgvector extension (agnohq/pgvector:16)
# 2. Python FastAPI application with UV ecosystem
# 3. Supervisord process management for coordination
#
# Target: Single container for Genie consultation service
# External Port: 45886 (FastAPI)
# Internal Port: 5432 (PostgreSQL)
# Database: hive_genie
#
# =============================================================================

# ============================================================================
# STAGE 1: UV Dependencies Builder (reuse existing pattern)
# ============================================================================
FROM python:3.11-slim as builder

# Install UV from official source
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files and README for package build
COPY pyproject.toml uv.lock README.md ./

# Install dependencies with UV sync (production only, no dev dependencies) + BuildKit cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ============================================================================
# STAGE 2: PostgreSQL Base with pgvector
# ============================================================================
FROM agnohq/pgvector:16 as postgres-base

# Install additional PostgreSQL tools and utilities
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STAGE 3: Genie Production - Unified PostgreSQL + FastAPI
# ============================================================================
FROM postgres-base as genie-production

# Build metadata labels for enterprise tracking
LABEL org.opencontainers.image.title="Automagik Hive Genie All-in-One"
LABEL org.opencontainers.image.description="Genie consultation service with integrated PostgreSQL"
LABEL org.opencontainers.image.vendor="Automagik"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.service="genie-consultation"

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python3 -> python3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Copy UV from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy Python virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Create application user and fix permissions
RUN groupadd --gid 1000 hive \
    && useradd --uid 1000 --gid hive --shell /bin/bash --create-home hive \
    && chown -R hive:hive /app/.venv

# Set working directory and create necessary directories
WORKDIR /app
RUN mkdir -p /app/logs /app/data /app/uploads \
    && chown -R hive:hive /app/logs /app/data /app/uploads \
    && chown hive:hive /app

# Copy application files with proper ownership
COPY --chown=hive:hive pyproject.toml uv.lock README.md ./
COPY --chown=hive:hive alembic.ini ./  
COPY --chown=hive:hive alembic/ ./alembic/
COPY --chown=hive:hive lib/ ./lib/
COPY --chown=hive:hive ai/ ./ai/
COPY --chown=hive:hive api/ ./api/
COPY --chown=hive:hive common/ ./common/
COPY --chown=hive:hive scripts/ ./scripts/
COPY --chown=hive:hive logging_whitelist.yaml ./

# Create supervisord configuration
RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor \
    && chown -R hive:hive /var/log/supervisor

# Supervisord main configuration
COPY --chown=hive:hive <<EOF /etc/supervisor/supervisord.conf
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700
username=hive
password=genie_supervisor

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock
username=hive
password=genie_supervisor

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[include]
files = /etc/supervisor/conf.d/*.conf
EOF

# PostgreSQL service configuration for supervisord
COPY --chown=hive:hive <<EOF /etc/supervisor/conf.d/postgresql.conf
[program:postgresql]
command=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data/pgdata -c config_file=/etc/postgresql/16/main/postgresql.conf
user=postgres
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/postgresql.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PGDATA="/var/lib/postgresql/data/pgdata"
EOF

# FastAPI application service configuration for supervisord
COPY --chown=hive:hive <<EOF /etc/supervisor/conf.d/fastapi.conf
[program:fastapi]
command=/app/.venv/bin/python api/serve.py
directory=/app
user=hive
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/fastapi.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="/app/.venv/bin:%(ENV_PATH)s",HIVE_API_PORT="45886",HIVE_DATABASE_URL="postgresql+psycopg://%(ENV_POSTGRES_USER)s:%(ENV_POSTGRES_PASSWORD)s@localhost:5432/%(ENV_POSTGRES_DB)s"
EOF

# PostgreSQL initialization script
COPY --chown=postgres:postgres <<EOF /docker-entrypoint-initdb.d/01-init-genie.sql
-- Genie database initialization
CREATE DATABASE hive_genie;
CREATE USER genie WITH ENCRYPTED PASSWORD 'genie';
GRANT ALL PRIVILEGES ON DATABASE hive_genie TO genie;

-- Connect to genie database and set up extensions
\c hive_genie

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant permissions on extensions
GRANT ALL ON SCHEMA public TO genie;
EOF

# Set PostgreSQL data directory permissions
RUN mkdir -p /var/lib/postgresql/data/pgdata \
    && chown -R postgres:postgres /var/lib/postgresql \
    && chmod 750 /var/lib/postgresql/data/pgdata

# Port configuration
ARG API_PORT=45886
ENV HIVE_API_PORT=${API_PORT}

# Expose ports
EXPOSE ${API_PORT}
EXPOSE 5432

# Health check for both services
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD pg_isready -U ${POSTGRES_USER:-genie} -d ${POSTGRES_DB:-hive_genie} && \
        curl -f http://localhost:${HIVE_API_PORT:-45886}/api/v1/health || exit 1

# Container startup script
COPY --chown=root:root <<EOF /usr/local/bin/genie-startup.sh
#!/bin/bash
set -e

echo "🧞 Starting Genie All-in-One Container..."

# Initialize PostgreSQL if needed
if [ ! -f "/var/lib/postgresql/data/pgdata/PG_VERSION" ]; then
    echo "🗄️ Initializing PostgreSQL database..."
    su postgres -c "initdb -D /var/lib/postgresql/data/pgdata"
    
    # Start PostgreSQL temporarily for initialization
    su postgres -c "pg_ctl -D /var/lib/postgresql/data/pgdata -l /tmp/pg_init.log start"
    
    # Wait for PostgreSQL to be ready
    while ! pg_isready -U postgres; do
        echo "⏳ Waiting for PostgreSQL to be ready..."
        sleep 2
    done
    
    # Run initialization scripts
    if [ -d "/docker-entrypoint-initdb.d" ]; then
        for f in /docker-entrypoint-initdb.d/*; do
            echo "🔧 Running initialization script: \$f"
            su postgres -c "psql -f \$f"
        done
    fi
    
    # Stop temporary PostgreSQL
    su postgres -c "pg_ctl -D /var/lib/postgresql/data/pgdata stop"
fi

echo "🚀 Starting services with supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
EOF

RUN chmod +x /usr/local/bin/genie-startup.sh

# Production startup using supervisord for multi-service management
CMD ["/usr/local/bin/genie-startup.sh"]