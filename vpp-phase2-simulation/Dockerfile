FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iputils-ping \
    net-tools \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY vpp-phase2-simulation/ .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8080 8081 8082 8083

# Create logs directories for all services
RUN mkdir -p logs/coordinator logs/power_generation logs/battery_system logs/load_manager

# Run application based on NODE_TYPE environment variable
CMD ["./entrypoint.sh"]
