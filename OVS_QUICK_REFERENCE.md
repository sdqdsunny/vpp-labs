# OVS网络流量镜像 - 快速参考

## 部署清单

### Phase 1: 环境准备 (15分钟)

- [ ] 安装OVS: `sudo apt-get install -y openvswitch-switch`
- [ ] 启动OVS: `sudo systemctl start openvswitch-switch`
- [ ] 验证OVS: `ovs-vsctl --version`
- [ ] 安装Docker: `curl -fsSL https://get.docker.com | sh`
- [ ] 安装Docker Compose: `sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`

### Phase 2: 项目部署 (10分钟)

```bash
# 1. 进入项目目录
cd network-mirror

# 2. 构建镜像
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 验证部署
docker-compose ps
```

### Phase 3: 验证检查 (5分钟)

```bash
# 检查OVS bridge
ovs-vsctl show

# 检查端口
ovs-ofctl dump-ports br-vpp

# 检查Mirror规则
ovs-vsctl list Mirror

# 查看分析工具日志
docker-compose logs vpp-analyzer
```

---

## 常用命令速查

### OVS命令

| 命令 | 功能 |
|------|------|
| `ovs-vsctl show` | 显示OVS配置 |
| `ovs-ofctl dump-ports br-vpp` | 显示端口统计 |
| `ovs-ofctl dump-flows br-vpp` | 显示流表 |
| `ovs-vsctl list Mirror` | 显示Mirror配置 |
| `ovs-ofctl snoop br-vpp` | 实时监控流量 |

### Docker命令

| 命令 | 功能 |
|------|------|
| `docker-compose ps` | 显示容器状态 |
| `docker-compose logs -f [service]` | 查看日志 |
| `docker-compose exec [service] bash` | 进入容器 |
| `docker-compose down` | 停止服务 |
| `docker-compose restart [service]` | 重启服务 |

### 网络诊断

| 命令 | 功能 |
|------|------|
| `ping 10.0.1.10` | 测试主站连通性 |
| `tcpdump -i veth-analyzer -w capture.pcap` | 手动抓包 |
| `wireshark capture.pcap` | 分析pcap文件 |

---

## 故障排查速查表

| 症状 | 原因 | 解决方案 |
|------|------|--------|
| Bridge创建失败 | OVS未启动 | `sudo systemctl start openvswitch-switch` |
| veth-pair创建失败 | 权限不足 | 使用`sudo`或`privileged: true` |
| 无法捕获流量 | 接口名称错误 | 检查`CAPTURE_INTERFACE`环境变量 |
| 流量未镜像 | Mirror规则未生效 | 重新运行`ovs-init.sh` |
| 容器无法通信 | 网络配置错误 | 检查`docker-compose.yml`中的网络配置 |

---

## 性能优化建议

### OVS优化

```bash
# 启用DPDK加速（可选）
ovs-vsctl set Open_vSwitch . other_config:dpdk-init=true

# 配置流表缓存
ovs-vsctl set Open_vSwitch . other_config:flow-limit=200000

# 启用多线程
ovs-vsctl set Open_vSwitch . other_config:n-handler-threads=4
```

### 分析工具优化

- 使用AF_PACKET加速捕获
- 配置采样率降低负载
- 异步处理数据包
- 定期轮转pcap文件

---

## 监控指标

### 关键指标

| 指标 | 目标值 | 检查命令 |
|------|--------|---------|
| 数据包丢失率 | < 0.1% | `ovs-ofctl dump-ports br-vpp` |
| 镜像延迟 | < 1ms | `tcpdump -i mirror-port` |
| CPU使用率 | < 30% | `docker stats` |
| 内存使用率 | < 500MB | `docker stats` |

### 监控命令

```bash
# 实时监控容器资源
docker stats

# 查看OVS性能
ovs-appctl dpif/show

# 查看流表统计
ovs-ofctl dump-aggregate br-vpp
```

---

## 日志位置

| 组件 | 日志位置 |
|------|---------|
| 主站 | `./logs/master/` |
| VCC | `./logs/vcc/` |
| UPF | `./logs/upf/` |
| 设备 | `./logs/gen/` |
| 分析工具 | `./logs/analyzer/` |
| pcap文件 | `./pcap/` |

---

## 常见问题

**Q: 如何重置OVS配置?**
```bash
docker-compose down
bash scripts/ovs-cleanup.sh
docker-compose up -d
```

**Q: 如何导出pcap文件?**
```bash
# pcap文件自动保存在./pcap/目录
ls -la ./pcap/
```

**Q: 如何修改镜像规则?**
```bash
# 编辑ovs-init.sh中的Mirror配置
# 然后重新运行初始化脚本
bash scripts/ovs-init.sh
```

**Q: 如何添加新的业务端口?**
```bash
# 在ovs-init.sh中添加新的create_veth_port调用
# 然后重新运行初始化脚本
```

---

## 相关文档

- [完整规范文档](OVS_NETWORK_TRAFFIC_MIRRORING_SPECIFICATION.md)
- [OVS官方文档](http://openvswitch.org/)
- [Docker Compose文档](https://docs.docker.com/compose/)

---

## 版本信息

- OVS版本: >= 2.13
- Docker版本: >= 20.10
- Docker Compose版本: >= 1.29
- Python版本: 3.10+

