# VPP Master Docker镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括编译工具、网络工具和 CAN 工具）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    cmake \
    build-essential \
    iproute2 \
    can-utils \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 复制bottle-framework (if needed)
# COPY ../bottle-framework ./bottle-framework

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 编译并安装 OpenDNP3
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

# 创建 Python dnp3 包装器
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

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
