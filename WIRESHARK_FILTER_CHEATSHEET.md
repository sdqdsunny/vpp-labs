# Wireshark 过滤器速查表 - 一页纸版本

## 🎯 最常用的 3 个过滤器

### 1️⃣ 抓所有业务流量（推荐）
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```
**看到什么**: vpp-master、vpp-vcc、vpp-upf 之间的 HTTP 通信

---

### 2️⃣ 只抓 vpp-master 的流量
```
tcp.port == 8080
```
**看到什么**: 每 10 秒一次的 POST 请求，每 30 秒一次的 GET 请求

---

### 3️⃣ 抓工控协议流量
```
tcp.port == 102 or tcp.port == 502 or tcp.port == 20000 or tcp.port == 1883
```
**看到什么**: IEC61850、Modbus、DNP3、MQTT 协议数据

---

## 📋 完整过滤器列表

### 按服务分类

| 服务 | 过滤器 | 端口 |
|------|--------|------|
| vpp-master | `tcp.port == 8080` | 8080 |
| vpp-vcc | `tcp.port == 8081` | 8081 |
| vpp-upf | `tcp.port == 8082` | 8082 |
| 所有业务 | `tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082` | 8080-8082 |

### 按协议分类

| 协议 | 过滤器 | 端口 |
|------|--------|------|
| IEC61850 | `tcp.port == 102` | 102 |
| Modbus | `tcp.port == 502` | 502 |
| DNP3 | `tcp.port == 20000` | 20000 |
| MQTT | `tcp.port == 1883` | 1883 |
| 所有工控 | `tcp.port == 102 or tcp.port == 502 or tcp.port == 20000 or tcp.port == 1883` | 多个 |

### 按 HTTP 方法分类

| 方法 | 过滤器 |
|------|--------|
| POST 请求 | `http.request.method == "POST"` |
| GET 请求 | `http.request.method == "GET"` |
| 所有 HTTP | `http` |

### 按 IP 地址分类

| 服务 | 过滤器 | IP 地址 |
|------|--------|---------|
| vpp-master | `ip.src == 10.0.1.10 or ip.dst == 10.0.1.10` | 10.0.1.10 |
| vpp-vcc | `ip.src == 10.0.1.20 or ip.dst == 10.0.1.20` | 10.0.1.20 |
| vpp-upf | `ip.src == 10.0.1.30 or ip.dst == 10.0.1.30` | 10.0.1.30 |
| vpp-gen | `ip.src == 10.0.1.40 or ip.dst == 10.0.1.40` | 10.0.1.40 |
| vpp-analyzer | `ip.src == 10.0.1.50 or ip.dst == 10.0.1.50` | 10.0.1.50 |

---

## 🔧 组合过滤器（高级用法）

### 排除系统流量
```
not dns and not arp
```

### 只看 HTTP 且来自 vpp-master
```
http and ip.src == 10.0.1.10
```

### 只看 POST 请求且来自 vpp-phase2-simulation
```
http.request.method == "POST" and tcp.port == 8080
```

### 看所有业务流量但排除 DNS
```
(tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082) and not dns
```

### 看工控协议但排除 MQTT
```
(tcp.port == 102 or tcp.port == 502 or tcp.port == 20000) and not tcp.port == 1883
```

---

## 📊 预期看到的流量模式

### 每 10 秒一次（设备同步）
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
```

### 每 30 秒一次（健康检查）
```
GET /api/v1/health HTTP/1.1
Host: vpp-master:8080

HTTP/1.1 200 OK
{
  "status": "healthy",
  "uptime": 300
}
```

---

## 🎨 数据包颜色含义

| 颜色 | 含义 | 说明 |
|------|------|------|
| 🟢 绿色 | TCP SYN | 连接建立 |
| 🔵 蓝色 | TCP 数据 | HTTP 请求/响应 |
| 🔴 红色 | TCP RST/FIN | 连接关闭 |
| ⚫ 黑色 | TCP ACK | 确认 |

---

## ⚡ 快速使用步骤

### 步骤 1：打开 Wireshark
```bash
wireshark &
```

### 步骤 2：选择网络接口
- 点击 **Capture → Interfaces**
- 选择 `docker0` 或 `br-` 开头的接口
- 点击 **Start**

### 步骤 3：在 Filter 栏输入过滤器
```
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082
```

### 步骤 4：按 Enter 应用过滤器

### 步骤 5：观察流量
- 每 10 秒看到一个 POST 请求
- 每 30 秒看到一个 GET 请求

---

## 🔍 分析数据包

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

## 🛠️ 命令行方法

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

## ❓ 故障排查

| 问题 | 解决方案 |
|------|--------|
| 看不到流量 | 检查容器是否运行: `docker ps \| grep vpp-` |
| 看不到 HTTP | 检查过滤器是否正确 |
| 看不到工控协议 | 检查端口号 (102, 502, 20000, 1883) |
| 只看到 DNS/ARP | 添加过滤器: `not dns and not arp` |
| 无法连接到容器 | 检查网络: `docker network inspect network-mirror_vpp-net` |

---

## 📌 记住这 3 个过滤器就够了

```
# 1. 所有业务流量
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082

# 2. 只看 vpp-master
tcp.port == 8080

# 3. 工控协议
tcp.port == 102 or tcp.port == 502 or tcp.port == 20000 or tcp.port == 1883
```

---

**提示**: 复制上面的过滤器，粘贴到 Wireshark 的 Filter 栏，按 Enter 即可！

