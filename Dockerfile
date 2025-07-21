# 🚀 Blazing Fast UV-Native Multi-Stage Docker Build
# Modern Python deployment with Astral.sh UV ecosystem

# ============================================================================
# STAGE 1: UV Dependencies Builder 
# ============================================================================
FROM python:3.12-slim as builder

# Install UV from official source
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files and README for package build
COPY pyproject.toml uv.lock README.md ./

# Install dependencies with UV sync (production only, no dev dependencies)
RUN uv sync --frozen --no-dev --no-cache

# ============================================================================
# STAGE 2: Production Runtime
# ============================================================================
FROM python:3.12-slim as production

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

# Create non-root user for security
RUN groupadd --gid 1000 hive \
    && useradd --uid 1000 --gid hive --shell /bin/bash --create-home hive

# Set working directory and copy application code
WORKDIR /app
COPY --chown=hive:hive . .

# Create necessary directories with proper ownership
RUN mkdir -p /app/logs /app/data /app/uploads \
    && chown -R hive:hive /app

# Switch to non-root user
USER hive

# Expose port for the application
EXPOSE 9888

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9888/api/v1/health', timeout=5)" || exit 1

# Production startup command using UV
CMD ["uv", "run", "python", "api/serve.py"]