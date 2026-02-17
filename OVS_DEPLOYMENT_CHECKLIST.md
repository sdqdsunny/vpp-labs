# OVS网络流量镜像 - 部署检查清单

**项目**: VPP OVS网络流量镜像系统  
**日期**: 2026年2月17日  
**版本**: 1.0

---

## 📋 部署前检查

### 系统要求

- [ ] Linux kernel >= 4.15 (`uname -r`)
- [ ] 至少2GB可用内存 (`free -h`)
- [ ] 至少10GB可用磁盘空间 (`df -h`)
- [ ] 网络连接正常 (`ping 8.8.8.8`)

### 软件依赖

- [ ] Docker已安装 (`docker --version`)
- [ ] Docker Compose已安装 (`docker-compose --version`)
- [ ] OVS已安装 (`ovs-vsctl --version`)
- [ ] Python 3.10+ (`python3 --version`)
- [ ] Git已安装 (`git --version`)

### 权限检查

- [ ] 当前用户可以运行Docker (`docker ps`)
- [ ] 当前用户可以运行OVS命令 (`ovs-vsctl show`)
- [ ] 当前用户有sudo权限 (`sudo -l`)

---

## 🔧 环境准备

### 安装OVS

```bash
# [ ] 更新包管理器
sudo apt-get update

# [ ] 安装OVS
sudo apt-get install -y openvswitch-switch openvswitch-common

# [ ] 启动OVS服务
sudo systemctl start openvswitch-switch

# [ ] 启用OVS开机自启
sudo systemctl enable openvswitch-switch

# [ ] 验证OVS安装
ovs-vsctl --version
```

### 安装Docker

```bash
# [ ] 下载Docker安装脚本
curl -fsSL https://get.docker.com -o get-docker.sh

# [ ] 运行安装脚本
sudo sh get-docker.sh

# [ ] 将当前用户添加到docker组
sudo usermod -aG docker $USER

# [ ] 重新登录或运行以下命令
newgrp docker

# [ ] 验证Docker安装
docker --version
```

### 安装Docker Compose

```bash
# [ ] 下载Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# [ ] 设置执行权限
sudo chmod +x /usr/local/bin/docker-compose

# [ ] 验证安装
docker-compose --version
```

---

## 📦 项目部署

### 获取项目代码

```bash
# [ ] 克隆项目仓库
git clone <repo-url>

# [ ] 进入项目目录
cd network-mirror

# [ ] 验证项目结构
ls -la
```

### 构建Docker镜像

```bash
# [ ] 构建所有镜像
docker-compose build

# [ ] 验证镜像构建成功
docker images | grep vpp

# [ ] 检查镜像大小
docker images --format "table {{.Repository}}\t{{.Size}}"
```

### 启动服务

```bash
# [ ] 启动所有服务
docker-compose up -d

# [ ] 等待服务启动 (约30秒)
sleep 30

# [ ] 验证所有容器运行
docker-compose ps

# [ ] 检查容器日志
docker-compose logs --tail=20
```

---

## ✅ 部署验证

### OVS配置验证

```bash
# [ ] 检查bridge创建
ovs-vsctl show | grep -A 20 "Bridge br-vpp"

# [ ] 检查端口创建
ovs-ofctl dump-ports br-vpp | grep -E "veth|mirror"

# [ ] 检查Mirror规则
ovs-vsctl list Mirror | grep -E "name|select-all|output-port"

# [ ] 检查流表
ovs-ofctl dump-flows br-vpp | head -5
```

### 容器验证

```bash
# [ ] 检查主站容器
docker-compose exec vpp-master curl -s http://localhost:8080/health

# [ ] 检查VCC容器
docker-compose exec vpp-vcc curl -s http://localhost:8081/health

# [ ] 检查UPF容器
docker-compose exec vpp-upf curl -s http://localhost:8082/health

# [ ] 检查分析工具日志
docker-compose logs vpp-analyzer | tail -20
```

### 网络连通性验证

```bash
# [ ] 测试主站连通性
ping -c 3 10.0.1.10

# [ ] 测试VCC连通性
ping -c 3 10.0.1.20

# [ ] 测试UPF连通性
ping -c 3 10.0.1.30

# [ ] 测试设备连通性
ping -c 3 10.0.1.40

# [ ] 测试分析工具连通性
ping -c 3 10.0.1.50
```

### 流量镜像验证

```bash
# [ ] 检查pcap文件生成
ls -la ./pcap/

# [ ] 检查pcap文件大小
du -sh ./pcap/

# [ ] 检查分析工具统计
docker-compose logs vpp-analyzer | grep "Statistics"

# [ ] 使用tcpdump验证镜像
sudo tcpdump -i mirror-port -c 10 -n
```

---

## 📊 性能验证

### 资源使用情况

```bash
# [ ] 检查容器资源使用
docker stats --no-stream

# [ ] 检查OVS内存使用
ps aux | grep ovs

# [ ] 检查系统负载
uptime

# [ ] 检查磁盘使用
df -h
```

### 流量统计

```bash
# [ ] 检查端口流量
ovs-ofctl dump-ports br-vpp

# [ ] 检查流表统计
ovs-ofctl dump-aggregate br-vpp

# [ ] 检查Mirror统计
ovs-vsctl get-statistics Mirror m0
```

---

## 🔍 故障排查

### 常见问题检查

| 问题 | 检查命令 | 预期结果 |
|------|---------|--------|
| OVS未启动 | `systemctl status openvswitch-switch` | active (running) |
| Bridge不存在 | `ovs-vsctl show` | 显示br-vpp |
| 端口未创建 | `ovs-ofctl dump-ports br-vpp` | 显示所有端口 |
| Mirror未配置 | `ovs-vsctl list Mirror` | 显示Mirror配置 |
| 容器未运行 | `docker-compose ps` | 所有容器状态为Up |
| 无法捕获流量 | `docker-compose logs vpp-analyzer` | 显示捕获统计 |

### 日志检查

```bash
# [ ] 检查主站日志
docker-compose logs vpp-master | tail -50

# [ ] 检查VCC日志
docker-compose logs vpp-vcc | tail -50

# [ ] 检查UPF日志
docker-compose logs vpp-upf | tail -50

# [ ] 检查分析工具日志
docker-compose logs vpp-analyzer | tail -50

# [ ] 检查系统日志
sudo journalctl -u openvswitch-switch -n 50
```

---

## 🚀 生产部署

### 性能优化

```bash
# [ ] 启用OVS DPDK加速（可选）
ovs-vsctl set Open_vSwitch . other_config:dpdk-init=true

# [ ] 配置流表缓存
ovs-vsctl set Open_vSwitch . other_config:flow-limit=200000

# [ ] 启用多线程
ovs-vsctl set Open_vSwitch . other_config:n-handler-threads=4

# [ ] 验证配置
ovs-vsctl get Open_vSwitch . other_config
```

### 监控设置

```bash
# [ ] 配置日志收集
docker-compose logs -f > deployment.log &

# [ ] 配置性能监控
watch -n 1 'docker stats --no-stream'

# [ ] 配置OVS监控
watch -n 1 'ovs-ofctl dump-ports br-vpp'
```

### 备份配置

```bash
# [ ] 备份OVS配置
sudo cp -r /etc/openvswitch /etc/openvswitch.backup

# [ ] 备份Docker Compose配置
cp docker-compose.yml docker-compose.yml.backup

# [ ] 备份脚本
cp -r scripts scripts.backup
```

---

## 📝 文档检查

- [ ] 已阅读完整规范: `OVS_NETWORK_TRAFFIC_MIRRORING_SPECIFICATION.md`
- [ ] 已阅读快速参考: `OVS_QUICK_REFERENCE.md`
- [ ] 已阅读项目说明: `network-mirror/README.md`
- [ ] 已保存部署清单副本
- [ ] 已记录部署时间和版本信息

---

## 🎯 部署完成确认

### 最终检查

- [ ] 所有系统要求满足
- [ ] 所有软件依赖安装
- [ ] 所有OVS配置正确
- [ ] 所有容器正常运行
- [ ] 所有网络连通性正常
- [ ] 流量镜像正常工作
- [ ] 分析工具正常捕获
- [ ] 性能指标达到目标
- [ ] 所有日志正常输出
- [ ] 备份配置已完成

### 部署信息记录

```
部署日期: _______________
部署人员: _______________
部署环境: _______________
OVS版本: _______________
Docker版本: _______________
Python版本: _______________
部署耗时: _______________
备注: _______________
```

---

## 📞 后续支持

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service-name]

# 重启服务
docker-compose restart [service-name]

# 停止服务
docker-compose down

# 清理资源
docker-compose down -v
```

### 获取帮助

1. 查看快速参考: `OVS_QUICK_REFERENCE.md`
2. 查看完整规范: `OVS_NETWORK_TRAFFIC_MIRRORING_SPECIFICATION.md`
3. 查看项目说明: `network-mirror/README.md`
4. 查看日志文件: `./logs/*/`

---

**部署检查清单完成日期**: _______________  
**检查人员签名**: _______________

