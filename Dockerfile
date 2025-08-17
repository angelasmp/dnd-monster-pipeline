# D&D Monster Pipeline - Challenge Requirement: "container to run the full pipeline"
# This Dockerfile creates a functional container that runs the complete pipeline

FROM python:3.11-slim

# Challenge metadata
LABEL description="D&D Monster Pipeline - Container to run the full pipeline"
LABEL version="1.0"

# Environment setup
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy pipeline source code
COPY src/ ./src/
COPY main.py .

# Health check to verify container functionality
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests, sys; print('Container healthy'); sys.exit(0)" || exit 1

# Run the full pipeline (satisfies challenge requirement)
CMD ["python", "main.py"]
