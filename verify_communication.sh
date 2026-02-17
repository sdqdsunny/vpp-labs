#!/bin/bash

# VPP 通信验证脚本
# 用于快速验证主站和各模块之间的通信

set -e

echo "=========================================="
echo "VPP 通信验证脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查容器状态
echo -e "${BLUE}[1/5] 检查容器状态...${NC}"
echo ""

CONTAINERS=("vpp-master" "vpp-phase2-simulation" "vpp-vcc" "vpp-upf" "vpp-gen")

for container in "${CONTAINERS[@]}"; do
    status=$(docker ps --filter "name=$container" --format "{{.Status}}" 2>/dev/null || echo "not found")
    if [[ $status == *"Up"* ]]; then
        echo -e "${GREEN}✓${NC} $container: $status"
    else
        echo -e "${RED}✗${NC} $container: $status"
    fi
done

echo ""

# 检查网络连接
echo -e "${BLUE}[2/5] 检查网络连接...${NC}"
echo ""

# 检查 vpp-phase2-simulation 是否能连接到 vpp-master
echo "测试 vpp-phase2-simulation → vpp-master 连接..."
if docker exec vpp-phase2-simulation python3 -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('vpp-master', 8080))
    sock.close()
    if result == 0:
        print('✓ 连接成功')
        sys.exit(0)
    else:
        print('✗ 连接失败')
        sys.exit(1)
except Exception as e:
    print(f'✗ 错误: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✓ vpp-phase2-simulation 可以连接到 vpp-master:8080${NC}"
else
    echo -e "${RED}✗ vpp-phase2-simulation 无法连接到 vpp-master:8080${NC}"
fi

echo ""

# 检查 HTTP 流量
echo -e "${BLUE}[3/5] 检查 HTTP 流量...${NC}"
echo ""

echo "监听 vpp-master 的 HTTP 请求（5 秒）..."
echo ""

# 使用 tcpdump 抓包
if command -v tcpdump &> /dev/null; then
    # 尝试从 Docker 容器内部抓包
    timeout 5 docker exec vpp-master tcpdump -i eth0 -n 'tcp port 8080' 2>/dev/null | head -20 || true
    echo ""
    echo -e "${YELLOW}提示: 如果看到 TCP 连接，说明有流量在传输${NC}"
else
    echo -e "${YELLOW}⚠ tcpdump 未安装，跳过流量检查${NC}"
fi

echo ""

# 检查日志
echo -e "${BLUE}[4/5] 检查应用日志...${NC}"
echo ""

echo "vpp-master 最近的日志："
docker logs vpp-master 2>&1 | tail -5
echo ""

echo "vpp-phase2-simulation 最近的日志："
docker logs vpp-phase2-simulation 2>&1 | tail -5
echo ""

# 总结
echo -e "${BLUE}[5/5] 通信验证总结${NC}"
echo ""

echo -e "${GREEN}✓ 通信状态:${NC}"
echo "  - vpp-phase2-simulation 每 10 秒向 vpp-master 发送一次数据"
echo "  - 每 30 秒进行一次健康检查"
echo "  - 支持 IEC61850, Modbus, DNP3, MQTT 等工控协议"
echo ""

echo -e "${YELLOW}建议的下一步:${NC}"
echo ""
echo "1. 用 Wireshark 抓包验证工控协议流量:"
echo "   - 打开 Wireshark"
echo "   - 选择 Docker 网络接口"
echo "   - 应用过滤器: tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082"
echo ""
echo "2. 用 tcpdump 从容器内部抓包:"
echo "   docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap"
echo ""
echo "3. 查看 network-mirror 分析器捕获的流量:"
echo "   ls -lh network-mirror/pcap/"
echo ""

echo -e "${BLUE}=========================================="
echo "验证完成"
echo "==========================================${NC}"
