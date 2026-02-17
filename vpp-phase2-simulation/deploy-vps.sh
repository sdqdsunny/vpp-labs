#!/bin/bash

################################################################################
# VPP Phase 2 Simulation - VPS 一键部署脚本
# 
# 使用方法:
#   chmod +x deploy-vps.sh
#   ./deploy-vps.sh
#
# 支持的操作系统:
#   - Ubuntu 20.04 LTS
#   - Ubuntu 22.04 LTS
#   - Debian 11
#   - Debian 12
#
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本必须以 root 用户运行"
        exit 1
    fi
}

# 检查操作系统
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测操作系统"
        exit 1
    fi
    
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    
    case $OS in
        ubuntu|debian)
            log_success "检测到操作系统: $OS $VERSION"
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
}

# 检查系统资源
check_resources() {
    log_info "检查系统资源..."
    
    # 检查 CPU
    CPU_CORES=$(nproc)
    log_info "CPU 核心数: $CPU_CORES"
    
    if [[ $CPU_CORES -lt 1 ]]; then
        log_warning "CPU 核心数过少 (最低 1 核)"
    fi
    
    # 检查内存
    MEMORY_MB=$(free -m | awk 'NR==2{print $2}')
    MEMORY_GB=$((MEMORY_MB / 1024))
    log_info "内存大小: ${MEMORY_GB}GB (${MEMORY_MB}MB)"
    
    if [[ $MEMORY_MB -lt 1024 ]]; then
        log_warning "内存过少 (最低 1GB)"
    fi
    
    # 检查磁盘
    DISK_GB=$(df / | awk 'NR==2{print $4/1024/1024}' | cut -d. -f1)
    log_info "可用磁盘空间: ${DISK_GB}GB"
    
    if [[ $DISK_GB -lt 20 ]]; then
        log_error "磁盘空间不足 (最低 20GB)"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_info "更新系统..."
    apt-get update
    apt-get upgrade -y
    apt-get autoremove -y
    log_success "系统更新完成"
}

# 安装基础依赖
install_dependencies() {
    log_info "安装基础依赖..."
    
    apt-get install -y \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        ufw \
        htop \
        vim \
        nano
    
    log_success "基础依赖安装完成"
}

# 安装 Docker
install_docker() {
    log_info "安装 Docker..."
    
    # 检查 Docker 是否已安装
    if command -v docker &> /dev/null; then
        log_warning "Docker 已安装，跳过安装"
        return
    fi
    
    # 添加 Docker GPG 密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加 Docker 仓库
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装 Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 启动 Docker
    systemctl start docker
    systemctl enable docker
    
    log_success "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    log_info "安装 Docker Compose..."
    
    # 检查 Docker Compose 是否已安装
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose 已安装，跳过安装"
        return
    fi
    
    # 下载 Docker Compose
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose 安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 启用 UFW
    ufw --force enable
    
    # 允许 SSH
    ufw allow 22/tcp
    
    # 允许 HTTP
    ufw allow 80/tcp
    
    # 允许 HTTPS
    ufw allow 443/tcp
    
    # 允许应用端口
    ufw allow 8080/tcp
    
    # 查看防火墙状态
    ufw status
    
    log_success "防火墙配置完成"
}

# 克隆项目
clone_project() {
    log_info "克隆项目..."
    
    if [[ -d "vpp-phase2-simulation" ]]; then
        log_warning "项目目录已存在，跳过克隆"
        cd vpp-phase2-simulation
        git pull origin main
    else
        git clone https://github.com/your-org/vpp-phase2-simulation.git
        cd vpp-phase2-simulation
    fi
    
    log_success "项目克隆完成"
}

# 配置环境变量
configure_env() {
    log_info "配置环境变量..."
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            log_success ".env 文件已创建"
        else
            log_warning ".env.example 不存在，创建默认 .env 文件"
            cat > .env << 'EOF'
# API 配置
API_HOST=0.0.0.0
API_PORT=8080
ENV=production
DEBUG=false
API_WORKERS=4

# 数据库配置
DATABASE_URL=postgresql://vpp_user:vpp_password@postgres:5432/vpp_phase2

# Redis 配置
REDIS_URL=redis://redis:6379/0

# Phase 1 集成
VPP_MASTER_URL=http://vpp-master:8001
VPP_MASTER_API_KEY=

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/vpp_phase2_sim.log
LOG_FORMAT=json
EOF
        fi
    else
        log_warning ".env 文件已存在，跳过创建"
    fi
    
    log_info "请编辑 .env 文件以配置必要的环境变量"
    log_info "nano .env"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    docker-compose up -d
    
    log_success "服务启动完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    sleep 10
    
    # 检查健康状态
    if curl -s http://localhost:8080/health > /dev/null; then
        log_success "健康检查通过"
    else
        log_error "健康检查失败"
        return 1
    fi
    
    # 检查就绪状态
    if curl -s http://localhost:8080/ready > /dev/null; then
        log_success "就绪检查通过"
    else
        log_error "就绪检查失败"
        return 1
    fi
    
    # 查看运行中的容器
    log_info "运行中的容器:"
    docker-compose ps
}

# 显示访问信息
show_access_info() {
    log_success "部署完成！"
    echo ""
    echo "================================"
    echo "📊 访问信息"
    echo "================================"
    echo ""
    
    # 获取 VPS IP
    VPS_IP=$(hostname -I | awk '{print $1}')
    
    echo "🌐 VPS IP: $VPS_IP"
    echo ""
    echo "📍 访问地址:"
    echo "  - 健康检查: http://$VPS_IP:8080/health"
    echo "  - 就绪检查: http://$VPS_IP:8080/ready"
    echo "  - 指标: http://$VPS_IP:8080/metrics"
    echo "  - 测试仪表板: http://$VPS_IP:8080/test-dashboard"
    echo "  - API 文档: http://$VPS_IP:8080/api/docs"
    echo ""
    echo "📚 有用的命令:"
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 查看容器: docker-compose ps"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 停止服务: docker-compose down"
    echo ""
    echo "================================"
}

# 主函数
main() {
    log_info "开始 VPP Phase 2 Simulation VPS 部署..."
    echo ""
    
    check_root
    check_os
    check_resources
    
    log_info "开始安装..."
    echo ""
    
    update_system
    install_dependencies
    install_docker
    install_docker_compose
    configure_firewall
    
    log_info "配置应用..."
    echo ""
    
    clone_project
    configure_env
    
    log_info "启动应用..."
    echo ""
    
    start_services
    verify_deployment
    
    echo ""
    show_access_info
}

# 运行主函数
main
