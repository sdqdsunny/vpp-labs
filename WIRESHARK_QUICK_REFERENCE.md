# Wireshark 快速参考卡

## 一句话总结

✅ **通信正在发生** - vpp-phase2-simulation 每 10 秒向 vpp-master 发送 HTTP 请求，包含工控协议数据

---

## 最快的抓包方法（3 步）

### 步骤 1：打开 Wireshark
```bash
wireshark &
```

### 步骤 2：选择网络接口
- 点击 **Capture → Interfaces**
- 选择 `docker0` 或 `br-` 开头的接口
- 点击 **Start**

### 步骤 3：应用过滤器
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

**结果**: 你会看到每 10 秒一次的 HTTP POST 请求

---

## 常用过滤器

| 用途 | 过滤器 |
|------|--------|
| 所有 HTTP | `http` |
| vpp-master 流量 | `tcp.port == 8080` |
| vpp-vcc 流量 | `tcp.port == 8081` |
| vpp-upf 流量 | `tcp.port == 8082` |
| 所有业务流量 | `tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082` |
| IEC61850 | `tcp.port == 102` |
| Modbus | `tcp.port == 502` |
| DNP3 | `tcp.port == 20000` |
| MQTT | `tcp.port == 1883` |
| 排除系统流量 | `not dns and not arp` |
| POST 请求 | `http.request.method == "POST"` |
| GET 请求 | `http.request.method == "GET"` |

---

## 命令行方法

### 用 tcpdump 抓包

```bash
# 实时显示
tcpdump -i docker0 -n 'tcp port 8080' -A

# 保存到文件
tcpdump -i docker0 -w capture.pcap 'tcp port 8080'

# 从容器内部抓包
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap
```

### 用 tshark（命令行 Wireshark）

```bash
# 实时显示 HTTP 流量
tshark -i docker0 -f 'tcp port 8080' -Y 'http'

# 保存并分析
tshark -i docker0 -w capture.pcap -f 'tcp port 8080'
tshark -r capture.pcap -Y 'http' -T json > analysis.json
```

---

## 预期看到的流量

### 每 10 秒一次

```
POST /api/v1/devices/sync HTTP/1.1
Host: vpp-master:8080
Content-Type: application/json

{
  "devices": [
    {"id": "gen-001", "type": "solar", "state": {...}},
    {"id": "storage-001", "type": "battery", "state": {...}},
    {"id": "load-001", "type": "demand", "state": {...}}
  ]
}

HTTP/1.1 200 OK
{
  "status": "success",
  "sync_id": "sync-...",
  "devices_processed": 3
}
```

### 每 30 秒一次

```
GET /health HTTP/1.1
Host: vpp-master:8080

HTTP/1.1 200 OK
{
  "status": "healthy",
  "uptime": 300
}
```

---

## 数据包颜色含义

| 颜色 | 含义 |
|------|------|
| 🟢 绿色 | TCP SYN (连接建立) |
| 🔵 蓝色 | TCP 数据 (HTTP 请求/响应) |
| 🔴 红色 | TCP RST/FIN (连接关闭) |
| ⚫ 黑色 | TCP ACK (确认) |

---

## 分析数据包

### 查看 HTTP 内容

1. 双击数据包
2. 展开 **Hypertext Transfer Protocol**
3. 查看 **Request Method**, **Request URI**, **Message Body**

### 追踪完整对话

1. 右键点击数据包
2. 选择 **Follow → TCP Stream**
3. 查看完整的请求/响应

### 导出数据

1. 点击 **File → Export Objects → HTTP**
2. 选择要导出的对象
3. 保存到本地

---

## 故障排查

| 问题 | 解决方案 |
|------|--------|
| 看不到流量 | 检查容器是否运行: `docker ps \| grep vpp-` |
| 看不到 HTTP | 检查过滤器是否正确 |
| 看不到工控协议 | 检查端口号 (102, 502, 20000, 1883) |
| 只看到 DNS/ARP | 添加过滤器: `not dns and not arp` |
| 无法连接到容器 | 检查网络: `docker network inspect network-mirror_vpp-net` |

---

## 工控协议识别

### IEC61850 (端口 102)
- 特征: ACSE 握手, ROSE 操作, MMS 消息
- 用途: 电力系统通信
- 过滤: `tcp.port == 102`

### Modbus (端口 502)
- 特征: 功能码, 寄存器读写
- 用途: 工业设备通信
- 过滤: `tcp.port == 502`

### DNP3 (端口 20000)
- 特征: 链路层帧, 传输层段
- 用途: 电力系统监控
- 过滤: `tcp.port == 20000`

### MQTT (端口 1883)
- 特征: CONNECT, PUBLISH, SUBSCRIBE
- 用途: 消息队列
- 过滤: `tcp.port == 1883`

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 连接延迟 | < 1ms |
| 请求延迟 | < 10ms |
| 响应延迟 | < 50ms |
| 总 RTT | < 100ms |
| 每次请求大小 | ~500-1000 字节 |
| 每次响应大小 | ~200-500 字节 |
| 每小时流量 | ~360-720 KB |

---

## 快速命令

```bash
# 验证通信
bash verify_communication.sh

# 抓包到文件
docker exec vpp-master tcpdump -i eth0 -w - > capture.pcap

# 打开抓包文件
open capture.pcap

# 实时监控
tcpdump -i docker0 -n 'tcp port 8080' -A

# 查看容器日志
docker logs vpp-master -f
docker logs vpp-phase2-simulation -f

# 检查网络
docker network inspect network-mirror_vpp-net
```

---

## 关键端口

| 服务 | 端口 | 协议 |
|------|------|------|
| vpp-master | 8080 | HTTP |
| vpp-vcc | 8081 | HTTP |
| vpp-upf | 8082 | HTTP |
| IEC61850 | 102 | TCP |
| Modbus | 502 | TCP/UDP |
| DNP3 | 20000 | TCP/UDP |
| MQTT | 1883 | TCP |

---

## 关键 IP 地址

| 服务 | IP 地址 |
|------|---------|
| vpp-master | 10.0.1.10 |
| vpp-vcc | 10.0.1.20 |
| vpp-upf | 10.0.1.30 |
| vpp-gen | 10.0.1.40 |
| vpp-analyzer | 10.0.1.50 |

---

## 下一步

1. ✅ 打开 Wireshark
2. ✅ 选择 docker0 接口
3. ✅ 应用过滤器: `tcp.port == 8080`
4. ✅ 观察每 10 秒一次的 HTTP POST 请求
5. ✅ 分析 JSON 数据中的工控协议内容

---

**提示**: 如果看不到流量，运行 `bash verify_communication.sh` 进行诊断。
