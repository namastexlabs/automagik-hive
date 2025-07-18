# Multi-stage Docker build for production deployment
# Using official Agno Python image with pre-installed dependencies

# Production stage - Use official Agno Python image
FROM agnohq/python:3.12 as production

# Build metadata labels for enterprise tracking
LABEL org.opencontainers.image.title="PagBank Multi-Agent System"
LABEL org.opencontainers.image.description="Enterprise-grade multi-agent AI system for customer service"
LABEL org.opencontainers.image.vendor="Automagik"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory and copy application code
WORKDIR /app
COPY . .

# Install project dependencies
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads

# Expose port for the application
EXPOSE 9888

# Production startup command
CMD ["python", "api/serve.py"]