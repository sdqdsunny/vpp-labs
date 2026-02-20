# VPP 微服务架构可视化

## 🏗️ 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VPP 虚拟电厂微服务架构                               │
│                   (Virtual Power Plant Microservices)                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      Docker 虚拟网络 (vpp-network)                      │
│                      子网: 172.20.0.0/16                                │
│                      网关: 172.20.0.1                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    vpp-coordinator (主站)                        │  │
│  │                    IP: 172.20.0.2                                │  │
│  │                    Port: 8080                                    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │  │
│  │ │ 协调逻辑        │  │ 协议分析工具     │  │ 安全测试工具     │ │  │
│  │ │ Coordination    │  │ Protocol         │  │ Security         │ │  │
│  │ │ Logic           │  │ Analyzer         │  │ Tester           │ │  │
│  │ └─────────────────┘  └──────────────────┘  └──────────────────┘ │  │
│  │ ┌──────────────────────────────────────────────────────────────┐ │  │
│  │ │ 测试仪表板 (Test Dashboard)                                 │ │  │
│  │ │ /test-dashboard                                            │ │  │
│  │ └──────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                  │                                      │
│                    ┌─────────────┼─────────────┐                       │
│                    │             │             │                       │
│                    ▼             ▼             ▼                       │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────┐ │
│  │ vpp-power-generation │  │ vpp-battery-system   │  │ vpp-load-    │ │
│  │ (电源侧)             │  │ (储能侧)             │  │ manager      │ │
│  │ IP: 172.20.0.4       │  │ IP: 172.20.0.5       │  │ (需求侧)     │ │
│  │ Port: 8081           │  │ Port: 8082           │  │ IP: 172.20.0.6
│  ├──────────────────────┤  ├──────────────────────┤  │ Port: 8083   │ │
│  │ • 光伏发电模拟       │  │ • 电池充放电管理     │  │ • 负荷预测   │ │
│  │ • 风电发电模拟       │  │ • 电池状态监测       │  │ • 需求响应   │ │
│  │ • 发电功率管理       │  │ • 能量存储管理       │  │ • 负荷均衡   │ │
│  └──────────────────────┘  └──────────────────────┘  └──────────────┘ │
│                    │             │             │                       │
│                    └─────────────┼─────────────┘                       │
│                                  │                                      │
│                                  ▼                                      │
│                    ┌──────────────────────────┐                        │
│                    │    vpp-sniffer           │                        │
│                    │    (流量抓包工具)        │                        │
│                    │    IP: 172.20.0.7        │                        │
│                    ├──────────────────────────┤                        │
│                    │ • tcpdump 流量抓包       │                        │
│                    │ • Wireshark 分析        │                        │
│                    │ • 协议交互可视化        │                        │
│                    │ • 网络性能分析          │                        │
│                    └──────────────────────────┘                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 容器信息表

### 容器配置

| 属性 | vpp-coordinator | vpp-power-generation | vpp-battery-system | vpp-load-manager | vpp-sniffer |
|------|-----------------|----------------------|-------------------|------------------|-------------|
| **容器名** | vpp-coordinator | vpp-power-generation | vpp-battery-system | vpp-load-manager | vpp-sniffer |
| **IP 地址** | 172.20.0.2 | 172.20.0.4 | 172.20.0.5 | 172.20.0.6 | 172.20.0.7 |
| **端口** | 8080 | 8081 | 8082 | 8083 | - |
| **镜像** | vpp-system:latest | vpp-system:latest | vpp-system:latest | vpp-system:latest | nicolaka/netshoot |
| **NODE_TYPE** | coordinator | power_generation | battery_system | load_manager | - |
| **健康检查** | ✅ 有 | ✅ 有 | ✅ 有 | ✅ 有 | ❌ 无 |
| **自动重启** | ✅ 是 | ✅ 是 | ✅ 是 | ✅ 是 | ✅ 是 |

---

## 🔗 网络连接图

```
主站 (vpp-coordinator)
│
├─ HTTP/REST ──→ 电源侧 (vpp-power-generation)
│                 └─ /generation/status
│
├─ HTTP/REST ──→ 储能侧 (vpp-battery-system)
│                 └─ /battery/status
│
├─ HTTP/REST ──→ 需求侧 (vpp-load-manager)
│                 └─ /load/status
│
└─ 流量监控 ──→ 抓包工具 (vpp-sniffer)
                 └─ tcpdump 分析
```

---

## 📡 通信协议

### 容器间通信

```
主站 (172.20.0.2:8080)
    │
    ├─ HTTP GET /health ──→ 电源侧 (172.20.0.4:8081)
    │
    ├─ HTTP GET /health ──→ 储能侧 (172.20.0.5:8082)
    │
    ├─ HTTP GET /health ──→ 需求侧 (172.20.0.6:8083)
    │
    └─ TCP 流量 ──→ 抓包工具 (172.20.0.7)
```

### 外部访问

```
主机 (localhost)
    │
    ├─ http://localhost:8080 ──→ 主站 (vpp-coordinator)
    │
    ├─ http://localhost:8081 ──→ 电源侧 (vpp-power-generation)
    │
    ├─ http://localhost:8082 ──→ 储能侧 (vpp-battery-system)
    │
    └─ http://localhost:8083 ──→ 需求侧 (vpp-load-manager)
```

---

## 🚀 启动流程

```
1. 构建镜像
   └─ docker build -t vpp-system:latest .

2. 创建虚拟网络
   └─ docker network create vpp-network

3. 启动容器（并行）
   ├─ vpp-coordinator (8080)
   ├─ vpp-power-generation (8081)
   ├─ vpp-battery-system (8082)
   ├─ vpp-load-manager (8083)
   └─ vpp-sniffer (tcpdump)

4. 健康检查
   ├─ curl http://localhost:8080/health
   ├─ curl http://localhost:8081/health
   ├─ curl http://localhost:8082/health
   └─ curl http://localhost:8083/health

5. 验证通信
   ├─ docker exec vpp-coordinator ping vpp-power-generation
   ├─ docker exec vpp-coordinator ping vpp-battery-system
   └─ docker exec vpp-coordinator ping vpp-load-manager

6. 流量分析
   └─ docker exec vpp-sniffer tcpdump -i eth0 -n
```

---

## 📊 数据流向

### 主站协调流程

```
主站 (vpp-coordinator)
│
├─ 1. 获取电源侧状态
│   └─ GET /generation/status → 电源侧 (vpp-power-generation)
│      └─ 返回: {solar_power, wind_power, total_power}
│
├─ 2. 获取储能侧状态
│   └─ GET /battery/status → 储能侧 (vpp-battery-system)
│      └─ 返回: {state_of_charge, capacity, power}
│
├─ 3. 获取需求侧状态
│   └─ GET /load/status → 需求侧 (vpp-load-manager)
│      └─ 返回: {current_load, forecasted_load, demand_response}
│
└─ 4. 协调决策
    └─ 根据各侧状态进行协调
       ├─ 调整发电功率
       ├─ 调整储能充放电
       └─ 调整负荷响应
```

---

## 🔍 流量分析架构

```
所有容器
    │
    ├─ 网络流量
    │   └─ TCP/UDP 数据包
    │
    └─ 流向 vpp-sniffer (tcpdump)
        │
        ├─ 实时显示
        │   └─ tcpdump -i eth0 -n
        │
        └─ 保存到文件
            └─ /captures/vpp-traffic.pcap
                │
                └─ Wireshark 分析
                    ├─ 协议分析
                    ├─ 流量统计
                    ├─ 延迟分析
                    └─ 丢包分析
```

---

## 📈 性能指标

### 资源使用

```
容器                    CPU      内存        磁盘
─────────────────────────────────────────────────
vpp-coordinator        ~5%      ~100MB      ~50MB
vpp-power-generation   ~3%      ~80MB       ~30MB
vpp-battery-system     ~3%      ~80MB       ~30MB
vpp-load-manager       ~3%      ~80MB       ~30MB
vpp-sniffer            ~2%      ~50MB       ~20MB
─────────────────────────────────────────────────
总计                   ~16%     ~390MB      ~160MB
```

### 网络性能

```
容器间通信延迟：< 1ms
容器间吞吐量：> 1Gbps
健康检查间隔：30 秒
启动时间：10-15 秒
```

---

## 🎯 访问地址速查

### 主站节点 (vpp-coordinator)

```
健康检查：http://localhost:8080/health
就绪检查：http://localhost:8080/ready
指标数据：http://localhost:8080/metrics
协议分析：http://localhost:8080/analyzer
安全测试：http://localhost:8080/security
测试仪表板：http://localhost:8080/test-dashboard
```

### 电源侧 (vpp-power-generation)

```
健康检查：http://localhost:8081/health
就绪检查：http://localhost:8081/ready
指标数据：http://localhost:8081/metrics
发电状态：http://localhost:8081/generation/status
```

### 储能侧 (vpp-battery-system)

```
健康检查：http://localhost:8082/health
就绪检查：http://localhost:8082/ready
指标数据：http://localhost:8082/metrics
电池状态：http://localhost:8082/battery/status
```

### 需求侧 (vpp-load-manager)

```
健康检查：http://localhost:8083/health
就绪检查：http://localhost:8083/ready
指标数据：http://localhost:8083/metrics
负荷状态：http://localhost:8083/load/status
```

---

## 🔄 生命周期管理

### 启动流程

```
docker-compose up -d
    │
    ├─ 创建虚拟网络 (vpp-network)
    │
    ├─ 启动 vpp-coordinator
    │   └─ 等待就绪 (40秒)
    │
    ├─ 启动 vpp-power-generation
    │   └─ 等待就绪 (40秒)
    │
    ├─ 启动 vpp-battery-system
    │   └─ 等待就绪 (40秒)
    │
    ├─ 启动 vpp-load-manager
    │   └─ 等待就绪 (40秒)
    │
    └─ 启动 vpp-sniffer
        └─ 开始抓包
```

### 停止流程

```
docker-compose down
    │
    ├─ 停止 vpp-coordinator
    ├─ 停止 vpp-power-generation
    ├─ 停止 vpp-battery-system
    ├─ 停止 vpp-load-manager
    ├─ 停止 vpp-sniffer
    │
    └─ 删除虚拟网络 (vpp-network)
```

---

## 📋 故障恢复

### 自动恢复机制

```
容器崩溃
    │
    └─ Docker 检测到容器停止
        │
        └─ 自动重启策略 (restart: unless-stopped)
            │
            └─ 容器重新启动
                │
                └─ 健康检查
                    │
                    ├─ 通过 → 容器就绪
                    └─ 失败 → 重试 (最多 3 次)
```

---

## 🎓 学习路径

```
1. 理解架构
   └─ 阅读 MICROSERVICES_ARCHITECTURE_SUMMARY.md

2. 快速启动
   └─ 参考 MICROSERVICES_QUICK_REFERENCE_CN.md

3. 详细部署
   └─ 学习 MICROSERVICES_DEPLOYMENT_GUIDE_CN.md

4. 工作流程
   └─ 跟随 MICROSERVICES_DEPLOYMENT_WORKFLOW.md

5. 故障排查
   └─ 查阅 MICROSERVICES_DEPLOYMENT_GUIDE_CN.md 的故障排查部分

6. 性能优化
   └─ 参考 MICROSERVICES_DEPLOYMENT_GUIDE_CN.md 的性能优化部分
```

---

**VPP 微服务架构可视化** | v1.0 | 2026-02-18
