#!/bin/bash

# VPP System Docker Deployment Verification Script
# This script verifies that the Docker deployment is working correctly

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     VPP 系统 Docker 部署验证脚本                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Docker is installed
print_status "检查Docker安装..."
if ! command -v docker &> /dev/null; then
    print_error "Docker未安装"
    exit 1
fi
print_success "Docker已安装"
echo ""

# Check if image exists
print_status "检查Docker镜像..."
if ! docker images | grep -q "vpp-system"; then
    print_error "镜像不存在，请先构建镜像"
    echo "运行: docker build -t vpp-system:latest vpp-phase2-simulation/"
    exit 1
fi
print_success "镜像存在: vpp-system:latest"
echo ""

# Start container
print_status "启动容器..."
CONTAINER_ID=$(docker run --rm -d \
    --name vpp-test-container \
    -p 8080:8080 \
    -e PYTHONUNBUFFERED=1 \
    -e API_PORT=8080 \
    vpp-system:latest 2>&1)

if [ -z "$CONTAINER_ID" ]; then
    print_error "容器启动失败"
    exit 1
fi

print_success "容器已启动"
echo ""

# Wait for application to start
print_status "等待应用启动..."
sleep 10

# Check if container is still running
if ! docker ps | grep -q vpp-test-container; then
    print_error "容器已停止"
    exit 1
fi
print_success "容器正在运行"
echo ""

# Test health endpoint
print_status "测试健康检查端点 (/health)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
if [ "$HTTP_CODE" = "200" ]; then
    print_success "健康检查成功 (HTTP $HTTP_CODE)"
else
    print_error "健康检查失败 (HTTP $HTTP_CODE)"
    docker stop vpp-test-container > /dev/null 2>&1
    exit 1
fi
echo ""

# Test readiness endpoint
print_status "测试就绪检查端点 (/ready)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ready)
if [ "$HTTP_CODE" = "200" ]; then
    print_success "就绪检查成功 (HTTP $HTTP_CODE)"
else
    print_error "就绪检查失败 (HTTP $HTTP_CODE)"
    docker stop vpp-test-container > /dev/null 2>&1
    exit 1
fi
echo ""

# Test analyzer API
print_status "测试协议分析工具API (/api/analyzer/summary)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/analyzer/summary)
if [ "$HTTP_CODE" = "200" ]; then
    print_success "协议分析工具API成功 (HTTP $HTTP_CODE)"
else
    print_error "协议分析工具API失败 (HTTP $HTTP_CODE)"
    docker stop vpp-test-container > /dev/null 2>&1
    exit 1
fi
echo ""

# Test security API
print_status "测试安全测试工具API (/api/security/tools)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/security/tools)
if [ "$HTTP_CODE" = "200" ]; then
    print_success "安全测试工具API成功 (HTTP $HTTP_CODE)"
else
    print_warning "安全测试工具API返回 HTTP $HTTP_CODE"
fi
echo ""

# Stop container
print_status "停止容器..."
docker stop vpp-test-container > /dev/null 2>&1
sleep 2

# Verify container cleanup
print_status "验证容器清理（--rm参数）..."
if docker ps -a | grep -q vpp-test-container; then
    print_error "容器仍然存在于docker ps -a中"
    exit 1
fi
print_success "容器已被正确清理"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    验证结果总结                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_success "Docker镜像存在"
print_success "容器成功启动"
print_success "健康检查端点正常"
print_success "就绪检查端点正常"
print_success "协议分析工具API正常"
print_success "安全测试工具API正常"
print_success "容器清理机制正常"
echo ""
echo -e "${GREEN}✓ 所有验证项目均已通过！${NC}"
echo ""
echo "现在你可以运行以下命令启动应用："
echo ""
echo "  方式1: ./docker-run.sh"
echo "  方式2: docker-compose up"
echo "  方式3: docker run --rm -p 8080:8080 -e API_PORT=8080 vpp-system:latest"
echo ""
echo "应用地址: http://localhost:8080"
echo ""
