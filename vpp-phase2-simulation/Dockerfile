FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including OpenDNP3 build tools, CAN tools, and network tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iputils-ping \
    net-tools \
    dnsutils \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    git \
    cmake \
    gcc \
    g++ \
    make \
    iproute2 \
    can-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Compile and install OpenDNP3
RUN cd /tmp && \
    git clone https://github.com/dnp3/opendnp3.git && \
    cd opendnp3 && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j4 && \
    make install && \
    ldconfig && \
    cd / && \
    rm -rf /tmp/opendnp3

# Create Python dnp3 wrapper for detection
RUN cat > /usr/local/lib/python3.11/site-packages/dnp3.py << 'EOF'
"""
OpenDNP3 Python wrapper
Provides basic detection and interface for OpenDNP3 library
"""

import ctypes
import os

# Try to load the opendnp3 shared library
_lib_path = '/usr/local/lib/libopendnp3.so'

if os.path.exists(_lib_path):
    try:
        _dnp3_lib = ctypes.CDLL(_lib_path)
        AVAILABLE = True
    except Exception as e:
        AVAILABLE = False
else:
    AVAILABLE = False

__version__ = '3.0.0'
__all__ = ['AVAILABLE']
EOF

# Copy application code
COPY . .

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
