# macOS 上 Wireshark 无法抓到 Docker 容器流量 - 完整解决方案

## 问题诊断

### 为什么 bridge0 看不到流量？

在 macOS Docker Desktop 上：
- **bridge0** = Thunderbolt Bridge（物理网络接口）
- **Docker 容器流量** = 在 Docker Desktop VM 内部隔离
- **结果** = Wireshark 在 macOS 主机上无法看到容器间的流量

---

## ✅ 解决方案 1：从容器内部抓包（最简单）

### 步骤 1：进入容器并安装 tcpdump

```bash
# 进入 vpp-master 容器
docker exec -it vpp-master bash

# 安装 tcpdump
apt-get update && apt-get install -y tcpdump

# 抓包 10 个数据包
tcpdump -i eth0 -c 10 'tcp port 8080'

# 或者保存到文件
tcpdump -i eth0 -w /tmp/capture.pcap 'tcp port 8080'
```

### 步骤 2：复制 pcap 文件到本机

```bash
# 从容器复制文件
docker cp vpp-master:/tmp/capture.pcap ./capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

## ✅ 解决方案 2：使用 Docker 的 tcpdump（无需进入容器）

```bash
# 直接从容器抓包并保存到本机
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap

# 用 Wireshark 打开
open capture.pcap
```

---

## ✅ 解决方案 3：使用 tshark（命令行 Wireshark）

### 从容器内部运行 tshark

```bash
# 进入容器
docker exec -it vpp-master bash

# 安装 tshark
apt-get update && apt-get install -y tshark

# 实时显示 HTTP 流量
tshark -i eth0 -f 'tcp port 8080' -Y 'http'

# 或者保存到文件
tshark -i eth0 -w /tmp/capture.pcap -f 'tcp port 8080'
```

---

## ✅ 解决方案 4：使用 Python 脚本抓包

### 创建 Python 抓包脚本

```python
# capture.py
import socket
import struct
import textwrap

def format_ipv4(bytes):
    bytes_str = map('{:02x}'.format, bytes)
    bytes_str = ''.join(bytes_str)
    bytes_str = textwrap.wrap(bytes_str, 2)
    return '.'.join(map(str, [int(bytes_str[i], 16) for i in range(0, 4)]))

def format_multi_line(ident, bytes, size):
    lines = [bytes[i:i+size].hex(' ') for i in range(0, len(bytes), size)]
    return ('\n' + ' ' * ident).join(lines)

def format_icmpv4_packet(data):
    destination_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
    return format_mac_addr(destination_mac), format_mac_addr(src_mac), proto, data[14:]

sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_TCP)
sock.bind(('eth0', 0))

print("正在监听 eth0 接口...")
try:
    for i in range(20):
        raw_data, addr = sock.recvfrom(65535)
        print(f"\n数据包 {i+1}: {len(raw_data)} 字节")
        print(f"源地址: {addr[4]}")
except KeyboardInterrupt:
    print("\n停止监听")
```

### 运行脚本

```bash
# 在容器内运行
docker exec vpp-master python3 -c "
import socket
sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.IPPROTO_TCP)
sock.bind(('eth0', 0))
sock.settimeout(10)
print('监听中...')
try:
    for i in range(10):
        data, addr = sock.recvfrom(65535)
        print(f'数据包 {i+1}: {len(data)} 字节')
except:
    pass
"
```

---

## 🔍 验证通信是否真的在发生

### 方法 1：检查容器日志

```bash
# 查看 vpp-master 的请求日志
docker logs vpp-master -f --tail 20

# 查看 vpp-phase2-simulation 的请求日志
docker logs vpp-phase2-simulation -f --tail 20
```

### 方法 2：进入容器并测试连接

```bash
# 进入 vpp-phase2-simulation 容器
docker exec -it vpp-phase2-simulation bash

# 测试是否能连接到 vpp-master
curl -v http://vpp-master:8080/health

# 或者用 nc 测试端口
nc -zv vpp-master 8080
```

### 方法 3：检查 Docker 网络

```bash
# 查看 Docker 网络
docker network ls

# 检查网络中的容器
docker network inspect network-mirror_vpp-net

# 或者检查 vpp-phase2-simulation 的网络
docker network inspect vpp-network
```

---

## ⚠️ 重要发现：两个独立的 Docker Compose 项目

### 问题
- **vpp-phase2-simulation** 在 `vpp-network` 网络中
- **network-mirror** (vpp-master, vpp-vcc, vpp-upf, vpp-gen) 在 `network-mirror_vpp-net` 网络中
- **它们不在同一个网络中！**

### 解决方案

#### 选项 A：将 vpp-phase2-simulation 连接到 network-mirror 网络

```bash
# 停止 vpp-phase2-simulation
docker-compose -f vpp-phase2-simulation/docker-compose.yml down

# 修改 vpp-phase2-simulation/docker-compose.yml
# 将 networks 改为：
# networks:
#   - network-mirror_vpp-net

# 重新启动
docker-compose -f vpp-phase2-simulation/docker-compose.yml up -d
```

#### 选项 B：修改 vpp-phase2-simulation 的环境变量

```bash
# 停止容器
docker stop vpp-phase2-simulation

# 重新启动时设置 VPP_MASTER_URL
docker run -d \
  --name vpp-phase2-simulation \
  -e VPP_MASTER_URL=http://vpp-master:8080 \
  -p 8080:8080 \
  -p 8081:8081 \
  vpp-phase2-simulation:latest
```

#### 选项 C：使用 Docker 的 --link 或 host 网络

```bash
# 使用 host 网络（不推荐，安全风险）
docker run -d \
  --network host \
  --name vpp-phase2-simulation \
  vpp-phase2-simulation:latest
```

---

## 📊 预期看到的流量

### 如果通信正常

```
vpp-phase2-simulation → vpp-master:8080
POST /api/v1/devices/sync HTTP/1.1
Content-Type: application/json

{
  "devices": [...]
}

HTTP/1.1 200 OK
```

### 如果通信失败

```
vpp-phase2-simulation → localhost:8080 (自己)
GET /health HTTP/1.1

HTTP/1.1 200 OK
```

---

## 🛠️ 快速诊断命令

```bash
# 1. 检查容器是否运行
docker ps | grep vpp-

# 2. 检查容器网络
docker inspect vpp-master | grep -A 10 NetworkSettings

# 3. 进入容器测试连接
docker exec vpp-phase2-simulation curl -v http://vpp-master:8080/health

# 4. 查看容器日志
docker logs vpp-master | tail -20
docker logs vpp-phase2-simulation | tail -20

# 5. 检查 Docker 网络
docker network ls
docker network inspect network-mirror_vpp-net
docker network inspect vpp-network

# 6. 从容器抓包
docker exec vpp-master tcpdump -i eth0 -c 5 'tcp port 8080'
```

---

## 📝 总结

### 为什么 Wireshark 在 macOS 上看不到 Docker 容器流量？
- macOS Docker Desktop 在虚拟机中运行 Docker
- 容器流量在虚拟机内部隔离
- Wireshark 在主机上无法访问虚拟机内部的网络接口

### 解决方案
1. **从容器内部抓包**（推荐）
2. **使用命令行工具**（tcpdump, tshark）
3. **检查容器日志**（最快）
4. **测试容器连接**（curl, nc）

### 当前问题
- vpp-phase2-simulation 和 network-mirror 在不同的 Docker 网络中
- 需要将它们连接到同一个网络，或者配置正确的 VPP_MASTER_URL

---

**建议下一步**：
1. 检查两个 Docker Compose 项目是否在同一个网络中
2. 如果不在，修改配置使它们在同一个网络中
3. 然后从容器内部抓包验证通信

