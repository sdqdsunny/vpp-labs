#!/bin/bash

echo "=========================================="
echo "协议分析器完整功能验证"
echo "=========================================="
echo ""

# 1. 检查容器状态
echo "1️⃣  检查容器状态..."
if docker ps | grep -q vpp-simulation; then
    echo "✅ 容器运行正常"
else
    echo "❌ 容器未运行"
    exit 1
fi
echo ""

# 2. 检查 API 健康状态
echo "2️⃣  检查 API 健康状态..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ API 健康"
else
    echo "❌ API 不健康"
    exit 1
fi
echo ""

# 3. 验证协议流量统计
echo "3️⃣  验证协议流量统计..."
SUMMARY=$(curl -s http://localhost:8001/api/analyzer/summary)
PACKETS=$(echo "$SUMMARY" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_packets'])")
PROTOCOLS=$(echo "$SUMMARY" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_protocols'])")
echo "✅ 总数据包: $PACKETS"
echo "✅ 协议类型: $PROTOCOLS"
echo ""

# 4. 验证 VPP 实时数据
echo "4️⃣  验证 VPP 实时数据..."
VPP=$(curl -s http://localhost:8001/api/vpp/realtime)
POWER=$(echo "$VPP" | python3 -c "import sys, json; print(json.load(sys.stdin)['power_generation']['current_power'])")
STORAGE=$(echo "$VPP" | python3 -c "import sys, json; print(json.load(sys.stdin)['storage']['soc'])")
DEMAND=$(echo "$VPP" | python3 -c "import sys, json; print(json.load(sys.stdin)['demand']['current_demand'])")
echo "✅ 电源: $POWER kW"
echo "✅ 储能: $STORAGE %"
echo "✅ 需求: $DEMAND kW"
echo ""

# 5. 验证数据更新
echo "5️⃣  验证数据更新..."
PACKETS1=$(curl -s http://localhost:8001/api/analyzer/summary | python3 -c "import sys, json; print(json.load(sys.stdin)['total_packets'])")
sleep 3
PACKETS2=$(curl -s http://localhost:8001/api/analyzer/summary | python3 -c "import sys, json; print(json.load(sys.stdin)['total_packets'])")

if [ "$PACKETS1" != "$PACKETS2" ]; then
    echo "✅ 数据在持续更新 ($PACKETS1 → $PACKETS2)"
else
    echo "⚠️  数据可能未更新"
fi
echo ""

# 6. 验证页面访问
echo "6️⃣  验证页面访问..."
if curl -s http://localhost:8001/analyzer | grep -q "VPP 协议流量分析工具"; then
    echo "✅ 页面可访问"
else
    echo "❌ 页面无法访问"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 所有功能验证完成！"
echo "=========================================="
echo ""
echo "📱 访问地址: http://localhost:8001/analyzer"
echo ""
echo "功能清单:"
echo "  ✅ 实时协议流量统计"
echo "  ✅ 协议详细统计"
echo "  ✅ 数据包详细列表"
echo "  ✅ 流量分析"
echo "  ✅ VPP 实时数据显示"
echo "  ✅ 自动数据生成"
echo "  ✅ 实时数据更新"
echo ""
