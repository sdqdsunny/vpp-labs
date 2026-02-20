#!/bin/bash

# VPP 系统完整功能验证脚本
# 用于验证所有已实现的功能

set -e

echo "=========================================="
echo "VPP 系统完整功能验证"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=${4:-}
    
    echo -n "测试 $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>&1)
    else
        response=$(curl -s "$url" 2>&1)
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
    fi
}

test_https_endpoint() {
    local name=$1
    local url=$2
    
    echo -n "测试 $name... "
    
    response=$(curl -k -s "$url" 2>&1)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
    fi
}

# ========== 第一步：验证核心服务 ==========
echo ""
echo "========== 第一步：验证核心服务 =========="
echo ""

echo "1.1 检查容器状态..."
if docker ps | grep -q vpp-master; then
    echo -e "${GREEN}✅ vpp-master 运行中${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ vpp-master 未运行${NC}"
    ((FAILED++))
fi

if docker ps | grep -q vpp-simulation; then
    echo -e "${GREEN}✅ vpp-simulation 运行中${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ vpp-simulation 未运行${NC}"
    ((FAILED++))
fi

echo ""
echo "1.2 验证服务健康状态..."
test_endpoint "vpp-master 健康检查" "http://localhost:5000/health"
test_endpoint "Coordinator 健康检查" "http://localhost:8000/health"
test_endpoint "Main API 健康检查" "http://localhost:8001/health"
test_https_endpoint "3D 后端健康检查" "https://localhost/api/health"

# ========== 第二步：验证主要应用 ==========
echo ""
echo "========== 第二步：验证主要应用 =========="
echo ""

test_endpoint "Test Dashboard" "http://localhost:8001/test-dashboard"
test_endpoint "Security Tester" "http://localhost:8001/security"
test_endpoint "Protocol Analyzer" "http://localhost:8001/analyzer"

# ========== 第三步：验证 3D 可视化 ==========
echo ""
echo "========== 第三步：验证 3D 可视化 =========="
echo ""

test_https_endpoint "3D 前端" "https://localhost/"
test_https_endpoint "3D API 健康" "https://localhost/api/health"

# ========== 第四步：验证协议支持 ==========
echo ""
echo "========== 第四步：验证协议支持 =========="
echo ""

test_endpoint "获取支持的安全工具" "http://localhost:8001/api/security/tools"
test_endpoint "获取 DNP3 告警状态" "http://localhost:8001/api/security/dnp3/alarm_state"
test_endpoint "获取 DNP3 统计" "http://localhost:8001/api/security/dnp3/statistics"

# ========== 第五步：验证流量分析 ==========
echo ""
echo "========== 第五步：验证流量分析 =========="
echo ""

test_endpoint "获取分析摘要" "http://localhost:8001/api/analyzer/summary"
test_endpoint "获取协议统计" "http://localhost:8001/api/analyzer/stats"
test_endpoint "获取最近数据包" "http://localhost:8001/api/analyzer/packets"
test_endpoint "获取活跃流" "http://localhost:8001/api/analyzer/flows"
test_endpoint "获取支持的协议" "http://localhost:8001/api/analyzer/protocols"

# ========== 第六步：验证实时数据 ==========
echo ""
echo "========== 第六步：验证实时数据 =========="
echo ""

test_endpoint "获取实时状态" "http://localhost:5000/api/realtime/status"
test_endpoint "获取 3D 组件信息" "https://localhost/api/visualization/components"

# ========== 总结 ==========
echo ""
echo "=========================================="
echo "验证结果总结"
echo "=========================================="
echo ""
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有功能验证通过！${NC}"
    echo ""
    echo "系统已准备好进行完整演示："
    echo "  1. 3D 可视化: https://localhost"
    echo "  2. Test Dashboard: http://localhost:8001/test-dashboard"
    echo "  3. Security Tester: http://localhost:8001/security"
    echo "  4. Protocol Analyzer: http://localhost:8001/analyzer"
    exit 0
else
    echo -e "${RED}❌ 有 $FAILED 个功能验证失败${NC}"
    exit 1
fi
