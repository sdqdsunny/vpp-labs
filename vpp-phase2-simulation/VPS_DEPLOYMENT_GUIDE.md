# VPS 部署指南 - VPP Phase 2 Simulation Framework

**最后更新**: 2026年2月17日

---

## 📋 目录

1. [最低配置要求](#最低配置要求)
2. [推荐配置](#推荐配置)
3. [支持的操作系统](#支持的操作系统)
4. [快速部署](#快速部署)
5. [详细部署步骤](#详细部署步骤)
6. [监控和维护](#监控和维护)
7. [故障排查](#故障排查)

---

## 最低配置要求

### CPU
- **最低**: 1 核心 (1 vCPU)
- **推荐**: 2 核心 (2 vCPU)
- **生产**: 4 核心 (4 vCPU)

### 内存
- **最低**: 1 GB RAM
- **推荐**: 2 GB RAM
- **生产**: 4-8 GB RAM

### 存储
- **最低**: 20 GB SSD
- **推荐**: 50 GB SSD
- **生产**: 100+ GB SSD

### 网络
- **带宽**: 最低 1 Mbps
- **推荐**: 10+ Mbps
- **公网 IP**: 需要 1 个公网 IP

### 成本估算

| 配置等级 | CPU | 内存 | 存储 | 月成本 |
|---------|-----|------|------|--------|
| 最低 | 1核 | 1GB | 20GB | $3-5 |
| 推荐 | 2核 | 2GB | 50GB | $8-15 |
| 生产 | 4核 | 4GB | 100GB | $20-40 |

---

## 推荐配置

### 开发/测试环境
```
CPU: 2 vCPU
内存: 2 GB
存储: 50 GB SSD
带宽: 5 Mbps
成本: ~$10/月
```

### 生产环境 (单机)
```
CPU: 4 vCPU
内存: 4-8 GB
存储: 100+ GB SSD
带宽: 20+ Mbps
成本: ~$30-50/月
```

### 生产环境 (高可用)
```
主服务器:
  CPU: 4 vCPU
  内存: 8 GB
  存储: 100 GB SSD

备份服务器:
  CPU: 2 vCPU
  内存: 4 GB
  存储: 100 GB SSD

数据库服务器:
  CPU: 2 vCPU
  内存: 4 GB
  存储: 200+ GB SSD

总成本: ~$80-120/月
```

---

## 支持的操作系统

### 推荐
- ✅ Ubuntu 20.04 LTS
- ✅ Ubuntu 22.04 LTS
- ✅ Debian 11
- ✅ Debian 12

### 支持
- ✅ CentOS 7
- ✅ CentOS 8
- ✅ Rocky Linux 8
- ✅ AlmaLinux 8

### 不支持
- ❌ Windows Server (需要 WSL2)
- ❌ macOS (仅用于开发)

---

## 快速部署

### 一键部署脚本

```bash
#!/bin/bash
# VPP Phase 2 Simulation - 一键部署脚本

# 1. 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 2. 安装依赖
sudo apt-get install -y \
  curl \
  wget \
  git \
  python3 \
  python3-pip \
  docker.io \
  docker-compose

# 3. 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 4. 添加当前用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 5. 克隆项目
git clone https://github.com/your-org/vpp-phase2-simulation.git
cd vpp-phase2-simulation

# 6. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量

# 7. 启动服务
docker-compose up -d

# 8. 验证部署
sleep 10
curl http://localhost:8080/health

echo "✅ 部署完成！"
echo "📊 访问地址: http://your-vps-ip:8080"
echo "📈 测试仪表板: http://your-vps-ip:8080/test-dashboard"
echo "📚 API 文档: http://your-vps-ip:8080/api/docs"
```

### 保存脚本并执行

```bash
# 保存脚本
cat > deploy.sh << 'EOF'
[上面的脚本内容]
EOF

# 赋予执行权限
chmod +x deploy.sh

# 执行脚本
./deploy.sh
```

---

## 详细部署步骤

### 步骤 1: 准备 VPS

#### 1.1 连接到 VPS
```bash
ssh root@your-vps-ip
# 或使用密钥
ssh -i /path/to/key.pem ubuntu@your-vps-ip
```

#### 1.2 更新系统
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
```

#### 1.3 配置防火墙
```bash
# 如果使用 UFW
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8080/tcp  # 应用端口

# 查看防火墙状态
sudo ufw status
```

### 步骤 2: 安装 Docker

#### 2.1 安装 Docker
```bash
# 安装依赖
sudo apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

#### 2.2 启动 Docker
```bash
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker run hello-world
```

#### 2.3 配置 Docker 权限
```bash
# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 应用新的组成员资格
newgrp docker

# 验证
docker ps
```

### 步骤 3: 部署应用

#### 3.1 克隆项目
```bash
git clone https://github.com/your-org/vpp-phase2-simulation.git
cd vpp-phase2-simulation
```

#### 3.2 配置环境变量
```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

**必要的环境变量**:
```env
# API 配置
API_HOST=0.0.0.0
API_PORT=8080
ENV=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://user:password@db:5432/vpp_phase2

# Redis 配置
REDIS_URL=redis://redis:6379/0

# Phase 1 集成
VPP_MASTER_URL=http://vpp-master:8001
VPP_MASTER_API_KEY=your-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/vpp_phase2_sim.log
```

#### 3.3 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看运行中的容器
docker-compose ps
```

#### 3.4 验证部署
```bash
# 检查健康状态
curl http://localhost:8080/health

# 检查就绪状态
curl http://localhost:8080/ready

# 查看指标
curl http://localhost:8080/metrics | head -20
```

### 步骤 4: 配置反向代理 (可选)

#### 4.1 安装 Nginx
```bash
sudo apt-get install -y nginx
```

#### 4.2 配置 Nginx
```bash
# 创建配置文件
sudo nano /etc/nginx/sites-available/vpp-phase2

# 添加以下内容:
```

```nginx
upstream vpp_phase2 {
    server localhost:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书 (使用 Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/vpp-phase2-access.log;
    error_log /var/log/nginx/vpp-phase2-error.log;

    # 代理配置
    location / {
        proxy_pass http://vpp_phase2;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4.3 启用配置
```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/vpp-phase2 /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 4.4 配置 SSL 证书 (Let's Encrypt)
```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

---

## 监控和维护

### 日志查看
```bash
# 查看应用日志
docker-compose logs -f vpp-phase2-simulation

# 查看数据库日志
docker-compose logs -f postgres

# 查看 Redis 日志
docker-compose logs -f redis

# 查看最后 100 行日志
docker-compose logs --tail 100 vpp-phase2-simulation
```

### 性能监控
```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看进程
ps aux | grep docker
```

### 备份数据库
```bash
# 备份 PostgreSQL
docker-compose exec postgres pg_dump -U vpp_user vpp_phase2 > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U vpp_user vpp_phase2 < backup.sql

# 定时备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U vpp_user vpp_phase2 > $BACKUP_DIR/backup_$DATE.sql
# 保留最近 7 天的备份
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到 crontab (每天凌晨 2 点备份)
crontab -e
# 添加: 0 2 * * * /path/to/backup.sh
```

### 更新应用
```bash
# 拉取最新代码
git pull origin main

# 重建镜像
docker-compose build

# 重启服务
docker-compose up -d

# 查看更新日志
docker-compose logs -f
```

---

## 故障排查

### 常见问题

#### 1. 端口被占用
```bash
# 查看占用 8080 端口的进程
lsof -i :8080

# 杀死进程
kill -9 <PID>

# 或修改 docker-compose.yml 中的端口
```

#### 2. 数据库连接失败
```bash
# 检查数据库容器
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

#### 3. 内存不足
```bash
# 查看内存使用
free -h

# 清理 Docker 缓存
docker system prune -a

# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. 磁盘空间不足
```bash
# 查看磁盘使用
df -h

# 查看大文件
du -sh /*

# 清理日志
docker-compose exec vpp-phase2-simulation rm -f /app/logs/*.log

# 清理 Docker 镜像
docker image prune -a
```

#### 5. 应用无法启动
```bash
# 查看详细日志
docker-compose logs vpp-phase2-simulation

# 检查环境变量
docker-compose config

# 验证配置文件
cat .env

# 手动启动容器进行调试
docker-compose run --rm vpp-phase2-simulation bash
```

### 性能优化

#### 1. 增加 API 工作进程
```env
API_WORKERS=8  # 根据 CPU 核心数调整
```

#### 2. 优化数据库连接池
```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

#### 3. 启用 Redis 缓存
```env
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600
```

#### 4. 启用 Gzip 压缩
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

---

## 云服务商推荐

### 低成本选项
- **Linode**: $5/月 (1GB RAM, 1 vCPU, 25GB SSD)
- **DigitalOcean**: $6/月 (1GB RAM, 1 vCPU, 25GB SSD)
- **Vultr**: $2.5/月 (512MB RAM, 1 vCPU, 10GB SSD)
- **Hetzner**: €3/月 (2GB RAM, 1 vCPU, 20GB SSD)

### 中等配置
- **DigitalOcean**: $12/月 (2GB RAM, 2 vCPU, 50GB SSD)
- **Linode**: $12/月 (4GB RAM, 2 vCPU, 80GB SSD)
- **AWS EC2**: $10-20/月 (t3.small)
- **阿里云**: ¥40-60/月 (1核2GB)

### 生产级别
- **DigitalOcean**: $24/月 (4GB RAM, 2 vCPU, 80GB SSD)
- **Linode**: $24/月 (8GB RAM, 4 vCPU, 160GB SSD)
- **AWS EC2**: $30-50/月 (t3.medium)
- **阿里云**: ¥100-150/月 (2核4GB)

---

## 访问应用

部署完成后，可以通过以下地址访问应用：

| 功能 | 地址 | 说明 |
|------|------|------|
| 健康检查 | `http://your-vps-ip:8080/health` | 系统健康状态 |
| 就绪检查 | `http://your-vps-ip:8080/ready` | 系统就绪状态 |
| 指标 | `http://your-vps-ip:8080/metrics` | Prometheus 指标 |
| 测试仪表板 | `http://your-vps-ip:8080/test-dashboard` | 交互式测试界面 |
| API 文档 | `http://your-vps-ip:8080/api/docs` | Swagger UI 文档 |
| OpenAPI 规范 | `http://your-vps-ip:8080/api/openapi.json` | 机器可读的 API 规范 |

---

## 支持和帮助

如有问题，请查看：
- 📚 [部署指南](DEPLOYMENT_GUIDE.md)
- 🚀 [快速开始](QUICK_START.md)
- 📖 [API 文档](vpp-phase2-simulation/routes/)
- 🐛 [故障排查](TROUBLESHOOTING_GUIDE.md)

---

**最后更新**: 2026年2月17日
**版本**: 1.0.0
