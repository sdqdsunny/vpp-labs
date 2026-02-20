# Wireshark 抓包 - 最终解决方案

## 🎯 问题总结

### 为什么 Wireshark 在 macOS 上看不到 Docker 容器流量？

1. **macOS Docker Desktop 限制**
   - Docker 在虚拟机中运行
   - 容器流量在虚拟机内部隔离
   - Wireshark 在主机上无法访问虚拟机内部的网络接口

2. **bridge0 不是 Docker 网络**
   - bridge0 = Thunderbolt Bridge（物理网络接口）
   - Docker 容器流量 = 在虚拟机内部
   - 结果 = Wireshark 看不到容器流量

---

## ✅ 解决方案：从容器内部抓包

### 最简单的方法（3 步）

#### 步骤 1：进入容器并安装 tcpdump

```bash
docker exec -it vpp-master bash
apt-get update && apt-get install -y tcpdump
```

#### 步骤 2：抓包

```bash
# 方法 A：实时显示
tcpdump -i eth0 -n 'tcp port 8080'

# 方法 B：保存到文件
tcpdump -i eth0 -w /tmp/capture.pcap 'tcp port 8080'
```

#### 步骤 3：复制到本机并用 Wireshark 打开

```bash
# 从容器复制文件
docker cp vpp-master:/tmp/capture.pcap ./capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

## ⚡ 更快的方法（一行命令）

```bash
# 直接从容器抓包到本机
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

## 📊 预期看到的流量

### 如果通信正常

```
Source: 10.0.1.X (vpp-phase2-simulation)
Destination: 10.0.1.10 (vpp-master)
Protocol: HTTP
Port: 8080

POST /api/v1/devices/sync HTTP/1.1
Host: vpp-master:8080
Content-Type: application/json

{
  "devices": [...]
}

HTTP/1.1 200 OK
```

### 过滤器

```
# 只看 HTTP 流量
http

# 只看特定端口
tcp.port == 8080

# 只看 POST 请求
http.request.method == "POST"

# 只看来自特定 IP
ip.src == 10.0.1.10
```

---

## 🔧 其他抓包方法

### 方法 1：使用 tshark（命令行 Wireshark）

```bash
# 进入容器
docker exec -it vpp-master bash

# 安装 tshark
apt-get update && apt-get install -y tshark

# 实时显示 HTTP 流量
tshark -i eth0 -f 'tcp port 8080' -Y 'http'

# 保存到文件
tshark -i eth0 -w /tmp/capture.pcap -f 'tcp port 8080'
```

### 方法 2：使用 Docker 的 tcpdump（无需进入容器）

```bash
# 直接从容器抓包
docker exec vpp-master tcpdump -i eth0 -c 20 'tcp port 8080'

# 保存到文件
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap
```

### 方法 3：使用 Python 脚本

```bash
# 进入容器
docker exec -it vpp-master bash

# 运行 Python 脚本
python3 << 'EOF'
import socket
import struct

sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_TCP)
sock.bind(('eth0', 0))
sock.settimeout(10)

print("监听 eth0 接口...")
try:
    for i in range(20):
        data, addr = sock.recvfrom(65535)
        print(f"数据包 {i+1}: {len(data)} 字节")
except:
    pass
EOF
```

---

## 🛠️ 快速命令参考

```bash
# 1. 最快的方法 - 一行命令抓包
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap && open capture.pcap

# 2. 进入容器手动抓包
docker exec -it vpp-master bash
apt-get update && apt-get install -y tcpdump
tcpdump -i eth0 -n 'tcp port 8080'

# 3. 查看容器日志
docker logs vpp-master -f --tail 50
docker logs vpp-phase2-simulation -f --tail 50

# 4. 测试容器连接
docker exec vpp-phase2-simulation curl -v http://vpp-master:8080/health

# 5. 检查 Docker 网络
docker network inspect network-mirror_vpp-net

# 6. 进入容器测试 DNS
docker exec -it vpp-master bash
nslookup vpp-phase2-simulation
ping vpp-phase2-simulation
```

---

## 📝 完整工作流

### 1. 连接两个 Docker 网络（已完成）

```bash
docker network connect network-mirror_vpp-net vpp-phase2-simulation
docker network connect network-mirror_vpp-net vpp-postgres
docker network connect network-mirror_vpp-net vpp-redis
```

### 2. 验证网络连接

```bash
# 检查网络中的容器
docker network inspect network-mirror_vpp-net | grep -A 100 "Containers"

# 应该看到 vpp-phase2-simulation, vpp-postgres, vpp-redis
```

### 3. 测试容器间通信

```bash
# 进入 vpp-phase2-simulation 容器
docker exec -it vpp-phase2-simulation bash

# 测试 DNS 解析
nslookup vpp-master

# 测试 HTTP 连接
curl -v http://vpp-master:8080/health
```

### 4. 从容器内部抓包

```bash
# 进入 vpp-master 容器
docker exec -it vpp-master bash

# 安装 tcpdump
apt-get update && apt-get install -y tcpdump

# 抓包
tcpdump -i eth0 -w /tmp/capture.pcap 'tcp port 8080'

# 等待几秒钟...
# Ctrl+C 停止

# 复制到本机
docker cp vpp-master:/tmp/capture.pcap ./capture.pcap
```

### 5. 用 Wireshark 打开

```bash
open capture.pcap
```

---

## 🎨 Wireshark 过滤器

### 基础过滤

| 用途 | 过滤器 |
|------|--------|
| 所有 HTTP | `http` |
| 特定端口 | `tcp.port == 8080` |
| 特定 IP | `ip.src == 10.0.1.10` |
| POST 请求 | `http.request.method == "POST"` |
| GET 请求 | `http.request.method == "GET"` |

### 组合过滤

```
# HTTP 且来自 vpp-master
http and ip.src == 10.0.1.10

# 所有业务流量
tcp.port == 8080 or tcp.port == 8081 or tcp.port == 8082

# 排除系统流量
not dns and not arp
```

---

## ⚠️ 常见问题

### Q: 看不到任何流量？

**A:** 检查以下几点：
1. 容器是否运行：`docker ps | grep vpp-`
2. 网络是否连接：`docker network inspect network-mirror_vpp-net`
3. 通信是否发生：`docker logs vpp-phase2-simulation -f`
4. 过滤器是否正确：尝试移除过滤器

### Q: 看不到 HTTP 内容？

**A:** 可能是 HTTPS 加密了，尝试：
```
ssl or tls
```

### Q: 只看到 DNS 和 ARP？

**A:** 添加过滤器排除这些：
```
not dns and not arp
```

### Q: 如何保存抓包文件？

**A:** 在 Wireshark 中：
1. 点击 **File → Export As**
2. 选择格式（pcap, pcapng 等）
3. 保存文件

---

## 📌 关键要点

1. **macOS 上 Wireshark 无法直接抓 Docker 容器流量**
   - 原因：Docker 在虚拟机中运行，容器流量隔离
   - 解决：从容器内部抓包

2. **最快的方法**
   ```bash
   docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap && open capture.pcap
   ```

3. **两个 Docker 网络已连接**
   - vpp-phase2-simulation 现在可以访问 vpp-master
   - 容器间通信应该正常工作

4. **预期看到的流量**
   - HTTP POST 请求（设备同步）
   - HTTP GET 请求（健康检查）
   - 工控协议数据（IEC61850, Modbus 等）

---

## 🚀 下一步

1. ✅ 从容器内部抓包
2. ✅ 用 Wireshark 打开 pcap 文件
3. ✅ 分析 HTTP 流量
4. ✅ 查看工控协议数据
5. ✅ 验证通信是否正常

---

**现在就试试吧！**

```bash
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap && open capture.pcap
```

