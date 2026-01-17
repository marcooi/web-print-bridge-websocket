# =============================================================================
# Local Print Bridge - Dockerfile
# =============================================================================
# Lightweight containerized FastAPI application for bridging D365 and local printers
#
# Build: docker build -t local-print-bridge .
# Run:   docker run -p 8000:8000 -v ./app_data:/app/data local-print-bridge
# =============================================================================

# Use Python 3.9 slim image for smaller footprint
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
# - Prevent Python from writing .pyc files
# - Ensure stdout/stderr are unbuffered for real-time logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create data directory for SQLite database persistence
# This directory will be mounted as a volume in production
RUN mkdir -p /app/data

# Copy requirements first for better Docker layer caching
# (changes to other files won't invalidate the pip install layer)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY templates/ templates/

# Expose the application port
EXPOSE 8000

# Health check to monitor container status
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the FastAPI application with Uvicorn
# - host 0.0.0.0: Listen on all interfaces (required for Docker)
# - port 8000: Default application port
# - workers 1: Single worker (sufficient for this use case, SQLite doesn't support concurrent writes well)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
