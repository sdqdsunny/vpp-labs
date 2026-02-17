FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including protocol libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    postgresql-client \
    curl \
    git \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install protocol library dependencies
# pymodbus - already in requirements.txt
# paho-mqtt - already in requirements.txt
# libiec61850 and opendnp3 are optional C/C++ libraries
# They can be installed if needed, but Python bindings are available via pip

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "app.py"]
