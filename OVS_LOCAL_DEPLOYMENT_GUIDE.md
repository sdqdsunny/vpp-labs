# OVS 本地部署指南 (macOS)

**日期**: 2026-02-17  
**状态**: 实施指南  
**目标**: 在 macOS 本地部署 Open vSwitch 网络基础设施

---

## 概述

由于 macOS 对 OVS 的支持有限，我们采用以下方案：

### 方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|---------|
| **Docker 容器** | 跨平台、易部署、隔离 | 网络配置复杂 | ✅ 推荐用于开发测试 |
| **Linux VM** | 完全支持、生产级 | 需要额外资源 | 生产环境 |
| **Homebrew** | 本地运行 | macOS 不支持 | 不可用 |

---

## 推荐方案：Docker 容器部署

### 步骤 1：验证 Docker 环境

```bash
# 检查 Docker 是否运行
docker ps

# 检查 Docker 版本
docker --version

# 预期输出：Docker version 20.10+
```

### 步骤 2：运行 OVS 初始化

#### 方法 A：使用脚本（推荐）

```bash
# 进入项目目录
cd network-mirror

# 运行 OVS 初始化脚本
bash scripts/run-ovs-init-docker.sh
```

#### 方法 B：手动运行 Docker 命令

```bash
# 在 Docker 容器中运行 OVS 初始化
docker run \
    --rm \
    --privileged \
    --network host \
    -v "$(pwd)/network-mirror/scripts:/scripts:ro" \
    ubuntu:22.04 \
    bash -c "
        apt-get update && \
        apt-get install -y openvswitch-switch && \
        service openvswitch-switch start && \
        bash /scripts/ovs-init.sh
    "
```

### 步骤 3：验证 OVS 配置

```bash
# 在 Docker 容器中验证
docker run \
    --rm \
    --privileged \
    --network host \
    ubuntu:22.04 \
    bash -c "
        apt-get update && \
        apt-get install -y openvswitch-switch && \
        ovs-vsctl show
    "
```

### 步骤 4：启动 Docker Compose 系统

```bash
# 进入 network-mirror 目录
cd network-mirror

# 启动所有服务
docker-compose up -d

# 验证服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

## 完整部署流程

### 快速部署（5 分钟）

```bash
#!/bin/bash

# 1. 进入项目目录
cd network-mirror

# 2. 初始化 OVS
docker run \
    --rm \
    --privileged \
    --network host \
    -v "$(pwd)/scripts:/scripts:ro" \
    ubuntu:22.04 \
    bash -c "
        apt-get update && \
        apt-get install -y openvswitch-switch && \
        service openvswitch-switch start && \
        bash /scripts/ovs-init.sh
    "

# 3. 启动 Docker Compose
docker-compose up -d

# 4. 验证部署
docker-compose ps
docker-compose logs analyzer
```

---

## 验证清单

### OVS 配置验证

```bash
# 检查 OVS 桥接
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && ovs-vsctl show"

# 预期输出：
# Bridge br-vpp
#     Port veth-master-br
#     Port veth-vcc-br
#     Port veth-upf-br
#     Port veth-gen-br
#     Port mirror-port
#     Port veth-analyzer-br
```

### Docker 服务验证

```bash
# 检查所有服务状态
docker-compose ps

# 预期输出：
# NAME              STATUS
# vpp-ovs-init      Exited
# vpp-master        Up (healthy)
# vpp-vcc           Up (healthy)
# vpp-upf           Up (healthy)
# vpp-gen           Up
# vpp-analyzer      Up
```

### 网络连接验证

```bash
# 检查容器网络
docker network inspect network-mirror_vpp-net

# 检查容器 IP
docker inspect vpp-master | grep IPAddress

# 预期：10.0.1.10
```

### 流量镜像验证

```bash
# 检查镜像规则
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && ovs-vsctl list Mirror"

# 预期输出：
# _uuid               : ...
# name                : m0
# output_port         : ...
# select_all          : true
```

---

## 故障排查

### 问题 1：Docker 权限错误

**症状**：`permission denied while trying to connect to Docker daemon`

**解决方案**：
```bash
# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker
```

### 问题 2：OVS 服务启动失败

**症状**：`invoke-rc.d: policy-rc.d denied execution`

**解决方案**：
```bash
# 这是 Docker 容器中的正常警告，不影响功能
# OVS 仍然可以正常运行
```

### 问题 3：网络连接失败

**症状**：容器无法相互通信

**解决方案**：
```bash
# 检查 Docker 网络
docker network ls

# 检查网络配置
docker network inspect network-mirror_vpp-net

# 重新创建网络
docker-compose down -v
docker-compose up -d
```

### 问题 4：镜像规则未生效

**症状**：分析器未捕获流量

**解决方案**：
```bash
# 验证镜像规则
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && ovs-vsctl list Mirror"

# 重新创建镜像规则
docker run --rm --privileged --network host \
    -v "$(pwd)/scripts:/scripts:ro" \
    ubuntu:22.04 \
    bash -c "
        apt-get update && \
        apt-get install -y openvswitch-switch && \
        bash /scripts/ovs-init.sh
    "
```

---

## 高级配置

### 持久化 OVS 配置

```bash
# 导出 OVS 配置
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && \
     ovs-vsctl get-config > /tmp/ovs-config.txt" && \
    cat /tmp/ovs-config.txt
```

### 监控 OVS 性能

```bash
# 监控端口统计
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && \
     watch -n 1 'ovs-ofctl dump-ports br-vpp'"
```

### 调试流量镜像

```bash
# 捕获镜像端口流量
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y tcpdump && \
     tcpdump -i mirror-port -c 100 -w /tmp/mirror.pcap"
```

---

## 清理和重置

### 完全清理

```bash
# 停止所有服务
docker-compose down

# 删除 OVS 配置
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && \
     bash /scripts/ovs-cleanup.sh"

# 删除 Docker 卷
docker volume prune -f
```

### 重新初始化

```bash
# 清理
docker-compose down -v

# 重新初始化 OVS
bash scripts/run-ovs-init-docker.sh

# 重新启动服务
docker-compose up -d
```

---

## 性能优化

### 增加 OVS 内存

```bash
# 在 docker-compose.yml 中添加
ovs-init:
  mem_limit: 512m
  memswap_limit: 512m
```

### 优化网络性能

```bash
# 禁用 OVS 流缓存（用于测试）
docker run --rm --privileged --network host ubuntu:22.04 bash -c \
    "apt-get update && apt-get install -y openvswitch-switch && \
     ovs-vsctl set Open_vSwitch . other_config:flow-restore-wait=false"
```

---

## 生产部署建议

对于生产环境，建议：

1. **使用 Linux VM 或物理服务器**
   - 完整的 OVS 功能支持
   - 更好的性能
   - 更容易的故障排查

2. **使用 Kubernetes**
   - 自动化部署和管理
   - 高可用性
   - 自动扩展

3. **使用 Ansible**
   - 基础设施即代码
   - 可重复部署
   - 版本控制

---

## 相关文档

- [OVS 官方文档](http://openvswitch.org/)
- [Docker Compose 指南](network-mirror/DOCKER_COMPOSE_GUIDE.md)
- [部署指南](network-mirror/DEPLOYMENT_GUIDE.md)
- [OVS 脚本文档](network-mirror/scripts/README.md)

---

## 支持和反馈

如有问题，请参考：
- 故障排查指南：`network-mirror/TROUBLESHOOTING.md`
- 快速参考：`TASK_4_QUICK_REFERENCE.md`
- 完整报告：`TASK_4_BUILD_AND_TEST_DOCKER_IMAGES_COMPLETION.md`

