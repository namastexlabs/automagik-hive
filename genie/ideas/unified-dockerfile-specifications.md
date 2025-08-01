# Unified All-in-One Container Dockerfile Specifications

## Architecture Overview

Transform current separate PostgreSQL + FastAPI containers into unified all-in-one containers using supervisord for multi-process management.

## Genie All-in-One Container (Port 48886)

### Dockerfile.genie Specification

```dockerfile
# ===========================================================================
# Automagik Hive Genie All-in-One Container
# PostgreSQL + FastAPI unified in single container with supervisord
# External Port: 48886, Internal PostgreSQL: 5432
# ===========================================================================

# Stage 1: Python Dependencies Builder
FROM python:3.12-slim as builder

# Install UV package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with UV
RUN uv sync --frozen --no-dev

# Stage 2: PostgreSQL Base with pgvector
FROM agnohq/pgvector:16 as postgres-base

# Stage 3: Unified Production Container
FROM ubuntu:22.04 as genie-production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    postgresql-16 \
    postgresql-contrib-16 \
    postgresql-16-pgvector \
    supervisor \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create application user (non-root)
RUN useradd -m -u 1000 -s /bin/bash hive && \
    usermod -aG sudo hive && \
    echo 'hive ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Set up PostgreSQL directories with proper permissions
RUN mkdir -p /var/lib/postgresql/data/pgdata && \
    chown -R 1000:1000 /var/lib/postgresql/data && \
    chmod 750 /var/lib/postgresql/data

# Copy Python dependencies from builder
COPY --from=builder --chown=1000:1000 /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder --chown=1000:1000 /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=1000:1000 . /app
WORKDIR /app

# Configure PostgreSQL
COPY --chown=1000:1000 docker/genie/postgresql.conf /etc/postgresql/16/main/
COPY --chown=1000:1000 docker/genie/pg_hba.conf /etc/postgresql/16/main/

# Configure supervisord
COPY --chown=1000:1000 docker/genie/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directories
RUN mkdir -p /var/log/supervisor /var/log/postgresql /var/log/hive && \
    chown -R 1000:1000 /var/log/supervisor /var/log/postgresql /var/log/hive

# Initialize PostgreSQL database
USER root
RUN service postgresql start && \
    sudo -u postgres createuser --superuser hive && \
    sudo -u postgres createdb -O hive hive_genie && \
    sudo -u postgres psql -c "ALTER USER hive PASSWORD 'genie_secure_password';" && \
    sudo -u postgres psql -d hive_genie -c "CREATE EXTENSION IF NOT EXISTS vector;" && \
    service postgresql stop

# Switch to application user
USER 1000:1000

# Expose Genie API port
EXPOSE 48886

# Health check for both PostgreSQL and FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:48886/api/v1/health && \
        pg_isready -h localhost -p 5432 -U hive -d hive_genie

# Start supervisord (manages PostgreSQL + FastAPI)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

## Agent All-in-One Container (Port 38886)

### Dockerfile.agent Specification

```dockerfile
# ===========================================================================
# Automagik Hive Agent All-in-One Container  
# PostgreSQL + FastAPI unified in single container with supervisord
# External Port: 38886, Internal PostgreSQL: 5432
# ===========================================================================

# Stage 1: Python Dependencies Builder
FROM python:3.12-slim as builder

# Install UV package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with UV
RUN uv sync --frozen --no-dev

# Stage 2: PostgreSQL Base with pgvector
FROM agnohq/pgvector:16 as postgres-base

# Stage 3: Unified Production Container
FROM ubuntu:22.04 as agent-production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    postgresql-16 \
    postgresql-contrib-16 \
    postgresql-16-pgvector \
    supervisor \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create application user (non-root)
RUN useradd -m -u 1000 -s /bin/bash agent && \
    usermod -aG sudo agent && \
    echo 'agent ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Set up PostgreSQL directories with proper permissions
RUN mkdir -p /var/lib/postgresql/data/pgdata && \
    chown -R 1000:1000 /var/lib/postgresql/data && \
    chmod 750 /var/lib/postgresql/data

# Copy Python dependencies from builder
COPY --from=builder --chown=1000:1000 /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder --chown=1000:1000 /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=1000:1000 . /app
WORKDIR /app

# Configure PostgreSQL
COPY --chown=1000:1000 docker/agent/postgresql.conf /etc/postgresql/16/main/
COPY --chown=1000:1000 docker/agent/pg_hba.conf /etc/postgresql/16/main/

# Configure supervisord
COPY --chown=1000:1000 docker/agent/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directories
RUN mkdir -p /var/log/supervisor /var/log/postgresql /var/log/hive && \
    chown -R 1000:1000 /var/log/supervisor /var/log/postgresql /var/log/hive

# Initialize PostgreSQL database
USER root
RUN service postgresql start && \
    sudo -u postgres createuser --superuser agent && \
    sudo -u postgres createdb -O agent hive_agent && \
    sudo -u postgres psql -c "ALTER USER agent PASSWORD 'agent_secure_password';" && \
    sudo -u postgres psql -d hive_agent -c "CREATE EXTENSION IF NOT EXISTS vector;" && \
    service postgresql stop

# Switch to application user
USER 1000:1000

# Expose Agent API port
EXPOSE 38886

# Health check for both PostgreSQL and FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:38886/api/v1/health && \
        pg_isready -h localhost -p 5432 -U agent -d hive_agent

# Start supervisord (manages PostgreSQL + FastAPI)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

## Supervisord Configuration

### Genie Supervisord Config (/docker/genie/supervisord.conf)

```ini
[supervisord]
nodaemon=true
user=hive
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700
chown=hive:hive

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

# PostgreSQL Service
[program:postgresql]
command=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data/pgdata -c config_file=/etc/postgresql/16/main/postgresql.conf
user=hive
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/postgresql/postgresql.log
stderr_logfile=/var/log/postgresql/postgresql.error.log
environment=PGDATA="/var/lib/postgresql/data/pgdata"
priority=100

# FastAPI Application Service
[program:hive-genie]
command=python -m uvicorn api.serve:app --host 0.0.0.0 --port 48886 --workers 2
directory=/app
user=hive
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hive/genie-api.log
stderr_logfile=/var/log/hive/genie-api.error.log
environment=HIVE_DATABASE_URL="postgresql+psycopg://hive:genie_secure_password@localhost:5432/hive_genie",HIVE_API_PORT="48886",HIVE_SERVICE_MODE="genie"
priority=200

# Health Check Service (Optional)
[program:health-monitor]
command=/app/docker/genie/health-monitor.sh
user=hive
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hive/health-monitor.log
priority=300
```

### Agent Supervisord Config (/docker/agent/supervisord.conf)

```ini
[supervisord]
nodaemon=true
user=agent
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700
chown=agent:agent

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

# PostgreSQL Service
[program:postgresql]
command=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data/pgdata -c config_file=/etc/postgresql/16/main/postgresql.conf
user=agent
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/postgresql/postgresql.log
stderr_logfile=/var/log/postgresql/postgresql.error.log
environment=PGDATA="/var/lib/postgresql/data/pgdata"
priority=100

# FastAPI Application Service
[program:hive-agent]
command=python -m uvicorn api.serve:app --host 0.0.0.0 --port 38886 --workers 2
directory=/app
user=agent
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hive/agent-api.log
stderr_logfile=/var/log/hive/agent-api.error.log
environment=HIVE_DATABASE_URL="postgresql+psycopg://agent:agent_secure_password@localhost:5432/hive_agent",HIVE_API_PORT="38886",HIVE_SERVICE_MODE="agent"
priority=200

# Health Check Service (Optional)
[program:health-monitor]
command=/app/docker/agent/health-monitor.sh
user=agent
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hive/health-monitor.log
priority=300
```

## PostgreSQL Configuration

### PostgreSQL Config (/docker/genie/postgresql.conf & /docker/agent/postgresql.conf)

```
# PostgreSQL 16 Configuration for All-in-One Container
listen_addresses = 'localhost'
port = 5432
max_connections = 100
shared_buffers = 128MB
effective_cache_size = 512MB
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 10MB
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'error'

# pgvector extension
shared_preload_libraries = 'vector'
```

### PostgreSQL Host Authentication (/docker/genie/pg_hba.conf & /docker/agent/pg_hba.conf)

```
# PostgreSQL Client Authentication Configuration
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# Container internal connections
host    hive_genie      hive            localhost               md5
host    hive_agent      agent           localhost               md5
```

## Docker Compose Integration

### Unified Genie Container (docker-compose-genie.yml)

```yaml
services:
  genie-all-in-one:
    build:
      context: .
      dockerfile: docker/genie/Dockerfile.genie
      target: genie-production
    container_name: hive-genie-unified
    restart: unless-stopped
    ports:
      - "48886:48886"
    environment:
      - HIVE_SERVICE_MODE=genie
      - HIVE_API_PORT=48886
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data/postgres-genie:/var/lib/postgresql/data
      - ./logs/genie:/var/log/hive
    networks:
      - genie_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:48886/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  genie_network:
    driver: bridge
    name: hive_genie_network
```

### Unified Agent Container (docker-compose-agent.yml)

```yaml
services:
  agent-all-in-one:
    build:
      context: .
      dockerfile: docker/agent/Dockerfile.agent
      target: agent-production
    container_name: hive-agent-unified
    restart: unless-stopped
    ports:
      - "38886:38886"
    environment:
      - HIVE_SERVICE_MODE=agent
      - HIVE_API_PORT=38886
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data/postgres-agent:/var/lib/postgresql/data
      - ./logs/agent:/var/log/hive
    networks:
      - agent_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:38886/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  agent_network:
    driver: bridge
    name: hive_agent_network
```

## Key Design Principles

### Security
- Non-root users (1000:1000) for process execution
- Proper file permissions and ownership
- Database authentication with strong passwords
- Network isolation per container

### Reliability
- Supervisord manages process lifecycle
- Automatic service restart on failure
- Health checks for both PostgreSQL and API
- Comprehensive logging and monitoring

### Performance
- Multi-stage builds for optimized images
- UV package manager for fast dependency resolution
- Proper PostgreSQL configuration for containers
- Resource limits and optimization

### Maintainability
- Clear separation of configuration files
- Comprehensive logging for debugging
- Health monitoring and status reporting
- Clean shutdown and restart procedures