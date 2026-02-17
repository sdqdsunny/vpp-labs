# VPP Protocol Analyzer Docker Image
# Captures and analyzes industrial control protocol traffic

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tcpdump \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy analyzer code
COPY main.py .

# Copy MQTT publisher (from fuxa-integration directory)
COPY mqtt-publisher.py .

# Create output directory
RUN mkdir -p /pcap /var/log/vpp

# Set permissions
RUN chmod +x main.py

# Set environment variables
ENV CAPTURE_INTERFACE=veth-analyzer
ENV OUTPUT_DIR=/pcap
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run analyzer
ENTRYPOINT ["python", "main.py"]
