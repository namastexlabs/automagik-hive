# 🚀 Blazing Fast UV-Native Multi-Stage Docker Build
# Modern Python deployment with Astral.sh UV ecosystem

# ============================================================================
# STAGE 1: UV Dependencies Builder 
# ============================================================================
FROM python:3.12-slim as builder

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV from official source
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files and README for package build
COPY pyproject.toml uv.lock README.md ./

# Install dependencies with UV sync (production only, no dev dependencies)
RUN uv sync --frozen --no-dev

# ============================================================================
# STAGE 2: Production Runtime
# ============================================================================
FROM python:3.12-slim as production

# Install runtime dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Build metadata labels for enterprise tracking
LABEL org.opencontainers.image.title="Automagik Hive Multi-Agent System"
LABEL org.opencontainers.image.description="Enterprise-grade multi-agent AI framework"
LABEL org.opencontainers.image.vendor="Automagik"
LABEL org.opencontainers.image.licenses="MIT"

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

# Create non-root user for security and fix .venv ownership
RUN groupadd --gid 1000 hive \
    && useradd --uid 1000 --gid hive --shell /bin/bash --create-home hive \
    && chown -R hive:hive /app/.venv

# Set working directory and create necessary directories with proper ownership BEFORE copying files
WORKDIR /app
RUN mkdir -p /app/logs /app/data /app/uploads \
    && chown -R hive:hive /app/logs /app/data /app/uploads \
    && chown hive:hive /app

# Copy application files in layers for optimal cache utilization
# Copy rarely changing files first (better cache hits)
COPY --chown=hive:hive pyproject.toml uv.lock README.md ./
COPY --chown=hive:hive alembic.ini ./
COPY --chown=hive:hive alembic/ ./alembic/

# Copy library code (changes less frequently)
COPY --chown=hive:hive lib/ ./lib/

# Copy AI agents and configurations (moderate change frequency)
COPY --chown=hive:hive ai/ ./ai/

# Copy API code (changes more frequently)
COPY --chown=hive:hive api/ ./api/
COPY --chown=hive:hive common/ ./common/

# Copy remaining files
COPY --chown=hive:hive scripts/ ./scripts/
COPY --chown=hive:hive logging_whitelist.yaml ./
COPY --chown=hive:hive .mcp.json ./

# Switch to non-root user
USER hive

# Set port environment variable with default
ARG API_PORT=8886
ENV HIVE_API_PORT=${API_PORT}

# Expose port for the application  
EXPOSE ${API_PORT}

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests, os; requests.get(f'http://localhost:{os.getenv(\"HIVE_API_PORT\", \"8886\")}/api/v1/health', timeout=5)" || exit 1

# Production startup command using UV
CMD ["uv", "run", "python", "api/serve.py"]