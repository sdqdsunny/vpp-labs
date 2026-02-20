# Docker 网络隔离问题 - 完整解决方案

## 问题诊断

### 当前网络配置

```
网络 1: network-mirror_vpp-net
├── vpp-master (10.0.1.10)
├── vpp-vcc (10.0.1.20)
├── vpp-upf (10.0.1.30)
├── vpp-gen (10.0.1.40)
└── vpp-analyzer (10.0.1.50)

网络 2: vpp-phase2-simulation_vpp-network
├── vpp-phase2-simulation (8080, 8081)
├── vpp-postgres (5432)
└── vpp-redis (6379)
```

### 问题
- **vpp-phase2-simulation** 和 **vpp-master** 在不同的 Docker 网络中
- 它们无法直接通信
- vpp-phase2-simulation 默认连接到 `localhost:8080`（自己）

---

## ✅ 解决方案：连接两个网络

### 方法 1：使用 Docker 网络连接（推荐）

#### 步骤 1：将 vpp-phase2-simulation 连接到 network-mirror_vpp-net

```bash
# 连接容器到网络
docker network connect network-mirror_vpp-net vpp-phase2-simulation
docker network connect network-mirror_vpp-net vpp-postgres
docker network connect network-mirror_vpp-net vpp-redis

# 验证连接
docker network inspect network-mirror_vpp-net | grep -A 50 "Containers"
```

#### 步骤 2：验证连接

```bash
# 进入 vpp-phase2-simulation 容器
docker exec -it vpp-phase2-simulation bash

# 测试是否能 ping 到 vpp-master
ping vpp-master

# 测试是否能连接到 vpp-master:8080
curl -v http://vpp-master:8080/health
```

#### 步骤 3：重启 vpp-phase2-simulation 的 Phase1IntegrationService

```bash
# 重启容器以重新初始化服务
docker restart vpp-phase2-simulation

# 查看日志确认连接
docker logs vpp-phase2-simulation -f --tail 50
```

---

### 方法 2：修改 docker-compose.yml（永久解决）

#### 编辑 vpp-phase2-simulation/docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    # ... 保持不变 ...
    networks:
      - vpp-network
      - network-mirror_vpp-net  # 添加这一行

  redis:
    # ... 保持不变 ...
    networks:
      - vpp-network
      - network-mirror_vpp-net  # 添加这一行

  vpp-api:
    # ... 保持不变 ...
    environment:
      # ... 保持不变 ...
      VPP_MASTER_URL: http://vpp-master:8080  # 添加这一行
    networks:
      - vpp-network
      - network-mirror_vpp-net  # 添加这一行

volumes:
  postgres_data:
  redis_data:

networks:
  vpp-network:
    driver: bridge
  network-mirror_vpp-net:  # 添加这一行
    external: true          # 添加这一行
```

#### 重新启动容器

```bash
# 停止旧容器
docker-compose -f vpp-phase2-simulation/docker-compose.yml down

# 启动新容器
docker-compose -f vpp-phase2-simulation/docker-compose.yml up -d

# 验证
docker logs vpp-phase2-simulation -f --tail 50
```

---

### 方法 3：使用环境变量（临时解决）

```bash
# 停止容器
docker stop vpp-phase2-simulation

# 重新启动时设置 VPP_MASTER_URL
docker run -d \
  --name vpp-phase2-simulation-new \
  --network network-mirror_vpp-net \
  -e VPP_MASTER_URL=http://vpp-master:8080 \
  -e DATABASE_URL=postgresql://vpp_user:vpp_password@vpp-postgres:5432/vpp_phase2_sim \
  -e REDIS_URL=redis://vpp-redis:6379/0 \
  -p 8080:8080 \
  -p 8081:8081 \
  vpp-phase2-simulation:latest

# 删除旧容器
docker rm vpp-phase2-simulation
```

---

## 🔍 验证解决方案

### 步骤 1：检查网络连接

```bash
# 查看 network-mirror_vpp-net 中的所有容器
docker network inspect network-mirror_vpp-net

# 应该看到：
# - vpp-master
# - vpp-vcc
# - vpp-upf
# - vpp-gen
# - vpp-analyzer
# - vpp-phase2-simulation (新增)
# - vpp-postgres (新增)
# - vpp-redis (新增)
```

### 步骤 2：测试容器间通信

```bash
# 进入 vpp-phase2-simulation 容器
docker exec -it vpp-phase2-simulation bash

# 测试 DNS 解析
nslookup vpp-master
nslookup vpp-postgres
nslookup vpp-redis

# 测试 HTTP 连接
curl -v http://vpp-master:8080/health

# 测试数据库连接
psql -h vpp-postgres -U vpp_user -d vpp_phase2_sim -c "SELECT 1"

# 测试 Redis 连接
redis-cli -h vpp-redis ping
```

### 步骤 3：查看日志确认通信

```bash
# 查看 vpp-phase2-simulation 日志
docker logs vpp-phase2-simulation -f --tail 50

# 应该看到：
# - "Phase 1 Integration Service initialized"
# - "master_url=http://vpp-master:8080"
# - 定期的 POST /api/v1/devices/sync 请求
# - 定期的 GET /health 请求
```

### 步骤 4：从容器内部抓包

```bash
# 进入 vpp-master 容器
docker exec -it vpp-master bash

# 安装 tcpdump
apt-get update && apt-get install -y tcpdump

# 抓包
tcpdump -i eth0 -c 20 'tcp port 8080'

# 应该看到来自 vpp-phase2-simulation 的 HTTP 请求
```

---

## 📊 预期结果

### 连接成功后

```
vpp-phase2-simulation (10.0.1.X)
    ↓ (HTTP POST 每 10 秒)
vpp-master (10.0.1.10)
    ↓ (HTTP 200 OK)
vpp-phase2-simulation
    ↓ (工控协议转换)
vpp-vcc, vpp-upf, vpp-gen
```

### 日志示例

```
[INFO] Phase 1 Integration Service initialized
[INFO] master_url=http://vpp-master:8080
[INFO] Scheduled sync started (interval: 10 seconds)
[INFO] POST /api/v1/devices/sync - 200 OK
[INFO] Scheduled health check started (interval: 30 seconds)
[INFO] GET /health - 200 OK
```

---

## 🎯 现在可以用 Wireshark 抓包了

### 从容器内部抓包

```bash
# 进入 vpp-master 容器
docker exec -it vpp-master bash

# 安装 tcpdump
apt-get update && apt-get install -y tcpdump

# 抓包到文件
tcpdump -i eth0 -w /tmp/capture.pcap 'tcp port 8080'

# 复制到本机
docker cp vpp-master:/tmp/capture.pcap ./capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

### 或者直接用 Docker 命令

```bash
# 直接抓包到本机
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

## 🛠️ 快速命令总结

```bash
# 1. 连接网络
docker network connect network-mirror_vpp-net vpp-phase2-simulation
docker network connect network-mirror_vpp-net vpp-postgres
docker network connect network-mirror_vpp-net vpp-redis

# 2. 重启容器
docker restart vpp-phase2-simulation

# 3. 验证连接
docker exec vpp-phase2-simulation curl -v http://vpp-master:8080/health

# 4. 查看日志
docker logs vpp-phase2-simulation -f --tail 50

# 5. 抓包
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap

# 6. 打开 Wireshark
open capture.pcap
```

---

## ⚠️ 注意事项

1. **网络连接是临时的** - 如果重启容器，需要重新连接
2. **永久解决** - 修改 docker-compose.yml 并重新启动
3. **环境变量** - 确保 VPP_MASTER_URL 设置正确
4. **防火墙** - 确保没有防火墙阻止容器间通信

---

## 📝 下一步

1. ✅ 连接两个 Docker 网络
2. ✅ 验证容器间通信
3. ✅ 查看日志确认 Phase1IntegrationService 正常工作
4. ✅ 从容器内部抓包
5. ✅ 用 Wireshark 分析流量

