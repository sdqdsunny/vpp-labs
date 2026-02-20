# VPP 虚拟电厂微服务架构 - 完整指南

## 🎉 欢迎！

你已经拥有了一个**完整的虚拟电厂微服务架构**！

本文档将帮助你快速了解和使用这个系统。

---

## ⚡ 30 秒快速启动

```bash
# 启动所有微服务
docker-compose -f docker-compose-microservices.yml up -d

# 验证所有服务
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health

# 查看流量
docker exec vpp-sniffer tcpdump -i eth0 -n
```

---

## 📊 系统架构

### 5 个独立容器

| 容器 | 端口 | 功能 |
|------|------|------|
| **vpp-coordinator** | 8080 | 主站节点 - 虚拟电厂协调中心 |
| **vpp-power-generation** | 8081 | 电源侧 - 光伏/风电模拟 |
| **vpp-battery-system** | 8082 | 储能侧 - 电池管理系统 |
| **vpp-load-manager** | 8083 | 需求侧 - 负荷管理 |
| **vpp-sniffer** | - | 流量抓包 - tcpdump 分析工具 |

### 虚拟网络

- **网络名称**：vpp-network
- **子网**：172.20.0.0/16
- **网关**：172.20.0.1

---

## 📁 文档导航

### 🚀 快速开始

**推荐阅读顺序**：

1. **本文档** (README_MICROSERVICES.md) - 总体概览
2. **MICROSERVICES_QUICK_REFERENCE_CN.md** - 快速查询命令
3. **MICROSERVICES_DEPLOYMENT_GUIDE_CN.md** - 详细部署指南

### 📚 详细文档

| 文档 | 用途 |
|------|------|
| MICROSERVICES_ARCHITECTURE_SUMMARY.md | 架构设计总结 |
| MICROSERVICES_ARCHITECTURE_VISUAL.md | 架构可视化 |
| MICROSERVICES_IMPLEMENTATION_SUMMARY.md | 实现总结 |
| MICROSERVICES_DEPLOYMENT_WORKFLOW.md | 完整部署工作流 |
| TASK2_COMPLETION_REPORT.md | 任务完成报告 |

---

## 🚀 常用命令

### 启动和停止

```bash
# 启动所有服务
docker-compose -f docker-compose-microservices.yml up -d

# 停止所有服务
docker-compose -f docker-compose-microservices.yml stop

# 重启所有服务
docker-compose -f docker-compose-microservices.yml restart

# 删除所有容器
docker-compose -f docker-compose-microservices.yml down
```

### 查看状态

```bash
# 查看容器状态
docker-compose -f docker-compose-microservices.yml ps

# 查看日志
docker-compose -f docker-compose-microservices.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose-microservices.yml logs coordinator
```

### 测试连接

```bash
# 进入主站容器
docker exec -it vpp-coordinator bash

# 测试与其他容器的连接
ping vpp-power-generation
curl http://vpp-power-generation:8081/health

# 退出容器
exit
```

### 流量分析

```bash
# 查看所有流量
docker exec vpp-sniffer tcpdump -i eth0 -n

# 查看主站通信
docker exec vpp-sniffer tcpdump -i eth0 -n 'host 172.20.0.2'

# 查看 HTTP 流量
docker exec vpp-sniffer tcpdump -i eth0 -n 'tcp port 8080 or tcp port 8081 or tcp port 8082 or tcp port 8083'
```

---

## 🔗 访问地址

### 主站节点 (vpp-coordinator)

```
http://localhost:8080/health          # 健康检查
http://localhost:8080/analyzer        # 协议分析工具
http://localhost:8080/security        # 安全测试工具
http://localhost:8080/test-dashboard  # 测试仪表板
```

### 电源侧 (vpp-power-generation)

```
http://localhost:8081/health              # 健康检查
http://localhost:8081/generation/status   # 发电状态
```

### 储能侧 (vpp-battery-system)

```
http://localhost:8082/health           # 健康检查
http://localhost:8082/battery/status   # 电池状态
```

### 需求侧 (vpp-load-manager)

```
http://localhost:8083/health        # 健康检查
http://localhost:8083/load/status   # 负荷状态
```

---

## ✅ 验证清单

启动后检查以下项目：

- [ ] 所有容器都在运行：`docker-compose -f docker-compose-microservices.yml ps`
- [ ] 主站健康：`curl http://localhost:8080/health`
- [ ] 电源侧健康：`curl http://localhost:8081/health`
- [ ] 储能侧健康：`curl http://localhost:8082/health`
- [ ] 需求侧健康：`curl http://localhost:8083/health`
- [ ] 容器间可通信：`docker exec vpp-coordinator ping vpp-power-generation`
- [ ] 流量可抓包：`docker exec vpp-sniffer tcpdump -i eth0 -n | head -5`

---

## 🐛 快速故障排查

| 问题 | 解决方案 |
|------|---------|
| 容器无法启动 | `docker-compose -f docker-compose-microservices.yml logs` |
| 端口被占用 | `lsof -i :8080` 然后 `kill -9 <PID>` |
| 容器间无法通信 | `docker network inspect vpp-network` |
| 无法访问服务 | `curl http://localhost:8080/health` 检查 |
| 流量抓包失败 | `docker exec vpp-sniffer ls -la /captures/` |

更多故障排查方法，请参考 **MICROSERVICES_DEPLOYMENT_GUIDE_CN.md**。

---

## 📊 架构优势

✅ **真正的虚拟电厂拓扑**
- 主站、电源侧、储能侧、需求侧独立分离
- 清晰的网络拓扑结构
- 易于理解和维护

✅ **完整的可观测性**
- tcpdump 流量抓包
- Wireshark 流量分析
- 容器间通信可视化
- 网络延迟和丢包分析

✅ **灵活的扩展性**
- 易于添加新的节点
- 支持独立扩展
- 支持集群部署

✅ **真实的网络模拟**
- 虚拟网络拓扑
- 容器间通信
- 网络隔离
- 可以模拟网络故障

---

## 📁 项目结构

```
vpp-project/
├── docker-compose-microservices.yml    # 微服务部署配置
├── vpp-phase2-simulation/
│   ├── Dockerfile                      # 多服务 Dockerfile
│   ├── app_coordinator.py              # 主站服务
│   ├── app_power_generation.py         # 电源侧服务
│   ├── app_battery_system.py           # 储能侧服务
│   ├── app_load_manager.py             # 需求侧服务
│   ├── app.py                          # 原始单体应用
│   └── logs/
│       ├── coordinator/
│       ├── power_generation/
│       ├── battery_system/
│       └── load_manager/
├── captures/                           # 流量抓包文件
├── README_MICROSERVICES.md             # 本文档
├── MICROSERVICES_QUICK_REFERENCE_CN.md # 快速参考
├── MICROSERVICES_DEPLOYMENT_GUIDE_CN.md # 详细指南
├── MICROSERVICES_ARCHITECTURE_SUMMARY.md # 架构总结
├── MICROSERVICES_ARCHITECTURE_VISUAL.md # 架构可视化
├── MICROSERVICES_IMPLEMENTATION_SUMMARY.md # 实现总结
├── MICROSERVICES_DEPLOYMENT_WORKFLOW.md # 部署工作流
└── TASK2_COMPLETION_REPORT.md          # 完成报告
```

---

## 🎯 典型使用场景

### 场景 1: 开发和测试

```bash
# 启动所有服务
docker-compose -f docker-compose-microservices.yml up -d

# 开发新功能，测试各节点间的通信
curl http://localhost:8080/health
curl http://localhost:8081/health

# 查看日志
docker-compose -f docker-compose-microservices.yml logs -f
```

### 场景 2: 流量分析

```bash
# 启动所有服务
docker-compose -f docker-compose-microservices.yml up -d

# 实时查看流量
docker exec vpp-sniffer tcpdump -i eth0 -n

# 或者保存到文件用 Wireshark 分析
# 文件位置: ./captures/vpp-traffic.pcap
```

### 场景 3: 性能测试

```bash
# 启动所有服务
docker-compose -f docker-compose-microservices.yml up -d

# 查看容器资源使用
docker stats

# 查看网络流量
docker exec vpp-sniffer tcpdump -i eth0 -n 'host 172.20.0.2'
```

### 场景 4: 故障排查

```bash
# 启动所有服务
docker-compose -f docker-compose-microservices.yml up -d

# 进入主站容器
docker exec -it vpp-coordinator bash

# 测试与其他容器的连接
ping vpp-power-generation
curl http://vpp-power-generation:8081/health

# 查看网络配置
ip addr show
```

---

## 💡 提示和技巧

### 1. 使用 --rm 参数自动删除容器

```bash
docker run --rm -it vpp-system:latest bash
```

### 2. 使用 -d 在后台运行容器

```bash
docker-compose -f docker-compose-microservices.yml up -d
```

### 3. 使用 logs -f 实时查看日志

```bash
docker-compose -f docker-compose-microservices.yml logs -f
```

### 4. 使用 exec 进入运行中的容器

```bash
docker exec -it vpp-coordinator bash
```

### 5. 使用 inspect 查看容器详细信息

```bash
docker inspect vpp-coordinator
```

---

## 🔄 下一步建议

### 1. 测试部署

```bash
# 启动所有服务
docker-compose -f docker-compose-microservices.yml up -d

# 验证所有服务
docker-compose -f docker-compose-microservices.yml ps

# 检查健康状态
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health
```

### 2. 测试容器间通信

```bash
# 进入主站容器
docker exec -it vpp-coordinator bash

# 测试与其他容器的连接
ping vpp-power-generation
curl http://vpp-power-generation:8081/health
```

### 3. 实现服务间通信

- 在各服务中实现 REST API 调用
- 实现主站协调逻辑
- 实现电源侧、储能侧、需求侧的业务逻辑

### 4. 添加监控和日志

- 配置日志聚合
- 配置告警规则
- 配置性能监控

---

## 📞 获取帮助

### 快速查询

- **快速命令**：MICROSERVICES_QUICK_REFERENCE_CN.md
- **访问地址**：本文档的"访问地址"部分
- **常用命令**：本文档的"常用命令"部分

### 详细指南

- **部署指南**：MICROSERVICES_DEPLOYMENT_GUIDE_CN.md
- **工作流程**：MICROSERVICES_DEPLOYMENT_WORKFLOW.md
- **架构设计**：MICROSERVICES_ARCHITECTURE_SUMMARY.md

### 故障排查

- **快速排查**：本文档的"快速故障排查"部分
- **详细排查**：MICROSERVICES_DEPLOYMENT_GUIDE_CN.md 的"故障排查"部分

---

## 🎓 学习资源

### 推荐阅读顺序

1. **本文档** - 总体概览
2. **MICROSERVICES_QUICK_REFERENCE_CN.md** - 快速查询
3. **MICROSERVICES_DEPLOYMENT_GUIDE_CN.md** - 详细部署
4. **MICROSERVICES_ARCHITECTURE_VISUAL.md** - 架构可视化
5. **MICROSERVICES_DEPLOYMENT_WORKFLOW.md** - 完整工作流

### 相关技术

- Docker 和 Docker Compose
- 虚拟网络和网络隔离
- tcpdump 和 Wireshark
- REST API 和 HTTP 协议
- 微服务架构设计

---

## 🎉 总结

你现在拥有了一个**完整的虚拟电厂微服务架构**！

✅ 5 个独立容器  
✅ 虚拟网络拓扑  
✅ 流量分析工具  
✅ 详细的中文文档  
✅ 快速启动脚本  

**现在就开始吧**：

```bash
docker-compose -f docker-compose-microservices.yml up -d
```

**所有容器都会自动启动并运行！**

---

## 📝 版本信息

- **版本**：1.0
- **创建日期**：2026-02-18
- **Python 版本**：3.11-slim
- **Docker Compose 版本**：3.8

---

**VPP 虚拟电厂微服务架构 - 完整指南** | v1.0 | 2026-02-18

祝你使用愉快！🚀
