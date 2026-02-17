# Wireshark 工控协议流量抓包指南

## 通信现状确认

✅ **是的，通信正在发生！**

根据代码分析，vpp-phase2-simulation 中的 Phase1IntegrationService 已配置为：

1. **主动定期同步** - 每 10 秒向主站发送一次数据
2. **健康检查** - 每 30 秒检查一次连接状态
3. **多种协议支持** - IEC61850, Modbus, DNP3, MQTT

### 通信流程

```
vpp-phase2-simulation (容器内)
    ↓ (HTTP POST 每 10 秒)
vpp-master (主站)
    ↓ (HTTP 响应)
vpp-phase2-simulation
    ↓ (工控协议转换)
各模块 (vpp-vcc, vpp-upf, vpp-gen)
```

---

## 在 macOS 上用 Wireshark 抓包

### 方案 1：抓 Docker 容器间的流量（推荐）

#### 步骤 1：找到 Docker 网络接口

```bash
# 列出所有网络接口
ifconfig | grep -E "^[a-z]|inet"

# 或者用 Docker 命令查看网络
docker network inspect network-mirror_vpp-net
```

#### 步骤 2：启动 Wireshark 并选择接口

1. 打开 Wireshark
2. 选择 **Capture → Interfaces**
3. 查找 Docker 相关的接口（通常是 `docker0` 或 `br-` 开头）
4. 点击 **Start** 开始抓包

#### 步骤 3：设置过滤器

在 Wireshark 的 Filter 栏输入：

```
# 抓所有 HTTP 流量
http

# 抓特定端口的流量（vpp-master 内部端口 8080）
tcp.port == 8080

# 抓特定 IP 的流量
ip.src == 10.0.1.10 or ip.dst == 10.0.1.10

# 抓工控协议
tcp.port == 102 or tcp.port == 502 or tcp.port == 20000 or tcp.port == 1883

# 组合过滤
(tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082) and http
```

---

### 方案 2：从 Docker 容器内部抓包

#### 步骤 1：进入容器并安装 tcpdump

```bash
# 进入 vpp-master 容器
docker exec -it vpp-master bash

# 安装 tcpdump（如果没有）
apt-get update && apt-get install -y tcpdump

# 抓包到文件
tcpdump -i eth0 -w /tmp/capture.pcap

# 或者实时显示
tcpdump -i eth0 -n 'tcp port 8080'
```

#### 步骤 2：复制 pcap 文件到本机

```bash
# 从容器复制文件
docker cp vpp-master:/tmp/capture.pcap ./capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

### 方案 3：使用 Docker 的 tcpdump（最简单）

```bash
# 直接从容器抓包并保存到本机
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

## 预期看到的流量

### HTTP 流量（主要）

**请求示例：**
```
POST /api/v1/devices/sync HTTP/1.1
Host: vpp-master:8080
Content-Type: application/json
User-Agent: VPP-Phase2-Simulation/1.0

{
  "devices": [
    {
      "id": "gen-001",
      "type": "solar",
      "state": {...},
      "metrics": {...}
    }
  ]
}
```

**响应示例：**
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "sync_id": "sync-12345",
  "timestamp": "2026-02-17T07:03:20Z"
}
```

### 工控协议流量

| 协议 | 端口 | 类型 | 说明 |
|------|------|------|------|
| IEC61850 | 102 | TCP | 电力系统通信 |
| Modbus | 502 | TCP/UDP | 工业设备通信 |
| DNP3 | 20000 | TCP/UDP | 电力系统监控 |
| MQTT | 1883 | TCP | 消息队列 |

---

## Wireshark 过滤器速查表

### 基础过滤

```
# HTTP 流量
http

# HTTPS 流量
ssl or tls

# TCP 流量
tcp

# UDP 流量
udp

# 特定端口
tcp.port == 8080
udp.port == 1883

# 特定 IP
ip.src == 10.0.1.10
ip.dst == 10.0.1.20
```

### 工控协议过滤

```
# IEC61850
tcp.port == 102

# Modbus
tcp.port == 502 or udp.port == 502

# DNP3
tcp.port == 20000 or udp.port == 20000

# MQTT
tcp.port == 1883 or tcp.port == 8883
```

### 组合过滤

```
# HTTP 且来自 vpp-master
http and ip.src == 10.0.1.10

# 所有工控协议
tcp.port == 102 or tcp.port == 502 or tcp.port == 20000 or tcp.port == 1883

# 排除 DNS 和 ARP
not dns and not arp

# 只看 POST 请求
http.request.method == "POST"
```

---

## 实时监控步骤

### 步骤 1：启动 Wireshark

```bash
# 从命令行启动
wireshark &

# 或者从应用菜单打开
```

### 步骤 2：选择网络接口

1. 点击 **Capture → Interfaces**
2. 选择 Docker 网络接口（如 `docker0`）
3. 点击 **Start**

### 步骤 3：应用过滤器

```
# 在 Filter 栏输入
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 步骤 4：观察流量

- 绿色 = TCP SYN
- 蓝色 = TCP 数据
- 红色 = TCP RST/FIN
- 黑色 = TCP ACK

### 步骤 5：分析数据包

1. 双击数据包查看详情
2. 展开 **Hypertext Transfer Protocol** 查看 HTTP 头
3. 查看 **Message Body** 查看 JSON 数据

---

## 常见问题

### Q: 看不到任何流量？

**A:** 检查以下几点：
1. 确认容器正在运行：`docker ps | grep vpp-`
2. 确认选择了正确的网络接口
3. 检查过滤器是否正确
4. 尝试移除过滤器看是否有其他流量

### Q: 只看到 DNS 和 ARP？

**A:** 添加过滤器排除这些：
```
not dns and not arp
```

### Q: 看不到 HTTP 内容？

**A:** 可能是 HTTPS 加密了，尝试：
```
ssl or tls
```

### Q: 如何保存抓包文件？

**A:** 
1. 点击 **File → Export As**
2. 选择格式（pcap, pcapng 等）
3. 保存文件

---

## 高级分析

### 统计流量

1. 点击 **Statistics → Conversations**
2. 查看 IP 对话统计
3. 查看端口使用情况

### 追踪 TCP 流

1. 右键点击数据包
2. 选择 **Follow → TCP Stream**
3. 查看完整的请求/响应

### 导出 HTTP 对象

1. 点击 **File → Export Objects → HTTP**
2. 查看所有 HTTP 请求/响应
3. 导出特定对象

---

## 预期的通信模式

### 每 10 秒一次的同步

```
时间 T+0s:   vpp-phase2 → vpp-master (POST /api/v1/devices/sync)
时间 T+0.1s: vpp-master → vpp-phase2 (HTTP 200 OK)

时间 T+10s:  vpp-phase2 → vpp-master (POST /api/v1/devices/sync)
时间 T+10.1s: vpp-master → vpp-phase2 (HTTP 200 OK)

时间 T+20s:  vpp-phase2 → vpp-master (POST /api/v1/devices/sync)
...
```

### 每 30 秒一次的健康检查

```
时间 T+0s:   vpp-phase2 → vpp-master (GET /api/v1/health)
时间 T+0.05s: vpp-master → vpp-phase2 (HTTP 200 OK)

时间 T+30s:  vpp-phase2 → vpp-master (GET /api/v1/health)
...
```

---

## 工控协议流量验证

### 验证 IEC61850 流量

```bash
# 在 Wireshark 中过滤
tcp.port == 102

# 查看 ACSE 握手
# 查看 ROSE 操作
# 查看 MMS 消息
```

### 验证 Modbus 流量

```bash
# 在 Wireshark 中过滤
tcp.port == 502

# 查看 Modbus 功能码
# 查看寄存器读写
```

### 验证 MQTT 流量

```bash
# 在 Wireshark 中过滤
tcp.port == 1883

# 查看 CONNECT 消息
# 查看 PUBLISH 消息
# 查看 SUBSCRIBE 消息
```

---

## 快速命令参考

```bash
# 启动 Wireshark
wireshark &

# 用 tcpdump 抓包
tcpdump -i docker0 -w capture.pcap

# 用 tcpdump 实时显示
tcpdump -i docker0 -n 'tcp port 8080'

# 从容器抓包
docker exec vpp-master tcpdump -i eth0 -w - > capture.pcap

# 用 tshark（命令行版 Wireshark）
tshark -i docker0 -f 'tcp port 8080'

# 分析 pcap 文件
tshark -r capture.pcap -Y 'http'
```

---

## 总结

✅ **通信确实在发生**
- vpp-phase2-simulation 每 10 秒主动向 vpp-master 发送数据
- 每 30 秒进行一次健康检查
- 支持多种工控协议（IEC61850, Modbus, DNP3, MQTT）

✅ **可以用 Wireshark 抓包**
- 选择 Docker 网络接口
- 应用适当的过滤器
- 观察 HTTP 和工控协议流量

✅ **预期看到的流量**
- HTTP POST 请求（设备同步）
- HTTP GET 请求（健康检查）
- 工控协议数据包（IEC61850, Modbus 等）

---

**建议**：先用方案 3（Docker tcpdump）快速验证，然后用 Wireshark 进行详细分析。
