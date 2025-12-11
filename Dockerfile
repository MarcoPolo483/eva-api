# EVA API - Azure Container Deployment
# Based on: https://learn.microsoft.com/azure/app-service/quickstart-python

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port 8000
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "eva_api.main:app", "--bind", "0.0.0.0:8000", "--timeout", "600"]
