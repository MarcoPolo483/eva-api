# Multi-stage Docker build for EVA API Platform
# Stage 1: Builder - Install dependencies and build
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Minimal image with application
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash evaapi

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/evaapi/.local

# Copy application code
COPY src/eva_api ./eva_api

# Set ownership
RUN chown -R evaapi:evaapi /app

# Switch to non-root user
USER evaapi

# Add local bin to PATH
ENV PATH=/home/evaapi/.local/bin:$PATH

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "eva_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
