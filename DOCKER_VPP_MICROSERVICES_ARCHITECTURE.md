# VPP 虚拟电厂微服务架构设计

## 🏗️ 架构概述

### 当前问题
- 所有组件在一个黑盒子里
- 没有网络拓扑
- 无法进行流量镜像和抓包分析
- 不像真正的虚拟电厂

### 解决方案
构建一个**真正的微服务架构**，包含：
- 独立的微服务容器（主站、电源侧、储能侧、需求侧）
- OVS虚拟交换机进行流量管理
- 完整的网络拓扑
- 流量镜像和抓包能力
- 可视化的网络拓扑

---

## 🏛️ 微服务架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     VPP 虚拟电厂系统                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              虚拟网络 (vpp-network)                      │  │
│  │  - 容器间通信                                            │  │
│  │  - 网络隔离                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ↑              ↑              ↑              ↑           │
│         │              │              │              │           │
│    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐     │
│    │  主站   │    │  电源侧  │   │  储能侧  │   │  需求侧  │     │
│    │ Master  │    │Generation│  │ Storage │   │ Demand  │     │
│    │ Node    │    │ Node      │  │ Node    │   │ Node    │     │
│    └────┬────┘    └────┬────┘   └────┬────┘   └────┬────┘     │
│         │              │              │              │           │
│    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐     │
│    │ API     │    │ Protocol │   │ Protocol │   │ Protocol │    │
│    │ Server  │    │ Adapter  │   │ Adapter  │   │ Adapter  │    │
│    │ :8080   │    │ :8081    │   │ :8082    │   │ :8083    │    │
│    └────┬────┘    └────┬────┘   └────┬────┘   └────┬────┘     │
│         │              │              │              │           │
│    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐     │
│    │ Database │    │ Database │   │ Database │   │ Database │    │
│    │ (SQLite) │    │ (SQLite) │   │ (SQLite) │   │ (SQLite) │    │
│    └──────────┘    └──────────┘   └──────────┘   └──────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           流量分析容器                                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  - tcpdump (流量抓包)                                    │  │
│  │  - Wireshark (流量分析)                                  │  │
│  │  - 网络拓扑可视化                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 微服务容器设计

### 1. 主站节点 (Master Node)
```
容器名: vpp-master
端口: 8080
功能:
  - 虚拟电厂协调
  - 能量管理
  - 实时监控
  - API 网关
```

### 2. 电源侧节点 (Generation Node)
```
容器名: vpp-generation
端口: 8081
功能:
  - 光伏/风电模拟
  - 发电量预测
  - 功率控制
  - 协议适配 (Modbus, IEC61850)
```

### 3. 储能侧节点 (Storage Node)
```
容器名: vpp-storage
端口: 8082
功能:
  - 电池管理系统 (BMS)
  - 充放电控制
  - 状态监测
  - 协议适配 (OPC UA, MQTT)
```

### 4. 需求侧节点 (Demand Node)
```
容器名: vpp-demand
端口: 8083
功能:
  - 负荷预测
  - 需求响应
  - 用户管理
  - 协议适配 (DNP3, XMPP)
```

### 5. OVS 虚拟交换机
```
容器名: vpp-ovs
功能:
  - 虚拟网络交换
  - 流量镜像 (SPAN)
  - QoS 管理
  - 网络隔离
```

### 6. 监控和分析
```
容器名: vpp-monitor
功能:
  - Prometheus 指标收集
  - Grafana 可视化
  - tcpdump 流量抓包
  - 日志聚合
```

---

## 🌐 网络拓扑

### 虚拟网络设计

```
┌─────────────────────────────────────────────────────────┐
│           Docker 虚拟网络 (vpp-network)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Master (172.20.0.2)                                   │
│     ↓                                                   │
│  虚拟网络 (172.20.0.0/16)                               │
│     ↓                                                   │
│  ┌──┴──┬──────┬──────┐                                 │
│  ↓     ↓      ↓      ↓                                  │
│ Gen  Storage Demand tcpdump                            │
│ (4)   (5)     (6)    (7)                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 网络配置

| 容器 | IP地址 | 端口 | 说明 |
|------|--------|------|------|
| Master | 172.20.0.2 | 8080 | 主站节点 |
| Generation | 172.20.0.4 | 8081 | 电源侧 |
| Storage | 172.20.0.5 | 8082 | 储能侧 |
| Demand | 172.20.0.6 | 8083 | 需求侧 |
| tcpdump | 172.20.0.7 | - | 流量抓包 |

---

## 🔄 通信流程

### 能量流向

```
Generation (发电)
    ↓
    └→ OVS Switch (流量转发)
         ↓
         ├→ Master (协调)
         ├→ Storage (充电)
         └→ Demand (供电)
```

### 控制流向

```
Master (主站)
    ↓
    ├→ Generation (控制发电)
    ├→ Storage (控制充放电)
    └→ Demand (控制需求响应)
```

### 监控流向

```
所有节点
    ↓
    └→ Monitor (Prometheus)
         ↓
         └→ Grafana (可视化)
```

---

## 🔍 流量抓包和分析

### tcpdump 流量抓包

```bash
# 查看抓包文件
ls -lh captures/

# 实时查看流量
docker exec vpp-tcpdump tcpdump -i eth0 -n

# 按协议统计
docker exec vpp-tcpdump tcpdump -i eth0 -n | grep -E "TCP|UDP|ICMP"

# 保存到文件进行离线分析
docker exec vpp-tcpdump tcpdump -i eth0 -w /captures/traffic.pcap
```

### 使用 Wireshark 分析

```bash
# 将抓包文件复制到本机
cp captures/vpp-traffic.pcap ~/Downloads/

# 在本机用 Wireshark 打开分析
wireshark ~/Downloads/vpp-traffic.pcap
```

### 流量分析示例

```bash
# 查看所有 TCP 连接
docker exec vpp-tcpdump tcpdump -i eth0 -n 'tcp'

# 查看特定端口的流量
docker exec vpp-tcpdump tcpdump -i eth0 -n 'port 8080'

# 查看主站和电源侧之间的通信
docker exec vpp-tcpdump tcpdump -i eth0 -n 'host 172.20.0.2 and host 172.20.0.4'

# 查看所有 HTTP 流量
docker exec vpp-tcpdump tcpdump -i eth0 -n 'tcp port 80 or tcp port 8080'
```

---

## 📊 流量分析和可视化

### 容器间通信分析

通过 tcpdump 可以实时观察各个微服务之间的通信：

```bash
# 启动微服务架构
docker-compose -f docker-compose-microservices.yml up -d

# 查看实时流量
docker exec vpp-tcpdump tcpdump -i eth0 -n

# 查看主站和各节点的通信
docker exec vpp-tcpdump tcpdump -i eth0 -n 'host 172.20.0.2'

# 查看电源侧和储能侧的通信
docker exec vpp-tcpdump tcpdump -i eth0 -n 'host 172.20.0.4 or host 172.20.0.5'
```

### 网络拓扑可视化

```bash
# 查看容器网络连接
docker network inspect vpp-network

# 查看容器间的通信关系
docker exec vpp-master curl -s http://vpp-generation:8081/health
docker exec vpp-master curl -s http://vpp-storage:8082/health
docker exec vpp-master curl -s http://vpp-demand:8083/health
```

---

## 🚀 部署方式

### 完整的微服务 docker-compose.yml

```yaml
version: '3.8'

services:
  # OVS 虚拟交换机
  ovs:
    image: openvswitch/ovs:latest
    container_name: vpp-ovs
    privileged: true
    networks:
      vpp-network:
        ipv4_address: 172.20.0.3
    volumes:
      - /var/run/openvswitch:/var/run/openvswitch

  # 主站节点
  master:
    build:
      context: .
      dockerfile: vpp-phase2-simulation/Dockerfile
    container_name: vpp-master
    environment:
      - NODE_TYPE=master
      - API_PORT=8080
    ports:
      - "8080:8080"
    networks:
      vpp-network:
        ipv4_address: 172.20.0.2
    depends_on:
      - ovs

  # 电源侧节点
  generation:
    build:
      context: .
      dockerfile: vpp-phase2-simulation/Dockerfile
    container_name: vpp-generation
    environment:
      - NODE_TYPE=generation
      - API_PORT=8081
    ports:
      - "8081:8081"
    networks:
      vpp-network:
        ipv4_address: 172.20.0.4
    depends_on:
      - ovs

  # 储能侧节点
  storage:
    build:
      context: .
      dockerfile: vpp-phase2-simulation/Dockerfile
    container_name: vpp-storage
    environment:
      - NODE_TYPE=storage
      - API_PORT=8082
    ports:
      - "8082:8082"
    networks:
      vpp-network:
        ipv4_address: 172.20.0.5
    depends_on:
      - ovs

  # 需求侧节点
  demand:
    build:
      context: .
      dockerfile: vpp-phase2-simulation/Dockerfile
    container_name: vpp-demand
    environment:
      - NODE_TYPE=demand
      - API_PORT=8083
    ports:
      - "8083:8083"
    networks:
      vpp-network:
        ipv4_address: 172.20.0.6
    depends_on:
      - ovs

  # 监控容器
  monitor:
    image: prom/prometheus:latest
    container_name: vpp-monitor
    ports:
      - "9090:9090"
    networks:
      vpp-network:
        ipv4_address: 172.20.0.7
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  # Grafana 可视化
  grafana:
    image: grafana/grafana:latest
    container_name: vpp-grafana
    ports:
      - "3000:3000"
    networks:
      vpp-network:
        ipv4_address: 172.20.0.8
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

networks:
  vpp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

---

## 📋 启动命令

```bash
# 启动完整的微服务架构
docker-compose -f docker-compose-microservices.yml up -d

# 查看所有容器
docker-compose -f docker-compose-microservices.yml ps

# 查看网络拓扑
docker network inspect vpp-network

# 查看实时流量
docker exec vpp-tcpdump tcpdump -i eth0 -n

# 查看抓包文件
ls -lh captures/

# 查看容器日志
docker-compose -f docker-compose-microservices.yml logs -f

# 停止所有容器
docker-compose -f docker-compose-microservices.yml down
```

---

## 🎯 优势

✅ **真正的虚拟电厂拓扑**
- 主站、电源侧、储能侧、需求侧独立分离
- 清晰的网络拓扑结构

✅ **完整的可观测性**
- OVS 流量镜像
- tcpdump 抓包分析
- Prometheus 指标收集
- Grafana 可视化

✅ **灵活的扩展性**
- 易于添加新的节点
- 支持独立扩展
- 支持集群部署

✅ **真实的网络模拟**
- 虚拟网络拓扑
- 网络延迟模拟
- QoS 管理
- 流量控制

---

## 📚 相关文档

- `docker-compose-microservices.yml` - 微服务部署配置
- `NETWORK_TOPOLOGY_GUIDE.md` - 网络拓扑指南
- `TRAFFIC_ANALYSIS_GUIDE.md` - 流量分析指南

---

**VPP 虚拟电厂微服务架构设计** | v1.0 | 2026-02-18
