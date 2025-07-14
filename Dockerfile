# Multi-stage Docker build for production deployment
# Enterprise-grade container with security and performance optimizations

# Build stage - Use official Python slim image for minimal attack surface
FROM python:3.12-slim as builder

# Set build arguments for flexibility
ARG BUILD_VERSION=latest
ARG BUILD_DATE
ARG GIT_SHA

# Install build dependencies and security updates
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install UV for fast dependency management
RUN pip install --no-cache-dir uv==0.4.18

# Set working directory
WORKDIR /app

# Copy dependency files first for better cache utilization
COPY pyproject.toml uv.lock ./

# Install dependencies in virtual environment
RUN uv venv /opt/venv && \
    uv pip install --no-cache-dir -r uv.lock

# Production stage - Minimal runtime image
FROM python:3.12-slim as production

# Build metadata labels for enterprise tracking
LABEL org.opencontainers.image.title="PagBank Multi-Agent System"
LABEL org.opencontainers.image.description="Enterprise-grade multi-agent AI system for customer service"
LABEL org.opencontainers.image.version=${BUILD_VERSION}
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.revision=${GIT_SHA}
LABEL org.opencontainers.image.vendor="Automagik"
LABEL org.opencontainers.image.licenses="MIT"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    RUNTIME_ENV=prd \
    POSTGRES_POOL_SIZE=20 \
    POSTGRES_MAX_OVERFLOW=30 \
    API_WORKERS=4

# Set working directory and copy application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/uploads && \
    chown -R appuser:appuser /app

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Expose port for the application
EXPOSE 8000

# Production startup command with proper process management
CMD ["python", "-m", "uvicorn", "api.serve:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--log-level", "info", \
     "--access-log", \
     "--no-server-header"]