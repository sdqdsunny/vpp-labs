# VPP 微服务标准架构和部署方案

## 📋 目录
1. [架构概述](#架构概述)
2. [容器配置](#容器配置)
3. [网络配置](#网络配置)
4. [部署流程](#部署流程)
5. [故障排查](#故障排查)
6. [关键要点](#关键要点)

---

## 架构概述

### 微服务架构（Option B - 真正的微服务）

VPP系统采用5个独立的微服务容器架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    VPP 微服务架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  vpp-master  │  │vpp-power-gen │  │ vpp-storage  │       │
│  │  (协调中心)   │  │  (电源侧)     │  │  (储能侧)    │       │
│  │   Port 8080  │  │  Port 8081   │  │  Port 8082   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            │                                  │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │  vpp-demand  │  │ vpp-sniffer  │                          │
│  │  (需求侧)    │  │ (流量抓包)    │                          │
│  │  Port 8083   │  │ (tcpdump)    │                          │
│  └──────────────┘  └──────────────┘                          │
│         │                  │                                  │
│         └──────────────────┘                                  │
│                                                               │
│         Docker Network: 10.0.8.0/24                          │
└─────────────────────────────────────────────────────────────┘
```

### 5个微服务容器

| 容器名称 | 功能 | 端口 | IP地址 | 应用文件 |
|---------|------|------|--------|---------|
| vpp-master | 虚拟电厂协调中心 | 8080 | 10.0.8.2 | app_coordinator.py |
| vpp-power-generation | 光伏/风电模拟 | 8081 | 10.0.8.4 | app_power_generation.py |
| vpp-storage | 电池管理系统 | 8082 | 10.0.8.5 | app_battery_system.py |
| vpp-demand | 负荷管理 | 8083 | 10.0.8.6 | app_load_manager.py |
| vpp-sniffer | 流量抓包分析 | - | 10.0.8.7 | tcpdump |

---

## 容器配置

### Dockerfile 标准配置

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iputils-ping \
    net-tools \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码（从vpp-phase2-simulation目录）
COPY vpp-phase2-simulation/ .

# 使entrypoint脚本可执行
RUN chmod +x entrypoint.sh

# 创建日志目录
RUN mkdir -p logs/coordinator logs/power_generation logs/storage logs/demand

# 暴露端口
EXPOSE 8080 8081 8082 8083

# 运行应用
CMD ["./entrypoint.sh"]
```

**关键点**：
- 使用 `COPY vpp-phase2-simulation/ .` 而不是 `COPY . .`
- `RUN chmod +x entrypoint.sh` 必须在 `COPY` 之后
- 使用 Python 3.11-slim（不要用3.14，兼容性问题）

### entrypoint.sh 标准配置

```bash
#!/bin/bash

# 从环境变量获取NODE_TYPE，默认为'master'
NODE_TYPE=${NODE_TYPE:-master}

# 根据NODE_TYPE映射到应用文件
case $NODE_TYPE in
  master)
    python3 app_coordinator.py
    ;;
  generation)
    python3 app_power_generation.py
    ;;
  storage)
    python3 app_battery_system.py
    ;;
  demand)
    python3 app_load_manager.py
    ;;
  *)
    echo "Unknown NODE_TYPE: $NODE_TYPE"
    python3 app_coordinator.py
    ;;
esac
```

### requirements.txt 标准依赖

```
bottle==0.12.25
sqlalchemy==2.0.23
python-dotenv==1.0.0
requests==2.31.0
apscheduler==3.10.4
tenacity==8.2.3
```

**注意**：
- ❌ 不要使用 prometheus-client（已移除）
- ✅ 使用简化的 prometheus_metrics.py stub实现

---

## 网络配置

### Docker Compose 网络配置

```yaml
networks:
  vpp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.8.0/24
          gateway: 10.0.8.1
```

**重要**：
- 子网必须是 `10.0.8.0/24`（避免与Docker管理接口冲突）
- 不要使用 `172.20.0.0/16` 或 `172.21.0.0/16`

### 容器网络配置示例

```yaml
services:
  master:
    # ... 其他配置 ...
    networks:
      vpp-network:
        ipv4_address: 10.0.8.2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

---

## 部署流程

### 第1步：准备工作

```bash
# 创建日志目录
mkdir -p vpp-phase2-simulation/logs/{coordinator,power_generation,storage,demand}
mkdir -p captures

# 验证文件结构
ls -la vpp-phase2-simulation/
# 应该包含：
# - Dockerfile
# - entrypoint.sh
# - app_coordinator.py
# - app_power_generation.py
# - app_battery_system.py
# - app_load_manager.py
# - requirements.txt
# - utils/
# - routes/
# - services/
# - config.py
```

### 第2步：构建镜像

```bash
# 构建所有镜像（不使用缓存）
docker-compose -f docker-compose-microservices.yml build --no-cache

# 输出应该显示：
# vpp-master:latest  Built
# vpp-power-generation:latest  Built
# vpp-storage:latest  Built
# vpp-demand:latest  Built
```

### 第3步：启动容器

```bash
# 启动所有容器
docker-compose -f docker-compose-microservices.yml up -d

# 验证容器状态
docker-compose -f docker-compose-microservices.yml ps

# 所有容器应该显示 "Up (healthy)"
```

### 第4步：验证部署

```bash
# 等待容器完全启动
sleep 5

# 检查网络连接
docker exec vpp-master ping -c 2 vpp-power-generation
docker exec vpp-master ping -c 2 vpp-storage
docker exec vpp-master ping -c 2 vpp-demand

# 检查HTTP端点
docker exec vpp-master curl -s http://localhost:8080/health | python3 -m json.tool
docker exec vpp-master curl -s http://vpp-power-generation:8081/health | python3 -m json.tool
docker exec vpp-master curl -s http://vpp-storage:8082/health | python3 -m json.tool
docker exec vpp-master curl -s http://vpp-demand:8083/health | python3 -m json.tool
```

### 第5步：停止容器

```bash
# 停止并移除所有容器
docker-compose -f docker-compose-microservices.yml down

# 清理镜像（可选）
docker rmi vpp-master vpp-power-generation vpp-storage vpp-demand
```

---

## 故障排查

### 问题1：容器不断重启

**症状**：容器状态显示 "Restarting"

**解决方案**：
```bash
# 查看容器日志
docker logs vpp-master

# 常见错误：
# - ModuleNotFoundError: 检查requirements.txt
# - NameError: 检查prometheus_metrics.py是否为stub实现
# - FileNotFoundError: 检查entrypoint.sh路径
```

### 问题2：网络连接失败

**症状**：ping失败或HTTP请求超时

**解决方案**：
```bash
# 检查网络
docker network ls
docker network inspect vpp-labs_vpp-network

# 检查容器IP
docker inspect vpp-master | grep IPAddress

# 应该显示 10.0.8.2
```

### 问题3：镜像构建失败

**症状**：`docker-compose build` 失败

**解决方案**：
```bash
# 清理旧镜像
docker rmi vpp-master vpp-power-generation vpp-storage vpp-demand

# 重新构建
docker-compose -f docker-compose-microservices.yml build --no-cache

# 检查Dockerfile中的COPY路径是否正确
```

### 问题4：端口冲突

**症状**：`Error response from daemon: Ports are not available`

**解决方案**：
```bash
# 查看占用的端口
lsof -i :8080
lsof -i :8081
lsof -i :8082
lsof -i :8083

# 停止占用端口的进程或修改docker-compose.yml中的端口映射
```

---

## 关键要点

### ✅ 必须做的事

1. **使用正确的Dockerfile路径**
   ```dockerfile
   COPY vpp-phase2-simulation/ .
   ```

2. **entrypoint.sh必须在COPY之后**
   ```dockerfile
   COPY vpp-phase2-simulation/ .
   RUN chmod +x entrypoint.sh
   ```

3. **使用Python 3.11-slim**
   ```dockerfile
   FROM python:3.11-slim
   ```

4. **使用正确的子网**
   ```yaml
   subnet: 10.0.8.0/24
   ```

5. **配置健康检查**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 40s
   ```

6. **配置自动重启**
   ```yaml
   restart: unless-stopped
   ```

### ❌ 不要做的事

1. ❌ 不要使用 `COPY . .`（会复制整个项目）
2. ❌ 不要在COPY之前运行 `chmod +x entrypoint.sh`
3. ❌ 不要使用Python 3.14（兼容性问题）
4. ❌ 不要使用 `172.20.0.0/16` 或 `172.21.0.0/16` 子网
5. ❌ 不要导入prometheus_client（已移除）
6. ❌ 不要忘记在docker-compose.yml中指定 `container_name`

### 🔧 常用命令速查

```bash
# 构建
docker-compose -f docker-compose-microservices.yml build --no-cache

# 启动
docker-compose -f docker-compose-microservices.yml up -d

# 查看状态
docker-compose -f docker-compose-microservices.yml ps

# 查看日志
docker logs vpp-master
docker logs -f vpp-master  # 实时日志

# 进入容器
docker exec -it vpp-master bash

# 停止
docker-compose -f docker-compose-microservices.yml down

# 清理
docker system prune -a
```

---

## 文件清单

部署所需的关键文件：

```
vpp-labs/
├── docker-compose-microservices.yml    # Docker Compose配置
├── requirements.txt                     # Python依赖
├── vpp-phase2-simulation/
│   ├── Dockerfile                       # Docker镜像定义
│   ├── entrypoint.sh                    # 容器启动脚本
│   ├── app_coordinator.py               # 主站应用
│   ├── app_power_generation.py          # 电源侧应用
│   ├── app_battery_system.py            # 储能侧应用
│   ├── app_load_manager.py              # 需求侧应用
│   ├── config.py                        # 配置文件
│   ├── utils/
│   │   ├── prometheus_metrics.py        # 指标收集（stub实现）
│   │   ├── logger.py
│   │   ├── structured_logger.py
│   │   ├── database.py
│   │   └── ...
│   ├── routes/
│   ├── services/
│   ├── middleware/
│   ├── static/
│   └── logs/                            # 日志目录
└── captures/                            # tcpdump抓包目录
```

---

## 版本信息

- **创建日期**: 2026-02-18
- **Python版本**: 3.11-slim
- **Docker Compose版本**: 3.8
- **网络子网**: 10.0.8.0/24
- **架构类型**: 真正的微服务架构（Option B）

---

## 更新历史

| 日期 | 变更 | 说明 |
|------|------|------|
| 2026-02-18 | 初始版本 | 5个微服务容器部署方案 |
| 2026-02-18 | 移除Prometheus | 使用stub实现替代prometheus-client |
| 2026-02-18 | 网络配置 | 使用10.0.8.0/24子网 |

